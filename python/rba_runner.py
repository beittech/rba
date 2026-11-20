"""Host-side helper for programs built with the RBA framework.

Run it with the Cerebras SDK's Python (``cs_python``), which provides ``cerebras.sdk``.
"""

import json
import os
from abc import abstractmethod
from typing import Any, Dict, Optional, Tuple

import numpy as np
from cerebras.sdk.runtime.sdkruntimepybind import MemcpyDataType, MemcpyOrder, SdkRuntime

__all__ = ["RBARunner"]


class RBARunner:
    """Base class for runners of programs constructed using the RBA framework.

    `path` is the output directory of `cslc` (the one containing `out.json`).
    Subclasses implement `dimensions()` and call `run(spreader=..., num_iterations=...)`.
    """

    def __init__(self, path: str, cmaddr: Optional[str] = None, suppress_simfab_trace: bool = True):
        with open(os.path.join(path, "out.json")) as f:
            self.compile_data = json.load(f)
        kwargs: Dict[str, Any] = {"suppress_simfab_trace": suppress_simfab_trace}
        if cmaddr:
            kwargs["cmaddr"] = cmaddr
        self.runner = SdkRuntime(path, **kwargs)
        self.num_tasks = int(self.compile_data["params"]["num_tasks"])
        self.height, self.width = self.dimensions()

    @abstractmethod
    def dimensions(self) -> Tuple[int, int]:
        """Deduce (height, width) of the PE grid, most likely from the compilation params."""
        raise NotImplementedError

    def h2d_stream(self, index: int = 1) -> int:
        """Color ID of the `index`-th (1-based) host-to-device stream, as passed to `cslc`."""
        return int(self.compile_data["params"][f"MEMCPYH2D_DATA_{index}_ID"])

    def run(self, *args, **kwargs):
        self.runner.load()
        self.runner.run()
        result = self.interaction(*args, **kwargs)
        self.runner.stop()
        return result

    def interaction(self, spreader, num_iterations: int = 1):
        """One call to `compute` after uploading the initial state produced by `spreader`."""
        self.construct_initial_state(spreader)
        self.upload_all()
        if num_iterations:
            self.runner.launch("compute", num_iterations, nonblock=False)
        return self.download_global(), self.download_local()

    def construct_initial_state(self, spreader):
        self.shared_global_state = np.array(spreader.construct_shared_global_state(), dtype=np.float32)
        self.task_global_state = np.array(
            [spreader.construct_task_global_state(t) for t in range(self.num_tasks)], dtype=np.float32)
        self.shared_local_state = np.array(
            [[spreader.construct_shared_local_state(x, y) for x in range(self.width)] for y in range(self.height)],
            dtype=np.float32)
        self.task_local_state = np.array(
            [[[spreader.construct_task_local_state(t, x, y) for t in range(self.num_tasks)]
              for x in range(self.width)] for y in range(self.height)],
            dtype=np.float32)

    _MEMCPY_KWARGS = {
        "order": MemcpyOrder.ROW_MAJOR,
        "data_type": MemcpyDataType.MEMCPY_32BIT,
        "nonblock": False,
    }

    def upload_all(self):
        global_loc = self.width, self.height, 1, 1
        local_loc = 0, 0, self.width, self.height
        kw = self._MEMCPY_KWARGS
        r = self.runner
        r.memcpy_h2d(r.get_id("shared_state"), self.shared_global_state.reshape(-1), *global_loc,
                     self.shared_global_state.shape[0], streaming=False, **kw)
        r.memcpy_h2d(r.get_id("task_state"), self.task_global_state.reshape(-1), *global_loc,
                     self.task_global_state.shape[0] * self.task_global_state.shape[1], streaming=False, **kw)
        r.memcpy_h2d(self.h2d_stream(1), self.shared_local_state.reshape(-1), *local_loc,
                     self.shared_local_state.shape[2], streaming=True, **kw)
        r.memcpy_h2d(r.get_id("task_state"), self.task_local_state.reshape(-1), *local_loc,
                     self.task_local_state.shape[2] * self.task_local_state.shape[3], streaming=False, **kw)

    def download_global(self):
        global_loc = self.width, self.height, 1, 1
        kw = self._MEMCPY_KWARGS
        r = self.runner
        r.memcpy_d2h(self.task_global_state.reshape(-1), r.get_id("task_state"), *global_loc,
                     self.task_global_state.shape[0] * self.task_global_state.shape[1], streaming=False, **kw)
        return self.task_global_state

    def download_local(self):
        local_loc = 0, 0, self.width, self.height
        self.runner.memcpy_d2h(self.task_local_state.reshape(-1), self.runner.get_id("task_state"), *local_loc,
                               self.task_local_state.shape[2] * self.task_local_state.shape[3],
                               streaming=False, **self._MEMCPY_KWARGS)
        return self.task_local_state

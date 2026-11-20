import struct

import numpy as np

from problem import Problem


def _bitcast_u32_to_f32(x: int) -> float:
    return struct.unpack('<f', struct.pack('<I', x))[0]


class ProblemSpreader:
    """
    Constructs arrays of initial state relevant to the problem provided, consistent with serializations defined in `rba_ops.csl`.
    """

    def __init__(self, p: Problem, patch_width: int, patch_height: int):
        self.p = p
        self.patch_width = patch_width
        self.patch_height = patch_height

    def construct_shared_global_state(self):
        return np.array([self.p.offset], dtype=np.float32)

    def construct_task_global_state(self, t: int):
        return np.array([_bitcast_u32_to_f32((t + 1) * 100)], dtype=np.float32)

    def construct_shared_local_state(self, x: int, y: int):
        patch_size = self.patch_width * self.patch_height
        x = x // self.patch_width
        y = y // self.patch_height
        return np.array((self.p.coeff[x, y] / patch_size, x, y), dtype=np.float32)

    def construct_task_local_state(self, t: int, x: int, y: int):
        return np.array([0, 0.5, 0, 1, 0, 1], dtype=np.float32)

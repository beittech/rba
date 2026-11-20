import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "python"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from problem import random_problem
from spreader import ProblemSpreader
from rba_runner import RBARunner


BUILD_DIR = os.environ.get("RBA_BUILD_DIR", "build")


class QFIsosurfaceRunner(RBARunner):
    def __init__(self, name: str = 'main'):
        super().__init__(path=os.path.join(BUILD_DIR, name))

    def dimensions(self):
        side_length = int(self.compile_data['params']['size'])
        patch_width = int(self.compile_data['params']['patch_width'])
        patch_height = int(self.compile_data['params']['patch_height'])
        return (side_length * patch_height, side_length * patch_width)

    def run(self, *args, **kwargs):
        task_global_state, task_local_state = super().run(*args, num_iterations=5, **kwargs)

        # Just print some result interpretation:

        patch_width = int(self.compile_data['params']['patch_width'])
        xs = np.average(task_local_state[0, :, :, 2:4], axis=2).T[:, ::patch_width]
        return xs


class QFIsosurfaceTest(unittest.TestCase):
    @staticmethod
    def _test_impl(name: str):
        runner = QFIsosurfaceRunner(name)
        problem = random_problem(int(runner.compile_data['params']['size']))
        ps = ProblemSpreader(problem, int(runner.compile_data['params']['patch_width']), int(runner.compile_data['params']['patch_height']))
        xs = runner.run(spreader=ps)

        print('Vectors:\n', xs)

        # Computing values of quadratic form `problem.coeff` for a bunch of vectors `xs` at once:
        values = np.einsum('ti,ij,tj->t', xs, problem.coeff, xs)
        print('Evaluate to values:', values)
        print('Expected to converge to:', problem.offset)

        np.testing.assert_allclose(values, problem.offset, rtol=0.10, atol=0.02)

    def test(self):
        # The variant (built with `build.sh PAD_X PAD_Y`) is chosen with RBA_VARIANT, e.g. iso_pad2x0.
        # Only one simulation fits in a process, hence one variant per invocation.
        self._test_impl(os.environ.get("RBA_VARIANT", "iso"))


if __name__ == '__main__':
    # Only one simulation fits in a process: run a single test per invocation, e.g.
    #   python run.py QFIsosurfaceTest.test
    unittest.main()

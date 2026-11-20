from dataclasses import dataclass

import numpy as np

@dataclass
class Problem:
    coeff: np.ndarray
    offset: float


def random_problem(size: int) -> Problem:
    np.random.seed(44)
    coeff = 2 * np.random.rand(size, size) - 1

    one = np.ones(size)
    maxi = one @ coeff @ one
    if maxi < 0:
        coeff = -coeff
        maxi = -maxi
    offset = np.random.random() * maxi  # arbitrary value in (0; maxi)

    return Problem(coeff=coeff, offset=offset)

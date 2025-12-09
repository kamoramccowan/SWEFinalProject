import random
from typing import List


def shuffle_grid(grid: List[List[str]]) -> List[List[str]]:
    """
    Randomly permute the multiset of letters across the grid cells.
    Preserves shape and letters; returns a new grid.
    """
    if not grid:
        return grid
    rows = len(grid)
    cols = len(grid[0])
    flat = [cell for row in grid for cell in row]
    random.shuffle(flat)
    return [flat[i * cols:(i + 1) * cols] for i in range(rows)]


def rotate_grid(grid: List[List[str]], direction: str = "clockwise", angle: int = 90) -> List[List[str]]:
    """
    Rotate a square grid in 90-degree increments. Supports clockwise and counterclockwise.
    Angle must be a multiple of 90.
    """
    if not grid:
        return grid
    n = len(grid)
    if any(len(row) != n for row in grid):
        raise ValueError("Grid must be square to rotate.")

    if angle % 90 != 0:
        raise ValueError("Angle must be a multiple of 90.")

    steps = (angle // 90) % 4
    if direction == "counterclockwise":
        steps = (4 - steps) % 4

    result = grid
    for _ in range(steps):
        result = [[result[n - j - 1][i] for j in range(n)] for i in range(n)]
    return result

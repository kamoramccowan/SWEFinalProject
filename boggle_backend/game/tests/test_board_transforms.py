from django.test import SimpleTestCase

from game.board_transforms import rotate_grid, shuffle_grid


class BoardTransformsTests(SimpleTestCase):
    def test_rotate_clockwise(self):
        grid = [
            ["A", "B"],
            ["C", "D"],
        ]
        rotated = rotate_grid(grid, "clockwise")
        self.assertEqual(rotated, [["C", "A"], ["D", "B"]])

    def test_shuffle_preserves_multiset(self):
        grid = [
            ["A", "B"],
            ["C", "D"],
        ]
        shuffled = shuffle_grid(grid)
        flat_original = sorted([c for row in grid for c in row])
        flat_shuffled = sorted([c for row in shuffled for c in row])
        self.assertEqual(flat_original, flat_shuffled)

    def test_rotate_180(self):
        grid = [
            ["A", "B"],
            ["C", "D"],
        ]
        rotated = rotate_grid(grid, angle=180)
        self.assertEqual(rotated, [["D", "C"], ["B", "A"]])

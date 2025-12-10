from django.test import SimpleTestCase

from game.boggle_engine import is_word_on_board, score_word


class BoggleEngineTests(SimpleTestCase):
    def test_is_word_on_board_simple(self):
        grid = [
            ["C", "A", "T"],
            ["D", "O", "G"],
            ["X", "Y", "Z"],
        ]
        self.assertTrue(is_word_on_board(grid, "CAT"))
        self.assertTrue(is_word_on_board(grid, "DOG"))
        self.assertFalse(is_word_on_board(grid, "CATS"))

    def test_is_word_on_board_case_insensitive(self):
        grid = [["Qu", "A"], ["B", "C"]]
        self.assertTrue(is_word_on_board(grid, "quac".upper()))  # QU + A + C
        self.assertTrue(is_word_on_board(grid, "quac"))

    def test_score_word(self):
        self.assertEqual(score_word("at"), 0)
        self.assertEqual(score_word("cat"), 3)
        self.assertEqual(score_word("CATER"), 5)

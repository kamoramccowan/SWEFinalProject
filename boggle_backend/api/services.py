from functools import lru_cache
from typing import List

from django.contrib.staticfiles import finders

from .boggle_solver import Boggle
from .readJSONFile import read_json_to_list


class DictionaryNotFound(Exception):
    """Raised when the bundled dictionary cannot be located."""


@lru_cache(maxsize=1)
def load_full_dictionary() -> List[str]:
    """
    Load the bundled dictionary once and cache it for subsequent requests.
    This keeps dictionary lookups fast to satisfy performance expectations.
    """
    file_path = finders.find("data/full-wordlist.json")
    if not file_path:
        raise DictionaryNotFound("Dictionary file data/full-wordlist.json is missing.")
    return read_json_to_list(file_path)


def normalize_grid(grid: List[List[str]]) -> List[List[str]]:
    """Ensure grid values are consistently trimmed strings."""
    normalized = []
    for row in grid:
        normalized_row = []
        for cell in row:
            value = "" if cell is None else str(cell).strip()
            normalized_row.append(value)
        normalized.append(normalized_row)
    return normalized


def generate_valid_words(grid: List[List[str]]) -> List[str]:
    """
    Generate all valid words for a grid using the shared dictionary.
    Returns a sorted list to keep responses stable for clients.
    """
    dictionary = load_full_dictionary()
    game = Boggle(grid, dictionary)
    solutions = game.getSolution()
    return sorted(solutions)

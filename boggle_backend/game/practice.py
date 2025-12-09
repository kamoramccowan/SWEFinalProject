import random
from functools import lru_cache
from typing import List

from django.contrib.staticfiles import finders

from api.boggle_solver import Boggle  # reuse existing solver
from .difficulty import difficulty_to_size
from .models import Challenge
from .boggle_engine import _normalize_word


def get_letter_pool(difficulty: str) -> str:
    diff = (difficulty or "").lower()
    if diff == "hard":
        # Heavier weighting toward rarer letters for hard mode
        return "ABCDEFGHIJKLMNOPQRSTUVWXYZQQQZZZXXX"
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_practice_grid(size: int, difficulty: str = "easy") -> List[List[str]]:
    letters = get_letter_pool(difficulty)
    return [[random.choice(letters) for _ in range(size)] for _ in range(size)]


@lru_cache(maxsize=1)
def load_full_dictionary() -> List[str]:
    path = finders.find("data/full-wordlist.json")
    if not path:
        return []
    import json
    with open(path, 'r') as f:
        data = json.load(f)
    words = []
    for v in data.values():
        if isinstance(v, list):
            words.extend(v)
    return [_normalize_word(w) for w in words]


def create_practice_challenge(difficulty: str, user_id: str | None) -> Challenge:
    """
    Create a transient Challenge record for practice mode using a generated grid and computed valid words.
    """
    size = difficulty_to_size(difficulty)
    grid = generate_practice_grid(size, difficulty)
    dictionary = load_full_dictionary()
    boggle = Boggle(grid, dictionary)
    solutions = boggle.getSolution()
    valid_words = list(solutions) if solutions else dictionary[:1000]
    creator = user_id or "practice"
    return Challenge.objects.create(
        creator_user_id=str(creator),
        title="Practice",
        description="Practice board",
        grid=grid,
        difficulty=difficulty or "easy",
        valid_words=valid_words,
        recipients=[],
        status=Challenge.STATUS_ACTIVE,
    )

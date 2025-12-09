"""
Lightweight Boggle helpers for word validation against a challenge grid and dictionary.
Reuses precomputed dictionaries to avoid heavy recomputation per submission.
"""
from functools import lru_cache
from typing import Iterable, List, Set

from django.utils import timezone

from .models import Challenge


def _normalize_word(word: str) -> str:
    return (word or "").strip().upper()


def get_valid_words(challenge: Challenge) -> Set[str]:
    """
    Return the valid words for a challenge as an uppercase set.
    Cached per challenge id; invalidated when the cached key changes.
    """
    return _get_valid_words_cached(challenge.id, tuple(challenge.valid_words or []))


@lru_cache(maxsize=256)
def _get_valid_words_cached(challenge_id, words: tuple) -> Set[str]:
    return {_normalize_word(w) for w in words if _normalize_word(w)}


def is_word_on_board(grid: List[List[str]], word: str) -> bool:
    """
    Check via DFS if `word` can be formed on the board using 8-directional adjacency without reusing tiles.
    Supports multi-letter tiles like "QU" by matching tile tokens as prefixes in the target word.
    """
    target = _normalize_word(word)
    if not grid or not target:
        return False

    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    norm_grid = [[_normalize_word(cell) for cell in row] for row in grid]

    def dfs(r: int, c: int, idx: int, visited: List[List[bool]]) -> bool:
        # Out of bounds or already used
        if r < 0 or c < 0 or r >= rows or c >= cols or visited[r][c]:
            return False

        cell = norm_grid[r][c]
        if not target.startswith(cell, idx):
            return False

        next_idx = idx + len(cell)
        if next_idx == len(target):
            return True

        visited[r][c] = True
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if dfs(r + dr, c + dc, next_idx, visited):
                    return True
        visited[r][c] = False
        return False

    visited = [[False for _ in range(cols)] for _ in range(rows)]
    for y in range(rows):
        for x in range(cols):
            if dfs(y, x, 0, visited):
                return True
    return False


def score_word(word: str) -> int:
    """
    Simple scoring: length-based. Words shorter than 3 score 0.
    """
    length = len(_normalize_word(word))
    if length < 3:
        return 0
    return length

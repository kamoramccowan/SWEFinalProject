DIFFICULTY_CONFIG = {
    "easy": {
        "grid_size": 4,
        "duration_seconds": 120,
        "min_word_length": 3,
    },
    "medium": {
        "grid_size": 5,
        "duration_seconds": 180,
        "min_word_length": 3,
    },
    "hard": {
        "grid_size": 6,
        "duration_seconds": 240,
        "min_word_length": 4,
    },
}


def get_difficulty_config(name: str):
    return DIFFICULTY_CONFIG.get((name or "").lower())


def validate_grid_for_difficulty(grid, difficulty: str):
    cfg = get_difficulty_config(difficulty)
    if not cfg:
        return False
    expected = cfg["grid_size"]
    return len(grid) == expected and all(len(row) == expected for row in grid)


def difficulty_to_size(difficulty: str) -> int:
    cfg = get_difficulty_config(difficulty)
    if not cfg:
        return DIFFICULTY_CONFIG["easy"]["grid_size"]
    return cfg["grid_size"]

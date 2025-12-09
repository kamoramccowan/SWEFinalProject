import random
from typing import List, Optional, Tuple


def choose_hint(unfound: List[str]) -> Optional[dict]:
    """
    Pick a simple hint from unfound words: first letter and length.
    Deterministic if possible to keep outputs predictable.
    """
    if not unfound:
        return None
    # Choose shortest, then lexicographically for determinism
    target = sorted(unfound, key=lambda w: (len(w), w))[0]
    return {"first_letter": target[0], "length": len(target), "word": target}

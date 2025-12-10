"""
Fast boggle word solver for challenge creation.
Uses a Trie for efficient prefix matching and DFS for board traversal.
"""
import json
import os
from functools import lru_cache
from typing import List, Set, Optional
from django.conf import settings


class TrieNode:
    """Trie node for efficient prefix/word lookup."""
    __slots__ = ['children', 'is_word']
    
    def __init__(self):
        self.children = {}
        self.is_word = False


class Trie:
    """Trie data structure for O(m) word/prefix lookup where m = word length."""
    
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word: str):
        node = self.root
        for char in word.upper():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_word = True
    
    def search(self, word: str) -> bool:
        node = self._traverse(word.upper())
        return node is not None and node.is_word
    
    def starts_with(self, prefix: str) -> bool:
        return self._traverse(prefix.upper()) is not None
    
    def _traverse(self, text: str) -> Optional[TrieNode]:
        node = self.root
        for char in text:
            if char not in node.children:
                return None
            node = node.children[char]
        return node


def _get_dictionary_path(language: str = 'en') -> str:
    """Get the path to the dictionary file for a given language."""
    base_path = os.path.join(settings.BASE_DIR, 'boggle_backend', 'static', 'data')
    
    if language == 'es':
        return os.path.join(base_path, 'spanish-wordlist.json')
    elif language == 'fr':
        return os.path.join(base_path, 'french-wordlist.json')
    else:
        return os.path.join(base_path, 'full-wordlist.json')


@lru_cache(maxsize=4)
def _load_dictionary(language: str = 'en') -> List[str]:
    """Load and cache the dictionary for a language."""
    path = _get_dictionary_path(language)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle different JSON formats
            if isinstance(data, dict) and 'words' in data:
                words = data['words']
            elif isinstance(data, list):
                words = data
            else:
                words = list(data.values()) if isinstance(data, dict) else []
            # Filter to words >= 3 chars
            return [w.upper() for w in words if isinstance(w, str) and len(w) >= 3]
    except FileNotFoundError:
        # Fall back to English
        if language != 'en':
            return _load_dictionary('en')
        return []


@lru_cache(maxsize=4)
def _get_trie(language: str = 'en') -> Trie:
    """Build and cache a Trie for efficient word lookup."""
    trie = Trie()
    for word in _load_dictionary(language):
        trie.insert(word)
    return trie


def solve_boggle(grid: List[List[str]], language: str = 'en', min_length: int = 3) -> List[str]:
    """
    Find all valid words in a Boggle grid.
    
    Args:
        grid: 2D list of letters (e.g., [['A','B'],['C','D']])
        language: Language code ('en', 'es', 'fr')
        min_length: Minimum word length (default 3)
    
    Returns:
        List of valid words found on the board
    """
    if not grid or not grid[0]:
        return []
    
    trie = _get_trie(language)
    rows = len(grid)
    cols = len(grid[0])
    
    # Normalize grid to uppercase
    norm_grid = [[cell.upper() if cell else '' for cell in row] for row in grid]
    
    found_words: Set[str] = set()
    
    def dfs(r: int, c: int, current: str, node: TrieNode, visited: Set[tuple]):
        """DFS to explore all paths from position (r, c)."""
        # Check if current path is a valid word
        if len(current) >= min_length and node.is_word:
            found_words.add(current)
        
        # Early termination: if no words start with this prefix, stop
        if not node.children:
            return
        
        # Explore all 8 adjacent cells
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                    cell = norm_grid[nr][nc]
                    # Handle multi-character tiles like "QU"
                    if cell and cell[0] in node.children:
                        next_node = node.children[cell[0]]
                        # For multi-char tiles, traverse through each char
                        valid = True
                        for i, char in enumerate(cell[1:], 1):
                            if char in next_node.children:
                                next_node = next_node.children[char]
                            else:
                                valid = False
                                break
                        if valid:
                            new_visited = visited | {(nr, nc)}
                            dfs(nr, nc, current + cell, next_node, new_visited)
    
    # Start DFS from each cell
    for r in range(rows):
        for c in range(cols):
            cell = norm_grid[r][c]
            if cell and cell[0] in trie.root.children:
                start_node = trie.root.children[cell[0]]
                # Handle multi-char starting tiles
                valid = True
                for char in cell[1:]:
                    if char in start_node.children:
                        start_node = start_node.children[char]
                    else:
                        valid = False
                        break
                if valid:
                    dfs(r, c, cell, start_node, {(r, c)})
    
    return sorted(found_words)


def generate_solvable_grid(size: int = 4, difficulty: str = 'medium', language: str = 'en', 
                           min_words: int = 10, max_attempts: int = 50) -> tuple:
    """
    Generate a random grid that has at least min_words valid solutions.
    
    Args:
        size: Grid size (4, 5, or 6)
        difficulty: Difficulty level affecting letter distribution
        language: Language code
        min_words: Minimum number of valid words required
        max_attempts: Maximum generation attempts
    
    Returns:
        Tuple of (grid, valid_words)
    """
    import random
    
    # Letter frequency for English (weighted toward vowels for playability)
    vowels = list('AEIOUA')  # Extra A for common words
    consonants = list('BCDFGHJKLMNPQRSTVWXYZ')
    
    # Difficulty affects vowel/consonant ratio
    vowel_ratio = {'easy': 0.45, 'medium': 0.38, 'hard': 0.32}.get(difficulty, 0.38)
    
    for attempt in range(max_attempts):
        # Generate grid
        grid = []
        for _ in range(size):
            row = []
            for _ in range(size):
                if random.random() < vowel_ratio:
                    letter = random.choice(vowels)
                else:
                    letter = random.choice(consonants)
                # Handle special tiles
                if letter == 'Q':
                    letter = 'QU'
                row.append(letter)
            grid.append(row)
        
        # Solve and check word count
        valid_words = solve_boggle(grid, language)
        if len(valid_words) >= min_words:
            return grid, valid_words
    
    # If we couldn't generate a good grid, return the last attempt
    return grid, valid_words

"""
generator.py
============
Genera puzzle Sudoku a difficoltà variabile.

Strategia:
  1. Parte da una griglia risolta di base.
  2. Applica permutazioni valide (shuffle righe dentro banda,
     shuffle colonne dentro banda, permutazione cifre)
     per ottenere una griglia risolta casuale.
  3. Rimuove celle in modo simmetrico (simmetria a 180°)
     fino alla difficoltà richiesta.

Celle rimosse (approssimativo):
  easy   → 33-36  (puzzle "aperti")
  medium → 45-48
  hard   → 52-56  (richiede tecniche avanzate)
"""

import random
from typing import List, Optional


N = 9

# Griglia base risolta — valida e verificata
BASE = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]

REMOVE_COUNTS = {
    "easy":   34,
    "medium": 46,
    "hard":   54,
}


def _copy(grid: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in grid]


def generate(difficulty: str = "medium", seed: Optional[int] = None) -> List[List[int]]:
    rng = random.Random(seed)

    grid = _copy(BASE)

    # --- Permuta le cifre 1-9 ---
    digit_perm = list(range(1, N + 1))
    rng.shuffle(digit_perm)
    mapping = {old: new for old, new in zip(range(1, N + 1), digit_perm)}
    grid = [[mapping[v] for v in row] for row in grid]

    # --- Shuffle righe dentro ogni banda orizzontale ---
    for band in range(3):
        rows = list(range(band * 3, band * 3 + 3))
        shuffled = rows[:]
        rng.shuffle(shuffled)
        band_data = [grid[r][:] for r in shuffled]
        for i, r in enumerate(range(band * 3, band * 3 + 3)):
            grid[r] = band_data[i]

    # --- Shuffle colonne dentro ogni banda verticale ---
    for band in range(3):
        cols = list(range(band * 3, band * 3 + 3))
        shuffled = cols[:]
        rng.shuffle(shuffled)
        col_map = {orig: shuf for orig, shuf in zip(cols, shuffled)}
        new_grid = _copy(grid)
        for r in range(N):
            for c in cols:
                new_grid[r][c] = grid[r][col_map[c]]
        grid = new_grid

    # --- Shuffle bande orizzontali ---
    bands = [0, 1, 2]
    rng.shuffle(bands)
    new_grid = []
    for b in bands:
        for r in range(b * 3, b * 3 + 3):
            new_grid.append(grid[r][:])
    grid = new_grid

    # --- Rimuovi celle con simmetria a 180° ---
    puzzle = _copy(grid)
    n_remove = REMOVE_COUNTS.get(difficulty, REMOVE_COUNTS["medium"])

    cells = [(r, c) for r in range(N) for c in range(N // 2)]  # metà griglia
    rng.shuffle(cells)

    removed = 0
    for r, c in cells:
        if removed >= n_remove // 2:
            break
        puzzle[r][c] = 0
        puzzle[N - 1 - r][N - 1 - c] = 0
        removed += 2

    return puzzle


# Puzzle pre-costruiti extra-difficili per test
EXPERT_PUZZLES = [
    # "AI Escargot" — uno dei Sudoku più difficili al mondo
    [
        [1, 0, 0, 0, 0, 7, 0, 9, 0],
        [0, 3, 0, 0, 2, 0, 0, 0, 8],
        [0, 0, 9, 6, 0, 0, 5, 0, 0],
        [0, 0, 5, 3, 0, 0, 9, 0, 0],
        [0, 1, 0, 0, 8, 0, 0, 0, 2],
        [6, 0, 0, 0, 0, 4, 0, 0, 0],
        [3, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 4, 0, 0, 0, 0, 0, 0, 7],
        [0, 0, 7, 0, 0, 0, 3, 0, 0],
    ]
]


def get_expert() -> List[List[int]]:
    return _copy(EXPERT_PUZZLES[0])

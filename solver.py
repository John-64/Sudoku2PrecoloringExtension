"""
solver.py
=========
Due algoritmi per GraphColoring applicato a Sudoku:

1. NAIVE  – backtracking riga-per-riga, prima cifra valida.
            Corrisponde a visitare l'albero di backtracking nell'ordine
            lessicografico, senza sfruttare la struttura del problema.

2. DSATUR – Degree of SATURation (Brélaz, 1979) + Forward Checking.
            Ad ogni passo colora il nodo con più colori distinti già
            usati dai vicini (massima saturazione); a parità, il nodo
            di grado più alto.  Dopo ogni assegnazione si propagano
            i vincoli (forward checking): se un nodo rimasto vuoto
            perde tutti i colori disponibili si fa backtrack subito.

            Corrisponde alle sezioni 2.7-2.8 della dispensa:
            "scegliere bene l'albero di backtracking" e
            "sfruttare le caratteristiche del problema".

Entrambi restituiscono:
  - solution    : griglia 9×9 soluzione (o None)
  - nodes       : nodi dell'albero esplorati
  - time_ms     : millisecondi
  - steps       : lista di (r, c, val)  val=0 → backtrack
  - success     : bool
"""

import time
from typing import List, Dict, Optional, Tuple
from reduction import ADJ, N, node_id, node_rc, grid_to_precoloring, coloring_to_grid


MAX_STEPS = 8_000   # limite step per l'animazione (non per il conteggio nodi)
MAX_NODES = 2_000_000  # guard per puzzle irrisolvibili / buggy input


# ---------------------------------------------------------------------------
# Helper comuni
# ---------------------------------------------------------------------------

def available_colors(uid: int, colors: Dict[int, int]) -> List[int]:
    """Cifre 1-9 non usate dai vicini colorati di uid."""
    used = {colors[nb] for nb in ADJ[uid] if nb in colors}
    return [c for c in range(1, N + 1) if c not in used]


def saturation(uid: int, colors: Dict[int, int]) -> int:
    """Numero di colori distinti usati dai vicini di uid."""
    return len({colors[nb] for nb in ADJ[uid] if nb in colors})


# ---------------------------------------------------------------------------
# 1. DSATUR + Forward Checking
# ---------------------------------------------------------------------------

def solve_dsatur(grid: List[List[int]]) -> dict:
    start = time.perf_counter()
    colors = grid_to_precoloring(grid)
    fixed = set(colors.keys())
    uncolored = [u for u in range(N * N) if u not in colors]

    nodes_explored = [0]
    anim_steps: List[Tuple[int, int, int]] = []
    overflow = [False]

    def _record(r, c, val):
        if not overflow[0]:
            anim_steps.append((r, c, val))
            if len(anim_steps) >= MAX_STEPS:
                overflow[0] = True

    def backtrack(uncolored_set: set, colors: Dict[int, int]) -> bool:
        if nodes_explored[0] > MAX_NODES:
            return False
        if not uncolored_set:
            return True

        # Scegli il nodo con saturazione massima; a parità, grado massimo
        uid = max(
            uncolored_set,
            key=lambda u: (saturation(u, colors), len(ADJ[u]))
        )

        for color in available_colors(uid, colors):
            nodes_explored[0] += 1
            colors[uid] = color
            r, c = node_rc(uid)
            _record(r, c, color)

            # Forward checking: nessun nodo deve rimanere senza colori
            remaining = uncolored_set - {uid}
            ok = all(available_colors(nb, colors) for nb in remaining if nb in ADJ[uid])

            if ok and backtrack(remaining, colors):
                return True

            del colors[uid]
            _record(r, c, 0)

        return False

    success = backtrack(set(uncolored), colors)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "algorithm": "DSATUR + Forward Checking",
        "success": success,
        "solution": coloring_to_grid(colors) if success else None,
        "nodes": nodes_explored[0],
        "time_ms": round(elapsed_ms, 2),
        "steps": anim_steps,
        "steps_overflow": overflow[0],
    }


# ---------------------------------------------------------------------------
# 2. Backtracking Naive (riga-per-riga)
# ---------------------------------------------------------------------------

def solve_naive(grid: List[List[int]]) -> dict:
    start = time.perf_counter()
    board = [row[:] for row in grid]
    nodes_explored = [0]
    anim_steps: List[Tuple[int, int, int]] = []
    overflow = [False]

    def _record(r, c, val):
        if not overflow[0]:
            anim_steps.append((r, c, val))
            if len(anim_steps) >= MAX_STEPS:
                overflow[0] = True

    def is_valid(r: int, c: int, val: int) -> bool:
        if val in board[r]:
            return False
        if any(board[i][c] == val for i in range(N)):
            return False
        br, bc = (r // 3) * 3, (c // 3) * 3
        for dr in range(3):
            for dc in range(3):
                if board[br + dr][bc + dc] == val:
                    return False
        return True

    def backtrack() -> bool:
        if nodes_explored[0] > MAX_NODES:
            return False
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    for val in range(1, N + 1):
                        nodes_explored[0] += 1
                        if is_valid(r, c, val):
                            board[r][c] = val
                            _record(r, c, val)
                            if backtrack():
                                return True
                            board[r][c] = 0
                            _record(r, c, 0)
                    return False
        return True

    success = backtrack()
    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "algorithm": "Backtracking Naive",
        "success": success,
        "solution": board if success else None,
        "nodes": nodes_explored[0],
        "time_ms": round(elapsed_ms, 2),
        "steps": anim_steps,
        "steps_overflow": overflow[0],
    }

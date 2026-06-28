import time
from typing import Dict, List, Tuple

from reduction import (
    DEFAULT_BLOCK_SIZE,
    get_graph,
    grid_size,
    grid_to_precoloring,
    coloring_to_grid,
    node_rc,
)


MAX_STEPS = 8_000   # limite step per l'animazione (non per il conteggio nodi)
MAX_NODES = 2_000_000  # guard per puzzle irrisolvibili / buggy input
MAX_SECONDS = 8.0   # guard sul tempo di parete: a n=4 (16 colori) la ricerca
                     # puo' esplodere combinatoriamente molto piu' in fretta
                     # che a n=3, anche restando sotto MAX_NODES

# Helper


def available_colors(uid: int, colors: Dict[int, int], adj: List[set], N: int) -> List[int]:
    """Cifre 1..N non usate dai vicini colorati di uid."""
    used = {colors[nb] for nb in adj[uid] if nb in colors}
    return [c for c in range(1, N + 1) if c not in used]


def saturation(uid: int, colors: Dict[int, int], adj: List[set]) -> int:
    """Numero di colori distinti usati dai vicini di uid."""
    return len({colors[nb] for nb in adj[uid] if nb in colors})

# 1. DSATUR + Forward Checking


def solve_dsatur(grid: List[List[int]], n: int = DEFAULT_BLOCK_SIZE) -> dict:
    start = time.perf_counter()
    N = grid_size(n)
    adj, _ = get_graph(n)

    colors = grid_to_precoloring(grid, n)
    uncolored = [u for u in range(N * N) if u not in colors]

    nodes_explored = [0]
    anim_steps: List[Tuple[int, int, int]] = []
    overflow = [False]
    guard_triggered = [False]

    def _record(r, c, val):
        if not overflow[0]:
            anim_steps.append((r, c, val))
            if len(anim_steps) >= MAX_STEPS:
                overflow[0] = True

    def _guard_hit() -> bool:
        if nodes_explored[0] > MAX_NODES:
            return True
        if nodes_explored[0] % 2048 == 0 and (time.perf_counter() - start) > MAX_SECONDS:
            return True
        return False

    def backtrack(uncolored_set: set, colors: Dict[int, int]) -> bool:
        if _guard_hit():
            guard_triggered[0] = True
            return False
        if not uncolored_set:
            return True

        # Scegli il nodo con saturazione massima; a parita', grado massimo
        uid = max(
            uncolored_set,
            key=lambda u: (saturation(u, colors, adj), len(adj[u]))
        )

        for color in available_colors(uid, colors, adj, N):
            nodes_explored[0] += 1
            colors[uid] = color
            r, c = node_rc(uid, n)
            _record(r, c, color)

            remaining = uncolored_set - {uid}
            affected = adj[uid] & remaining
            ok = all(available_colors(nb, colors, adj, N) for nb in affected)

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
        "solution": coloring_to_grid(colors, n) if success else None,
        "nodes": nodes_explored[0],
        "time_ms": round(elapsed_ms, 2),
        "steps": anim_steps,
        "steps_overflow": overflow[0],
        "guard_triggered": guard_triggered[0],
    }

# 2. Backtracking Naive (riga-per-riga)


def solve_naive(grid: List[List[int]], n: int = DEFAULT_BLOCK_SIZE) -> dict:
    start = time.perf_counter()
    N = grid_size(n)
    board = [row[:] for row in grid]
    nodes_explored = [0]
    anim_steps: List[Tuple[int, int, int]] = []
    overflow = [False]
    guard_triggered = [False]

    def _record(r, c, val):
        if not overflow[0]:
            anim_steps.append((r, c, val))
            if len(anim_steps) >= MAX_STEPS:
                overflow[0] = True

    def _guard_hit() -> bool:
        if nodes_explored[0] > MAX_NODES:
            return True
        if nodes_explored[0] % 2048 == 0 and (time.perf_counter() - start) > MAX_SECONDS:
            return True
        return False

    def is_valid(r: int, c: int, val: int) -> bool:
        if val in board[r]:
            return False
        if any(board[i][c] == val for i in range(N)):
            return False
        br, bc = (r // n) * n, (c // n) * n
        for dr in range(n):
            for dc in range(n):
                if board[br + dr][bc + dc] == val:
                    return False
        return True

    def backtrack() -> bool:
        if _guard_hit():
            guard_triggered[0] = True
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
        "guard_triggered": guard_triggered[0],
    }

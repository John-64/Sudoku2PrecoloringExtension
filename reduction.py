from typing import List, Tuple, Set, Dict


N = 9  # dimensione griglia


def node_id(r: int, c: int) -> int:
    """Indice lineare del nodo (r, c): 0 … 80."""
    return r * N + c


def node_rc(idx: int) -> Tuple[int, int]:
    """Ritorna (riga, colonna) dall'indice lineare."""
    return divmod(idx, N)


def build_graph() -> Tuple[List[Set[int]], List[Tuple[int, int]]]:
    """
    Costruisce il grafo dell'istanza GraphColoring.

    Returns
    -------
    adj   : list[set[int]]  – adj[u] = vicini del nodo u
    edges : list[(u,v)]     – archi con u < v
    """
    adj: List[Set[int]] = [set() for _ in range(N * N)]

    def add_edge(a: int, b: int) -> None:
        if a != b:
            adj[a].add(b)
            adj[b].add(a)

    for r in range(N):
        for c in range(N):
            u = node_id(r, c)
            # stessa riga
            for c2 in range(N):
                if c2 != c:
                    add_edge(u, node_id(r, c2))
            # stessa colonna
            for r2 in range(N):
                if r2 != r:
                    add_edge(u, node_id(r2, c))
            # stesso blocco 3×3
            br, bc = (r // 3) * 3, (c // 3) * 3
            for dr in range(3):
                for dc in range(3):
                    r2, c2 = br + dr, bc + dc
                    if (r2, c2) != (r, c):
                        add_edge(u, node_id(r2, c2))

    edges: List[Tuple[int, int]] = []
    for u in range(N * N):
        for v in adj[u]:
            if v > u:
                edges.append((u, v))

    return adj, edges


def grid_to_precoloring(grid: List[List[int]]) -> Dict[int, int]:
    """Converte la griglia Sudoku in una pre-colorazione parziale."""
    colors: Dict[int, int] = {}
    for r in range(N):
        for c in range(N):
            if grid[r][c] != 0:
                colors[node_id(r, c)] = grid[r][c]
    return colors


def coloring_to_grid(colors: Dict[int, int]) -> List[List[int]]:
    """Converte la colorazione completa nella griglia Sudoku soluzione."""
    grid = [[0] * N for _ in range(N)]
    for uid, color in colors.items():
        r, c = node_rc(uid)
        grid[r][c] = color
    return grid


ADJ, EDGES = build_graph()


def graph_json() -> dict:
    """Serializzazione JSON per il frontend."""
    return {
        "nodes": [{"id": i, "r": i // N, "c": i % N} for i in range(N * N)],
        "edges": [{"u": u, "v": v} for u, v in EDGES],
    }
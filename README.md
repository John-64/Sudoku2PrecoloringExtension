# Sudoku2GraphColoring reduction
Un risolutore di Sudoku tramite una riduzione polinomiale al problema della colorazione di grafi.

...

# Theoretical foundations
- [The Sudoku problem as an NP-Hard problem](#the-sudoku-problem-as-an-np-hard-problem)
- [The GraphColoring problem](#the-graph-coloring-problem)
- [Sudoku2GraphColoring reduction](#sudoku2graphcoloring-reduction)
- [Correctness and complexity of the reduction](#correctness-and-complexity-of-the-reduction)

## The Sudoku problem as an NP-Hard problem
The Sudoku puzzle is played on an $n \times n$ grid (where $n = k^2$, typically $n = 9, k = 3$).

Each cell must contain a value from the set $\{1, \ldots, n\}$, satisfying three families of constraints:
* **Row:** Each value appears exactly once per row.
* **Column:** Each value appears exactly once per column.
* **Block:** Each value appears exactly once in each $k \times k$ sub-grid.

> **Theorem (Yato & Seta, 2003):** The decision problem for the generalized Sudoku on an $n \times n$ grid is **NP-complete**.

To establish NP-completeness, we must verify:

1. **Membership in NP:** Given a completed grid, verifying that it satisfies all constraints takes $\mathcal{O}(n^2)$ time.
2. **NP-hardness:** Shown via reduction from the *Latin Square* problem, which is known to be NP-complete.

Since no efficient solution exists (unless $\text{P} = \text{NP}$), we must rely on intelligent exhaustive search: **backtracking** combined with heuristics that drastically prune the search space.

## The GraphColoring problem

**Definition:** Given a graph $G = (V, E)$ and an integer $k$, the $k$-GraphColoring problem asks whether there exists a function $f : V \to \{1, \ldots, k\}$ such that:

$$\forall (u, v) \in E \implies f(u) \neq f(v)$$

Such a function $f$ is called a **proper $k$-coloring** of $G$.

> **Theorem:** $3\text{-SAT} \le_p 3\text{-GraphColoring}$. Consequently, $k$-GraphColoring is **NP-complete** for $k \geq 3$.

## Sudoku2GraphColoring reduction

Given a Sudoku instance on an $n \times n$ grid, we construct an instance of $n$-GraphColoring in polynomial time as follows.

### Graph Construction
Let $G = (V, E)$ with $k = n$.

- Each cell of the grid becomes a vertex:

    $$V = \{(r, c) \mid 0 \leq r, c < n\} \qquad |V| = n^2$$

- Two vertices are connected by an edge if and only if their corresponding cells share a constraint:

    $$E = \bigl\{\{(r_1, c_1),\, (r_2, c_2)\} \mid \text{same row} \;\lor\; \text{same column} \;\lor\; \text{same block}\bigr\}$$

For $n = 9$: 
* $|V| = 81$
* $|E| = 810$

Each vertex has a degree of exactly $\delta = 20$ neighbors ($8$ in the same row + $8$ in the same column + $4$ in the same block, excluding those already counted).

### Pre-coloring
The non-empty cells of the Sudoku instance become fixed coloring constraints:

$$\text{precolor}(r, c) = \text{grid}[r][c] \qquad \text{if } \text{grid}[r][c] \neq 0$$

### The Naive Backtracking approach

The naive algorithm solves the colored graph by scanning the cells in lexicographical order (row 0 $\to$ row 8, column 0 $\to$ column 8). For each empty cell, it attempts to assign digits $1, 2, \ldots, 9$ in their natural order, assigns the first valid one, and recurses. If no digit is valid, it backtracks.

```c
NAIVE(board, pos):
    if pos == 81: 
        return SOLVED
        
    r = pos / 9
    c = pos % 9
    
    if board[r][c] != 0: 
        return NAIVE(board, pos + 1)   // Fixed cell (pre-colored)
        
    for d = 1 to 9:
        if valid(board, r, c, d):
            board[r][c] = d
            if NAIVE(board, pos + 1) == SOLVED: 
                return SOLVED
            board[r][c] = 0            // Backtrack
            
    return UNSOLVABLE
```
The main drawback here is that the backtracking tree is constructed in an inefficient order. Cells at the beginning of the grid often have many available digits due to fewer active constraints at that stage. This generates a high branching factor and causes a massive amount of avoidable backtracking steps.
- It is crucial to choose the most useful backtracking tree.

### The DSATUR Strategy (Brélaz, 1979)
**DSATUR (Degree of SATURation)** is the optimal strategy for the Graph Coloring problem. It perfectly implements two key principles from Section 2.8 of the course lecture notes (*"exploiting problem characteristics"*):

## 1. MRV Heuristic — Vertex Selection
At each step, instead of proceeding in a fixed order, we select the uncolored vertex with the **maximum saturation degree**:

$$\text{sat}(v) = \bigl|\{f(u) \mid u \in N(v), \; u \text{ is already colored}\}\bigr|$$

In other words, $\text{sat}(v)$ is the number of *distinct* colors used by its already colored neighbors. In case of a tie, the vertex with the maximum degree in the uncolored subgraph is chosen.

* **Rationale:** The most saturated vertex has the fewest remaining available colors. By choosing it, we hit potential conflicts earlier, allowing the algorithm to prune the search tree much faster (**fail-first** principle). This corresponds exactly to the **MRV (Minimum Remaining Values)** heuristic used in Constraint Satisfaction Problems (CSPs).

## 2. Forward Checking — Constraint Propagation
Immediately after assigning a color $f(v) = d$, we update the domains of all uncolored neighbors: we remove $d$ from the domain of every $u \in N(v)$. 
If any neighbor's domain becomes empty, it means $u$ can no longer be colored. The algorithm triggers an **immediate backtrack**, preventing any further useless exploration down that branch of the tree.

```c
DSATUR(uncolored, colors):
    if uncolored == ∅: 
        return SOLVED
        
    // MRV: Select vertex with max saturation (break ties with max degree)
    v = argmax_{u ∈ uncolored} (sat(u, colors), deg(u))    
    
    for d in available_colors(v, colors):
        colors[v] = d
        
        // Forward Checking: Check if any neighbor's domain becomes empty
        if ∀ u ∈ uncolored \ {v}: available_colors(u, colors) != ∅:
            if DSATUR(uncolored \ {v}, colors) == SOLVED: 
                return SOLVED
                
        del colors[v]                                      // Backtrack
        
    return UNSOLVABLE
```

Both algorithms share the exact same **theoretical worst-case complexity** (since the underlying problem is NP-hard). However, **DSATUR** explores a backtracking tree that is exponentially smaller on real-world instances. 

This drastic performance gain is entirely due to its **informed choice** of which vertex to color next, allowing it to prune dead ends immediately rather than blindly searching through the solution space.

### Construction complexity
The time complexity to build the graph is bounded by the number of vertices and edges generated:

$$T_{\text{reduction}} = \mathcal{O}(n^2) \text{ vertices} + \mathcal{O}(n^3) \text{ edges} = \mathcal{O}(n^3)$$


## Instruction to run the project
1. Install all the requirements in the file by executing:
    ```
    pip install -r requirements.txt
    ```
2. Run the main server by executing:
    ```
    python app.py
    ```

### Some notes
...

## Screenshots
...

## Info and credits
This project was created for the course "Algoritmi Avanzati" at the Università degli Studi di Salerno. 
- [Complexity and Completeness of Finding Another Solution and Its Application to Puzzles - Takayuki Yato](https://www.cs.umd.edu/users/gasarch/BLOGPAPERS/msasp.pdf)

## Contribution
If you'd like to contribute, please follow these steps:
- Fork the repository;
- Create a new branch (```git checkout -b feature/YourFeatureName```);
- Commit your changes (```git commit -m 'Add some feature'```);
- Push to the branch (```git push origin feature/YourFeatureName```);
- Open a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

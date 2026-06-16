"""
app.py  –  Sudoku → GraphColoring  (Flask webapp)

Route:
  GET  /              → pagina principale
  GET  /graph         → struttura del grafo (JSON statico)
  POST /solve         → risolvi puzzle { grid, algorithm, compare }
  GET  /generate      → genera puzzle ?difficulty=easy|medium|hard|expert&seed=N
"""

from flask import Flask, render_template, request, jsonify
from reduction import graph_json
from solver import solve_dsatur, solve_naive
from generator import generate, get_expert

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/graph")
def graph():
    """Restituisce nodi e archi del grafo GraphColoring per il frontend."""
    return jsonify(graph_json())


@app.route("/solve", methods=["POST"])
def solve():
    data = request.get_json(force=True)
    grid = data.get("grid")
    algorithm = data.get("algorithm", "dsatur")   # dsatur | naive | both
    compare = data.get("compare", False)

    if not grid or len(grid) != 9 or any(len(r) != 9 for r in grid):
        return jsonify({"error": "Griglia non valida"}), 400

    if algorithm == "dsatur":
        result = solve_dsatur(grid)
        return jsonify({"primary": result})

    if algorithm == "naive":
        result = solve_naive(grid)
        return jsonify({"primary": result})

    if algorithm == "both":
        dsatur_res = solve_dsatur(grid)
        naive_res  = solve_naive(grid)
        return jsonify({
            "primary": dsatur_res,
            "secondary": naive_res,
        })

    return jsonify({"error": "Algoritmo non riconosciuto"}), 400


@app.route("/generate")
def generate_puzzle():
    difficulty = request.args.get("difficulty", "medium")
    seed_str   = request.args.get("seed", None)
    seed       = int(seed_str) if seed_str and seed_str.isdigit() else None

    if difficulty == "expert":
        puzzle = get_expert()
    else:
        puzzle = generate(difficulty=difficulty, seed=seed)

    return jsonify({"grid": puzzle, "difficulty": difficulty})


if __name__ == "__main__":
    app.run(debug=True, port=5056)

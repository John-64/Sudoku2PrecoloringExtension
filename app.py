from __future__ import annotations

import logging
import os
from typing import Any, Optional

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from reduction import graph_json
from solver import solve_dsatur, solve_naive
from generator import DIFFICULTIES, generate, get_expert

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sudoku2graphcoloring")

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

VALID_ALGORITHMS = {"dsatur", "naive", "both"}


def validate_grid(grid: Any) -> Optional[str]:
    """Validate the structure and contents of the grid received from the client.

    Returns an error message (str) if the grid is invalid,
    otherwise None. Empty cells are represented by 0.
    """
    if not isinstance(grid, list) or len(grid) != 9:
        return "The grid must contain exactly 9 rows."
    for row in grid:
        if not isinstance(row, list) or len(row) != 9:
            return "Each row must contain exactly 9 cells."
        for value in row:
            # bool is a subclass of int in Python, so we explicitly reject it.
            if isinstance(value, bool) or not isinstance(value, int) or not (0 <= value <= 9):
                return "Each cell must be an integer between 0 and 9 (0 = empty)."
    return None


@app.errorhandler(HTTPException)
def handle_http_error(err: HTTPException):
    return jsonify({"error": err.description}), err.code or 500


@app.errorhandler(Exception)
def handle_unexpected_error(err: Exception):
    logger.exception("Unhandled error during request")
    return jsonify({"error": "Internal server error."}), 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/graph")
def graph():
    """Return the Graph Coloring graph nodes and edges for the frontend."""
    return jsonify(graph_json())


@app.route("/solve", methods=["POST"])
def solve():
    data = request.get_json(silent=True) or {}
    grid = data.get("grid")
    algorithm = data.get("algorithm", "dsatur")

    error = validate_grid(grid)
    if error:
        return jsonify({"error": error}), 400

    if algorithm not in VALID_ALGORITHMS:
        return jsonify({"error": f"Unknown algorithm: {algorithm!r}"}), 400

    if algorithm == "dsatur":
        return jsonify({"primary": solve_dsatur(grid)})

    if algorithm == "naive":
        return jsonify({"primary": solve_naive(grid)})

    # algorithm == "both": run both algorithms for direct comparison
    return jsonify({
        "primary": solve_dsatur(grid),
        "secondary": solve_naive(grid),
    })


@app.route("/generate")
def generate_puzzle():
    difficulty = request.args.get("difficulty", "medium")
    seed_param = request.args.get("seed")

    if difficulty not in DIFFICULTIES and difficulty != "expert":
        return jsonify({"error": f"Unknown difficulty: {difficulty!r}"}), 400

    seed: Optional[int] = None
    if seed_param is not None:
        try:
            seed = int(seed_param)
        except ValueError:
            return jsonify({"error": "The seed must be an integer."}), 400

    puzzle = get_expert() if difficulty == "expert" else generate(difficulty=difficulty, seed=seed)
    return jsonify({"grid": puzzle, "difficulty": difficulty, "seed": seed})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5059))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, port=port)
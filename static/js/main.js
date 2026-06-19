(() => {
  "use strict";

  const N = 9;
  const CELL = 10;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const els = {
    grid: document.getElementById("sudoku-grid"),
    svg: document.getElementById("graph-svg"),
    difficulty: document.getElementById("difficulty"),
    seed: document.getElementById("seed"),
    algorithm: document.getElementById("algorithm"),
    btnGenerate: document.getElementById("btn-generate"),
    btnClear: document.getElementById("btn-clear"),
    btnSolve: document.getElementById("btn-solve"),
    stats: document.getElementById("stats"),
    banner: document.getElementById("error-banner"),
  };

  const DIFFICULTY_LABELS = { easy: "Facile", medium: "Media", hard: "Difficile", expert: "Esperto" };
  const MAX_HISTORY = 25;

  const state = {
    grid: emptyGrid(),
    given: emptyGrid(),
    adjacency: new Map(),
    selected: null,
    busy: false,
    inputEls: [],
    nodeEls: [],
    edgesGroup: null,
    history: [],
    runCounter: 0,
    puzzleLabel: "—",
  };

  function emptyGrid() {
    return Array.from({ length: N }, () => Array(N).fill(0));
  }

  function idx(r, c) { return r * N + c; }

  // Init

  function buildSudokuDOM() {
    const frag = document.createDocumentFragment();
    for (let r = 0; r < N; r++) {
      state.inputEls.push([]);
      for (let c = 0; c < N; c++) {
        const input = document.createElement("input");
        input.type = "text";
        input.inputMode = "numeric";
        input.maxLength = 1;
        input.autocomplete = "off";
        input.dataset.r = r;
        input.dataset.c = c;
        input.setAttribute("aria-label", `Riga ${r + 1}, colonna ${c + 1}`);

        input.addEventListener("focus", () => selectCell(r, c));
        input.addEventListener("click", () => selectCell(r, c));
        input.addEventListener("input", onCellInput);
        input.addEventListener("keydown", onCellKeydown);

        state.inputEls[r].push(input);
        frag.appendChild(input);
      }
    }
    els.grid.appendChild(frag);
  }

  function buildGraphDOM() {
    const svg = els.svg;

    // block guide lines, mirroring the sudoku's thick 3x3 borders
    const guides = document.createElementNS(svg.namespaceURI, "g");
    [30, 60].forEach((pos) => {
      guides.appendChild(line(pos, 0, pos, 90, "guide strong"));
      guides.appendChild(line(0, pos, 90, pos, "guide strong"));
    });
    svg.appendChild(guides);

    state.edgesGroup = document.createElementNS(svg.namespaceURI, "g");
    state.edgesGroup.setAttribute("id", "edges");
    svg.appendChild(state.edgesGroup);

    const nodesGroup = document.createElementNS(svg.namespaceURI, "g");
    for (let r = 0; r < N; r++) {
      state.nodeEls.push([]);
      for (let c = 0; c < N; c++) {
        const [x, y] = coordsFor(r, c);
        const circle = document.createElementNS(svg.namespaceURI, "circle");
        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        circle.setAttribute("r", 3.1);
        circle.classList.add("node", "empty");
        circle.dataset.r = r;
        circle.dataset.c = c;
        state.nodeEls[r].push(circle);
        nodesGroup.appendChild(circle);
      }
    }
    svg.appendChild(nodesGroup);
  }

  function coordsFor(r, c) {
    return [c * CELL + CELL / 2, r * CELL + CELL / 2];
  }

  function line(x1, y1, x2, y2, cls) {
    const el = document.createElementNS(els.svg.namespaceURI, "line");
    el.setAttribute("x1", x1); el.setAttribute("y1", y1);
    el.setAttribute("x2", x2); el.setAttribute("y2", y2);
    el.setAttribute("class", cls);
    return el;
  }

  async function loadGraph() {
    try {
      const res = await fetch("/graph");
      if (!res.ok) throw new Error("graph fetch failed");
      const data = await res.json();
      state.adjacency = new Map(data.nodes.map((n) => [n.id, new Set()]));
      data.edges.forEach(({ u, v }) => {
        state.adjacency.get(u).add(v);
        state.adjacency.get(v).add(u);
      });
    } catch (err) {
      showError("Impossibile caricare la struttura del grafo. Riavvia il server e ricarica la pagina.");
    }
  }

  // Render

  function renderCell(r, c) {
    const v = state.grid[r][c];
    const input = state.inputEls[r][c];
    input.value = v === 0 ? "" : String(v);
    input.dataset.v = v === 0 ? "" : String(v);
    input.readOnly = !!state.given[r][c];
    input.classList.toggle("given", !!state.given[r][c]);

    const node = state.nodeEls[r][c];
    if (v === 0) {
      node.classList.add("empty");
      node.removeAttribute("data-v");
    } else {
      node.classList.remove("empty");
      node.dataset.v = String(v);
    }
  }

  function renderAll() {
    for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) renderCell(r, c);
  }

  // Selection

  function selectCell(r, c) {
    if (state.selected && state.selected.r === r && state.selected.c === c) return;
    clearSelection();
    state.selected = { r, c };

    const u = idx(r, c);
    const neighbours = state.adjacency.get(u) || new Set();

    state.inputEls[r][c].classList.add("selected");
    state.nodeEls[r][c].classList.add("selected");

    state.edgesGroup.innerHTML = "";
    const [x1, y1] = coordsFor(r, c);

    neighbours.forEach((nIdx) => {
      const nr = Math.floor(nIdx / N), nc = nIdx % N;
      state.inputEls[nr][nc].classList.add("related");
      state.nodeEls[nr][nc].classList.add("related");
      const [x2, y2] = coordsFor(nr, nc);
      state.edgesGroup.appendChild(line(x1, y1, x2, y2, "edge lit"));
    });
  }

  function clearSelection() {
    if (!state.selected) return;
    document.querySelectorAll(".selected, .related").forEach((el) => {
      el.classList.remove("selected", "related");
    });
    state.edgesGroup.innerHTML = "";
    state.selected = null;
  }

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".panel")) clearSelection();
  });

  // Editing

  function onCellInput(e) {
    const input = e.target;
    const r = Number(input.dataset.r), c = Number(input.dataset.c);
    const digits = input.value.replace(/[^1-9]/g, "").slice(-1);
    state.grid[r][c] = digits === "" ? 0 : Number(digits);
    state.puzzleLabel = "personalizzato";
    renderCell(r, c);
    input.value = digits;
    if (state.selected && state.selected.r === r && state.selected.c === c) {
      selectCellRefresh();
    }
  }

  function selectCellRefresh() {
    const { r, c } = state.selected;
    state.selected = null;
    selectCell(r, c);
  }

  function onCellKeydown(e) {
    const r = Number(e.target.dataset.r), c = Number(e.target.dataset.c);
    const moves = {
      ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1],
    };
    if (moves[e.key]) {
      e.preventDefault();
      const [dr, dc] = moves[e.key];
      const nr = Math.min(N - 1, Math.max(0, r + dr));
      const nc = Math.min(N - 1, Math.max(0, c + dc));
      state.inputEls[nr][nc].focus();
    }
  }

  // Actions

  function setBusy(busy) {
    state.busy = busy;
    [els.btnGenerate, els.btnClear, els.btnSolve].forEach((b) => (b.disabled = busy));
  }

  function showError(msg) {
    els.banner.textContent = msg;
    els.banner.classList.add("visible");
  }

  function hideError() {
    els.banner.classList.remove("visible");
  }

  async function generatePuzzle() {
    if (state.busy) return;
    hideError();
    setBusy(true);
    try {
      const params = new URLSearchParams({ difficulty: els.difficulty.value });
      const seed = els.seed.value.trim();
      if (seed !== "") params.set("seed", seed);

      const res = await fetch(`/generate?${params.toString()}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Generazione fallita");

      clearSelection();
      state.grid = data.grid;
      state.given = data.grid.map((row) => row.map((v) => (v !== 0 ? 1 : 0)));
      state.puzzleLabel = DIFFICULTY_LABELS[data.difficulty] || data.difficulty;
      if (data.seed !== null && data.seed !== undefined) state.puzzleLabel += ` · seed ${data.seed}`;
      renderAll();
    } catch (err) {
      showError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function clearPuzzle() {
    if (state.busy) return;
    hideError();
    clearSelection();
    state.grid = emptyGrid();
    state.given = emptyGrid();
    state.puzzleLabel = "—";
    renderAll();
    resetHistory();
  }

  async function solvePuzzle() {
    if (state.busy) return;
    hideError();
    setBusy(true);
    const algorithm = els.algorithm.value;
    const snapshot = state.grid.map((row) => row.slice());

    try {
      const res = await fetch("/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grid: state.grid, algorithm }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Risoluzione fallita");

      clearSelection();
      await animateSteps(data.primary.steps || []);

      if (data.primary.success) {
        state.grid = data.primary.solution;
      } else {
        state.grid = snapshot;
      }
      renderAll();
      addRun(data.primary, data.secondary);
    } catch (err) {
      showError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function animateSteps(steps) {
    return new Promise((resolve) => {
      if (steps.length === 0 || reducedMotion) {
        steps.forEach(([r, c, v]) => { state.grid[r][c] = v; renderCell(r, c); });
        resolve();
        return;
      }
      const maxFrames = 420;
      const batch = Math.max(1, Math.ceil(steps.length / maxFrames));
      const frameDelay = 16;
      let i = 0;
      const tick = () => {
        for (let k = 0; k < batch && i < steps.length; k++, i++) {
          const [r, c, v] = steps[i];
          state.grid[r][c] = v;
          renderCell(r, c);
        }
        if (i < steps.length) requestAnimationFrame(() => setTimeout(tick, frameDelay));
        else resolve();
      };
      tick();
    });
  }

  function resetHistory() {
    state.history = [];
    state.runCounter = 0;
    renderHistory();
  }

  function computeDelta(primary, secondary) {
    if (primary.nodes > 0 && secondary.nodes > 0) {
      const ratio = secondary.nodes / primary.nodes;
      return `DSATUR esplora ${ratio.toFixed(1)}× meno nodi del backtracking naive su questa istanza.`;
    }
    return null;
  }

  function addRun(primary, secondary) {
    state.runCounter += 1;
    state.history.unshift({
      run: state.runCounter,
      puzzle: state.puzzleLabel,
      rows: secondary ? [primary, secondary] : [primary],
      delta: secondary ? computeDelta(primary, secondary) : null,
    });
    if (state.history.length > MAX_HISTORY) state.history.pop();
    renderHistory();
  }

  function renderHistory() {
    if (state.history.length === 0) {
      els.stats.innerHTML = '<p class="stats-empty">Genera o compila un puzzle, poi premi «Risolvi»: i risultati restano in elenco finché non premi «Pulisci».</p>';
      return;
    }

    const body = state.history.map((entry, i) => {
      const group = i % 2 === 0 ? "run-a" : "run-b";
      const algoRows = entry.rows.map((r) => `
        <tr class="${group}">
          <td class="num">${entry.run}</td>
          <td>${entry.puzzle}</td>
          <td>${r.algorithm}</td>
          <td><span class="tag ${r.success ? "success" : "fail"}">${r.success ? "risolto" : "nessuna soluzione"}</span></td>
          <td class="num">${r.nodes.toLocaleString("it-IT")}</td>
          <td class="num">${r.time_ms.toLocaleString("it-IT")} ms</td>
        </tr>`).join("");
      const deltaRow = entry.delta
        ? `<tr class="${group} delta-row"><td colspan="6">${entry.delta}</td></tr>`
        : "";
      return algoRows + deltaRow;
    }).join("");

    els.stats.innerHTML = `
      <table class="stat-table">
        <thead><tr><th>Run</th><th>Puzzle</th><th>Algoritmo</th><th>Esito</th><th>Nodi esplorati</th><th>Tempo</th></tr></thead>
        <tbody>${body}</tbody>
      </table>`;
  }

  // Wire

  els.btnGenerate.addEventListener("click", generatePuzzle);
  els.btnClear.addEventListener("click", clearPuzzle);
  els.btnSolve.addEventListener("click", solvePuzzle);

  (async function init() {
    buildSudokuDOM();
    buildGraphDOM();
    await loadGraph();
    renderAll();
  })();
})();
"use strict";

let editor = null;
let currentLevel = null;
let levels = [];

// File explorer state.
let files = [];            // [{id, label, editable}]
let currentFile = null;    // id of the file shown in the editor
let solutionCode = "";     // source of truth for solution.py (survives tab switches)

// ---- Monaco editor ----
require.config({
  paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs" },
});

function initEditor(code) {
  return new Promise((resolve) => {
    require(["vs/editor/editor.main"], () => {
      editor = monaco.editor.create(document.getElementById("editor"), {
        value: code,
        language: "python",
        theme: "vs-dark",
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 13,
      });
      // Keep the solution buffer in sync while it is the active file.
      editor.onDidChangeModelContent(() => {
        if (currentFile === "solution") solutionCode = editor.getValue();
      });
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, runTests);
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, saveSolution);
      resolve();
    });
  });
}

// ---- API ----
async function api(path, opts) {
  const res = await fetch(path, opts);
  return res.json();
}

async function loadState() {
  const state = await api("/api/state");
  levels = state.levels;
  currentLevel = state.current;
  solutionCode = state.solution || "";
  renderTabs();
  if (currentLevel) await loadLevel(currentLevel);
  if (!editor) await initEditor(solutionCode);
  files = await api("/api/files");
  renderFileTabs();
  await openFile("solution");
}

async function loadLevel(n) {
  currentLevel = n;
  renderTabs();
  const data = await api(`/api/level/${n}`);
  document.getElementById("readme").innerHTML = marked.parse(data.readme_md || "");
}

function renderTabs() {
  const nav = document.getElementById("level-tabs");
  nav.innerHTML = "";
  levels.forEach((n) => {
    const b = document.createElement("button");
    b.textContent = `Level ${n}`;
    if (n === currentLevel) b.classList.add("active");
    b.onclick = () => loadLevel(n);
    nav.appendChild(b);
  });
}

// ---- file explorer ----
function renderFileTabs() {
  const bar = document.getElementById("file-tabs");
  bar.innerHTML = "";
  files.forEach((f) => {
    const b = document.createElement("button");
    b.className = "file-tab" + (f.editable ? "" : " readonly");
    b.textContent = f.label + (f.editable ? "" : "  (read-only)");
    b.dataset.id = f.id;
    if (f.id === currentFile) b.classList.add("active");
    b.onclick = () => openFile(f.id);
    bar.appendChild(b);
  });
}

async function openFile(id) {
  const meta = files.find((f) => f.id === id);
  if (!meta || !editor) return;

  // Persist edits to the solution buffer before leaving it.
  if (currentFile === "solution") solutionCode = editor.getValue();

  let content;
  if (id === "solution") {
    content = solutionCode;
  } else {
    const data = await api(`/api/file/${id}`);
    content = data.content || "";
  }

  currentFile = id;
  editor.setValue(content);
  editor.updateOptions({ readOnly: !meta.editable });
  renderFileTabs();
}

// ---- actions (always operate on the solution, never the viewed test) ----
function syncSolution() {
  if (currentFile === "solution") solutionCode = editor.getValue();
}

async function saveSolution() {
  syncSolution();
  await api("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: solutionCode }),
  });
}

async function runTests() {
  syncSolution();
  const body = document.getElementById("results-body");
  body.innerHTML = '<span class="muted">Running…</span>';
  const data = await api("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level: currentLevel, code: solutionCode }),
  });
  renderResults(data);
}

function renderResults(data) {
  const body = document.getElementById("results-body");
  body.innerHTML = "";

  const pub = data.public;
  const sum = document.createElement("div");
  sum.className = "summary " + (pub.passed ? "ok" : "fail");
  sum.textContent = pub.passed
    ? `Public tests PASSED (levels 1..${currentLevel})`
    : `Public tests FAILED (levels 1..${currentLevel})`;
  body.appendChild(sum);

  pub.tests.forEach((t) => body.appendChild(testRow(t)));

  const h = data.hidden;
  if (h && h.total) {
    const hs = document.createElement("div");
    hs.className = "summary " + (h.passed ? "ok" : "fail");
    hs.textContent = `Hidden tests: ${h.passed_count}/${h.total} passed (feedback)`;
    body.appendChild(hs);
    h.tests.filter((t) => t.status !== "ok").forEach((t) => body.appendChild(testRow(t)));
  }
}

function testRow(t) {
  const div = document.createElement("div");
  div.className = "test " + t.status;
  const badge = { ok: "PASS", fail: "FAIL", error: "ERROR", skip: "SKIP" }[t.status] || t.status;
  div.innerHTML = `<span class="badge">${badge}</span><span>${t.short || t.name}</span>`;
  if (t.message && (t.status === "fail" || t.status === "error")) {
    const pre = document.createElement("pre");
    pre.textContent = t.message;
    div.appendChild(pre);
  }
  return div;
}

// ---- boot ----
document.getElementById("btn-run").onclick = runTests;
document.getElementById("btn-save").onclick = saveSolution;
loadState();

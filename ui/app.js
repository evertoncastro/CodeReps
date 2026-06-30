"use strict";

// Challenge id comes from the URL path, e.g. /warehouse_inventory.
const CHALLENGE = location.pathname.replace(/^\/+|\/+$/g, "");
const API = `/api/${CHALLENGE}`;

let editor = null;
let currentLevel = null;
let levels = [];

// File state.
let files = [];             // openable files: [{id, label, editable}]
let openTabs = ["solution"]; // ids open as editor tabs; solution is always present
let activeTab = "solution";  // focused tab id
let solutionCode = "";       // source of truth for solution.py (survives tab switches)
const contentCache = {};     // id -> content for read-only files

let timerInterval = null;
let locked = false;

// ---- countdown clock ----
function startTimer(remainingSeconds) {
  const el = document.getElementById("timer");
  if (timerInterval) clearInterval(timerInterval);
  let secs = Number.isFinite(remainingSeconds) ? remainingSeconds : 0;

  const render = () => {
    const left = Math.max(0, secs);
    const m = Math.floor(left / 60);
    const s = left % 60;
    el.textContent = `⏱ ${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    el.classList.toggle("expired", secs <= 0);
  };

  render();
  if (secs <= 0) lockUI();
  timerInterval = setInterval(() => {
    secs -= 1;
    render();
    if (secs <= 0) {
      clearInterval(timerInterval);
      lockUI();
    }
  }, 1000);
}

// Lock the challenge once time is up: disable actions and show a banner.
function lockUI() {
  if (locked) return;
  locked = true;
  document.getElementById("btn-run").disabled = true;
  document.getElementById("btn-save").disabled = true;
  document.getElementById("timer").classList.add("expired");
  const body = document.getElementById("results-body");
  const banner = document.createElement("div");
  banner.className = "summary fail";
  banner.textContent = "⏱ Time is up — the challenge is locked.";
  body.prepend(banner);
}

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
      editor.onDidChangeModelContent(() => {
        if (activeTab === "solution") solutionCode = editor.getValue();
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
  const state = await api(`${API}/state`);
  levels = state.levels;
  currentLevel = state.current;
  solutionCode = state.solution || "";
  if (state.title) {
    document.getElementById("brand-title").textContent = state.title;
    document.title = `${state.title} — ICA`;
  }
  startTimer(state.remaining_seconds);
  renderLevelTabs();
  if (currentLevel) await loadLevel(currentLevel);
  if (!editor) await initEditor(solutionCode);
  await refreshFiles();
  setActive("solution");
}

async function refreshFiles() {
  files = await api(`${API}/files`);
  renderExplorer();
}

async function loadLevel(n) {
  currentLevel = n;
  renderLevelTabs();
  const data = await api(`${API}/level/${n}`);
  document.getElementById("readme").innerHTML = marked.parse(data.readme_md || "");
}

function renderLevelTabs() {
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

// ---- left explorer ----
function renderExplorer() {
  const list = document.getElementById("file-list");
  list.innerHTML = "";
  files.forEach((f) => {
    const li = document.createElement("li");
    li.textContent = f.label;
    li.className = "file-item";
    if (f.id === activeTab) li.classList.add("active");
    else if (openTabs.includes(f.id)) li.classList.add("open");
    if (!f.editable) li.classList.add("readonly");
    li.onclick = () => openFile(f.id);
    list.appendChild(li);
  });
}

// ---- center open tabs ----
function renderOpenTabs() {
  const bar = document.getElementById("file-tabs");
  bar.innerHTML = "";
  openTabs.forEach((id) => {
    const meta = files.find((f) => f.id === id) || { label: id, editable: id === "solution" };
    const tab = document.createElement("span");
    tab.className = "file-tab" + (id === activeTab ? " active" : "");
    const name = document.createElement("button");
    name.className = "file-tab-name";
    name.textContent = meta.label;
    name.onclick = () => setActive(id);
    tab.appendChild(name);
    if (id !== "solution") {
      const close = document.createElement("button");
      close.className = "file-tab-close";
      close.textContent = "×";
      close.title = "Close";
      close.onclick = (e) => { e.stopPropagation(); closeFile(id); };
      tab.appendChild(close);
    }
    bar.appendChild(tab);
  });
}

async function openFile(id) {
  if (!openTabs.includes(id)) openTabs.push(id);
  await setActive(id);
}

async function setActive(id) {
  const meta = files.find((f) => f.id === id) || { editable: id === "solution" };
  if (!editor) return;
  if (activeTab === "solution") solutionCode = editor.getValue();

  let content;
  if (id === "solution") {
    content = solutionCode;
  } else if (contentCache[id] !== undefined) {
    content = contentCache[id];
  } else {
    const data = await api(`${API}/file/${id}`);
    content = data.content || "";
    contentCache[id] = content;
  }

  activeTab = id;
  editor.setValue(content);
  editor.updateOptions({ readOnly: !meta.editable });
  renderOpenTabs();
  renderExplorer();
}

function closeFile(id) {
  if (id === "solution") return;
  openTabs = openTabs.filter((t) => t !== id);
  if (activeTab === id) setActive(openTabs[openTabs.length - 1] || "solution");
  else { renderOpenTabs(); renderExplorer(); }
}

// ---- actions (always operate on the solution buffer) ----
function syncSolution() {
  if (activeTab === "solution") solutionCode = editor.getValue();
}

async function saveSolution() {
  if (locked) return;
  syncSolution();
  const res = await api(`${API}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: solutionCode }),
  });
  if (res.error === "time_up") lockUI();
}

async function runTests() {
  if (locked) return;
  syncSolution();
  const body = document.getElementById("results-body");
  body.innerHTML = '<span class="muted">Running…</span>';
  const data = await api(`${API}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level: currentLevel, code: solutionCode }),
  });
  if (data.error === "time_up") {
    lockUI();
    return;
  }
  if (Array.isArray(data.unlocked)) {
    levels = data.unlocked;
    renderLevelTabs();
    await refreshFiles();
  }
  renderResults(data);
}

function renderResults(data) {
  const body = document.getElementById("results-body");
  body.innerHTML = "";

  if (data.unlocked_now) {
    const u = document.createElement("div");
    u.className = "summary ok";
    u.textContent = `🎉 Level ${data.unlocked_now} unlocked!`;
    body.appendChild(u);
  }

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

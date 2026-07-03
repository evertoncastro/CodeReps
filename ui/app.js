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
const models = {};           // id -> Monaco text model (holds content + undo history)
const viewStates = {};       // id -> editor view state (scroll + cursor), per file

function solutionValue() {
  return models["solution"] ? models["solution"].getValue() : "";
}

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

// Challenge finished (last level passed): stop the clock and turn it green.
function markComplete() {
  if (timerInterval) clearInterval(timerInterval);
  const t = document.getElementById("timer");
  t.classList.remove("expired");
  t.classList.add("done");
}

function successBanner() {
  const div = document.createElement("div");
  div.className = "success-banner";
  div.textContent = "🎉 Challenge complete — all levels passed!";
  return div;
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

function initEditor(initialSolution) {
  return new Promise((resolve) => {
    require(["vs/editor/editor.main"], () => {
      models["solution"] = monaco.editor.createModel(initialSolution, "python");
      editor = monaco.editor.create(document.getElementById("editor"), {
        model: models["solution"],
        theme: "vs-dark",
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 13,
        wordWrap: "off", // long lines scroll left/right instead of wrapping
        scrollbar: {
          // Keep the horizontal scrollbar visible (not auto-hiding) and easy to
          // grab, so long lines can be scrolled left/right like in VS Code.
          horizontal: "visible",
          horizontalScrollbarSize: 14,
          verticalScrollbarSize: 14,
        },
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
  if (state.title) {
    document.getElementById("brand-title").textContent = state.title;
    document.title = `${state.title} — ICA`;
  }
  startTimer(state.remaining_seconds);
  if (state.challenge_complete) {
    markComplete();
    const body = document.getElementById("results-body");
    body.innerHTML = "";
    body.appendChild(successBanner());
  }
  renderLevelTabs();
  if (currentLevel) await loadLevel(currentLevel);
  if (!editor) await initEditor(state.solution || "");
  await refreshFiles();
  setActive("solution");
}

async function refreshFiles() {
  files = await api(`${API}/files`);
  renderExplorer();
}

function updateRunButton() {
  const btn = document.getElementById("btn-run");
  btn.textContent = currentLevel ? `Run tests for level ${currentLevel}` : "Run tests";
}

async function loadLevel(n) {
  currentLevel = n;
  renderLevelTabs();
  updateRunButton();
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
  if (!editor) return;
  const meta = files.find((f) => f.id === id) || { editable: id === "solution" };

  // Save the current file's scroll/cursor before switching away, so each file
  // keeps its own view position.
  if (activeTab) viewStates[activeTab] = editor.saveViewState();

  let model = models[id];
  if (!model) {
    let content = "";
    if (id !== "solution") {
      const data = await api(`${API}/file/${id}`);
      content = data.content || "";
    }
    model = monaco.editor.createModel(content, "python");
    models[id] = model;
  }

  editor.setModel(model);
  editor.updateOptions({ readOnly: !meta.editable });
  if (viewStates[id]) editor.restoreViewState(viewStates[id]);
  else editor.setScrollTop(0);
  activeTab = id;
  editor.focus();
  renderOpenTabs();
  renderExplorer();
}

function closeFile(id) {
  if (id === "solution") return;
  openTabs = openTabs.filter((t) => t !== id);
  if (activeTab === id) setActive(openTabs[openTabs.length - 1] || "solution");
  else { renderOpenTabs(); renderExplorer(); }
}

// ---- actions (always operate on the solution model, never the viewed test) ----
async function restartChallenge() {
  const data = await api(`${API}/restart`, { method: "POST" });
  // Unlock the UI (the timer may have been expired) and restart the countdown.
  locked = false;
  document.getElementById("btn-run").disabled = false;
  document.getElementById("btn-save").disabled = false;
  document.getElementById("timer").classList.remove("expired");
  const body = document.getElementById("results-body");
  body.innerHTML = '<span class="muted">Timer restarted. Run the tests to see results.</span>';
  startTimer(data.remaining_seconds);
}

async function saveSolution() {
  if (locked) return;
  const res = await api(`${API}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: solutionValue() }),
  });
  if (res.error === "time_up") lockUI();
}

async function runTests() {
  if (locked) return;
  const body = document.getElementById("results-body");
  body.innerHTML = '<span class="muted">Running…</span>';
  const data = await api(`${API}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level: currentLevel, code: solutionValue() }),
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
  if (data.challenge_complete) markComplete();
  // Passing unlocks the next level — move to it automatically.
  if (data.unlocked_now) await loadLevel(data.unlocked_now);
}

function renderResults(data) {
  const body = document.getElementById("results-body");
  body.innerHTML = "";

  if (data.challenge_complete) {
    body.appendChild(successBanner());
  }

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
    hs.textContent = `Hidden tests: ${h.passed_count}/${h.total} passed`;
    body.appendChild(hs);
    h.tests.filter((t) => t.status !== "ok").forEach((t) => body.appendChild(testRow(t)));
  }
}

function testRow(t) {
  const div = document.createElement("div");
  div.className = "test " + t.status;
  const badge = { ok: "PASS", fail: "FAIL", error: "ERROR", skip: "SKIP" }[t.status] || t.status;

  const head = document.createElement("div");
  head.className = "test-head";
  head.innerHTML = `<span class="badge">${badge}</span><span class="test-name">${t.short || t.name}</span>`;
  div.appendChild(head);

  if (t.message && (t.status === "fail" || t.status === "error")) {
    const pre = document.createElement("pre");
    pre.className = "test-detail";
    pre.textContent = t.message;
    div.appendChild(pre);
  }
  return div;
}

// ---- resizable panels (IDE-style draggable gutters) ----
function initSplit() {
  const KEY = "ica-split-sizes";
  let saved = null;
  try {
    saved = JSON.parse(localStorage.getItem(KEY) || "null");
  } catch (e) {
    saved = null;
  }
  Split(["#statement", "#center", "#right"], {
    sizes: saved || [28, 44, 28],
    minSize: [180, 320, 220],
    gutterSize: 6,
    snapOffset: 0,
    elementStyle: (dim, size, gutterSize) => ({
      "flex-basis": `calc(${size}% - ${gutterSize}px)`,
    }),
    gutterStyle: (dim, gutterSize) => ({ "flex-basis": `${gutterSize}px` }),
    onDragEnd: (sizes) => localStorage.setItem(KEY, JSON.stringify(sizes)),
  });
}

// ---- boot ----
document.getElementById("btn-run").onclick = runTests;
document.getElementById("btn-save").onclick = saveSolution;
document.getElementById("btn-restart").onclick = restartChallenge;
initSplit();
loadState();

"use strict";

// The IDE URL is /<format>/<challenge>/run/<runId>.
const M = location.pathname.match(/^\/([^/]+)\/([^/]+)\/run\/(\d+)$/);
const FORMAT = M ? M[1] : "";
const CHALLENGE = M ? M[2] : "";
const RUN_ID = M ? M[3] : "";
const API = `/api/${FORMAT}/${CHALLENGE}/run/${RUN_ID}`;

let editor = null;
let currentStage = null;
let stages = [];
let totalStages = 0;
let stageLabel = "Stage";
let readOnly = false;

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
let autosaveTimer = null;

// ---- helpers ----
function fmtDuration(secs) {
  secs = Math.max(0, Math.round(secs || 0));
  return `${String(Math.floor(secs / 60)).padStart(2, "0")}:${String(secs % 60).padStart(2, "0")}`;
}
function fmtDate(epoch) {
  return epoch ? new Date(epoch * 1000).toLocaleString() : "—";
}

// ---- clock: the timebox is a target; it keeps counting past 0 (overtime) ----
function startTimer(remainingSeconds) {
  const el = document.getElementById("timer");
  if (timerInterval) clearInterval(timerInterval);
  let secs = Number.isFinite(remainingSeconds) ? remainingSeconds : 0;

  const render = () => {
    if (secs >= 0) {
      el.textContent = `⏱ ${fmtDuration(secs)}`;
      el.classList.remove("overtime");
    } else {
      el.textContent = `⏱ +${fmtDuration(-secs)} over`;
      el.classList.add("overtime");
    }
  };

  render();
  timerInterval = setInterval(() => {
    secs -= 1;
    render();
  }, 1000);
}

// Challenge finished (last stage passed): stop the clock and turn it green.
function markComplete() {
  if (timerInterval) clearInterval(timerInterval);
  const t = document.getElementById("timer");
  t.classList.remove("overtime", "expired");
  t.classList.add("done");
}

function successBanner(overTime) {
  const div = document.createElement("div");
  div.className = "success-banner";
  const all = `all ${stageLabel.toLowerCase()}s passed`;
  div.textContent = overTime
    ? `🎉 Challenge complete — ${all} (over the time limit).`
    : `🎉 Challenge complete — ${all}!`;
  return div;
}

// ---- pause/resume: the clock only runs while the attempt is open ----
async function resumeTimer() {
  const r = await api(`${API}/resume`, { method: "POST" });
  if (r) startTimer(r.remaining_seconds);
}

function pauseTimer() {
  if (readOnly) return;
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
  if (navigator.sendBeacon) navigator.sendBeacon(`${API}/pause`);
  else api(`${API}/pause`, { method: "POST" });
}

// ---- autosave (debounced), replaces the old Save button ----
function scheduleAutosave() {
  if (readOnly) return;
  if (autosaveTimer) clearTimeout(autosaveTimer);
  autosaveTimer = setTimeout(flushAutosave, 800);
}

async function flushAutosave() {
  if (autosaveTimer) { clearTimeout(autosaveTimer); autosaveTimer = null; }
  if (readOnly) return;
  await api(`${API}/autosave`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: solutionValue() }),
  });
}

// ---- Monaco editor ----
require.config({
  paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs" },
});

function initEditor(initialSolution) {
  return new Promise((resolve) => {
    require(["vs/editor/editor.main"], () => {
      models["solution"] = monaco.editor.createModel(initialSolution, "python");
      // Autosave only the solution model — never a focused read-only test tab.
      models["solution"].onDidChangeContent(scheduleAutosave);
      editor = monaco.editor.create(document.getElementById("editor"), {
        model: models["solution"],
        theme: "vs-dark",
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 13,
        wordWrap: "off",
        scrollbar: {
          horizontal: "visible",
          horizontalScrollbarSize: 14,
          verticalScrollbarSize: 14,
        },
      });
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, runTests);
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, flushAutosave);
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
  stages = state.stages;
  totalStages = state.total_stages || stages.length;
  currentStage = state.current;
  stageLabel = state.stage_label || "Stage";
  readOnly = state.read_only;
  document.querySelector(".brand").setAttribute("href", `/${FORMAT}/${CHALLENGE}`);
  if (state.title) {
    document.getElementById("brand-title").textContent = state.title;
    document.title = state.title;
  }
  renderStageTabs();
  if (currentStage) await loadStage(currentStage);
  if (!editor) await initEditor(state.solution || "");
  else models["solution"].setValue(state.solution || "");
  await refreshFiles();
  setActive("solution");

  if (readOnly) {
    enterViewMode(state);
  } else {
    await resumeTimer(); // starts counting active time for this attempt
  }
}

// Finished/expired attempt: read-only review of the final code + performance.
function enterViewMode(state) {
  document.getElementById("btn-run").disabled = true;
  const t = document.getElementById("timer");
  if (state.status === "completed") {
    t.textContent = `⏱ ${fmtDuration(state.duration_seconds)}`;
    t.classList.add("done");
  } else {
    t.textContent = "⏱ 00:00";
    t.classList.add("expired");
  }
  renderPerformance(state);
}

function renderPerformance(state) {
  const body = document.getElementById("results-body");
  body.innerHTML = "";
  const done = state.status === "completed";
  if (done) body.appendChild(successBanner(state.over_time));

  const sum = document.createElement("div");
  sum.className = "summary " + (done ? "ok" : "fail");
  sum.textContent = done
    ? totalStages > 1
      ? `Completed all ${state.total_stages} ${stageLabel.toLowerCase()}s`
      : "Completed"
    : `Reached ${stageLabel.toLowerCase()} ${state.completed}/${state.total_stages}`;
  body.appendChild(sum);

  const limit = (state.timebox_minutes || 0) * 60;
  const withinLine = done
    ? (state.over_time
        ? `<div>Within time limit: no (limit ${fmtDuration(limit)})</div>`
        : `<div>Within time limit: yes</div>`)
    : "";
  const info = document.createElement("div");
  info.className = "perf muted";
  info.innerHTML =
    `<div>${stageLabel}s completed: ${state.completed}/${state.total_stages}</div>` +
    `<div>Time taken: ${state.duration_seconds != null ? fmtDuration(state.duration_seconds) : "—"}</div>` +
    withinLine +
    `<div>Started: ${fmtDate(state.started_at)}</div>` +
    `<div>Ended: ${fmtDate(state.ended_at)}</div>` +
    `<div style="margin-top:8px">Read-only — start a new attempt to try again.</div>`;
  body.appendChild(info);
}

async function refreshFiles() {
  files = await api(`${API}/files`);
  renderExplorer();
}

function updateRunButton() {
  const btn = document.getElementById("btn-run");
  // A single-stage format has nothing to disambiguate.
  btn.textContent =
    currentStage && totalStages > 1
      ? `Run tests for ${stageLabel.toLowerCase()} ${currentStage}`
      : "Run tests";
}

async function loadStage(n) {
  currentStage = n;
  renderStageTabs();
  updateRunButton();
  const data = await api(`${API}/stage/${n}`);
  document.getElementById("readme").innerHTML = marked.parse(data.doc_md || "");
}

function renderStageTabs() {
  const nav = document.getElementById("stage-tabs");
  nav.innerHTML = "";
  // Single-stage formats (one window, no progression) get no tab strip. Keyed
  // on the TOTAL, so ICA still shows its tabs while only level 1 is unlocked.
  if (totalStages < 2) return;
  stages.forEach((n) => {
    const b = document.createElement("button");
    b.textContent = `${stageLabel} ${n}`;
    if (n === currentStage) b.classList.add("active");
    b.onclick = () => loadStage(n);
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

  // Save the current file's scroll/cursor before switching away.
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
  // A read-only attempt makes even the solution read-only.
  editor.updateOptions({ readOnly: readOnly || !meta.editable });
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

// ---- actions ----
async function newAttempt() {
  pauseTimer(); // stop the clock on the attempt we're leaving
  const res = await api(`/api/${FORMAT}/${CHALLENGE}/runs`, { method: "POST" });
  if (res && res.run_id) location.href = `/${FORMAT}/${CHALLENGE}/run/${res.run_id}`;
}

async function runTests() {
  if (readOnly) return;
  await flushAutosave();
  const body = document.getElementById("results-body");
  body.innerHTML = '<span class="muted">Running…</span>';
  const data = await api(`${API}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stage: currentStage, code: solutionValue() }),
  });
  if (data.error === "read_only") return;
  if (Array.isArray(data.unlocked)) {
    stages = data.unlocked;
    renderStageTabs();
    await refreshFiles();
  }
  renderResults(data);
  if (data.challenge_complete) {
    markComplete();
    readOnly = true;
    editor.updateOptions({ readOnly: true });
    document.getElementById("btn-run").disabled = true;
  }
  // Passing unlocks the next stage — move to it automatically.
  if (data.unlocked_now) await loadStage(data.unlocked_now);
}

function renderResults(data) {
  const body = document.getElementById("results-body");
  body.innerHTML = "";

  if (data.challenge_complete) {
    body.appendChild(successBanner(data.over_time));
  }

  if (data.unlocked_now) {
    const u = document.createElement("div");
    u.className = "summary ok";
    u.textContent = `🎉 ${stageLabel} ${data.unlocked_now} unlocked!`;
    body.appendChild(u);
  }

  const pub = data.public;
  const sum = document.createElement("div");
  sum.className = "summary " + (pub.passed ? "ok" : "fail");
  sum.textContent = pub.passed
    ? `Public tests PASSED${scopeSuffix()}`
    : `Public tests FAILED${scopeSuffix()}`;
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

// "(levels 1..3)" only means something when stages accumulate.
function scopeSuffix() {
  return totalStages > 1 ? ` (${stageLabel.toLowerCase()}s 1..${currentStage})` : "";
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
  if (t.output) {
    const out = document.createElement("pre");
    out.className = "test-output";
    out.textContent = t.output;
    div.appendChild(out);
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

// Pause the clock when leaving/hiding the attempt; resume when it's visible again.
document.addEventListener("visibilitychange", () => {
  if (readOnly) return;
  if (document.hidden) pauseTimer();
  else resumeTimer();
});
window.addEventListener("pagehide", () => {
  if (!readOnly) pauseTimer();
});

// ---- boot ----
document.getElementById("btn-run").onclick = runTests;
document.getElementById("btn-restart").onclick = newAttempt;
initSplit();
loadState();

"use strict";

// The attempts page URL is /<challenge>.
const CID = location.pathname.replace(/^\/+|\/+$/g, "");

function fmtDur(s) {
  s = Math.max(0, Math.round(s || 0));
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}
function fmtDate(e) {
  return e ? new Date(e * 1000).toLocaleString() : "—";
}

function timeInfo(r) {
  if (r.status === "in_progress") {
    const rem = r.remaining_seconds || 0;
    return rem > 0 ? `${Math.ceil(rem / 60)} min left` : "over time";
  }
  if (r.status === "completed") return `time taken: ${fmtDur(r.duration_seconds)}`;
  return "time up";
}

async function newAttempt() {
  const res = await fetch(`/api/${CID}/runs`, { method: "POST" });
  const d = await res.json();
  if (d.run_id) location.href = `/${CID}/run/${d.run_id}`;
}

async function deleteAttempt(id) {
  if (!confirm(`Delete attempt #${id}? This cannot be undone.`)) return;
  await fetch(`/api/${CID}/run/${id}`, { method: "DELETE" });
  load();
}

async function load() {
  document.getElementById("btn-new").onclick = newAttempt;
  const res = await fetch(`/api/${CID}/runs`);
  const data = await res.json();

  if (data.title) {
    document.getElementById("brand-title").textContent = data.title;
    document.title = `${data.title} — Attempts`;
  }

  const root = document.getElementById("challenge-list");
  root.innerHTML = "";
  if (!data.runs.length) {
    root.innerHTML = '<p class="muted">No attempts yet. Click “New attempt” to start.</p>';
    return;
  }

  const labels = { in_progress: "In progress", completed: "Completed", expired: "Expired" };
  data.runs.forEach((r) => {
    const card = document.createElement("a");
    card.className = "challenge-card attempt-card";
    card.href = `/${CID}/run/${r.id}`;
    const action = r.status === "in_progress" ? "Continue" : "View";
    card.innerHTML =
      `<h2>Attempt #${r.id} ` +
      `<span class="attempt-status ${r.status}">${labels[r.status] || r.status}</span></h2>` +
      `<div class="meta">` +
      `<span>started: ${fmtDate(r.started_at)}</span>` +
      `<span>levels: ${r.completed_level}/${r.total_levels}</span>` +
      `<span>${timeInfo(r)}</span>` +
      `<span class="status">${action} →</span>` +
      `</div>`;

    const del = document.createElement("button");
    del.className = "attempt-delete";
    del.title = "Delete attempt";
    del.textContent = "🗑";
    del.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      deleteAttempt(r.id);
    };
    card.appendChild(del);

    root.appendChild(card);
  });
}

load();

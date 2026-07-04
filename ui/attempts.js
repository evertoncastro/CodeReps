"use strict";

// The attempts page URL is /<challenge>.
const CID = location.pathname.replace(/^\/+|\/+$/g, "");
let showArchived = false;

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

async function setArchived(id, archived, number) {
  const verb = archived ? "Archive" : "Unarchive";
  if (!confirm(`${verb} attempt #${number}?`)) return;
  await fetch(`/api/${CID}/run/${id}/${archived ? "archive" : "unarchive"}`, { method: "POST" });
  load();
}

function toggleArchived() {
  showArchived = !showArchived;
  load();
}

async function load() {
  document.getElementById("btn-new").onclick = newAttempt;
  const toggle = document.getElementById("btn-toggle");
  toggle.onclick = toggleArchived;
  toggle.textContent = showArchived ? "Hide archived" : "Show archived";
  toggle.classList.toggle("active", showArchived);

  const res = await fetch(`/api/${CID}/runs${showArchived ? "?all=1" : ""}`);
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
    card.className = "challenge-card attempt-card" + (r.archived ? " archived" : "");
    card.href = `/${CID}/run/${r.id}`;
    const action = r.status === "in_progress" ? "Continue" : "View";
    card.innerHTML =
      `<h2>Attempt #${r.number} ` +
      `<span class="attempt-status ${r.status}">${labels[r.status] || r.status}</span>` +
      (r.archived ? `<span class="attempt-status archived-tag">Archived</span>` : "") +
      `</h2>` +
      `<div class="meta">` +
      `<span>started: ${fmtDate(r.started_at)}</span>` +
      `<span>levels: ${r.completed_level}/${r.total_levels}</span>` +
      `<span>${timeInfo(r)}</span>` +
      `<span class="status">${action} →</span>` +
      `</div>`;

    const btn = document.createElement("button");
    btn.className = "attempt-archive";
    btn.title = r.archived ? "Unarchive attempt" : "Archive attempt";
    btn.textContent = r.archived ? "↩" : "🗄";
    btn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      setArchived(r.id, !r.archived, r.number);
    };
    card.appendChild(btn);

    root.appendChild(card);
  });
}

load();

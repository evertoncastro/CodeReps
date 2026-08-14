"use strict";

// The challenge list URL is /<format>.
const FORMAT = location.pathname.replace(/^\/+|\/+$/g, "");

function statusText(c) {
  if (c.has_active) return "in progress";
  if (c.best_completed >= c.stages && c.stages > 0) return "completed";
  if (c.attempts) return "tried";
  return "not started";
}

async function load() {
  const root = document.getElementById("challenge-list");
  const res = await fetch(`/api/${FORMAT}/challenges`);
  const data = await res.json();
  const challenges = data.challenges || [];

  if (data.format && data.format.title) {
    document.getElementById("brand-title").textContent = data.format.title;
    document.title = data.format.title;
  }

  if (!challenges.length) {
    root.innerHTML = `<p class="muted">No challenges found under challenges/${FORMAT}/.</p>`;
    return;
  }

  challenges.forEach((c) => {
    const card = document.createElement("a");
    card.className = "challenge-card";
    card.href = `/${FORMAT}/${c.id}`;
    const stageLabel = (c.stage_label || "stage").toLowerCase();
    const done = c.best_completed >= c.stages && c.stages > 0;
    card.innerHTML = `
      <h2>${c.title}</h2>
      <div class="meta">
        <span>${c.stages} ${stageLabel}s</span>
        <span>${c.timebox_minutes} min</span>
        <span>${c.attempts} attempt(s)</span>
        <span>best: ${c.best_completed}/${c.stages}${done ? " ✓" : ""}</span>
        <span class="status">${statusText(c)}</span>
      </div>`;
    root.appendChild(card);
  });
}

load();

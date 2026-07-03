"use strict";

function statusText(c) {
  if (c.has_active) return "in progress";
  if (c.best_completed >= c.levels && c.levels > 0) return "completed";
  if (c.attempts) return "tried";
  return "not started";
}

async function load() {
  const root = document.getElementById("challenge-list");
  const res = await fetch("/api/challenges");
  const challenges = await res.json();

  if (!challenges.length) {
    root.innerHTML = '<p class="muted">No challenges found under challenges/.</p>';
    return;
  }

  challenges.forEach((c) => {
    const card = document.createElement("a");
    card.className = "challenge-card";
    card.href = "/" + c.id;
    const done = c.best_completed >= c.levels && c.levels > 0;
    card.innerHTML = `
      <h2>${c.title}</h2>
      <div class="meta">
        <span>${c.levels} levels</span>
        <span>${c.timebox_minutes} min</span>
        <span>${c.attempts} attempt(s)</span>
        <span>best: ${c.best_completed}/${c.levels}${done ? " ✓" : ""}</span>
        <span class="status">${statusText(c)}</span>
      </div>`;
    root.appendChild(card);
  });
}

load();

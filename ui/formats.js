"use strict";

// The landing page: one card per assessment format.
async function load() {
  const root = document.getElementById("challenge-list");
  const res = await fetch("/api/formats");
  const formats = await res.json();

  if (!formats.length) {
    root.innerHTML = '<p class="muted">No assessment formats registered.</p>';
    return;
  }

  formats.forEach((f) => {
    const card = document.createElement("a");
    card.className = "challenge-card";
    card.href = "/" + f.id;
    card.innerHTML = `
      <h2>${f.title}</h2>
      <p class="format-description">${f.description}</p>
      <div class="meta">
        <span>${f.challenges} challenge(s)</span>
        <span>${f.attempts} attempt(s)</span>
        <span class="status">Open →</span>
      </div>`;
    root.appendChild(card);
  });
}

load();

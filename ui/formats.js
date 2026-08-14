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
    // An unavailable format (missing dependency) is shown, not hidden: silently
    // vanishing looks like a bug in the app rather than a missing package.
    const card = document.createElement(f.available ? "a" : "div");
    card.className = "challenge-card" + (f.available ? "" : " unavailable");
    if (f.available) card.href = "/" + f.id;
    card.innerHTML = f.available
      ? `
      <h2>${f.title}</h2>
      <p class="format-description">${f.description}</p>
      <div class="meta">
        <span>${f.challenges} challenge(s)</span>
        <span>${f.attempts} attempt(s)</span>
        <span class="status">Open →</span>
      </div>`
      : `
      <h2>${f.title}</h2>
      <p class="format-description">Unavailable: ${f.unavailable_reason}</p>
      <div class="meta">
        <span class="status">install its dependencies to enable it</span>
      </div>`;
    root.appendChild(card);
  });
}

load();

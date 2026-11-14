// Catálogo de experimentos reales (viene de data/knowledge/experiments.json vía /api/catalog).
import { api } from "./api.js";

const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;");

export async function initCatalog(onAsk) {
  const items = await api.catalog();
  const box = document.getElementById("catalog");
  const render = (q = "") => {
    const ql = q.toLowerCase();
    const list = items.filter((c) => !ql || JSON.stringify(c).toLowerCase().includes(ql));
    box.innerHTML = list.map((c) => `
      <div class="card exp">
        <span class="tag real">DATO REAL</span>${c.psi_available ? '<span class="tag">EN PSI</span>' : ""}
        ${c.tags.map((t) => `<span class="tag">${esc(t)}</span>`).join("")}
        <h3>${esc(c.id)}</h3><div class="full">${esc(c.name)} · ${esc(c.platform)}</div>
        <p>${esc(c.summary)}</p>
        <p><b>Hallazgo:</b> ${esc(c.finding)}</p>
        <div class="safety"><b>Lección de seguridad →</b> ${esc(c.safety)}</div>
        <div class="note">${(c.sources || []).map((u, i) => `<a href="${esc(u)}" target="_blank" rel="noopener">fuente ${i + 1}</a>`).join(" · ")}</div>
        <button class="ask" data-id="${esc(c.id)}">Preguntar a la IA →</button>
      </div>`).join("") || '<p class="note">Sin resultados.</p>';
    box.querySelectorAll(".ask").forEach((b) => (b.onclick = () =>
      onAsk(`Explícame ${b.dataset.id} en lenguaje sencillo y qué significa para diseñar un hábitat lunar.`)));
  };
  document.getElementById("search").addEventListener("input", (e) => render(e.target.value));
  render();
}

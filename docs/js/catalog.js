// Catálogo de experimentos reales (viene de data/knowledge/experiments.json vía /api/catalog).
import { api } from "./api.js";
import { t, pick } from "./i18n.js";

const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;");

export async function initCatalog(onAsk) {
  const items = await api.catalog();
  const box = document.getElementById("catalog");
  const render = (q = "") => {
    const ql = q.toLowerCase();
    const list = items.filter((c) => !ql || JSON.stringify(c).toLowerCase().includes(ql));
    box.innerHTML = list.map((c) => `
      <div class="glass card exp">
        <span class="tag real">${t("realData")}</span>${c.psi_available ? `<span class="tag">${t("inPsi")}</span>` : ""}
        ${pick(c, "tags").map((g) => `<span class="tag">${esc(g)}</span>`).join("")}
        <h3>${esc(c.id)}</h3><div class="full">${esc(pick(c, "name"))} · ${esc(pick(c, "platform"))}</div>
        <p>${esc(pick(c, "summary"))}</p>
        <p><b>${t("finding")}</b> ${esc(pick(c, "finding"))}</p>
        <div class="safety"><b>${t("lesson")}</b> ${esc(pick(c, "safety"))}</div>
        <div class="note">${(c.sources || []).map((u, i) => `<a href="${esc(u)}" target="_blank" rel="noopener">${t("source")} ${i + 1}</a>`).join(" · ")}</div>
        <button class="ask" data-id="${esc(c.id)}"><img src="img/mascot-head.webp" alt="">${t("askAi")}</button>
      </div>`).join("") || `<p class="note">${t("noResults")}</p>`;
    box.querySelectorAll(".ask").forEach((b) => (b.onclick = () =>
      onAsk(t("askAbout", { id: b.dataset.id }))));
  };
  document.getElementById("search").addEventListener("input", (e) => render(e.target.value));
  render();
}

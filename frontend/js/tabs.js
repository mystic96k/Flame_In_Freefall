// Pestañas: cada sección vive en su propio espacio. La URL guarda la pestaña (#simulador, #asistente…).
const TABS = ["inicio", "simulador", "datos", "experimentos", "mas-datos", "asistente"];

export function showTab(name, { push = true } = {}) {
  if (!TABS.includes(name)) name = "inicio";
  document.querySelectorAll("[data-panel]").forEach((p) => { p.hidden = p.dataset.panel !== name; });
  document.querySelectorAll(".tabs [data-tab]").forEach((b) => {
    const on = b.dataset.tab === name;
    b.classList.toggle("on", on);
    b.setAttribute("aria-selected", on);
  });
  document.body.dataset.tab = name;
  if (push && location.hash !== "#" + name) history.replaceState(null, "", location.pathname + location.search + "#" + name);
  window.scrollTo({ top: 0, behavior: "smooth" });
  window.dispatchEvent(new Event("resize")); // las gráficas y la llama se ajustan al hacerse visibles
}

export function initTabs() {
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-tab]");
    if (!el) return;
    e.preventDefault();
    showTab(el.dataset.tab);
  });
  window.addEventListener("hashchange", () => showTab(location.hash.slice(1), { push: false }));
  showTab(location.hash.slice(1) || "inicio", { push: false });
}

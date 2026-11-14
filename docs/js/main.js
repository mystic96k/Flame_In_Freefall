// Punto de entrada: carga datos del backend e inicializa cada módulo.
import { api, MODE } from "./api.js";
import { initSimulator } from "./simulator.js";
import { initCharts } from "./charts.js";
import { initCatalog } from "./catalog.js";
import { initExtra } from "./extra.js";
import { initChat, ask } from "./chat.js";

function initNav() {
  const go = (id) => {
    document.getElementById(id).scrollIntoView({ behavior: "smooth", block: "start" });
    document.querySelectorAll("nav button").forEach((b) => b.classList.toggle("on", b.dataset.go === id));
  };
  document.querySelectorAll("nav button").forEach((b) => (b.onclick = () => go(b.dataset.go)));
}

async function main() {
  initNav();
  try {
    const [health, summary] = await Promise.all([api.health(), api.summary()]);
    if (summary.uses_demo_data) document.getElementById("demo-banner").classList.remove("hidden");
    initSimulator(summary.materials);
    initChat(health.llm, MODE);
    await Promise.all([initCharts(summary), initCatalog(ask), initExtra().catch((e) => console.warn("extra", e))]);
  } catch (e) {
    document.getElementById("r-insight").innerHTML =
      `<b>No pude conectar con el backend.</b><br>${e.message}<br>¿Ya corriste <code>python -m pipeline.run_pipeline</code>, <code>python -m ml.train_classifier</code> y <code>uvicorn api.main:app</code>?`;
  }
}

main();

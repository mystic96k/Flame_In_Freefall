// Punto de entrada: carga datos del backend e inicializa cada módulo.
import { applyStatic, t } from "./i18n.js?v=36f3875c";
import { api, MODE } from "./api.js?v=36f3875c";
import { initSimulator } from "./simulator.js?v=36f3875c";
import { initCharts } from "./charts.js?v=36f3875c";
import { initCatalog } from "./catalog.js?v=36f3875c";
import { initExtra } from "./extra.js?v=36f3875c";
import { initChat, ask } from "./chat.js?v=36f3875c";
import { initTabs } from "./tabs.js?v=36f3875c";

const fmt = (n) => (n == null ? "—" : String(n));

async function main() {
  applyStatic();
  initTabs();
  try {
    const [health, summary] = await Promise.all([api.health(), api.summary()]);
    if (summary.uses_demo_data) document.getElementById("demo-banner").classList.remove("hidden");
    initSimulator(summary.materials);
    initChat(health.llm, MODE);
    document.getElementById("h-n").textContent = fmt(summary.n_runs);
    api.extra().then((e) => {
      document.getElementById("h-flex").textContent = fmt(e?.flex?.n_tests);
      document.getElementById("h-gas").textContent = fmt(e?.gases?.n_tests);
    }).catch(() => {});
    await Promise.all([initCharts(summary), initCatalog(ask), initExtra().catch((e) => console.warn("extra", e))]);
  } catch (e) {
    document.getElementById("r-insight").innerHTML =
      `${t("noBackend")}<br>${e.message}<br>¿Ya corriste <code>python -m pipeline.run_pipeline</code>, <code>python -m ml.train_classifier</code> y <code>uvicorn api.main:app</code>?`;
  }
}

main();

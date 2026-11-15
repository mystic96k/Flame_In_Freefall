// Controles del simulador: sliders → estado → /api/predict → lecturas.
import { api } from "./api.js?v=530f90a1";
import { scenario, setScenario, setPrediction, onScenario } from "./state.js?v=530f90a1";
import { startFlame } from "./flame.js?v=530f90a1";
import { t, material } from "./i18n.js?v=530f90a1";

const $ = (id) => document.getElementById(id);
const shapeName = (g) => t(g < 0.05 ? "sphere" : g < 0.5 ? "dome" : "teardrop");

function explain(p) {
  const s = scenario;
  const loc = p.limiting_o2_pct != null ? `${p.limiting_o2_pct.toFixed(1)}%` : t("moreThan60");
  const v = { flow: s.flow_cm_s.toFixed(0), mat: material(s.material), loc };
  let out;
  if (s.gravity_g < 0.05 && s.flow_cm_s < 2) out = t("simNoFlow");
  else if (s.gravity_g < 0.05) out = t("simMicro", v);
  else if (s.gravity_g < 0.5) out = t("simPartial", v);
  else out = t("simEarth", v);
  if (p.extrapolating) out += ` <span class="tag demo">${t("extrapolating")}</span> ${t("outOfRange")}`;
  return out;
}

function render(p) {
  $("r-risk").textContent = `${p.risk_score}/100`;
  $("r-risk").style.color = p.risk_score > 70 ? "var(--bad)" : p.risk_score > 35 ? "var(--flame2)" : "var(--ok)";
  $("r-meter").style.width = `${p.risk_score}%`;
  $("r-loc").textContent = p.limiting_o2_pct != null ? `${p.limiting_o2_pct.toFixed(1)} %` : "> 60 %";
  $("r-margin").textContent = p.margin_pct != null
    ? `${p.margin_pct >= 0 ? "+" : ""}${p.margin_pct.toFixed(1)} ${t("vsLimit")}` +
      (p.predicted_spread_mm_s ? ` · ${t("spread")} ~${p.predicted_spread_mm_s} mm/s` : "")
    : "";
  const burning = p.state === "burning";
  $("b-state").textContent = `${t("state")} · ${t(burning ? (p.burn_probability < 0.7 ? "edge" : "burning") : "out")}`;
  $("b-state").style.color = burning ? (p.burn_probability < 0.7 ? "var(--flame2)" : "var(--bad)") : "var(--ok)";
  $("r-insight").innerHTML = explain(p);
}

function labels() {
  const s = scenario;
  $("v-g").textContent = `${s.gravity_g.toFixed(3)} g`;
  $("v-o2").textContent = `${s.o2_pct.toFixed(1)} %`;
  $("v-u").textContent = `${s.flow_cm_s.toFixed(1)} cm/s`;
  $("v-p").textContent = `${s.pressure_kpa.toFixed(1)} kPa`;
  $("b-shape").textContent = `${t("shape")} · ${shapeName(s.gravity_g)}`;
  document.querySelectorAll("#presets button").forEach((b) =>
    b.classList.toggle("on", Math.abs(+b.dataset.g - s.gravity_g) < 0.003));
}

let timer = null, seq = 0;
function schedulePredict() {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const id = ++seq;
    try {
      const p = await api.predict(scenario);
      if (id !== seq) return; // descarta respuestas viejas
      setPrediction(p);
      render(p);
    } catch (e) {
      $("r-insight").textContent = `${t("noModel")} ${e.message}`;
    }
  }, 120);
}

export function initSimulator(materials) {
  const sel = $("mat");
  sel.innerHTML = materials.map((m) => `<option value="${m}">${material(m)}</option>`).join("");
  if (!materials.includes(scenario.material)) setScenario({ material: materials[0] });
  sel.value = scenario.material;

  const bind = (id, key) => $(id).addEventListener("input", (e) => setScenario({ [key]: +e.target.value }));
  bind("g", "gravity_g"); bind("o2", "o2_pct"); bind("u", "flow_cm_s"); bind("p", "pressure_kpa");
  sel.addEventListener("change", (e) => setScenario({ material: e.target.value }));
  document.querySelectorAll("#presets button").forEach((b) =>
    b.addEventListener("click", () => { $("g").value = b.dataset.g; setScenario({ gravity_g: +b.dataset.g }); }));

  onScenario(() => { labels(); schedulePredict(); });
  labels();
  schedulePredict();
  startFlame($("flame"));
}

// Controles del simulador: sliders → estado → /api/predict → lecturas.
import { api } from "./api.js";
import { scenario, setScenario, setPrediction, onScenario } from "./state.js";
import { startFlame } from "./flame.js";

const $ = (id) => document.getElementById(id);
const shapeName = (g) => (g < 0.05 ? "ESFÉRICA" : g < 0.5 ? "DOMO ALARGADO" : "LÁGRIMA (VELA)");

function explain(p) {
  const s = scenario;
  const loc = p.limiting_o2_pct != null ? `${p.limiting_o2_pct.toFixed(1)}%` : "más de 60%";
  let t;
  if (s.gravity_g < 0.05 && s.flow_cm_s < 2)
    t = `<b>Sin gravedad y sin ventilación</b> no llega oxígeno fresco: la llama se ahoga en sus propios productos. Por eso cortar la ventilación es una respuesta clásica a incendios en naves.`;
  else if (s.gravity_g < 0.05)
    t = `<b>En microgravedad la ventilación hace el papel de la gravedad.</b> Con ${s.flow_cm_s.toFixed(0)} cm/s, el modelo estima que ${s.material} necesita ~${loc} de O₂ para arder.`;
  else if (s.gravity_g < 0.5)
    t = `<b>Gravedad parcial (Luna/Marte):</b> la flotación es débil y puede quedar cerca del punto de máxima inflamabilidad. O₂ límite estimado: ${loc}.`;
  else
    t = `<b>En la Tierra</b> la flotación renueva el aire muy rápido: la llama toma forma de vela y el hollín brilla amarillo. O₂ límite estimado: ${loc}.`;
  if (p.extrapolating) t += ` <span class="tag demo">EXTRAPOLANDO</span> fuera del rango de los datos de entrenamiento.`;
  return t;
}

function render(p) {
  $("r-risk").textContent = `${p.risk_score}/100`;
  $("r-risk").style.color = p.risk_score > 70 ? "var(--bad)" : p.risk_score > 35 ? "var(--flame2)" : "var(--ok)";
  $("r-meter").style.width = `${p.risk_score}%`;
  $("r-loc").textContent = p.limiting_o2_pct != null ? `${p.limiting_o2_pct.toFixed(1)} %` : "> 60 %";
  $("r-margin").textContent = p.margin_pct != null
    ? `${p.margin_pct >= 0 ? "+" : ""}${p.margin_pct.toFixed(1)} pts vs. límite` +
      (p.predicted_spread_mm_s ? ` · propagación ~${p.predicted_spread_mm_s} mm/s` : "")
    : "";
  const burning = p.state === "burning";
  $("b-state").textContent = burning ? (p.burn_probability < 0.7 ? "ESTADO · AL LÍMITE" : "ESTADO · ARDIENDO") : "ESTADO · EXTINGUIDA";
  $("b-state").style.color = burning ? (p.burn_probability < 0.7 ? "var(--flame2)" : "var(--bad)") : "var(--ok)";
  $("r-insight").innerHTML = explain(p);
}

function labels() {
  const s = scenario;
  $("v-g").textContent = `${s.gravity_g.toFixed(3)} g`;
  $("v-o2").textContent = `${s.o2_pct.toFixed(1)} %`;
  $("v-u").textContent = `${s.flow_cm_s.toFixed(1)} cm/s`;
  $("v-p").textContent = `${s.pressure_kpa.toFixed(1)} kPa`;
  $("b-shape").textContent = `FORMA · ${shapeName(s.gravity_g)}`;
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
      $("r-insight").textContent = `No pude contactar el modelo: ${e.message}`;
    }
  }, 120);
}

export function initSimulator(materials) {
  const sel = $("mat");
  sel.innerHTML = materials.map((m) => `<option>${m}</option>`).join("");
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

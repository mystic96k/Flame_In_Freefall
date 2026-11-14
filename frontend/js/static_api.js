// Modo estático: misma interfaz que el backend, pero todo corre en el navegador
// con datos y coeficientes que Python exportó (ml/export_static.py → data/static.json).

let bundlePromise = null;
const load = () => (bundlePromise ??= fetch("data/static.json").then((r) => {
  if (!r.ok) throw new Error("No encontré data/static.json. Corre: python -m ml.export_static");
  return r.json();
}));

function probability(m, s) {
  const ueff = Math.sqrt(s.flow_cm_s ** 2 + (m.buoyant_flow_1g * s.gravity_g) ** 2) + 0.3;
  const lu = Math.log(ueff);
  const values = { o2_pct: s.o2_pct, log_ueff: lu, log_ueff_sq: lu * lu, pressure_kpa: s.pressure_kpa };
  let z = m.intercept;
  m.numeric_features.forEach((f, i) => { z += m.coef[i] * ((values[f] - m.mean[i]) / m.scale[i]); });
  const k = m.categories.indexOf(s.material);
  if (k >= 0) z += m.coef[m.numeric_features.length + k];
  return 1 / (1 + Math.exp(-z));
}

function limitingO2(m, s) {
  let lo = 8, hi = 60;
  if (probability(m, { ...s, o2_pct: hi }) < 0.5) return null;
  if (probability(m, { ...s, o2_pct: lo }) >= 0.5) return lo;
  for (let i = 0; i < 30; i++) {
    const mid = (lo + hi) / 2;
    if (probability(m, { ...s, o2_pct: mid }) >= 0.5) hi = mid; else lo = mid;
  }
  return Math.round(((lo + hi) / 2) * 100) / 100;
}

function predict(m, s) {
  const p = probability(m, s);
  const loc = limitingO2(m, s);
  const r = m.feature_ranges;
  return {
    burn_probability: Math.round(p * 1e4) / 1e4,
    risk_score: Math.round(p * 100),
    limiting_o2_pct: loc,
    margin_pct: loc == null ? null : Math.round((s.o2_pct - loc) * 100) / 100,
    predicted_spread_mm_s: null,
    extrapolating: s.gravity_g < r.gravity_g[0] || s.gravity_g > r.gravity_g[1] ||
                   s.flow_cm_s < r.flow_cm_s[0] || s.flow_cm_s > r.flow_cm_s[1],
    state: p >= 0.5 ? "burning" : "extinguished",
  };
}

// Búsqueda simple por palabras para elegir fuentes del catálogo.
function search(catalog, text, k = 3) {
  const words = text.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").match(/[a-z0-9]{3,}/g) || [];
  return catalog
    .map((c) => {
      const hay = JSON.stringify(c).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
      const score = words.reduce((n, w) => n + (hay.includes(w) ? 1 : 0), 0) + (text.toUpperCase().includes(c.id) ? 5 : 0);
      return { c, score };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map((x) => x.c);
}

function answer(b, question, s, report = false) {
  const p = predict(b.model, s);
  const hits = search(b.catalog, question + " " + s.material);
  const lines = [];
  if (report) lines.push("## Resumen");
  lines.push(`Escenario: ${s.gravity_g} g, ${s.o2_pct}% O₂, ${s.flow_cm_s} cm/s, ${s.pressure_kpa} kPa, ${s.material}.`);
  if (report) lines.push("## Nivel de riesgo");
  lines.push(`- Probabilidad de combustión sostenida: **${p.risk_score}/100**` +
             (p.limiting_o2_pct ? `; O₂ límite estimado ${p.limiting_o2_pct}%.` : "."));
  if (p.extrapolating) lines.push("- ⚠️ El modelo está extrapolando fuera del rango de los datos.");
  if (report) lines.push("## Evidencia experimental relacionada");
  hits.forEach((c) => lines.push(`- **${c.id}:** ${c.finding} Lección: ${c.safety}`));
  if (report) {
    lines.push("## Recomendaciones");
    b.insights.slice(0, 3).forEach((i) => lines.push(`- ${i.text}`));
    lines.push("## Datos de NASA PSI para validarlo");
    lines.push("- Experiment Tables de BASS / BASS-II (sólidos con flujo y oxígeno controlados).");
  } else {
    b.insights.slice(0, 2).forEach((i) => lines.push(`- ${i.text}`));
  }
  lines.push("_Versión estática: respuestas generadas con el modelo de ML y el catálogo, sin modelo de lenguaje._");
  return {
    answer: lines.join("\n"),
    sources: hits.map((c) => ({ id: c.id, title: c.name, url: (c.sources || [""])[0], kind: "catalog" })),
    mode: "offline",
  };
}

export const staticApi = {
  health: async () => ({ status: "ok", llm: false, data: true, mode: "static" }),
  summary: async () => (await load()).summary,
  runs: async (material) => (await load()).runs.filter((r) => !material || r.material === material),
  boundary: async () => (await load()).boundary,
  insights: async () => (await load()).insights,
  catalog: async () => (await load()).catalog,
  predict: async (s) => predict((await load()).model, s),
  ask: async (q, s) => answer(await load(), q, s),
  report: async (s) => answer(await load(), "reporte riesgo ventilación", s, true),
};

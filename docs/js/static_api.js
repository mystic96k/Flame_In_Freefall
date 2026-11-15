// Modo estático: misma interfaz que el backend, pero todo corre en el navegador
// con datos y coeficientes que Python exportó (ml/export_static.py → data/static.json).

import { EN, LANG, t, pick, material, withLang } from "./i18n.js?v=fad0ab4b";

const REPORT_EN = `Write a SAFETY REPORT for the current scenario, in English, with these Markdown sections:
## Summary (2 lines)
## Risk level and why (Measured vs. Model)
## Related experimental evidence (cite the context sources)
## 3 design or operations recommendations (consistent with the risk)
## Which NASA PSI data I would use to validate it (only investigations named in the context)`;

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
    extrapolating: [["gravity_g", 0.01], ["flow_cm_s", 0.5], ["pressure_kpa", 2], ["o2_pct", 1]]
      .some(([k, tol]) => r[k] && (s[k] < r[k][0] - tol || s[k] > r[k][1] + tol)),
    state: p >= 0.5 ? "burning" : "extinguished",
  };
}

const norm = (t) => String(t).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

// Pregunta frecuente más parecida (palabras clave + palabras de la pregunta).
function matchFaq(faq, question) {
  const q = norm(question);
  const qWords = new Set(q.match(/[a-z0-9]{4,}/g) || []);
  let best = null, bestScore = 0;
  for (const f of faq || []) {
    let score = 0;
    for (const k of pick(f, "keywords") || []) if (q.includes(norm(k))) score += norm(k).includes(" ") ? 3 : 2;
    for (const w of norm(pick(f, "question")).match(/[a-z0-9]{4,}/g) || []) if (qWords.has(w)) score += 1;
    if (score > bestScore) { best = f; bestScore = score; }
  }
  return bestScore >= 3 ? best : null;
}

// IA real opcional: si js/config.js define window.FIREFALL_API (backend en Render con Claude),
// las preguntas se mandan ahí; si no responde, se usa la base de conocimiento local.
const REMOTE = (window.FIREFALL_API || "").replace(/\/$/, "");
if (REMOTE) fetch(REMOTE + "/api/health").catch(() => {}); // despierta el servidor gratis

async function remote(path, body, ms = 45000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    const r = await fetch(REMOTE + path, { method: "POST", headers: { "Content-Type": "application/json" },
                                           body: JSON.stringify(body), signal: ctrl.signal });
    if (!r.ok) throw new Error(r.status);
    return await r.json();
  } finally { clearTimeout(t); }
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
  const faq = report ? null : matchFaq(b.faq, question);
  if (faq) {
    return {
      answer: `**${pick(faq, "question")}**\n\n${pick(faq, "answer")}`,
      sources: (faq.sources || []).map((u, i) => ({ id: `${faq.id}${faq.sources.length > 1 ? "-" + (i + 1) : ""}`, title: pick(faq, "question"), url: u, kind: "faq" })),
      mode: "offline",
    };
  }
  const hits = search(b.catalog, question + " " + s.material);
  const lines = [];
  if (report) lines.push(`## ${t("sSummary")}`);
  lines.push(`${t("sScenario")}: ${s.gravity_g} g, ${s.o2_pct}% O₂, ${s.flow_cm_s} cm/s, ${s.pressure_kpa} kPa, ${material(s.material)}.`);
  if (report) lines.push(`## ${t("sRisk")}`);
  lines.push(`- ${t("sProb")}: **${p.risk_score}/100**` +
             (p.limiting_o2_pct ? `; ${t("sLimit")} ${p.limiting_o2_pct}%.` : "."));
  if (p.extrapolating) lines.push(`- ${t("sExtrap")}`);
  if (report) lines.push(`## ${t("sEvidence")}`);
  hits.forEach((c) => lines.push(`- **${c.id}:** ${pick(c, "finding")} ${t("sLesson")} ${pick(c, "safety")}`));
  if (report) {
    lines.push(`## ${t("sRecs")}`);
    b.insights.slice(0, 3).forEach((i) => lines.push(`- ${pick(i, "text")}`));
    lines.push(`## ${t("sPsi")}`);
    lines.push(`- ${t("sPsiLine")}`);
  } else {
    b.insights.slice(0, 2).forEach((i) => lines.push(`- ${pick(i, "text")}`));
  }
  lines.push(t("sStaticNote"));
  return {
    answer: lines.join("\n"),
    sources: hits.map((c) => ({ id: c.id, title: c.name, url: (c.sources || [""])[0], kind: "catalog" })),
    mode: "offline",
  };
}

export const staticApi = {
  health: async () => ({ status: "ok", llm: Boolean(REMOTE), data: true, mode: "static" }),
  summary: async () => (await load()).summary,
  runs: async (material) => (await load()).runs.filter((r) => !material || r.material === material),
  boundary: async () => (await load()).boundary,
  insights: async () => (await load()).insights,
  catalog: async () => (await load()).catalog,
  extra: async () => (await load()).extra,
  predict: async (s) => predict((await load()).model, s),
  ask: async (q, s, history) => {
    if (REMOTE) {
      try { return await remote("/api/ask", { question: withLang(q), scenario: s, history: history || [], lang: LANG }); }
      catch { const a = answer(await load(), q, s); a.answer += "\n\n" + t("sWaking"); return a; }
    }
    return answer(await load(), q, s);
  },
  report: async (s) => {
    if (REMOTE) {
      try {
        // En inglés se pide el reporte como pregunta: así funciona aunque el servidor tenga una versión anterior.
        return EN
          ? await remote("/api/ask", { question: withLang(REPORT_EN), scenario: s, history: [], lang: LANG }, 60000)
          : await remote(`/api/report?lang=${LANG}`, s, 60000);
      } catch { /* usa respaldo local */ }
    }
    return answer(await load(), t("reportQuery"), s, true);
  },
};

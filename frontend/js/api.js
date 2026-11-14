// Cliente del backend con dos modos:
//  - "server": habla con la API de FastAPI (Render, Docker, tu compu).
//  - "static": si no hay backend (Hugging Face Static, GitHub Pages), usa data/static.json
//              y calcula las predicciones en el navegador.
// Si sirves el frontend aparte y SÍ tienes backend, define window.FIREFALL_API = "https://tu-backend".
import { staticApi } from "./static_api.js";

export const API_BASE = window.FIREFALL_API || "";

async function request(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

const serverApi = {
  health: () => request("/api/health"),
  summary: () => request("/api/summary"),
  runs: (material) => request("/api/runs" + (material ? `?material=${encodeURIComponent(material)}` : "")),
  boundary: (g = 0) => request(`/api/boundary?gravity_g=${g}`),
  insights: () => request("/api/insights"),
  catalog: () => request("/api/catalog"),
  predict: (scenario) => request("/api/predict", { method: "POST", body: JSON.stringify(scenario) }),
  ask: (question, scenario, history) =>
    request("/api/ask", { method: "POST", body: JSON.stringify({ question, scenario, history }) }),
  report: (scenario) => request("/api/report", { method: "POST", body: JSON.stringify(scenario) }),
};

async function hasServer() {
  if (window.FIREFALL_STATIC) return false;
  try {
    const r = await fetch(API_BASE + "/api/health");
    return r.ok && (r.headers.get("content-type") || "").includes("json");
  } catch {
    return false;
  }
}

export const MODE = (await hasServer()) ? "server" : "static";
export const api = MODE === "server" ? serverApi : staticApi;

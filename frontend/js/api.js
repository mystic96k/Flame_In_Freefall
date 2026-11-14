// Cliente del backend. Si sirves el frontend aparte (p. ej. GitHub Pages),
// cambia API_BASE por la URL de tu backend desplegado.
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

export const api = {
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

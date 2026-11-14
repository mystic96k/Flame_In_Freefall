// Chat con el analista IA (/api/ask) y reporte de seguridad (/api/report).
import { api } from "./api.js";
import { scenario } from "./state.js";

const $ = (id) => document.getElementById(id);
const history = [];
let busy = false;

const QUICK = [
  "¿Por qué la llama es esférica en el espacio?",
  "¿Qué nivel de ventilación es más peligroso y por qué?",
  "Compara FLEX y Saffire: ¿qué aprendimos de cada uno?",
  "¿Cómo debería responder la tripulación a un incendio en la ISS?",
  "¿Mi escenario actual es seguro? Explícame el riesgo.",
];

function md(s) {
  const e = s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
  return e
    .replace(/^#{2,3} (.*)$/gm, "<h4>$1</h4>")
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(/_(.+?)_/g, "<i>$1</i>")
    .replace(/(?:^|\n)((?:[-•] .*(?:\n|$))+)/g, (m, l) =>
      "<ul>" + l.trim().split("\n").map((x) => `<li>${x.replace(/^[-•] /, "")}</li>`).join("") + "</ul>")
    .replace(/\n/g, "<br>");
}

function add(role, html) {
  const d = document.createElement("div");
  d.className = `m ${role}`;
  d.innerHTML = html;
  $("msgs").appendChild(d);
  $("msgs").scrollTop = 1e9;
  return d;
}

function refs(sources) {
  if (!sources?.length) return "";
  return `<div class="refs">Fuentes: ${sources.map((s) =>
    `<a href="${s.url}" target="_blank" rel="noopener">[${s.id}]</a>`).join(" ")}</div>`;
}

async function run(label, call) {
  if (busy) return;
  busy = true; $("send").disabled = true;
  add("u", md(label));
  const box = add("a", '<span style="color:var(--dim)">Analizando…</span>');
  try {
    const res = await call();
    box.innerHTML = md(res.answer) + refs(res.sources);
    history.push({ role: "user", content: label }, { role: "assistant", content: res.answer });
    $("aistatus").textContent = res.mode === "llm" ? "IA conectada (LLM + RAG + ML)" : "Modo sin LLM: respuestas del modelo de ML + fuentes";
  } catch (e) {
    box.textContent = `Error: ${e.message}`;
  } finally {
    busy = false; $("send").disabled = false;
  }
}

export function ask(question) {
  if (!question.trim()) return;
  $("q").value = "";
  document.getElementById("s-ai").scrollIntoView({ behavior: "smooth" });
  run(question, () => api.ask(question, { ...scenario }, history.slice(-6)));
}

export function initChat(llmAvailable) {
  add("a", "Hola 👋 Soy el analista de <b>FIREFALL</b>. Uso fuentes de la NASA, el modelo de ML y tu escenario del simulador. Pregúntame lo que quieras.");
  $("aistatus").textContent = llmAvailable ? "IA conectada" : "Sin LLM configurado: respondo con el modelo de ML y las fuentes (configura .env)";
  QUICK.forEach((t) => {
    const b = document.createElement("button");
    b.textContent = t;
    b.onclick = () => ask(t);
    $("quick").appendChild(b);
  });
  $("send").onclick = () => ask($("q").value);
  $("q").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask($("q").value); } });
  $("report").onclick = () => {
    document.getElementById("s-ai").scrollIntoView({ behavior: "smooth" });
    run("⚡ Reporte de seguridad de mi escenario", () => api.report({ ...scenario }));
  };
}

// Chat con el analista IA (/api/ask) y reporte de seguridad (/api/report).
import { api } from "./api.js";
import { scenario } from "./state.js";
import { t } from "./i18n.js";
import { showTab } from "./tabs.js";

const AVATAR = "img/mascot-head.webp";

const $ = (id) => document.getElementById(id);
const history = [];
let busy = false;

const QUICK = t("quick");

function md(s) {
  const e = s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
  return e
    .replace(/^#{2,3} (.*)$/gm, "<h4>$1</h4>")
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(/_(.+?)_/g, "<i>$1</i>")
    .replace(/(?:^|\n)((?:[ \t]*(?:[-•*]|\d+\.) .*(?:\n|$))+)/g, (m, l) =>
      "<ul>" + l.trim().split("\n").map((x) => `<li>${x.trim().replace(/^(?:[-•*]|\d+\.) /, "")}</li>`).join("") + "</ul>")
    .replace(/\n/g, "<br>");
}

function add(role, html) {
  const row = document.createElement("div");
  row.className = `row ${role}`;
  if (role === "a") {
    const av = document.createElement("img");
    av.className = "av"; av.src = AVATAR; av.alt = "";
    row.appendChild(av);
  }
  const d = document.createElement("div");
  d.className = `m ${role}`;
  d.innerHTML = html;
  row.appendChild(d);
  $("msgs").appendChild(row);
  $("msgs").scrollTop = 1e9;
  return d;
}

function refs(sources) {
  if (!sources?.length) return "";
  return `<div class="refs">${t("sources")} ${sources.map((s) => s.url
    ? `<a href="${s.url}" target="_blank" rel="noopener">[${s.id}]</a>`
    : `[${s.id}]`).join(" ")}</div>`;
}

async function run(label, call) {
  if (busy) return;
  busy = true; $("send").disabled = true;
  add("u", md(label));
  const box = add("a", `<span class="typing" aria-label="${t("thinking")}"><i></i><i></i><i></i></span>`);
  try {
    const res = await call();
    box.innerHTML = md(res.answer) + refs(res.sources);
    history.push({ role: "user", content: label }, { role: "assistant", content: res.answer });
    $("aistatus").textContent = res.mode === "llm" ? t("aiOn") : t("aiKb");
  } catch (e) {
    box.textContent = `${t("error")} ${e.message}`;
  } finally {
    busy = false; $("send").disabled = false;
  }
}

export function ask(question) {
  if (!question.trim()) return;
  $("q").value = "";
  showTab("asistente");
  run(question, () => api.ask(question, { ...scenario }, history.slice(-6)));
}

export function initChat(llmAvailable, mode = "server") {
  add("a", t("hello"));
  $("aistatus").textContent = llmAvailable
    ? t("aiOn")
    : mode === "static" ? t("aiStatic") : t("aiNoLlm");
  QUICK.forEach((q) => {
    const b = document.createElement("button");
    b.textContent = q;
    b.onclick = () => ask(q);
    $("quick").appendChild(b);
  });
  $("send").onclick = () => ask($("q").value);
  $("q").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask($("q").value); } });
  $("report").onclick = () => {
    showTab("asistente");
    run(t("reportLabel"), () => api.report({ ...scenario }));
  };
}

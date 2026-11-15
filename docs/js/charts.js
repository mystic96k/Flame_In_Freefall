// Gráficas con Chart.js: dispersión + frontera del modelo, e importancia de variables.
import { api } from "./api.js?v=fad0ab4b";
import { t, pick, material, EN } from "./i18n.js?v=fad0ab4b";

const $ = (id) => document.getElementById(id);

Chart.defaults.color = "#8b97b8";
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 11;
Chart.defaults.borderColor = "#1d2747";

let scatter, boundaries = {}, active;

async function drawScatter(material) {
  active = material;
  const runs = await api.runs(material);
  const pt = (r) => ({ x: Math.max(r.flow_cm_s, 0.6), y: r.o2_pct, r });
  const ds = [
    { label: t("burned"), data: runs.filter((r) => r.burned === 1).map(pt), backgroundColor: "#ff9a3c", pointRadius: 5 },
    { label: t("wentOut"), data: runs.filter((r) => r.outcome === "extinct").map(pt), backgroundColor: "rgba(77,163,255,.15)",
      borderColor: "#4da3ff", borderWidth: 1.5, pointRadius: 5 },
    { label: t("noIgn"), data: runs.filter((r) => r.outcome === "no_ignition").map(pt),
      pointStyle: "crossRot", borderColor: "#8b97b8", borderWidth: 2, pointRadius: 6 },
    { label: t("boundary"), type: "line", borderColor: "#ffd27a", borderWidth: 2, borderDash: [6, 4],
      pointRadius: 0, data: (boundaries[material] || []).map((p) => ({ x: p.flow_cm_s, y: p.o2_pct })) },
    { label: t("cabinAir"), type: "line", borderColor: "rgba(231,236,247,.35)", borderWidth: 1, pointRadius: 0,
      data: [{ x: 0.6, y: 21 }, { x: 60, y: 21 }] },
  ];
  if (scatter) { scatter.data.datasets = ds; scatter.update(); return; }
  scatter = new Chart($("scatter"), {
    type: "scatter",
    data: { datasets: ds },
    options: {
      maintainAspectRatio: false, animation: { duration: 300 },
      scales: {
        x: { type: "logarithmic", min: 0.6, max: 60, title: { display: true, text: t("flowAxis") },
             ticks: { callback: (v) => ([0.6, 1, 2, 5, 10, 20, 50].includes(+v) ? v : "") }, grid: { color: "#141c36" } },
        y: { min: 12, max: 34, title: { display: true, text: t("o2Axis") }, grid: { color: "#141c36" } },
      },
      plugins: {
        legend: { labels: { usePointStyle: true, boxWidth: 8 } },
        tooltip: { callbacks: { label: (c) => {
          const r = c.raw.r;
          return r ? `${r.run_id} · ${r.flow_cm_s} cm/s · ${r.o2_pct}% O₂ · ${r.pressure_kpa} kPa · ${t("outcome_" + r.outcome)}`
                   : `${t("boundaryTip")}: ${c.raw.y.toFixed(1)}% O₂ @ ${c.raw.x.toFixed(1)} cm/s`;
        } } },
      },
    },
  });
}

function drawImportance(items) {
  const top = items.slice(0, 5);
  new Chart($("importance"), {
    type: "bar",
    data: { labels: top.map((i) => t("feat_" + i.feature)),
            datasets: [{ data: top.map((i) => Math.max(0, i.importance)), backgroundColor: "#4da3ff", borderRadius: 6 }] },
    options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false } },
               scales: { x: { title: { display: true, text: t("aucDrop") }, grid: { color: "#141c36" } },
                         y: { grid: { display: false } } } },
  });
}

export async function initCharts(summary) {
  $("k-n").textContent = summary.n_runs;
  $("k-inv").textContent = `${summary.n_investigations} ${t("investigations")}`;
  $("k-burn").textContent = `${summary.burn_rate_pct}%`;
  $("k-acc").textContent = `${summary.cv_accuracy_pct}%`;
  $("k-auc").textContent = summary.cv_auc.toFixed(3);
  $("k-model").textContent = `${t("model")}: ${summary.model}`;
  $("data-note").innerHTML = summary.uses_demo_data
    ? `<span class="tag demo">${t("demoTag")}</span> ${t("demoNote")}`
    : `<span class="tag real">${t("realTag")}</span> ${summary.investigations.join(", ")} · ` +
      (summary.sources || []).map((s) => {
        const m = s.match(/NTRS (\d+)/);
        const label = EN ? s.replace("Apéndice", "Appendix") : s;
        return m ? `<a href="https://ntrs.nasa.gov/citations/${m[1]}" target="_blank" rel="noopener">${label}</a>` : label;
      }).join(" · ") + `. ${t("twoObs")}`;

  boundaries = await api.boundary(0);
  const filter = $("matfilter");
  const renderChips = () => {
    filter.innerHTML = "";
    summary.materials.forEach((m) => {
      const b = document.createElement("button");
      b.className = "chip" + (m === active ? " on" : "");
      b.textContent = material(m);
      b.onclick = () => { drawScatter(m).then(renderChips); };
      filter.appendChild(b);
    });
  };
  await drawScatter(summary.materials.includes("PMMA") ? "PMMA" : summary.materials[0]);
  renderChips();
  drawImportance(summary.feature_importance);

  const ins = await api.insights();
  $("insights").innerHTML = ins.map((i) => `<p>${pick(i, "text")}</p>`).join("");
}

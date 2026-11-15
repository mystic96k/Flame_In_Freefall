// 04 · Más datos reales de la NASA: gases (BASS-II), gotas (FLEX), BASS-I y SAFFIRE-I.
// Los datos los prepara Python (pipeline/nasa_extra.py) y llegan por /api/extra o data/static.json.
import { api } from "./api.js?v=377bfcd0";
import { t, pick } from "./i18n.js?v=377bfcd0";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;");
const grid = { color: "#141c36" };
const DIL_COLOR = { "N₂": "#ff9a3c", "CO₂": "#4da3ff", "He": "#8f7dff" };

const fuelName = (f) => t(f === "Metanol" ? "fuelMethanol" : "fuelHeptane");

function gases(g) {
  $("x-gas").textContent = g.n_tests;
  const rows = g.by_material.filter((b) => b.d_co_ppm != null);
  new Chart($("gas-chart"), {
    type: "bar",
    data: {
      labels: rows.map((b) => `${pick(b, "material")} (${b.n})`),
      datasets: [{ label: t("coLabel"), data: rows.map((b) => b.d_co_ppm),
                   backgroundColor: "#ff5d6c", borderRadius: 6 }],
    },
    options: {
      indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false },
        tooltip: { callbacks: { afterLabel: (c) => {
          const b = rows[c.dataIndex];
          return [`ΔO₂: ${b.d_o2_pct} pts · ΔCO₂: ${b.d_co2_pct} pts`, `${t("coMax")}: ${b.co_max_ppm} ppm`,
                  b.co_co2_ratio_pct != null ? `CO/CO₂: ${b.co_co2_ratio_pct}% (${t("incomplete")})` : ""];
        } } } },
      scales: { x: { title: { display: true, text: t("coAxis") }, grid }, y: { grid: { display: false } } },
    },
  });
  $("gas-find").innerHTML = pick(g, "findings").map((x) => `<p>${esc(x)}</p>`).join("");
  $("gas-note").innerHTML = `${esc(pick(g, "note"))} <a href="${g.source.url}" target="_blank" rel="noopener">PSI-25 · DOI ${g.source.doi}</a>`;
}

let flexChart;
function flexScatter(f, fuel) {
  const pts = f.points.filter((p) => p.ratio != null && p.o2 != null && (!fuel || p.fuel === fuel));
  const ds = ["N₂", "CO₂", "He"].map((d) => ({
    label: d === "N₂" ? t("air") : t("withDil", { d }),
    data: pts.filter((p) => p.diluent === d).map((p) => ({ x: p.o2 * 100, y: p.ratio, p })),
    backgroundColor: DIL_COLOR[d], pointRadius: 4,
  }));
  ds.push({ label: t("limitLine"), type: "line", borderColor: "rgba(255,93,108,.6)", borderDash: [6, 4],
            borderWidth: 1.5, pointRadius: 0, data: [{ x: 11, y: 1 }, { x: 35, y: 1 }] });
  if (flexChart) { flexChart.data.datasets = ds; flexChart.update(); return; }
  flexChart = new Chart($("flex-chart"), {
    type: "scatter", data: { datasets: ds },
    options: {
      maintainAspectRatio: false, animation: { duration: 300 },
      scales: { x: { min: 11, max: 35, title: { display: true, text: t("o2Axis") }, grid },
                y: { min: 0, max: 1.05, title: { display: true, text: t("ratioAxis") }, grid } },
      plugins: { legend: { labels: { usePointStyle: true, boxWidth: 8 } },
        tooltip: { callbacks: { label: (c) => {
          const p = c.raw.p;
          return p ? `#${p.test} ${fuelName(p.fuel)} · ${(p.o2 * 100).toFixed(0)}% O₂ · CO₂ ${p.co2} · He ${p.he} · ${p.p_atm} atm · D₀ ${p.d0} mm · ${t("end_" + p.end)}` : "";
        } } } },
    },
  });
}

function flex(f) {
  $("x-flex").textContent = f.n_tests;
  $("x-auc").textContent = f.metrics.auc_extinction.toFixed(2);
  $("flex-find").innerHTML = pick(f, "findings").map((x) => `<p>${esc(x)}</p>`).join("");
  $("flex-note").innerHTML = `${esc(pick(f, "note"))} <a href="${f.source.url}" target="_blank" rel="noopener">PSI-69 · DOI ${f.source.doi}</a>`;
  const box = $("flex-filter");
  const opts = [["", t("all")], ["Metanol", t("fuelMethanol")], ["Heptano", t("fuelHeptane")]];
  box.innerHTML = opts.map(([v, label], i) => `<button class="chip${i ? "" : " on"}" data-f="${v}">${label}</button>`).join("");
  box.querySelectorAll("button").forEach((b) => (b.onclick = () => {
    box.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    flexScatter(f, b.dataset.f);
  }));
  flexScatter(f, "");
  dropletSimulator(f.model);
}

// Mini-simulador: regresión logística exportada por Python (features estandarizadas).
function dropletSimulator(m) {
  let dil = "n2";
  const read = () => {
    const o2 = +$("fx-o2").value / 100, frac = dil === "n2" ? 0 : +$("fx-frac").value / 100;
    return { o2, co2: dil === "co2" ? frac : 0, he: dil === "he" ? frac : 0,
             pressure_atm: +$("fx-p").value, d0_mm: +$("fx-d").value, heptane: +$("fx-fuel").value };
  };
  const update = () => {
    const x = read();
    $("fx-v-o2").textContent = `${(x.o2 * 100).toFixed(0)}%`;
    $("fx-v-frac").textContent = `${$("fx-frac").value}%`;
    $("fx-v-p").textContent = `${(+$("fx-p").value).toFixed(2)} atm`;
    $("fx-v-d").textContent = `${(+$("fx-d").value).toFixed(1)} mm`;
    $("fx-frac-box").classList.toggle("hidden", dil === "n2");
    let z = m.intercept;
    m.features.forEach((f, i) => { z += m.coef[i] * ((x[f] - m.mean[i]) / m.scale[i]); });
    const p = 1 / (1 + Math.exp(-z));
    $("fx-p-out").textContent = `${Math.round(p * 100)}%`;
    $("fx-meter").style.width = `${Math.round(p * 100)}%`;
    const out = m.features.filter((f) => m.ranges[f] && (x[f] < m.ranges[f][0] - 1e-6 || x[f] > m.ranges[f][1] + 1e-6));
    const total = x.o2 + x.co2 + x.he;
    $("fx-warn").textContent = total > 1 ? t("over100")
      : out.length ? t("outFlex", { f: out.map((f) => t("fx_" + f)).join(", ") })
      : p >= 0.5 ? t("goesOut") : t("burnsAll");
  };
  $("fx-dil").querySelectorAll("button").forEach((b) => (b.onclick = () => {
    dil = b.dataset.d;
    $("fx-dil").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    update();
  }));
  ["fx-o2", "fx-frac", "fx-p", "fx-d", "fx-fuel"].forEach((id) => $(id).addEventListener("input", update));
  update();
}

function saffire(s) {
  new Chart($("saffire-chart"), {
    type: "bar",
    data: { labels: s.tests.map((x) => `${x.sample} · ${pick(x, "direction").split(" (")[0]}`),
            datasets: [{ data: s.tests.map((x) => x.burn_s), backgroundColor: ["#ff9a3c", "#4da3ff"], borderRadius: 6 }] },
    options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false } },
               scales: { x: { title: { display: true, text: t("burnTime") }, grid }, y: { grid: { display: false } } } },
  });
  $("saffire-find").innerHTML = `${esc(pick(s, "finding"))} <span style="color:var(--dim)">${t("saffireMeta")} ` +
    `<a href="${s.source.url}" target="_blank" rel="noopener">PSI-98</a></span>`;
}

function bass1(b) {
  $("x-bass1").textContent = b.n_tests;
  new Chart($("bass1-chart"), {
    type: "bar",
    data: { labels: b.inventory.map((i) => pick(i, "material")), datasets: [{ data: b.inventory.map((i) => i.n), backgroundColor: "#3ddc97", borderRadius: 6 }] },
    options: { indexAxis: "y", maintainAspectRatio: false, plugins: { legend: { display: false } },
               scales: { x: { title: { display: true, text: t("nTests") }, grid }, y: { grid: { display: false } } } },
  });
  $("bass1-note").innerHTML = pick(b, "facts").map(esc).join(" ") + ` <a href="${b.source.url}" target="_blank" rel="noopener">PSI-26</a>`;
}

function sources(list) {
  $("x-sources").innerHTML = list.map((s) =>
    `<a href="${s.url}" target="_blank" rel="noopener">${esc(s.id)} · ${esc(s.name)}<small>${s.doi ? "DOI " + esc(s.doi) : "NASA PSI"}</small></a>`).join("") +
    `<a href="https://ntrs.nasa.gov/citations/20150008962" target="_blank" rel="noopener">NTRS 20150008962 · BASS-II (31)<small>${t("clfTable")}</small></a>` +
    `<a href="https://ntrs.nasa.gov/api/citations/20170009141/downloads/20170009141.pdf" target="_blank" rel="noopener">NTRS 20170009141 · BRE<small>Markan et al. 2017</small></a>` +
    `<a href="https://ntrs.nasa.gov/api/citations/19970020585/downloads/19970020585.pdf" target="_blank" rel="noopener">NTRS 19970020585 · ${t("candlesMir")}<small>Candle Flames in Microgravity</small></a>` +
    `<a href="https://science.nasa.gov/biological-physical/investigations/e-field-flames/" target="_blank" rel="noopener">E-FIELD Flames<small>NASA Science</small></a>`;
}

export async function initExtra() {
  const e = await api.extra();
  if (!e || !e.gases) { $("s-more").classList.add("hidden"); return; }
  gases(e.gases);
  flex(e.flex);
  saffire(e.saffire1);
  bass1(e.bass1);
  sources(e.sources);
}

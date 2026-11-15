// Idioma de la página: español (por defecto) o inglés.
// Se elige con el botón ES / EN, con ?lang=en en la URL, o se recuerda del último uso.
// Textos fijos del HTML: se traducen por coincidencia exacta (STATIC_EN).
// Textos que arma JavaScript: t("clave", {vars}).  Datos de Python: pick(obj, "campo") usa "campo_en".

const params = new URLSearchParams(location.search);
function initialLang() {
  const q = params.get("lang");
  if (q === "es" || q === "en") return q;
  try { const s = localStorage.getItem("firefall-lang"); if (s === "es" || s === "en") return s; } catch { /* sin storage */ }
  return "es"; // español por defecto; el botón EN cambia a inglés
}

export const LANG = initialLang();
export const EN = LANG === "en";

export function setLang(lang) {
  try { localStorage.setItem("firefall-lang", lang); } catch { /* sin storage */ }
  const u = new URL(location.href);
  u.searchParams.set("lang", lang);
  location.href = u.toString(); // recarga: gráficas y textos se vuelven a dibujar en el idioma nuevo
}

/** Campo traducido de un objeto que trae `campo` (español) y `campo_en` (inglés). */
/** Instrucción de idioma que viaja con cada pregunta a la IA (refuerza el parámetro lang del servidor). */
export const withLang = (q) => (EN
  ? `${q}\n\n[IMPORTANT: The user is reading the English version of the site. Answer ENTIRELY in English, including headings and labels, even if the context or earlier rules are in Spanish.]`
  : `${q}\n\n[Responde en español.]`);

export const pick = (o, f) => (EN && o && o[f + "_en"] != null ? o[f + "_en"] : o?.[f]);

const MATERIALS_EN = { "SIBAL (algodón/fibra de vidrio)": "SIBAL (cotton/fiberglass)" };
export const material = (m) => (EN ? MATERIALS_EN[m] || m : m);

const STATIC_EN = {
  "Inicio": "Home", "Simulador": "Simulator", "Datos y ML": "Data & ML", "Experimentos": "Experiments",
  "Más datos NASA": "More NASA data",
  "El modelo está entrenado con": "The model is trained on",
  "Seguridad contra incendios en el espacio": "Fire safety in space",
  "El fuego no se comporta igual sin gravedad.": "Fire doesn't behave the same without gravity.",
  "FIREFALL junta pruebas reales de la NASA hechas en la Estación Espacial, las explica con machine learning y te deja preguntar lo que quieras a Astro, nuestro copiloto.":
    "FIREFALL brings together real NASA tests run on the Space Station, explains them with machine learning and lets you ask Astro, our copilot, anything you want.",
  "observaciones de BASS-II para el modelo": "BASS-II observations for the model",
  "gotas de combustible de FLEX": "FLEX fuel droplets", "pruebas con gases medidos": "tests with measured gases",
  "Probar el simulador": "Try the simulator", "Hablar con Astro": "Talk to Astro",
  "¡Hola! Soy": "Hi! I'm", ". Te ayudo a entender cómo se comporta el fuego en microgravedad.": ". I help you understand how fire behaves in microgravity.",
  "Cambia gravedad, oxígeno y ventilación y mira cómo reacciona la llama.": "Change gravity, oxygen and ventilation and watch how the flame reacts.",
  "Las pruebas reales de la ISS y la frontera que aprendió el modelo.": "The real ISS tests and the boundary the model learned.",
  "Once investigaciones de la NASA traducidas a lecciones de seguridad.": "Eleven NASA investigations translated into safety lessons.",
  "Gases tóxicos, gotas, supresores e incendios grandes.": "Toxic gases, droplets, suppressants and large fires.",
  "Copiloto de seguridad contra incendios": "Fire-safety copilot",
  "Generar reporte de seguridad de mi escenario": "Generate a safety report for my scenario",
  "¿Dudas? Pregúntale a Astro": "Questions? Ask Astro",
  "FIREFALL · Seguridad contra incendios en microgravedad": "FIREFALL · Fire safety in microgravity",
  "NASA Space Apps 2026 · Reto “Flame in Freefall”": "NASA Space Apps 2026 · “Flame in Freefall” challenge",
  "Panel con IA que resume, clasifica e interpreta datos de combustión en microgravedad para convertirlos en decisiones de seguridad contra incendios en el espacio.":
    "AI-powered dashboard that summarizes, classifies and interprets microgravity combustion data and turns it into fire-safety decisions for space.",
  "01 Simulador": "01 Simulator", "02 Datos + ML": "02 Data + ML", "03 Experimentos": "03 Experiments",
  "04 Más datos NASA": "04 More NASA data", "05 Analista IA": "05 AI analyst",
  "⚠️ El modelo está entrenado con": "⚠️ The model is trained on", "datos de demostración": "demo data",
  ". Carga las Experiment Tables reales de NASA PSI para el pitch final.": ". Load the real NASA PSI Experiment Tables for the final pitch.",
  "Misma llama, distinta gravedad": "Same flame, different gravity",
  "El modelo de machine learning calcula el riesgo en tiempo real.": "The machine-learning model computes the risk in real time.",
  "FORMA · —": "SHAPE · —", "ESTADO · —": "STATE · —", "Luna": "Moon", "Marte": "Mars", "Tierra": "Earth",
  "Gravedad": "Gravity", "Oxígeno": "Oxygen", "Flujo de ventilación": "Ventilation flow", "Presión": "Pressure",
  "Probabilidad de combustión": "Burn probability", "O₂ límite (modelo)": "O₂ limit (model)",
  "Conectando con el modelo…": "Connecting to the model…",
  "Explorador de pruebas + clasificador": "Test explorer + classifier",
  "Frontera “se quema / se apaga” aprendida por el modelo.": "“Burns / goes out” boundary learned by the model.",
  "Pruebas": "Tests", "Se quemaron": "Burned", "combustión sostenida": "sustained burning",
  "Precisión (validación cruzada)": "Accuracy (cross-validation)", "1.0 = separación perfecta": "1.0 = perfect separation",
  "¿Qué pesa más en la predicción?": "What weighs most in the prediction?", "Hallazgos automáticos": "Automatic findings",
  "Catálogo de experimentos reales": "Catalog of real experiments",
  "Lo que la NASA ya descubrió, traducido a lecciones de seguridad.": "What NASA already discovered, translated into safety lessons.",
  "Buscar: gotas, sólidos, ventilación, extinción, hollín…": "Search: droplets, solids, ventilation, extinction, soot…",
  "Más datos reales de la NASA": "More real NASA data",
  "Gases tóxicos, gotas de combustible, supresores e incendios grandes.": "Toxic gases, fuel droplets, suppressants and large fires.",
  "Gases medidos · BASS-II": "Measured gases · BASS-II", "pruebas con O₂, CO₂ y CO": "tests with O₂, CO₂ and CO",
  "Gotas · FLEX": "Droplets · FLEX", "metanol y heptano en la ISS": "methanol and heptane on the ISS",
  "Sólidos · BASS-I": "Solids · BASS-I", "pruebas en la guantera de la ISS": "tests in the ISS glovebox",
  "Modelo FLEX (AUC)": "FLEX model (AUC)", "¿se apaga antes de terminar la gota?": "does it go out before the droplet is gone?",
  "Gases de combustión por material · PSI-25": "Combustion gases by material · PSI-25",
  "¿Se apaga la gota? · modelo entrenado con FLEX": "Does the droplet flame go out? · model trained on FLEX",
  "Supresor": "Suppressant", "N₂ (aire)": "N₂ (air)", "Helio": "Helium", "Fracción del supresor": "Suppressant fraction",
  "Diámetro de la gota": "Droplet diameter", "Combustible": "Fuel", "Metanol": "Methanol", "Heptano": "Heptane",
  "Probabilidad de que la llama se apague antes de consumir la gota": "Probability that the flame goes out before the droplet is consumed",
  "FLEX · ¿qué tan cerca del límite? (D_ext / D₀) · PSI-69": "FLEX · how close to the limit? (D_ext / D₀) · PSI-69",
  "SAFFIRE-I · misma tela, distinta dirección del aire · PSI-98": "SAFFIRE-I · same fabric, different airflow direction · PSI-98",
  "BASS-I · qué se quemó en la ISS · PSI-26": "BASS-I · what was burned on the ISS · PSI-26",
  "Fuentes de datos (NASA PSI, licencia CC0, con DOI)": "Data sources (NASA PSI, CC0 license, with DOI)",
  "Analista IA": "AI analyst",
  "Responde con fuentes NASA (RAG), el modelo de ML y tu escenario.": "Answers with NASA sources (RAG), the ML model and your scenario.",
  "Ej. ¿Qué ventilación es más riesgosa para una base lunar?": "E.g. Which ventilation is riskiest for a lunar base?",
  "Enviar": "Send", "Preguntas rápidas": "Quick questions",
  "⚡ Generar reporte de seguridad de mi escenario": "⚡ Generate a safety report for my scenario",
  "Fuentes: NASA Physical Sciences Informatics (PSI-25 BASS-II, PSI-26 BASS-I, PSI-69 FLEX, PSI-98 SAFFIRE-I, PSI-10 ACME), NASA Technical Reports Server (NTRS), NASA Science, NASA Glenn (GRC) y NASA Image and Video Library. Cada ficha del catálogo enlaza a su publicación original. Las predicciones son de un modelo estadístico y no sustituyen pruebas de certificación de materiales.":
    "Sources: NASA Physical Sciences Informatics (PSI-25 BASS-II, PSI-26 BASS-I, PSI-69 FLEX, PSI-98 SAFFIRE-I, PSI-10 ACME), NASA Technical Reports Server (NTRS), NASA Science, NASA Glenn (GRC) and NASA Image and Video Library. Each catalog card links to its original publication. Predictions come from a statistical model and do not replace material certification tests.",
};

// Textos que arma JavaScript. {x} se reemplaza con vars.x
const DICT = {
  es: {
    shape: "FORMA", state: "ESTADO", sphere: "ESFÉRICA", dome: "DOMO ALARGADO", teardrop: "LÁGRIMA (VELA)",
    burning: "ARDIENDO", edge: "AL LÍMITE", out: "EXTINGUIDA", moreThan60: "más de 60%",
    simNoFlow: "<b>Sin gravedad y sin ventilación</b> no llega oxígeno fresco: la llama se ahoga en sus propios productos. Por eso cortar la ventilación es una respuesta clásica a incendios en naves.",
    simMicro: "<b>En microgravedad la ventilación hace el papel de la gravedad.</b> Con {flow} cm/s, el modelo estima que {mat} necesita ~{loc} de O₂ para arder.",
    simPartial: "<b>Gravedad parcial (Luna/Marte):</b> la flotación es débil y puede quedar cerca del punto de máxima inflamabilidad. O₂ límite estimado: {loc}.",
    simEarth: "<b>En la Tierra</b> la flotación renueva el aire muy rápido: la llama toma forma de vela y el hollín brilla amarillo. O₂ límite estimado: {loc}.",
    extrapolating: "EXTRAPOLANDO", outOfRange: "fuera del rango de los datos de entrenamiento.",
    vsLimit: "pts vs. límite", spread: "propagación", noModel: "No pude contactar el modelo:",
    noBackend: "<b>No pude conectar con el backend.</b>",
    // gráficas
    burned: "Se quemó", wentOut: "Se apagó", noIgn: "No encendió (no usada por el modelo)",
    boundary: "Frontera del modelo (50%)", cabinAir: "Aire de cabina (21%)",
    flowAxis: "Flujo de aire (cm/s, escala log)", o2Axis: "Oxígeno (%)", boundaryTip: "frontera",
    aucDrop: "caída de AUC al mezclar la variable", investigations: "investigación(es)", model: "modelo",
    demoTag: "DATOS DE DEMOSTRACIÓN", demoNote: "Sustitúyelos por Experiment Tables de NASA PSI (ver README).",
    realTag: "DATOS REALES NASA", twoObs: "Cada prueba con flujo cambiado aporta dos observaciones (antes y después del cambio).",
    feat_o2_pct: "Oxígeno", feat_log_ueff: "Flujo efectivo", feat_log_ueff_sq: "Curvatura del flujo",
    feat_pressure_kpa: "Presión", feat_material: "Material",
    outcome_burn: "ardió", outcome_extinct: "se apagó", outcome_no_ignition: "no encendió",
    // catálogo
    realData: "DATO REAL", inPsi: "EN PSI", finding: "Hallazgo:", lesson: "Lección de seguridad →", source: "fuente",
    askAi: "Pregúntale a Astro", noResults: "Sin resultados.",
    askAbout: "Explícame {id} en lenguaje sencillo y qué significa para diseñar un hábitat lunar.",
    // datos extra
    coAxis: "CO generado por prueba (ppm)", coLabel: "CO generado por prueba (ppm, promedio)", coMax: "CO máximo",
    incomplete: "combustión incompleta", all: "Todos", withDil: "con {d}", air: "O₂ + N₂",
    limitLine: "Límite (la llama muere al encender)", ratioAxis: "D_ext / D₀ (1 = se apagó casi al encender)",
    burnTime: "Tiempo de combustión (s)", nTests: "Número de pruebas (clasificación aproximada)",
    over100: "⚠️ O₂ + supresor supera el 100%: reduce alguno.",
    outFlex: "⚠️ Fuera del rango medido en FLEX ({f}): el modelo extrapola.",
    goesOut: "La llama tiende a apagarse sola antes de consumir la gota (cerca del límite).",
    burnsAll: "La gota tiende a quemarse completa: el fuego se sostiene.",
    saffireMeta: "Tela SIBAL de 40.6 × 94 cm, 20 cm/s, ≈21.5% O₂.", clfTable: "tabla del clasificador",
    candlesMir: "Velas en la Mir", fx_o2: "oxígeno", fx_co2: "CO₂", fx_he: "helio", fx_pressure_atm: "presión",
    fx_d0_mm: "diámetro", fx_heptane: "combustible", fuelMethanol: "Metanol", fuelHeptane: "Heptano",
    end_Extinction: "Extinción", end_Completion: "Completa", end_Disruption: "Interrumpida",
    // chat
    hello: "¡Hola! Soy <b>Astro</b>, el copiloto de FIREFALL. Respondo con datos reales de la NASA, el modelo de ML y lo que pongas en el simulador. ¿Qué quieres saber del fuego en el espacio?",
    thinking: "Analizando…", sources: "Fuentes:", error: "Error:",
    aiOn: "IA conectada (modelo de lenguaje + fuentes NASA + modelo de ML)",
    aiKb: "Respuesta de la base de conocimiento (sin modelo de lenguaje)",
    aiStatic: "Respondo con la base de conocimiento de FIREFALL y el modelo de ML (sin modelo de lenguaje)",
    aiNoLlm: "Sin LLM configurado: respondo con el modelo de ML y las fuentes (configura .env)",
    reportLabel: "Reporte de seguridad de mi escenario",
    quick: [
      "¿Por qué la llama es esférica en el espacio?",
      "¿Qué nivel de ventilación es más peligroso y por qué?",
      "Compara FLEX y Saffire: ¿qué aprendimos de cada uno?",
      "¿Qué gases tóxicos deja un incendio en una nave?",
      "¿Qué gas apaga mejor el fuego en el espacio: CO₂, helio o nitrógeno?",
      "¿Cómo debería responder la tripulación a un incendio en la ISS?",
      "¿Mi escenario actual es seguro? Explícame el riesgo.",
    ],
    // respuestas sin IA (modo estático)
    sScenario: "Escenario", sProb: "Probabilidad de combustión sostenida", sLimit: "O₂ límite estimado",
    sExtrap: "⚠️ El modelo está extrapolando fuera del rango de los datos.", sLesson: "Lección:",
    sSummary: "Resumen", sRisk: "Nivel de riesgo", sEvidence: "Evidencia experimental relacionada",
    sRecs: "Recomendaciones", sPsi: "Datos de NASA PSI para validarlo",
    sPsiLine: "Experiment Tables de BASS / BASS-II (sólidos con flujo y oxígeno controlados).",
    sStaticNote: "_Versión estática: respuestas generadas con el modelo de ML y el catálogo, sin modelo de lenguaje._",
    sWaking: "_La IA está despertando o no respondió; intenta de nuevo en un minuto._",
    reportQuery: "reporte riesgo ventilación",
  },
  en: {
    shape: "SHAPE", state: "STATE", sphere: "SPHERICAL", dome: "ELONGATED DOME", teardrop: "TEARDROP (CANDLE)",
    burning: "BURNING", edge: "AT THE LIMIT", out: "EXTINGUISHED", moreThan60: "more than 60%",
    simNoFlow: "<b>With no gravity and no ventilation</b> no fresh oxygen arrives: the flame suffocates in its own products. That is why shutting off ventilation is a classic response to spacecraft fires.",
    simMicro: "<b>In microgravity, ventilation plays the role of gravity.</b> At {flow} cm/s, the model estimates that {mat} needs ~{loc} O₂ to burn.",
    simPartial: "<b>Partial gravity (Moon/Mars):</b> buoyancy is weak and can sit close to the point of maximum flammability. Estimated O₂ limit: {loc}.",
    simEarth: "<b>On Earth</b> buoyancy renews the air very fast: the flame takes a candle shape and soot glows yellow. Estimated O₂ limit: {loc}.",
    extrapolating: "EXTRAPOLATING", outOfRange: "outside the range of the training data.",
    vsLimit: "pts vs. limit", spread: "spread", noModel: "Could not reach the model:",
    noBackend: "<b>Could not connect to the backend.</b>",
    burned: "Burned", wentOut: "Went out", noIgn: "Did not ignite (not used by the model)",
    boundary: "Model boundary (50%)", cabinAir: "Cabin air (21%)",
    flowAxis: "Airflow (cm/s, log scale)", o2Axis: "Oxygen (%)", boundaryTip: "boundary",
    aucDrop: "AUC drop when the variable is shuffled", investigations: "investigation(s)", model: "model",
    demoTag: "DEMO DATA", demoNote: "Replace it with NASA PSI Experiment Tables (see README).",
    realTag: "REAL NASA DATA", twoObs: "Each test with a flow change contributes two observations (before and after the change).",
    feat_o2_pct: "Oxygen", feat_log_ueff: "Effective flow", feat_log_ueff_sq: "Flow curvature",
    feat_pressure_kpa: "Pressure", feat_material: "Material",
    outcome_burn: "burned", outcome_extinct: "went out", outcome_no_ignition: "no ignition",
    realData: "REAL DATA", inPsi: "IN PSI", finding: "Finding:", lesson: "Safety lesson →", source: "source",
    askAi: "Ask Astro", noResults: "No results.",
    askAbout: "Explain {id} in plain language and what it means for designing a lunar habitat.",
    coAxis: "CO produced per test (ppm)", coLabel: "CO produced per test (ppm, average)", coMax: "Max CO",
    incomplete: "incomplete combustion", all: "All", withDil: "with {d}", air: "O₂ + N₂",
    limitLine: "Limit (flame dies right after ignition)", ratioAxis: "D_ext / D₀ (1 = went out right after ignition)",
    burnTime: "Burn time (s)", nTests: "Number of tests (approximate classification)",
    over100: "⚠️ O₂ + suppressant exceeds 100%: reduce one of them.",
    outFlex: "⚠️ Outside the range measured in FLEX ({f}): the model extrapolates.",
    goesOut: "The flame tends to go out on its own before the droplet is consumed (near the limit).",
    burnsAll: "The droplet tends to burn completely: the fire sustains itself.",
    saffireMeta: "SIBAL fabric 40.6 × 94 cm, 20 cm/s, ≈21.5% O₂.", clfTable: "classifier table",
    candlesMir: "Candles on Mir", fx_o2: "oxygen", fx_co2: "CO₂", fx_he: "helium", fx_pressure_atm: "pressure",
    fx_d0_mm: "diameter", fx_heptane: "fuel", fuelMethanol: "Methanol", fuelHeptane: "Heptane",
    end_Extinction: "Extinction", end_Completion: "Completion", end_Disruption: "Disruption",
    hello: "Hi! I'm <b>Astro</b>, FIREFALL's copilot. I answer with real NASA data, the ML model and whatever you set in the simulator. What do you want to know about fire in space?",
    thinking: "Analyzing…", sources: "Sources:", error: "Error:",
    aiOn: "AI connected (language model + NASA sources + ML model)",
    aiKb: "Answer from the knowledge base (no language model)",
    aiStatic: "I answer with FIREFALL's knowledge base and the ML model (no language model)",
    aiNoLlm: "No LLM configured: I answer with the ML model and sources (configure .env)",
    reportLabel: "Safety report for my scenario",
    quick: [
      "Why is a flame spherical in space?",
      "Which ventilation level is most dangerous and why?",
      "Compare FLEX and Saffire: what did we learn from each?",
      "What toxic gases does a spacecraft fire leave behind?",
      "Which gas puts out fire best in space: CO₂, helium or nitrogen?",
      "How should the crew respond to a fire on the ISS?",
      "Is my current scenario safe? Explain the risk.",
    ],
    sScenario: "Scenario", sProb: "Probability of sustained burning", sLimit: "estimated O₂ limit",
    sExtrap: "⚠️ The model is extrapolating outside the data range.", sLesson: "Lesson:",
    sSummary: "Summary", sRisk: "Risk level", sEvidence: "Related experimental evidence",
    sRecs: "Recommendations", sPsi: "NASA PSI data to validate it",
    sPsiLine: "BASS / BASS-II Experiment Tables (solids with controlled flow and oxygen).",
    sStaticNote: "_Static version: answers generated from the ML model and the catalog, without a language model._",
    sWaking: "_The AI is waking up or did not respond; try again in a minute._",
    reportQuery: "report risk ventilation",
  },
};

export function t(key, vars = {}) {
  const s = DICT[LANG][key] ?? DICT.es[key] ?? key;
  return typeof s === "string" ? s.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "") : s;
}

const norm = (s) => s.replace(/\s+/g, " ").trim();

/** Traduce los textos fijos del HTML y pone el selector de idioma. */
export function applyStatic() {
  document.documentElement.lang = LANG;
  if (EN) {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const n of nodes) {
      const key = norm(n.nodeValue);
      if (key && STATIC_EN[key]) n.nodeValue = n.nodeValue.replace(n.nodeValue.trim(), STATIC_EN[key]);
    }
    document.querySelectorAll("[placeholder]").forEach((el) => {
      const v = STATIC_EN[norm(el.placeholder)];
      if (v) el.placeholder = v;
    });
    document.title = STATIC_EN[norm(document.title)] || document.title;
    document.querySelectorAll("[aria-label]").forEach((el) => {
      const v = { "Hablar con Astro": "Talk to Astro" }[el.getAttribute("aria-label")];
      if (v) el.setAttribute("aria-label", v);
    });
  }
  const nav = document.querySelector("nav.tabs");
  const box = document.createElement("div");
  box.className = "lang";
  box.setAttribute("role", "group");
  box.setAttribute("aria-label", EN ? "Language" : "Idioma");
  box.innerHTML = ["es", "en"].map((l) =>
    `<button data-lang="${l}" class="${l === LANG ? "on" : ""}" aria-pressed="${l === LANG}">${l.toUpperCase()}</button>`).join("");
  box.querySelectorAll("button").forEach((b) => (b.onclick = () => b.dataset.lang !== LANG && setLang(b.dataset.lang)));
  nav.appendChild(box);
}

// Estado compartido del escenario + suscriptores (sin frameworks).
const listeners = new Set();

export const scenario = {
  material: "PMMA",
  o2_pct: 21,
  flow_cm_s: 10,
  gravity_g: 0,
  pressure_kpa: 101.3,
};

export let prediction = null;

export function setScenario(patch) {
  Object.assign(scenario, patch);
  listeners.forEach((fn) => fn(scenario));
}

export function setPrediction(p) {
  prediction = p;
}

export function onScenario(fn) {
  listeners.add(fn);
}

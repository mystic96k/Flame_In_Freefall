"""Datos REALES adicionales de NASA PSI: gases de combustión (BASS-II), gotas FLEX,
inventario de BASS-I y SAFFIRE-I. Genera data/processed/extra.json para el panel y la IA.

Fuentes (todas con licencia CC0-1.0 en NASA PSI):
  - PSI-25 BASS-II   DOI 10.60555/4qc4-de67  → data/raw/nasa/psi25_bass2_gases_raw.csv
  - PSI-69 FLEX      DOI 10.60555/mbq8-0451  → data/raw/nasa/psi69_flex_rows_p*.txt
  - PSI-26 BASS-I    DOI 10.60555/58h4-dy80  → inventario de muestras (abajo)
  - PSI-98 SAFFIRE-I DOI 10.60555/0t15-1z43  → tabla de 2 pruebas (abajo)

Uso:
    python -m pipeline.nasa_extra
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config.settings import PROCESSED_DIR, ROOT

RAW = ROOT / "data" / "raw" / "nasa"
EXTRA_JSON = PROCESSED_DIR / "extra.json"
MMHG_PER_ATM = 760.0

PSI = {
    "PSI-25": {"name": "BASS-II", "doi": "10.60555/4qc4-de67",
               "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-25"},
    "PSI-26": {"name": "BASS-I", "doi": "10.60555/58h4-dy80",
               "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-26"},
    "PSI-69": {"name": "FLEX", "doi": "10.60555/mbq8-0451",
               "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-69"},
    "PSI-98": {"name": "SAFFIRE-I", "doi": "10.60555/0t15-1z43",
               "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-98"},
    "PSI-10": {"name": "ACME (Flame Design, E-FIELD, BRE…)", "doi": None,
               "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-10"},
}


# ----------------------------------------------------------------------------------------------
# BASS-II · gases (PSI-25)
# ----------------------------------------------------------------------------------------------
def _gas_material(test: str, note: str) -> str:
    p = test[0]
    if p == "B":
        return "PMMA película delgada"
    if p == "F":
        return "Vela de cera japonesa" if test == "F4" else "Nomex"
    if p == "M":
        return "PMMA losa gruesa"
    if p in "OP":
        return "PMMA barra"
    if p == "T":
        return "PMMA sección esférica" if "sphere" in note else "Tela SIBAL"
    return "Otro"


MATERIAL_EN = {
    "PMMA película delgada": "PMMA thin film", "PMMA losa gruesa": "PMMA thick slab", "PMMA barra": "PMMA rod",
    "PMMA sección esférica": "PMMA spherical section", "Tela SIBAL": "SIBAL fabric", "Nomex": "Nomex",
    "Vela de cera japonesa": "Japan wax candle", "Otro": "Other",
}
OUTCOME_EN = {"ardió": "burned", "se apagó": "went out", "se apagó (blow-off)": "went out (blow-off)",
              "no encendió": "no ignition", "sólo post-combustión": "post-burn only"}


def _gas_outcome(note: str) -> str:
    n = note.lower()
    if "no ign" in n:
        return "no encendió"
    if "blowoff" in n:
        return "se apagó (blow-off)"
    if any(k in n for k in ("ext", "out", "would not stay lit")):
        return "se apagó"
    if "postburn" in n:
        return "sólo post-combustión"
    return "ardió"


def _num(v) -> tuple[float, bool]:
    """Convierte celdas como 'OR', 'over', '>500', 'none' → (valor, saturado)."""
    s = str(v).strip().lower()
    if s in ("", "none", "nan"):
        return np.nan, False
    if s in ("or", "over"):
        return np.nan, True        # fuera de rango del sensor (saturado)
    if s.startswith(">"):
        return float(s[1:]), True
    return float(s), False


def load_gases() -> pd.DataFrame:
    raw = pd.read_csv(RAW / "psi25_bass2_gases_raw.csv", dtype=str, keep_default_na=False)
    rows = []
    for _, r in raw.iterrows():
        rec = {"test": r["test"], "note": r["note"], "material": _gas_material(r["test"], r["note"]),
               "outcome": _gas_outcome(r["note"]), "co_saturated": False}
        for c in ["o2_i_pct", "o2_f_pct", "co2_i_pct", "co2_f_pct", "co_i_ppm", "co_f_ppm"]:
            v, sat = _num(r[c])
            rec[c] = v
            if sat and c.startswith("co_"):
                rec["co_saturated"] = True
        # Lecturas físicamente imposibles (fallas del sensor reportadas tal cual en la tabla)
        for c in ["o2_i_pct", "o2_f_pct"]:
            if not (5 <= (rec[c] if rec[c] == rec[c] else 10) <= 30):
                rec[c] = np.nan
        rows.append(rec)
    df = pd.DataFrame(rows)
    df["d_o2_pct"] = df["o2_f_pct"] - df["o2_i_pct"]
    df["d_co2_pct"] = df["co2_f_pct"] - df["co2_i_pct"]
    df["d_co_ppm"] = df["co_f_ppm"] - df["co_i_ppm"]
    # Relación CO/CO2 producida (en %): indicador de combustión incompleta
    ok = (df["d_co2_pct"] > 0.02) & df["d_co_ppm"].notna()
    df["co_co2_ratio_pct"] = np.where(ok, df["d_co_ppm"] / (df["d_co2_pct"] * 1e4) * 100, np.nan)
    df.loc[df["d_co_ppm"] < 0, "d_co_ppm"] = np.nan  # deriva del sensor entre pruebas
    return df


def analyze_gases(df: pd.DataFrame) -> dict:
    by = []
    for mat, g in df.groupby("material"):
        by.append({
            "material": mat, "material_en": MATERIAL_EN.get(mat, mat), "n": int(len(g)),
            "d_o2_pct": _r(g["d_o2_pct"].mean(), 2),
            "d_co2_pct": _r(g["d_co2_pct"].mean(), 2),
            "d_co_ppm": _r(g["d_co_ppm"].mean(), 0),
            "co_max_ppm": _r(g["co_f_ppm"].max(), 0),
            "co_co2_ratio_pct": _r(g["co_co2_ratio_pct"].median(), 1),
        })
    by.sort(key=lambda x: -(x["d_co_ppm"] or 0))
    rods = df[df["material"] == "PMMA barra"]
    # Sólo primeras igniciones ("b" = la misma muestra re-encendida con el O₂ ya consumido)
    burn_rods = rods[(rods["outcome"] == "ardió") & ~rods["test"].str.endswith("b")]
    low_burn = burn_rods.nsmallest(3, "o2_i_pct")[["test", "o2_i_pct"]]
    ext_rods = rods[rods["outcome"].str.startswith("se apagó")].nsmallest(1, "o2_i_pct")
    no_ign = df[df["outcome"] == "no encendió"]
    top_co = df.dropna(subset=["co_f_ppm"]).nlargest(1, "co_f_ppm").iloc[0]
    n_sat = int(df["co_saturated"].sum())
    thin = next((b for b in by if b["material"] == "PMMA película delgada"), None)
    thick = next((b for b in by if b["material"] == "PMMA losa gruesa"), None)
    findings = [
        f"El CO llegó a {top_co['co_f_ppm']:.0f} ppm al final de la prueba {top_co['test']} "
        f"({top_co['material']}); además {n_sat} lecturas saturaron el sensor (\"OR\", \"over\", \">500\"). "
        "En una cabina cerrada el CO se acumula prueba tras prueba.",
        f"Una barra de PMMA encendió y ardió con sólo {low_burn['o2_i_pct'].min():.1f}% de O₂ inicial "
        f"(prueba {low_burn.iloc[0]['test']}); "
        + (f"con {ext_rods.iloc[0]['o2_i_pct']:.1f}% se apagó ({ext_rods.iloc[0]['test']}) " if len(ext_rods) else "")
        + (f"y con {no_ign.iloc[0]['o2_i_pct']:.1f}% ya no encendió ({no_ign.iloc[0]['test']}). " if len(no_ign) else ". ")
        + "Ése es el límite real medido en el espacio: muy por debajo del 21% del aire.",
    ]
    if thin and thick:
        findings.append(
            f"Material grueso = más gases: la losa de PMMA produjo en promedio {thick['d_co_ppm']:.0f} ppm de CO "
            f"por prueba contra {thin['d_co_ppm']:.0f} ppm de la película delgada.")
    findings.append("Cada prueba consume poco O₂ (décimas de punto porcentual), pero el CO sube cientos de ppm: "
                    "el riesgo tóxico aparece mucho antes que la falta de oxígeno.")
    findings_en = [
        f"CO reached {top_co['co_f_ppm']:.0f} ppm at the end of test {top_co['test']} "
        f"({MATERIAL_EN[top_co['material']]}); {n_sat} readings also saturated the sensor (\"OR\", \"over\", \">500\"). "
        "In a closed cabin CO builds up test after test.",
        f"A PMMA rod ignited and burned with only {low_burn['o2_i_pct'].min():.1f}% initial O₂ "
        f"(test {low_burn.iloc[0]['test']}); "
        + (f"at {ext_rods.iloc[0]['o2_i_pct']:.1f}% it went out ({ext_rods.iloc[0]['test']}) " if len(ext_rods) else "")
        + (f"and at {no_ign.iloc[0]['o2_i_pct']:.1f}% it no longer ignited ({no_ign.iloc[0]['test']}). " if len(no_ign) else ". ")
        + "That is the real limit measured in space: far below the 21% of air.",
    ]
    if thin and thick:
        findings_en.append(f"Thicker material = more gas: the PMMA slab produced on average {thick['d_co_ppm']:.0f} ppm of CO "
                           f"per test versus {thin['d_co_ppm']:.0f} ppm for the thin film.")
    findings_en.append("Each test consumes little O₂ (tenths of a percentage point), but CO rises by hundreds of ppm: "
                       "the toxic hazard appears long before the lack of oxygen.")
    return {
        "source": PSI["PSI-25"], "n_tests": int(len(df)), "by_material": by, "findings": findings,
        "findings_en": findings_en,
        "note_en": "Readings accumulate within each session; Δ = final − initial per test is used. "
                   "Impossible sensor values (e.g. O₂ of 0.6% or 40%) are discarded.",
        "points": [{"test": r.test, "material": r.material, "material_en": MATERIAL_EN.get(r.material, r.material), "o2_i": _r(r.o2_i_pct, 2), "d_o2": _r(r.d_o2_pct, 2),
                    "d_co2": _r(r.d_co2_pct, 2), "d_co": _r(r.d_co_ppm, 0), "outcome": r.outcome}
                   for r in df.itertuples()],
        "note": "Las lecturas se acumulan dentro de cada sesión; se usa Δ = final − inicial por prueba. "
                "Valores imposibles del sensor (p. ej. O₂ de 0.6% o 40%) se descartan.",
    }


# ----------------------------------------------------------------------------------------------
# FLEX · gotas (PSI-69)
# ----------------------------------------------------------------------------------------------
def _flex_tail(vals: list[str]) -> dict:
    """Asigna los valores finales a D0, Dext, K, tb (la tabla omite celdas vacías)."""
    def f(s):
        s = s.replace("~", "")
        return np.nan if s == "?" else float(s)
    v = [f(x) for x in vals]
    out = {"d0_mm": np.nan, "dext_mm": np.nan, "k_mm2_s": np.nan, "burn_s": np.nan}
    if len(v) == 4:
        out.update(d0_mm=v[0], dext_mm=v[1], k_mm2_s=v[2], burn_s=v[3])
    elif len(v) == 3:
        if v[2] == v[2] and v[2] < 1 and v[1] == v[1] and v[1] > 1:   # falta el tiempo de combustión
            out.update(d0_mm=v[0], dext_mm=v[1], k_mm2_s=v[2])
        else:                                                         # falta el diámetro de extinción
            out.update(d0_mm=v[0], k_mm2_s=v[1], burn_s=v[2])
    elif len(v) == 2:
        out.update(d0_mm=v[0], burn_s=v[1])
    elif len(v) == 1 and v[0] == v[0]:
        out.update(**({"burn_s": v[0]} if v[0] >= 3 else {"d0_mm": v[0]}))
    return out


def load_flex() -> pd.DataFrame:
    rows = []
    for path in sorted(RAW.glob("psi69_flex_rows_p*.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            t = line.split()
            if len(t) < 8:
                continue
            i = 3 if ":" in t[3] else 2
            fuel, nums, end = t[i + 1], t[i + 2:-1], t[-1]
            p, o2, n2, co2, he = (float(x) for x in nums[:5])
            rec = {"test": int(t[0]), "id": t[1], "fuel": "Metanol" if fuel == "Methanol" else "Heptano",
                   "pressure_atm": p / MMHG_PER_ATM if p > 0 else np.nan,
                   "o2": o2, "n2": n2, "co2": co2, "he": he, "end": end, **_flex_tail(nums[5:])}
            rows.append(rec)
    df = pd.DataFrame(rows)
    df["diluent"] = np.select([df["co2"] > 0, df["he"] > 0], ["CO₂", "He"], "N₂")
    df["ratio_ext"] = np.where((df["dext_mm"] > 0) & (df["d0_mm"] > 0), df["dext_mm"] / df["d0_mm"], np.nan)
    return df


FLEX_FEATURES = ["o2", "co2", "he", "pressure_atm", "d0_mm", "heptane"]


def _flex_xy(df):
    d = df[df["end"].isin(["Extinction", "Completion"])].dropna(subset=["o2", "pressure_atm", "d0_mm"]).copy()
    d["heptane"] = (d["fuel"] == "Heptano").astype(float)
    return d[FLEX_FEATURES].astype(float), (d["end"] == "Extinction").astype(int)


def analyze_flex(df: pd.DataFrame) -> dict:
    X, y = _flex_xy(df)
    model = Pipeline([("sc", StandardScaler()), ("lr", LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000))])
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    auc = cross_val_score(model, X, y, cv=cv, scoring="roc_auc").mean()
    model.fit(X, y)
    sc, lr = model.named_steps["sc"], model.named_steps["lr"]

    # ¿Qué tan cerca del límite? Dext/D0 → 1 significa que la llama murió casi al encender.
    r = df.dropna(subset=["ratio_ext", "o2", "pressure_atm", "d0_mm"]).copy()
    r["heptane"] = (r["fuel"] == "Heptano").astype(float)
    rf = RandomForestRegressor(300, min_samples_leaf=3, random_state=0)
    r2 = cross_val_score(rf, r[FLEX_FEATURES], r["ratio_ext"], cv=KFold(5, shuffle=True, random_state=0), scoring="r2").mean()
    rf.fit(r[FLEX_FEATURES], r["ratio_ext"])
    imp = sorted(zip(FLEX_FEATURES, rf.feature_importances_), key=lambda x: -x[1])

    groups = []
    for (fuel, dil), g in df.groupby(["fuel", "diluent"]):
        groups.append({"fuel": fuel, "diluent": dil, "n": int(len(g)),
                       "o2_min": _r(g["o2"].min(), 2), "k_mean": _r(g["k_mm2_s"].mean(), 3),
                       "ext_share": _r((g["end"] == "Extinction").mean(), 3)})
    # Burning rate: He lo sube (difunde rápido), CO2 lo baja
    k_air = df[(df["diluent"] == "N₂") & df["o2"].between(0.2, 0.22)]["k_mm2_s"].mean()
    k_he = df[df["diluent"] == "He"]["k_mm2_s"].mean()
    k_co2 = df[df["diluent"] == "CO₂"]["k_mm2_s"].mean()
    near = df[df["ratio_ext"] >= 0.95]
    low = df[df["diluent"] == "N₂"].nsmallest(1, "o2").iloc[0]
    findings = [
        f"{len(df)} pruebas reales en la ISS (2009–2011): {int((df['end'] == 'Extinction').sum())} terminaron con la llama "
        f"apagándose antes de consumir la gota, {int((df['end'] == 'Completion').sum())} quemaron la gota completa y "
        f"{int((df['end'] == 'Disruption').sum())} se interrumpieron (la gota se rompió o se movió).",
        f"Hubo llama con apenas {low['o2'] * 100:.0f}% de O₂ en nitrógeno ({low['fuel'].lower()}, prueba {low['test']}). "
        "Por eso FLEX se diseñó para hallar el índice límite de oxígeno: en microgravedad no hay flotación que 'ahogue' la llama.",
        f"En {len(near)} pruebas la llama se apagó con la gota casi intacta (D_ext/D₀ ≥ 0.95): estaban justo en el límite "
        "de inflamabilidad. Ese cociente es el mejor 'termómetro' de qué tan cerca estás de que el fuego no se sostenga.",
        f"El helio aceleró la combustión (K ≈ {k_he:.2f} mm²/s) frente al aire (≈ {k_air:.2f}); el CO₂ la frenó (≈ {k_co2:.2f}). "
        "Un supresor que diluye no siempre ayuda: el helio transporta calor y oxígeno más rápido.",
        f"Modelo ML de FLEX: predice si la llama se apaga antes de terminar la gota con AUC {auc:.2f} (validación cruzada). "
        f"Para el cociente D_ext/D₀ (R² {r2:.2f}) lo que más pesa es {_FEAT_ES[imp[0][0]]} y {_FEAT_ES[imp[1][0]]}.",
    ]
    findings_en = [
        f"{len(df)} real ISS tests (2009–2011): {int((df['end'] == 'Extinction').sum())} ended with the flame going out "
        f"before the droplet was consumed, {int((df['end'] == 'Completion').sum())} burned the whole droplet and "
        f"{int((df['end'] == 'Disruption').sum())} were disrupted (the droplet broke apart or moved).",
        f"A flame existed with only {low['o2'] * 100:.0f}% O₂ in nitrogen ({'methanol' if low['fuel'] == 'Metanol' else 'heptane'}, "
        f"test {low['test']}). That is why FLEX was designed to find the limiting oxygen index: in microgravity there is "
        "no buoyancy to 'smother' the flame.",
        f"In {len(near)} tests the flame went out with the droplet almost intact (D_ext/D₀ ≥ 0.95): they were right at the "
        "flammability limit. That ratio is the best 'thermometer' of how close a fire is to not sustaining itself.",
        f"Helium sped up burning (K ≈ {k_he:.2f} mm²/s) compared with air (≈ {k_air:.2f}); CO₂ slowed it (≈ {k_co2:.2f}). "
        "A diluting suppressant does not always help: helium transports heat and oxygen faster.",
        f"FLEX ML model: predicts whether the flame goes out before the droplet is consumed with AUC {auc:.2f} (cross-validation). "
        f"For the D_ext/D₀ ratio (R² {r2:.2f}) the strongest factors are {_FEAT_EN[imp[0][0]]} and {_FEAT_EN[imp[1][0]]}.",
    ]
    return {
        "findings_en": findings_en,
        "note_en": "The PSI web table leaves empty cells; when values are missing they are assigned by position "
                   "(initial diameter, extinction, rate K, time). Check the official CSV for fine-grained analysis.",
        "source": PSI["PSI-69"], "n_tests": int(len(df)), "groups": groups, "findings": findings,
        "metrics": {"auc_extinction": _r(auc, 3), "r2_ratio": _r(r2, 3), "n_model": int(len(y)),
                    "importance": [{"feature": _FEAT_ES[f], "feature_en": _FEAT_EN[f], "importance": _r(v, 3)} for f, v in imp]},
        "model": {"features": FLEX_FEATURES, "mean": sc.mean_.round(6).tolist(), "scale": sc.scale_.round(6).tolist(),
                  "coef": lr.coef_[0].round(6).tolist(), "intercept": round(float(lr.intercept_[0]), 6),
                  "ranges": {f: [_r(X[f].min(), 3), _r(X[f].max(), 3)] for f in FLEX_FEATURES}},
        "points": [{"test": int(t.test), "fuel": t.fuel, "diluent": t.diluent, "o2": t.o2, "co2": t.co2, "he": t.he,
                    "p_atm": _r(t.pressure_atm, 2), "d0": _r(t.d0_mm, 2), "ratio": _r(t.ratio_ext, 3),
                    "k": _r(t.k_mm2_s, 3), "burn_s": _r(t.burn_s, 2), "end": t.end} for t in df.itertuples()],
        "note": "La tabla de PSI deja celdas vacías; cuando faltan valores se asignan por posición "
                "(diámetro inicial, extinción, tasa K, tiempo). Revisa el CSV oficial para análisis finos.",
    }


_FEAT_EN = {"o2": "oxygen", "co2": "CO₂", "he": "helium", "pressure_atm": "pressure",
            "d0_mm": "droplet size", "heptane": "fuel type"}
_FEAT_ES = {"o2": "el oxígeno", "co2": "el CO₂", "he": "el helio", "pressure_atm": "la presión",
            "d0_mm": "el tamaño de la gota", "heptane": "el tipo de combustible"}


# ----------------------------------------------------------------------------------------------
# BASS-I inventario (PSI-26) y SAFFIRE-I (PSI-98)
# ----------------------------------------------------------------------------------------------
BASS1_INVENTORY = [  # clasificación manual de los 122 ensayos de la Experimental Table de PSI-26
    {"material": "Esferas de PMMA (1–2 cm)", "material_en": "PMMA spheres (1–2 cm)", "n": 50},
    {"material": "Placas de PMMA 1–2 cm", "material_en": "PMMA plates 1–2 cm", "n": 16},
    {"material": "Velas (cera japonesa / parafina)", "material_en": "Candles (Japan wax / paraffin)", "n": 17},
    {"material": "Tela SIBAL", "material_en": "SIBAL fabric", "n": 12},
    {"material": "Losa gruesa de PMMA", "material_en": "Thick PMMA slab", "n": 8},
    {"material": "Placa de cera / parafina", "material_en": "Wax / paraffin slab", "n": 6},
    {"material": "Nomex", "material_en": "Nomex", "n": 6},
    {"material": "Ultem", "material_en": "Ultem", "n": 2},
]

SAFFIRE1 = [
    {"sample": "S1", "material": "Tela SIBAL 0.37 mm", "size_cm": "40.6 × 94", "flow_cm_s": 20,
     "o2_pct": "21.5–21.7", "ignition": "182 W · 8 s", "burn_s": 420, "direction": "Concurrente (a favor del flujo)",
     "direction_en": "Concurrent (with the flow)"},
    {"sample": "S2", "material": "Tela SIBAL 0.37 mm", "size_cm": "40.6 × 94", "flow_cm_s": 20,
     "o2_pct": "≈21.5", "ignition": "182 W · 8 s", "burn_s": 70, "direction": "Opuesta (contra el flujo)",
     "direction_en": "Opposed (against the flow)"},
]


def build() -> dict:
    gases, flex = load_gases(), load_flex()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    gases.to_csv(PROCESSED_DIR / "bass2_gases.csv", index=False)
    flex.to_csv(PROCESSED_DIR / "flex_droplets.csv", index=False)
    extra = {
        "gases": analyze_gases(gases),
        "flex": analyze_flex(flex),
        "bass1": {"source": PSI["PSI-26"], "n_tests": 122, "inventory": BASS1_INVENTORY,
                  "facts": ["ISS, Microgravity Science Glovebox, oct-2009 a jun-2013.",
                            "Ducto de 76 × 76 mm con flujo de aire de hasta 40 cm/s; N₂ como supresor.",
                            "Base del estudio 'Thickness and Fuel Preheating Effects on Material Flammability "
                            "in Microgravity from the BASS Experiment'."],
                  "facts_en": ["ISS, Microgravity Science Glovebox, Oct 2009 to Jun 2013.",
                               "76 × 76 mm duct with airflow up to 40 cm/s; N₂ as suppressant.",
                               "Basis of the study 'Thickness and Fuel Preheating Effects on Material Flammability "
                               "in Microgravity from the BASS Experiment'."]},
        "saffire1": {"source": PSI["PSI-98"], "tests": SAFFIRE1,
                     "finding": "La misma tela ardió 420 s con la llama a favor del flujo y sólo 70 s contra el flujo: "
                                "la dirección de la ventilación cambia por completo el tamaño del incendio.",
                     "finding_en": "The same fabric burned 420 s with the flame spreading with the flow and only 70 s against it: "
                                   "ventilation direction completely changes the size of the fire.",
                     "facts": ["Vehículo de carga Cygnus, después de dejar la ISS (sin riesgo para la tripulación).",
                               "Midió termopares, radiómetros, presión, O₂/CO₂ y anemómetros."],
                     "facts_en": ["Cygnus cargo vehicle, after leaving the ISS (no risk to the crew).",
                                  "Measured thermocouples, radiometers, pressure, O₂/CO₂ and anemometers."]},
        "sources": [{"id": k, **v} for k, v in PSI.items()],
    }
    EXTRA_JSON.write_text(json.dumps(extra, ensure_ascii=False, default=_json_default), encoding="utf-8")
    return extra


def knowledge_chunks(extra: dict | None = None) -> list[dict]:
    """Textos para la base de conocimiento de la IA (RAG)."""
    extra = extra or load_extra()
    if not extra:
        return []
    g, f = extra["gases"], extra["flex"]
    gas_tab = "; ".join(f"{b['material']}: ΔO₂ {b['d_o2_pct']} pts, ΔCO₂ {b['d_co2_pct']} pts, ΔCO {b['d_co_ppm']} ppm, "
                        f"CO máx {b['co_max_ppm']} ppm" for b in g["by_material"])
    flex_tab = "; ".join(f"{x['fuel']} con {x['diluent']}: {x['n']} pruebas, O₂ mínimo {x['o2_min']}, K medio {x['k_mean']} mm²/s, "
                         f"{(x['ext_share'] or 0) * 100:.0f}% extinción" for x in f["groups"])
    return [
        {"id": "PSI-25-GASES", "title": "BASS-II: gases de combustión (O₂, CO₂, CO) medidos en la ISS",
         "text": "BASS-II gases combustion CO monoxido de carbono CO2 oxigeno toxicidad cabina. "
                 + " ".join(g["findings"]) + " Promedios por material: " + gas_tab + ". " + g["note"]
                 + " | EN: carbon monoxide toxic cabin gases. " + " ".join(g.get("findings_en", [])),
         "source": g["source"]["url"]},
        {"id": "PSI-69-FLEX", "title": "FLEX: 274 gotas de combustible en la ISS (metanol, heptano, N₂/CO₂/He)",
         "text": "FLEX gotas droplet extincion supresor helio CO2 nitrogeno metanol heptano indice limite de oxigeno. "
                 + " ".join(f["findings"]) + " Grupos: " + flex_tab + ". " + f["note"]
                 + " | EN: droplets suppressant helium nitrogen. " + " ".join(f.get("findings_en", [])),
         "source": f["source"]["url"]},
        {"id": "PSI-26-BASS1", "title": "BASS-I: 122 pruebas de sólidos en la ISS",
         "text": "BASS-I BASS inventario materiales PMMA esferas velas SIBAL Nomex Ultem. "
                 + " ".join(extra["bass1"]["facts"]) + " Muestras: "
                 + ", ".join(f"{i['material']} ({i['n']})" for i in extra["bass1"]["inventory"]) + ".",
         "source": extra["bass1"]["source"]["url"]},
        {"id": "PSI-98-SAFFIRE1", "title": "SAFFIRE-I: incendio grande en el Cygnus",
         "text": "SAFFIRE-I Saffire Cygnus tela SIBAL incendio grande concurrente opuesto large fire. " + extra["saffire1"]["finding"]
                 + " " + extra["saffire1"].get("finding_en", "")
                 + " " + " ".join(extra["saffire1"]["facts"]) + " Muestras: 40.6 × 94 cm, 20 cm/s, 21.5% O₂, "
                 "ignición 182 W por 8 s; S1 concurrente 420 s, S2 opuesta 70 s.",
         "source": extra["saffire1"]["source"]["url"]},
    ]


def load_extra() -> dict:
    return json.loads(EXTRA_JSON.read_text(encoding="utf-8")) if EXTRA_JSON.exists() else {}


def _r(v, n):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), n)


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    raise TypeError(type(o))


if __name__ == "__main__":
    e = build()
    print(f"✅ extra.json: {e['gases']['n_tests']} pruebas de gases (PSI-25), {e['flex']['n_tests']} gotas FLEX (PSI-69)")
    for s in ("gases", "flex"):
        for t in e[s]["findings"]:
            print("  •", t)

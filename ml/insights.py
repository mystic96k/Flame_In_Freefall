"""Convierte el modelo y los datos en hallazgos en lenguaje natural (sin LLM).

Estos hallazgos se muestran en el dashboard y también se pasan como contexto
a la IA, para que sus respuestas se apoyen en números calculados y no inventados.
"""
from __future__ import annotations

import pandas as pd

from ml.predict import boundary_curves, limiting_o2, load_classifier
from pipeline.features import add_features

GRAVITY_PRESETS = {"ISS (0 g)": 0.0, "Luna (0.165 g)": 0.165, "Marte (0.38 g)": 0.38, "Tierra (1 g)": 1.0}


def summary(df: pd.DataFrame) -> dict:
    m = load_classifier()["metrics"]
    return {
        "n_runs": int(len(df)),
        "n_investigations": int(df["investigation"].nunique()),
        "burn_rate_pct": round(100 * df["burned"].mean(), 1),
        "uses_demo_data": bool(df["is_demo"].astype(str).str.lower().eq("true").any()),
        "model": m["chosen_model"],
        "cv_accuracy_pct": round(100 * m["chosen_scores"]["accuracy"], 1),
        "cv_auc": m["chosen_scores"]["roc_auc"],
        "feature_importance": m["feature_importance"],
        "sources": m.get("sources", []),
    }


def generate(df: pd.DataFrame) -> list[dict]:
    df = add_features(df)
    materials = sorted(df["material"].dropna().astype(str).unique())
    curves = boundary_curves(materials)
    out: list[dict] = []

    worst = {m: min(c, key=lambda p: p["o2_pct"]) for m, c in curves.items() if c}
    if worst:
        mat = min(worst, key=lambda k: worst[k]["o2_pct"])
        w = worst[mat]
        lead = (f"{mat} es el material más inflamable" if len(worst) > 1 else f"Para {mat}")
        tested = df[df["material"] == mat]
        min_burn = tested.loc[tested["burned"] == 1, "o2_pct"].min()
        text = (f"{lead}: el modelo predice combustión desde {w['o2_pct']:.1f}% O₂ con un flujo de "
                f"~{w['flow_cm_s']:.0f} cm/s — por debajo del 21% del aire de cabina.")
        if pd.notna(min_burn) and w["o2_pct"] < min_burn:
            text += f" Ojo: es una extrapolación; el O₂ más bajo con llama sostenida medido fue {min_burn:g}%."
        noign = tested[tested["outcome"] == "no_ignition"]
        if len(noign):
            text += (f" En {len(noign)} pruebas con {noign['o2_pct'].min():g}–{noign['o2_pct'].max():g}% O₂ "
                     "la muestra ni siquiera encendió.")
        out.append({"icon": "🔥", "kind": "material", "text": text})
        flows = [p["flow_cm_s"] for p in worst.values()]
        zone = (f"≈{min(flows):.0f} cm/s" if round(min(flows)) == round(max(flows))
                else f"{min(flows):.0f}–{max(flows):.0f} cm/s")
        out.append({"icon": "🌬️", "kind": "flow",
                    "text": f"Zona de ventilación más peligrosa: {zone}. "
                            "Con menos aire la llama se ahoga y con más se 'sopla'."})

    real = df[~df["is_demo"].astype(str).str.lower().eq("true")]
    notes = real["notes"].astype(str).str.lower()
    ext = real["outcome"] == "extinct"
    q = real[ext & notes.str.contains("quench")]
    bo = real[ext & notes.str.contains("blow-off") & ~notes.str.contains("no blow-off")]
    if len(q):
        out.append({"icon": "📉", "kind": "measured",
                    "text": f"Medido en la ISS: la llama se apagó por falta de flujo ('quenching') en {len(q)} pruebas, "
                            f"con flujos de {q['flow_cm_s'].min():g}–{q['flow_cm_s'].max():g} cm/s y "
                            f"{q['o2_pct'].min():g}–{q['o2_pct'].max():g}% O₂."
                            + (f" Por exceso de flujo ('blow-off') se apagó {len(bo)} vez, a {bo['flow_cm_s'].max():g} cm/s."
                               if len(bo) else "")})

    low = df[(df["u_eff"] < 2) & (df["o2_pct"] <= 21)]
    if len(low):
        out.append({"icon": "🧯", "kind": "quiescent",
                    "text": f"Con flujo casi nulo (<2 cm/s) y aire normal, ardieron {int(low['burned'].sum())} de "
                            f"{len(low)} pruebas → apagar la ventilación ayuda, pero Saffire mostró que no siempre apaga rápido."})

    if materials and df["gravity_g"].nunique() > 1:  # sólo si los datos traen distintas gravedades
        ref = "PMMA" if "PMMA" in materials else materials[0]
        locs = {name: limiting_o2(ref, 0.0, g) for name, g in GRAVITY_PRESETS.items()}
        valid = {k: v for k, v in locs.items() if v is not None}
        if valid:
            riskiest = min(valid, key=valid.get)
            out.append({"icon": "🌙", "kind": "gravity",
                        "text": f"Sin ventilación forzada, para {ref} el O₂ límite estimado más bajo es en {riskiest} "
                                f"({valid[riskiest]:.1f}%). Ojo: fuera de 0 g el modelo extrapola con un término de flotación."})

    if df["gravity_g"].nunique() == 1:
        out.append({"icon": "🌙", "kind": "gravity",
                    "text": "Todas las pruebas son en microgravedad (ISS). Las predicciones para Luna, Marte o Tierra "
                            "son extrapolaciones del modelo y se marcan como tales."})

    imp = load_classifier()["metrics"]["feature_importance"]
    if imp:
        names = {"o2_pct": "el oxígeno", "log_ueff": "el flujo efectivo", "log_ueff_sq": "la curvatura del flujo",
                 "pressure_kpa": "la presión", "material": "el material"}
        top = [names.get(i["feature"], i["feature"]) for i in imp[:2]]
        out.append({"icon": "🧠", "kind": "model",
                    "text": f"Lo que más pesa en la predicción: {top[0]} y {top[1]}."})
    return out

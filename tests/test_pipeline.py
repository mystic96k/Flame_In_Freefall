import pandas as pd

from pipeline.ingest_psi_tables import auto_map, unit_factor
from pipeline.schema import conform, normalize_material, normalize_outcome, validate


def test_normalize_outcome():
    assert normalize_outcome("Burned to completion") == "burn"
    assert normalize_outcome("Quenching extinction") == "extinct"
    assert normalize_outcome("Blow-off") == "extinct"
    assert normalize_outcome("No ignition") == "no_ignition"
    assert normalize_outcome(1) == "burn"
    assert normalize_outcome(None) == "unknown"


def test_normalize_material():
    assert normalize_material("Acrylic sphere") == "PMMA"
    assert normalize_material("SIBAL fabric") == "SIBAL (algodón/fibra de vidrio)"


def test_auto_map_typical_headers():
    cols = ["Test Number", "Sample Material", "Flow Velocity (cm/s)", "O2 (%)", "Pressure (psia)", "Result"]
    m = auto_map(cols)
    assert m["Test Number"] == "run_id"
    assert m["Flow Velocity (cm/s)"] == "flow_cm_s"
    assert m["O2 (%)"] == "o2_pct"
    assert m["Pressure (psia)"] == "pressure_kpa"
    assert m["Result"] == "outcome"
    assert abs(unit_factor("Pressure (psia)", "pressure_kpa") - 6.89476) < 1e-6


def test_conform_and_validate():
    raw = pd.DataFrame({"material": ["PMMA", "cotton/fiberglass"], "flow_cm_s": ["10 cm/s", "5"],
                        "o2_pct": [21, 17.5], "outcome": ["burned", "quench"]})
    df = conform(raw, investigation="TEST", source="unit")
    assert list(df["burned"]) == [1, 0]
    assert df["flow_cm_s"].tolist() == [10.0, 5.0]
    assert validate(df) == []

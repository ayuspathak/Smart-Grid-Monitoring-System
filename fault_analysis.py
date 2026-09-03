"""Simplified feeder fault calculations for academic use."""

from __future__ import annotations
import math

FEEDER_VOLTAGE_KV = {"Industrial": 11.0, "Commercial": 10.8, "Residential": 10.6}
FAULT_FACTOR = {"3-phase": 1.00, "line-line": 0.88, "single-line-ground": 0.63}
BASE_IMPEDANCE = {"3-phase": 0.17, "line-line": 0.22, "single-line-ground": 0.30}


def calculate(fault_type: str, feeder: str, resistance: float = 0.08) -> dict:
    kv = FEEDER_VOLTAGE_KV[feeder]
    z = BASE_IMPEDANCE[fault_type] + max(float(resistance), 0.0)
    v_phase = kv * 1000 / math.sqrt(3)
    current_ka = v_phase / z / 1000 * FAULT_FACTOR[fault_type]
    multiple = max(current_ka / 0.40, 1.0)
    clearing_ms = max(35.0, min(180.0, 115.0 / (multiple ** 1.45)))
    severity = "HIGH" if current_ka >= 3 else "MEDIUM" if current_ka >= 1.5 else "LOW"
    dip = min(0.45, 0.055 + 0.028 * current_ka)
    profile = [{"node": n, "voltage_pu": round(max(0.70, 1.0 - dip*i/3), 3)}
               for i, n in enumerate(("Substation", f"{feeder} feeder", "Feeder end"), 1)]
    return {"fault_type": fault_type, "feeder": feeder, "fault_current_ka": round(current_ka,3),
            "clearing_ms": round(clearing_ms,1), "severity": severity, "voltage_profile": profile}

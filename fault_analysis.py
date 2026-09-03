"""Simplified fault-study calculations for academic use."""

from __future__ import annotations

import math

FEEDER_KV = {"Industrial": 11.0, "Commercial": 10.8, "Residential": 10.6}
FAULT_FACTOR = {"3-phase": 1.00, "line-line": 0.87, "single-line-ground": 0.62}
BASE_Z = {"3-phase": 0.16, "line-line": 0.21, "single-line-ground": 0.29}


def calculate(fault_type: str, feeder: str, resistance: float) -> dict:
    kv = FEEDER_KV[feeder]
    z = BASE_Z[fault_type] + max(float(resistance), 0.0)
    phase_v = kv * 1000 / math.sqrt(3)
    current_ka = phase_v / z / 1000 * FAULT_FACTOR[fault_type]

    pickup = 0.40
    ratio = max(current_ka / pickup, 1.0)
    clearing_ms = max(40.0, min(160.0, 110.0 / (ratio ** 1.55)))
    severity = "HIGH" if current_ka >= 3.0 else "MEDIUM" if current_ka >= 1.5 else "LOW"

    base_drop = min(0.42, 0.06 + 0.032 * current_ka)
    nodes = ["Substation", f"{feeder} feeder", "End node"]
    profile = []
    for i, node in enumerate(nodes, start=1):
        profile.append({"node": node, "voltage_pu": round(max(0.70, 1 - base_drop * i / 3), 3)})

    return {
        "fault_type": fault_type,
        "feeder": feeder,
        "fault_current_ka": round(current_ka, 3),
        "clearing_ms": round(clearing_ms, 1),
        "severity": severity,
        "voltage_profile": profile,
    }


if __name__ == "__main__":
    print(calculate("3-phase", "Commercial", 0.08))

"""A simplified feeder fault study for academic demonstration.

The equations here are intentionally approximate. They are useful for comparing
scenarios in software, not for relay settings or field protection design.
"""

from __future__ import annotations

import math

FEEDER_VOLTAGE_KV = {
    "Industrial": 11.0,
    "Commercial": 10.8,
    "Residential": 10.6,
}

FAULT_FACTOR = {
    "3-phase": 1.00,
    "line-line": 0.88,
    "single-line-ground": 0.63,
}

BASE_IMPEDANCE = {
    "3-phase": 0.17,
    "line-line": 0.22,
    "single-line-ground": 0.30,
}


def calculate(fault_type: str, feeder: str, resistance: float = 0.08) -> dict:
    voltage_kv = FEEDER_VOLTAGE_KV[feeder]
    total_impedance = BASE_IMPEDANCE[fault_type] + max(float(resistance), 0.0)
    phase_voltage = voltage_kv * 1000 / math.sqrt(3)

    current_ka = phase_voltage / total_impedance / 1000
    current_ka *= FAULT_FACTOR[fault_type]

    pickup_ka = 0.40
    multiple = max(current_ka / pickup_ka, 1.0)
    clearing_ms = max(35.0, min(180.0, 115.0 / (multiple ** 1.45)))

    if current_ka >= 3.0:
        severity = "HIGH"
    elif current_ka >= 1.5:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    dip = min(0.45, 0.055 + 0.028 * current_ka)
    profile = []
    for idx, node in enumerate(("Substation", f"{feeder} feeder", "Feeder end"), 1):
        profile.append({
            "node": node,
            "voltage_pu": round(max(0.70, 1.0 - dip * idx / 3), 3),
        })

    return {
        "fault_type": fault_type,
        "feeder": feeder,
        "fault_current_ka": round(current_ka, 3),
        "clearing_ms": round(clearing_ms, 1),
        "severity": severity,
        "voltage_profile": profile,
    }

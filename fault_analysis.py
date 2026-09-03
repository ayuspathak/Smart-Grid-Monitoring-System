"""Simple educational fault-study calculations."""

import math


def simulate_fault(fault_type="3PH", location="Commercial Feeder", fault_resistance=0.05):
    """Return a repeatable what-if fault estimate for the demo feeder.

    The calculation is intentionally simplified. It is for software testing,
    not protection-setting or field design.
    """
    base_kv = {"Industrial Feeder": 11.0, "Commercial Feeder": 10.9, "Residential Feeder": 10.8}.get(location, 10.9)
    z_grid = 0.18 if fault_type == "3PH" else 0.24 if fault_type == "LL" else 0.31
    phase_kv = base_kv / math.sqrt(3)
    current_ka = (phase_kv / 1000) / max(z_grid + fault_resistance, 0.001)
    current_ka *= {"3PH": 1.25, "LL": 0.92, "SLG": 0.68}.get(fault_type, 1.0)
    current_ka = round(current_ka, 3)

    pickup_ka = 0.45
    ratio = max(current_ka / pickup_ka, 1.01)
    trip_ms = max(35.0, min(180.0, 95.0 / (ratio ** 1.8)))
    trip_ms = round(trip_ms, 1)

    if current_ka >= 2.5:
        severity = "HIGH"
    elif current_ka >= 1.2:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # A small voltage-sag profile along the feeder.
    drop = min(0.55, 0.08 + current_ka * 0.045)
    profile = []
    for idx, node in enumerate(["Substation", "Industrial Feeder", "Commercial Feeder", "Residential Feeder"]):
        sag = min(0.75, drop * (idx + 1) / 4)
        profile.append({"node": node, "voltage_pu": round(1.0 - sag, 3)})

    return {
        "fault_type": fault_type,
        "location": location,
        "fault_current_ka": current_ka,
        "trip_time_ms": trip_ms,
        "severity": severity,
        "voltage_profile": profile,
    }


if __name__ == "__main__":
    print(simulate_fault())

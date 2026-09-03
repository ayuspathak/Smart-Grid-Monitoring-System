"""Generate fake three-phase meter readings for local testing.

This file stands in for a future ESP32/MQTT source. It only writes demo data
to the local SQLite database; no hardware connection is required.
"""

from __future__ import annotations

import math
import random
import time
from datetime import datetime

import database


def sample(step: int, node: str = "AYUSH_NODE_01") -> dict:
    angle = (step % 96) / 96 * 2 * math.pi
    load = 1.0 + 0.09 * math.sin(angle) + random.uniform(-0.015, 0.015)
    phase_shift = random.uniform(-0.008, 0.008)

    va = 230.0 * load
    vb = 230.0 * load * (1.0 + phase_shift)
    vc = 230.0 * load * (1.0 - phase_shift * 0.8)

    ia = 10.0 * load + random.uniform(-0.25, 0.25)
    ib = 9.8 * load + random.uniform(-0.25, 0.25)
    ic = 9.9 * load + random.uniform(-0.25, 0.25)
    pf = max(0.86, min(0.99, 0.95 + random.uniform(-0.012, 0.012)))
    power_kw = (va * ia + vb * ib + vc * ic) * pf / 1000.0

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "node_id": node,
        "voltage_a": round(va, 2),
        "voltage_b": round(vb, 2),
        "voltage_c": round(vc, 2),
        "current_a": round(ia, 2),
        "current_b": round(ib, 2),
        "current_c": round(ic, 2),
        "active_power": round(power_kw, 3),
        "power_factor": round(pf, 3),
        "frequency": round(50.0 + random.uniform(-0.03, 0.03), 3),
        "status": "NORMAL",
    }


def run(interval_seconds: float = 2.0) -> None:
    step = 0
    database.initialize()
    while True:
        database.log_telemetry(sample(step))
        step += 1
        time.sleep(interval_seconds)


if __name__ == "__main__":
    database.initialize()
    for i in range(10):
        database.log_telemetry(sample(i))
    print("Added 10 sample telemetry readings.")

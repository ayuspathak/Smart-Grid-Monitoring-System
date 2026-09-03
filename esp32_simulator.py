"""Generate sample three-phase telemetry for local testing."""

from datetime import datetime
import math
import random
import time
import database as db


def make_packet(step=0):
    angle = (step % 120) / 120 * 2 * math.pi
    load = 1.0 + 0.10 * math.sin(angle) + random.uniform(-0.025, 0.025)
    imbalance = random.uniform(-1.2, 1.2)
    voltage_a = 230.0 * load
    voltage_b = 230.0 * load * (1 + imbalance / 100)
    voltage_c = 230.0 * load * (1 - imbalance / 120)
    current_a = 10.5 * load
    current_b = 10.1 * load * (1 + imbalance / 150)
    current_c = 10.3 * load
    pf = max(0.82, min(0.99, 0.94 + random.uniform(-0.015, 0.015)))
    power = (voltage_a * current_a + voltage_b * current_b + voltage_c * current_c) * pf / 1000
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "node_id": "AYUSH_NODE_01",
        "voltage_a": round(voltage_a, 2), "voltage_b": round(voltage_b, 2), "voltage_c": round(voltage_c, 2),
        "current_a": round(current_a, 2), "current_b": round(current_b, 2), "current_c": round(current_c, 2),
        "active_power": round(power, 3), "power_factor": round(pf, 3),
        "frequency": round(50.0 + random.uniform(-0.04, 0.04), 3),
        "status": "NORMAL",
    }


def run_simulator(interval_sec=2):
    step = 0
    while True:
        db.log_telemetry(make_packet(step))
        step += 1
        time.sleep(interval_sec)


if __name__ == "__main__":
    db.init_db()
    for step in range(5):
        db.log_telemetry(make_packet(step))
        time.sleep(0.2)
    print("Added sample telemetry records.")

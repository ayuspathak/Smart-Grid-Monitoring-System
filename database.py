"""Local SQLite storage for the Smart-grid project."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "smart_grid.db")


def connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def initialize() -> None:
    con = connection()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        node_id TEXT NOT NULL,
        voltage_a REAL NOT NULL,
        voltage_b REAL NOT NULL,
        voltage_c REAL NOT NULL,
        current_a REAL NOT NULL,
        current_b REAL NOT NULL,
        current_c REAL NOT NULL,
        active_power REAL NOT NULL,
        power_factor REAL NOT NULL,
        frequency REAL NOT NULL,
        status TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS feeder_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        load_factor REAL,
        pv_mw REAL,
        min_voltage_pu REAL,
        peak_loading_pct REAL,
        losses_kw REAL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS fault_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        fault_type TEXT,
        feeder TEXT,
        current_ka REAL,
        clearing_ms REAL,
        severity TEXT
    )""")
    con.commit()
    cur.execute("SELECT COUNT(*) FROM telemetry")
    empty = cur.fetchone()[0] == 0
    con.close()
    if empty:
        add_sample_batch(96)


def add_sample_batch(count: int = 24) -> None:
    rng = np.random.default_rng()
    now = datetime.now()
    rows = []
    for i in range(count):
        stamp = now - timedelta(minutes=(count - 1 - i) * 10)
        t = stamp.hour + stamp.minute / 60.0
        demand_shape = 0.78 + 0.18 * np.exp(-((t - 18.5) / 3.8) ** 2) + 0.03 * np.sin(t)
        for node, offset in (("NODE_01", 0.0), ("FEEDER_A", -0.8), ("FEEDER_B", 0.6)):
            base = 230.0 + offset
            spread = rng.normal(0, 0.9, 3)
            va, vb, vc = base + spread
            current = 9.0 + 18.0 * demand_shape
            ia, ib, ic = current + rng.normal(0, 0.45, 3)
            pf = float(np.clip(0.94 + rng.normal(0, 0.012), 0.86, 0.99))
            power = (va * ia + vb * ib + vc * ic) * pf / 1000.0
            freq = float(50.0 + rng.normal(0, 0.025))
            status = "NORMAL"
            if i % 31 == 0:
                vb *= 0.965
                status = "CHECK"
            rows.append((stamp.strftime("%Y-%m-%d %H:%M:%S"), node, va, vb, vc,
                         ia, ib, ic, power, pf, freq, status))
    con = connection()
    con.executemany("""INSERT INTO telemetry
        (timestamp,node_id,voltage_a,voltage_b,voltage_c,current_a,current_b,current_c,
         active_power,power_factor,frequency,status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    con.commit(); con.close()


def log_telemetry(packet: dict) -> None:
    con = connection()
    con.execute("""INSERT INTO telemetry
        (timestamp,node_id,voltage_a,voltage_b,voltage_c,current_a,current_b,current_c,
         active_power,power_factor,frequency,status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
        packet.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        packet.get("node_id", "NODE_01"), packet.get("voltage_a", 230.0),
        packet.get("voltage_b", 230.0), packet.get("voltage_c", 230.0),
        packet.get("current_a", 10.0), packet.get("current_b", 10.0), packet.get("current_c", 10.0),
        packet.get("active_power", 6.5), packet.get("power_factor", 0.95),
        packet.get("frequency", 50.0), packet.get("status", "NORMAL")))
    con.commit(); con.close()


def recent_telemetry(limit: int = 100, node: str | None = None) -> pd.DataFrame:
    con = connection()
    if node:
        df = pd.read_sql_query("SELECT * FROM telemetry WHERE node_id=? ORDER BY id DESC LIMIT ?", con, params=(node, limit))
    else:
        df = pd.read_sql_query("SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", con, params=(limit,))
    con.close()
    return df


def save_feeder_result(result: dict, load_factor: float, pv_mw: float) -> None:
    con = connection()
    con.execute("""INSERT INTO feeder_runs(timestamp,load_factor,pv_mw,min_voltage_pu,peak_loading_pct,losses_kw)
                   VALUES(?,?,?,?,?,?)""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), load_factor, pv_mw,
                   result["minimum_voltage_pu"], result["peak_loading_pct"], result["losses_kw"]))
    con.commit(); con.close()


def save_fault_result(result: dict) -> None:
    con = connection()
    con.execute("""INSERT INTO fault_cases(timestamp,fault_type,feeder,current_ka,clearing_ms,severity)
                   VALUES(?,?,?,?,?,?)""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), result["fault_type"],
                   result["feeder"], result["fault_current_ka"], result["clearing_ms"], result["severity"]))
    con.commit(); con.close()


def recent_faults(limit: int = 20) -> pd.DataFrame:
    con = connection(); df = pd.read_sql_query("SELECT * FROM fault_cases ORDER BY id DESC LIMIT ?", con, params=(limit,)); con.close(); return df


if __name__ == "__main__":
    initialize()
    print(f"Database ready: {DB_PATH}")

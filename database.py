"""SQLite helpers for telemetry and analysis history."""

import os
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "smart_grid.db")


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        node_id TEXT NOT NULL,
        voltage_a REAL, voltage_b REAL, voltage_c REAL,
        current_a REAL, current_b REAL, current_c REAL,
        active_power REAL, power_factor REAL, frequency REAL,
        status TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS fault_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        fault_type TEXT,
        location TEXT,
        fault_current_ka REAL,
        trip_time_ms REAL,
        severity TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS powerflow_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        load_scale REAL,
        solar_mw REAL,
        min_voltage_pu REAL,
        max_loading_pct REAL,
        losses_kw REAL
    )""")
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM telemetry")
    if cur.fetchone()[0] < 60:
        seed_demo_data(conn)
    conn.close()


def seed_demo_data(conn):
    now = datetime.now()
    rng = np.random.default_rng(42)
    rows = []
    for step in range(144):
        ts = now - timedelta(minutes=step * 10)
        hour = ts.hour + ts.minute / 60
        shape = 0.55 + 0.30 * np.exp(-((hour - 18) / 4) ** 2) + 0.08 * np.sin(hour / 2)
        for node in ("AYUSH_NODE_01", "FEEDER_A", "FEEDER_B"):
            base_v = 230.0 if node != "AYUSH_NODE_01" else 229.5
            va, vb, vc = base_v + rng.normal(0, 1.2, 3)
            ia, ib, ic = 8 + 22 * shape + rng.normal(0, 0.7, 3)
            pf = float(np.clip(0.94 + rng.normal(0, 0.018), 0.82, 0.99))
            power = float((va * ia + vb * ib + vc * ic) * pf / 1000)
            freq = float(50 + rng.normal(0, 0.035))
            status = "NORMAL"
            if step % 47 == 0:
                va *= 0.94
                status = "CHECK"
            rows.append((ts.strftime("%Y-%m-%d %H:%M:%S"), node, va, vb, vc,
                         ia, ib, ic, power, pf, freq, status))
    conn.executemany("""INSERT INTO telemetry
        (timestamp,node_id,voltage_a,voltage_b,voltage_c,current_a,current_b,current_c,
         active_power,power_factor,frequency,status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    conn.commit()


def log_telemetry(data):
    conn = get_connection()
    conn.execute("""INSERT INTO telemetry
        (timestamp,node_id,voltage_a,voltage_b,voltage_c,current_a,current_b,current_c,
         active_power,power_factor,frequency,status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
        data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        data.get("node_id", "AYUSH_NODE_01"), data.get("voltage_a", 230.0),
        data.get("voltage_b", 230.0), data.get("voltage_c", 230.0),
        data.get("current_a", 10.0), data.get("current_b", 10.0), data.get("current_c", 10.0),
        data.get("active_power", 6.5), data.get("power_factor", 0.95),
        data.get("frequency", 50.0), data.get("status", "NORMAL")))
    conn.commit(); conn.close()


def get_recent_telemetry(limit=100, node_id=None):
    conn = get_connection()
    if node_id:
        df = pd.read_sql_query("SELECT * FROM telemetry WHERE node_id=? ORDER BY id DESC LIMIT ?", conn, params=(node_id, limit))
    else:
        df = pd.read_sql_query("SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", conn, params=(limit,))
    conn.close()
    return df


def log_fault_event(fault_type, location, current_ka, trip_ms, severity):
    conn = get_connection()
    conn.execute("INSERT INTO fault_events(timestamp,fault_type,location,fault_current_ka,trip_time_ms,severity) VALUES(?,?,?,?,?,?)",
                 (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fault_type, location, current_ka, trip_ms, severity))
    conn.commit(); conn.close()


def get_all_faults():
    conn = get_connection(); df = pd.read_sql_query("SELECT * FROM fault_events ORDER BY id DESC", conn); conn.close(); return df


def log_powerflow(result, load_scale, solar_mw):
    conn = get_connection()
    conn.execute("INSERT INTO powerflow_history(timestamp,load_scale,solar_mw,min_voltage_pu,max_loading_pct,losses_kw) VALUES(?,?,?,?,?,?)",
                 (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), load_scale, solar_mw,
                  result["min_voltage_pu"], result["max_line_loading_pct"], result["total_loss_kw"]))
    conn.commit(); conn.close()


def get_powerflow_history(limit=50):
    conn=get_connection(); df=pd.read_sql_query("SELECT * FROM powerflow_history ORDER BY id DESC LIMIT ?", conn, params=(limit,)); conn.close(); return df


if __name__ == "__main__":
    init_db()
    print("Database ready:", DB_PATH)

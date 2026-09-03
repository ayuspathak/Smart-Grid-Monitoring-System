"""Start the dashboard and prepare its local data store."""

import subprocess
import sys

import database as db


def main():
    db.init_db()
    print("Smart Grid Monitoring System")
    print("Launching Streamlit dashboard...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=False)


if __name__ == "__main__":
    main()

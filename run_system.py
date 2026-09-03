"""Launch the Smart Grid dashboard."""

import subprocess
import sys

import database


def main() -> None:
    database.initialize()
    print("Smart Grid Monitoring System")
    print("Starting Streamlit dashboard...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=False)


if __name__ == "__main__":
    main()

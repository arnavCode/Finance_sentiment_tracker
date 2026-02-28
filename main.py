#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def run_step(label: str, script_path: Path) -> None:
    print(f"[Pipeline] Starting: {label} ({script_path})")
    subprocess.run([sys.executable, str(script_path)], check=True)
    print(f"[Pipeline] Finished: {label}")


def main() -> None:
    root = Path(__file__).resolve().parent

    steps = [
        ("Ingest Articles", root / "src" / "ingest.py"),
        ("Score Sentiment", root / "src" / "score.py"),
        ("Ingest Prices", root / "src" / "ingest_prices.py"),
    ]

    for label, script in steps:
        if not script.exists():
            raise FileNotFoundError(f"Required script not found: {script}")
        run_step(label, script)

    print("[Pipeline] All steps completed.")


if __name__ == "__main__":
    main()

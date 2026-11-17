#!/usr/bin/env python3
"""Check everything needed before running a baseline. Does not call any API."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT.parent / "datasets" / "AutomationBench"


def ok(value: bool) -> str:
    return "OK" if value else "MISSING"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default=str(DEFAULT_DATASET))
    args = parser.parse_args()
    dataset = Path(args.dataset_dir).expanduser().resolve()

    rows = []
    rows.append(("Python >= 3.13", ok(sys.version_info >= (3, 13)), sys.version.split()[0]))
    rows.append(("uv", ok(shutil.which("uv") is not None), shutil.which("uv") or "-"))
    rows.append(("dataset dir", ok(dataset.is_dir()), str(dataset)))
    rows.append(("pyproject.toml", ok((dataset / "pyproject.toml").is_file()), ""))
    rows.append(("uv environment", ok((dataset / ".venv").is_dir()), str(dataset / ".venv")))

    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_BASE_URL"):
        value = os.environ.get(var)
        rows.append((var, "SET" if value else "not set", "***" if value else "-"))

    commit = "-"
    if (dataset / ".git").is_dir():
        try:
            commit = subprocess.check_output(
                ["git", "-C", str(dataset), "rev-parse", "--short", "HEAD"], text=True
            ).strip()
        except subprocess.SubprocessError:
            pass
    rows.append(("dataset git commit", commit != "-", commit))

    width = max(len(r[0]) for r in rows) + 2
    print(f"{'item':<{width}} {'status':<10} detail")
    print("-" * (width + 50))
    for name, status, detail in rows:
        print(f"{name:<{width}} {status:<10} {detail}")

    print()
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("No API key found: dry-run is possible, real runs are not.")
        print("Set OPENAI_API_KEY (and OPENAI_BASE_URL if using a gateway).")
    else:
        print("API key present. You can run the smoke test.")


if __name__ == "__main__":
    main()

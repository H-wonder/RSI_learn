#!/usr/bin/env python3
"""Create compact, audit-friendly result JSONs (no full conversations).

Outputs:
  reports/small-18.compact.json
  reports/medium-60.compact.json

Each task keeps score, assertion-level results, steps, tokens and cost; the
full `messages` / `end_state` fields are dropped.
"""

from __future__ import annotations

import csv
import json
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"


def load_tasks(paths: list[Path]) -> dict[str, dict]:
    tasks: dict[str, dict] = {}
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data.get("tasks") or []:
            name = task.get("name") or ""
            if not name:
                continue
            if name not in tasks or float(task.get("score", 0)) > float(
                tasks[name].get("score", 0)
            ):
                tasks[name] = task
    return tasks


def compact(task: dict) -> dict:
    return {
        "name": task.get("name"),
        "domain": (task.get("name") or "").split(".", 1)[0],
        "score": float(task.get("score", 0.0)),
        "passed": bool(task.get("passed")),
        "assertions_total": task.get("assertions_total"),
        "assertions_passed": task.get("assertions_passed"),
        "assertion_results": task.get("assertion_results") or [],
        "steps": task.get("steps"),
        "input_tokens": task.get("input_tokens"),
        "output_tokens": task.get("output_tokens"),
        "cost": task.get("cost"),
    }


def write(path: Path, tasks: list[dict], label: str, sources: list[str]) -> None:
    scores = [t["score"] for t in tasks]
    payload = {
        "meta": {
            "label": label,
            "generated": datetime.now().isoformat(timespec="seconds"),
            "n": len(tasks),
            "pass_rate": sum(1 for t in tasks if t["passed"]) / len(tasks),
            "avg_partial_credit": statistics.mean(scores),
            "total_cost": sum(float(t.get("cost") or 0) for t in tasks),
            "sources": sources,
            "note": "Full messages/end_state are intentionally omitted; see results/ locally.",
        },
        "tasks": tasks,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path} ({len(tasks)} tasks, {path.stat().st_size / 1024:.0f} KB)")


def main() -> None:
    small_paths = sorted(
        p for p in (ROOT / "results" / "small").glob("*.json") if p.name != "manifest.json"
    )
    medium_paths = sorted(
        p for p in (ROOT / "results" / "medium").glob("*.json") if p.name != "manifest.json"
    )

    small = load_tasks(small_paths)
    write(
        REPORTS / "small-18.compact.json",
        [compact(t) for t in sorted(small.values(), key=lambda x: x["name"])],
        "small-18",
        [str(p.relative_to(ROOT)) for p in small_paths],
    )

    allowed = {
        row["task_name"]
        for row in csv.DictReader(
            open(ROOT / "data" / "tasks" / "medium_from_annotation.csv", encoding="utf-8-sig")
        )
    }
    merged = load_tasks(small_paths + medium_paths)
    medium = [compact(t) for name, t in merged.items() if name in allowed]
    write(
        REPORTS / "medium-60.compact.json",
        sorted(medium, key=lambda x: x["name"]),
        "medium-60",
        [str(p.relative_to(ROOT)) for p in small_paths + medium_paths],
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Join baseline results with the manual annotation sheet (problem types).

Produces the "problem type x pass rate" table (table 2 in the report).

Usage:
    python scripts/analyze_by_type.py --dir results/full \
        --annotation data/annotation/tasks_to_label.csv \
        --out-md reports/full.by_type.md --out-csv reports/full.by_type.csv

Tasks without a filled primary_type are grouped as `unlabeled`, so the command
is safe to run before the annotation is complete.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

TYPE_ORDER = [
    "P1",
    "P2",
    "P3",
    "P4a",
    "P4b",
    "P5",
    "P6",
    "P7",
    "P8",
    "P9",
    "unlabeled",
]


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


def load_annotation(path: Path) -> dict[str, dict]:
    result: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            name = (row.get("task_name") or "").strip()
            if not name:
                continue
            result[name] = {
                "primary": (row.get("primary_type") or "").strip(),
                "subtype": (row.get("primary_subtype") or "").strip(),
                "secondary": (row.get("secondary_types") or "").strip(),
            }
    return result


def pct(num: float, den: float) -> str:
    return f"{100 * num / den:.1f}%" if den else "-"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        action="append",
        help="directory with result JSON files; repeat to merge runs",
    )
    parser.add_argument("files", nargs="*")
    parser.add_argument("--annotation", default="data/annotation/tasks_to_label.csv")
    parser.add_argument(
        "--tasks-file",
        help="CSV with a task_name column; keep only these tasks (for merged runs)",
    )
    parser.add_argument("--out-md", default="reports/by_type.md")
    parser.add_argument("--out-csv", default="reports/by_type.csv")
    args = parser.parse_args()

    if args.dir:
        paths = []
        for directory in args.dir:
            paths.extend(
                p for p in Path(directory).rglob("*.json") if p.name != "manifest.json"
            )
        paths = sorted(set(paths))
    else:
        paths = [Path(p) for p in args.files]
    if not paths:
        raise SystemExit("no result JSON files found")

    tasks = load_tasks(paths)
    if args.tasks_file:
        with open(args.tasks_file, newline="", encoding="utf-8-sig") as fh:
            allowed = {row["task_name"] for row in csv.DictReader(fh)}
        tasks = {k: v for k, v in tasks.items() if k in allowed}
    annotation = load_annotation(Path(args.annotation))

    groups: dict[str, list[dict]] = defaultdict(list)
    for name, task in tasks.items():
        ann = annotation.get(name, {})
        primary = ann.get("subtype") or ann.get("primary") or "unlabeled"
        if primary == "P4" and not ann.get("subtype"):
            raise SystemExit(f"P4 task without primary_subtype: {name}")
        if primary not in TYPE_ORDER:
            primary = "unlabeled"
        groups[primary].append(task)

    labeled = sum(len(groups[t]) for t in TYPE_ORDER if t != "unlabeled")
    total = len(tasks)

    lines = []
    lines.append("# 问题类型 × 基线表现")
    lines.append("")
    lines.append(f"- tasks with results: {total}")
    lines.append(f"- tasks with a primary_type: {labeled} ({pct(labeled, total)})")
    lines.append("")
    lines.append("| problem type | n | pass rate | partial credit | avg steps | example tasks |")
    lines.append("|---|---:|---:|---:|---:|---|")
    csv_rows = []
    for ptype in TYPE_ORDER:
        group = groups.get(ptype, [])
        if not group:
            continue
        scores = [float(t.get("score", 0)) for t in group]
        steps = [float(t.get("steps", 0) or 0) for t in group]
        pass_rate = sum(1 for s in scores if s >= 1.0 - 1e-9) / len(scores)
        examples = ", ".join(t.get("name", "") for t in group[:3])
        lines.append(
            f"| {ptype} | {len(group)} | {100 * pass_rate:.1f}% | "
            f"{statistics.mean(scores):.3f} | {statistics.mean(steps):.1f} | {examples} |"
        )
        csv_rows.append(
            {
                "problem_type": ptype,
                "n": len(group),
                "pass_rate": f"{pass_rate:.4f}",
                "partial_credit": f"{statistics.mean(scores):.4f}",
                "avg_steps": f"{statistics.mean(steps):.1f}",
                "examples": examples,
            }
        )

    if "unlabeled" in groups:
        lines.append("")
        lines.append(
            "> `unlabeled` means the task is not in the annotation CSV or its "
            "`primary_type` is empty. Fill the annotation first for table 2."
        )

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["problem_type", "n", "pass_rate", "partial_credit", "avg_steps", "examples"],
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"wrote {out_md}")
    print(f"wrote {out_csv}")


if __name__ == "__main__":
    main()

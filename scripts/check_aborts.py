#!/usr/bin/env python3
"""Detect tasks that were cut off mid-work (aborts) in AutomationBench results.

Why this exists: `auto-bench` only runs its `--ensure-complete` healing pass for
full-dataset runs. Runs driven by `--tasks` (which is how we run a fixed sample)
skip it, so a transient network/API cut-off would silently be scored as 0.

The signature of a healthy finished task is a final assistant message with no
tool calls (the model wrote a closing answer). An abort instead ends on a tool
call or a tool result. This script is offline and stdlib-only.

Usage:
    python scripts/check_aborts.py --dir results/medium-max
    python scripts/check_aborts.py --dir results/medium-max --out-csv /tmp/retry.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_tasks(paths: list[Path]) -> list[tuple[Path, dict]]:
    rows: list[tuple[Path, dict]] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        max_steps = (data.get("meta") or {}).get("max_steps")
        for task in data.get("tasks") or []:
            task["_max_steps"] = max_steps
            rows.append((path, task))
    return rows


def abort_reason(task: dict) -> str | None:
    if task.get("died_on_refusal"):
        return "refusal"
    messages = task.get("messages") or []
    if not messages:
        return "no messages"
    last = messages[-1]
    role = last.get("role")
    tool_calls = last.get("tool_calls") or []
    if role == "tool":
        return "ended on tool result"
    if role == "assistant" and tool_calls:
        return "ended on assistant tool call"
    if role != "assistant":
        return f"ended on {role!r}"
    content = last.get("content")
    if isinstance(content, list):
        content = " ".join(str(part) for part in content)
    if not (content or "").strip() and not last.get("reasoning_content"):
        return "empty final assistant message"
    return None


def domain_of(name: str) -> str:
    return name.split(".", 1)[0] if "." in name else "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", action="append", required=True, help="result directory; repeatable")
    parser.add_argument("--out-csv", help="write aborted tasks as domain,task_name for a rerun")
    args = parser.parse_args()

    paths: list[Path] = []
    for directory in args.dir:
        paths.extend(p for p in Path(directory).rglob("*.json") if p.name != "manifest.json")
    paths = sorted(set(paths))
    if not paths:
        raise SystemExit("no result JSON files found")

    tasks = load_tasks(paths)
    aborts = []
    for path, task in tasks:
        reason = abort_reason(task)
        if reason:
            aborts.append((path, task, reason))

    print(f"files: {len(paths)} | tasks: {len(tasks)} | aborts: {len(aborts)}")
    for path, task, reason in aborts:
        print(
            f"  {task.get('name', '?')} | score={float(task.get('score', 0)):.3f} "
            f"| steps={task.get('steps')} | {reason} | {path}"
        )
    if aborts and args.out_csv:
        with open(args.out_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["domain", "task_name"])
            for _, task, _ in aborts:
                name = task.get("name", "")
                writer.writerow([domain_of(name), name])
        print(f"rerun CSV: {args.out_csv}")
    if aborts:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

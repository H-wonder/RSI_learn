#!/usr/bin/env python3
"""One-screen digest of every failing task, for manual root-cause coding.

Usage:
    python scripts/failure_digest.py --dir results/medium-max --maxlen 220
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_tasks(directory: Path) -> list[dict]:
    tasks: dict[str, dict] = {}
    for path in sorted(directory.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        for task in json.loads(path.read_text(encoding="utf-8")).get("tasks") or []:
            tasks[task.get("name", "")] = task
    return list(tasks.values())


def clip(value, limit: int) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = " ".join(text.split())
    return text[:limit] + ("..." if len(text) > limit else "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--maxlen", type=int, default=220)
    args = parser.parse_args()

    tasks = [t for t in load_tasks(Path(args.dir)) if float(t.get("score", 0)) < 1.0]
    tasks.sort(key=lambda t: (float(t.get("score", 0)), t.get("name", "")))
    print(f"failing tasks: {len(tasks)}\n")
    for task in tasks:
        failures = [
            a
            for a in (task.get("assertion_results") or [])
            if not a.get("excluded") and not a.get("passed")
        ]
        print("=" * 100)
        print(
            f"{task['name']} | score={float(task.get('score', 0)):.3f} "
            f"| {task.get('assertions_passed')}/{task.get('assertions_total')} "
            f"| steps={task.get('steps')}"
        )
        print("failed assertions:")
        for a in failures[:8]:
            print(f"  - {a.get('type')}: {clip(a.get('params'), args.maxlen)}")
        if len(failures) > 8:
            print(f"  ... {len(failures) - 8} more")
        calls = []
        for message in task.get("messages") or []:
            for call in message.get("tool_calls") or []:
                if isinstance(call, str):
                    try:
                        call = json.loads(call)
                    except json.JSONDecodeError:
                        continue
                if isinstance(call, dict):
                    name = call.get("name") or (call.get("function") or {}).get("name")
                    arguments = call.get("arguments") or (call.get("function") or {}).get("arguments")
                    calls.append(f"{name}({clip(arguments, 90)})")
        print("tool calls:")
        for call in calls[:12]:
            print(f"  {call}")
        if len(calls) > 12:
            print(f"  ... {len(calls) - 12} more")
        final = ""
        for message in reversed(task.get("messages") or []):
            if message.get("role") == "assistant":
                final = message.get("content") or ""
                break
        print(f"final: {clip(final, args.maxlen)}")
        print()


if __name__ == "__main__":
    main()

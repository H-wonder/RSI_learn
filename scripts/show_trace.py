#!/usr/bin/env python3
"""Print one task's trajectory from an exported AutomationBench result JSON.

Usage:
    python scripts/show_trace.py --dir results/medium-max --task sales.multi_hop_lookup
    python scripts/show_trace.py --dir results/medium-max --task sales.foo --maxlen 0
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def find_task(directory: Path, name: str) -> tuple[dict, dict]:
    for path in sorted(directory.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data.get("tasks") or []:
            if task.get("name") == name:
                return data, task
    raise SystemExit(f"task not found: {name}")


def shorten(value, maxlen: int) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if maxlen and len(text) > maxlen:
        return text[:maxlen] + f"... [{len(text) - maxlen} chars]"
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--maxlen", type=int, default=400, help="0 = no truncation")
    args = parser.parse_args()

    data, task = find_task(Path(args.dir), args.task)
    meta = data.get("meta") or {}
    print(f"# {task['name']}")
    print(
        f"meta: model={meta.get('model')} effort={meta.get('reasoning_effort')} "
        f"toolset={meta.get('toolset')} max_steps={meta.get('max_steps')}"
    )
    print(
        f"score={float(task.get('score', 0)):.3f} passed={task.get('passed')} "
        f"assertions={task.get('assertions_passed')}/{task.get('assertions_total')} "
        f"steps={task.get('steps')} cost={task.get('cost')}"
    )
    print("\n## failed assertions")
    for assertion in task.get("assertion_results") or []:
        if assertion.get("excluded") or assertion.get("passed"):
            continue
        print(f"- {assertion.get('type')}: {shorten(assertion.get('params'), args.maxlen)}")
    print("\n## trajectory")
    for i, message in enumerate(task.get("messages") or [], 1):
        role = message.get("role")
        if role == "assistant":
            content = message.get("content") or ""
            print(f"\n[{i}] assistant: {shorten(content, args.maxlen)}")
            for call in message.get("tool_calls") or []:
                if isinstance(call, str):
                    try:
                        call = json.loads(call)
                    except json.JSONDecodeError:
                        pass
                if isinstance(call, dict):
                    name = call.get("name") or (call.get("function") or {}).get("name")
                    arguments = call.get("arguments") or (call.get("function") or {}).get("arguments")
                    print(f"    -> {name}({shorten(arguments, args.maxlen)})")
                else:
                    print(f"    -> {shorten(call, args.maxlen)}")
        elif role == "tool":
            print(f"[{i}] tool: {shorten(message.get('content'), args.maxlen)}")
        else:
            print(f"[{i}] {role}: {shorten(message.get('content'), args.maxlen)}")


if __name__ == "__main__":
    main()

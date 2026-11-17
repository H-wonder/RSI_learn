#!/usr/bin/env python3
"""Print one AutomationBench task in a readable form.

Run from the repo root with the benchmark environment:
    uv run --project ../datasets/AutomationBench python scripts/inspect_task.py \
        --domain sales --index 0

    uv run --project ../datasets/AutomationBench python scripts/inspect_task.py \
        --domain sales --task sales.multi_hop_lookup
"""

from __future__ import annotations

import argparse
import json

from automationbench.domains import get_domain_dataset


def is_negative(assertion_type: str) -> bool:
    return "not" in assertion_type.split("_")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True)
    parser.add_argument("--task")
    parser.add_argument("--index", type=int)
    args = parser.parse_args()

    ds = get_domain_dataset(args.domain)
    found = None
    for i, candidate in enumerate(ds):
        info = json.loads(candidate["info"])
        if args.task and info.get("task_name") == args.task:
            found = (i, candidate, info)
            break
        if args.index is not None and i == args.index:
            found = (i, candidate, info)
            break
    if found is None:
        raise SystemExit("task not found")

    index, row, info = found
    print(f"# index={index}  example_id={row['example_id']}  task={info['task_name']}\n")
    for message in row["prompt"]:
        print(f"## {message['role']}")
        print(message["content"])
        print()
    print("## tools")
    for tool in info.get("zapier_tools", []):
        print(f"- {tool}")
    print("\n## assertions")
    for n, assertion in enumerate(info.get("assertions", []), 1):
        flag = "NEG" if is_negative(assertion["type"]) else "POS"
        print(f"{n:02d}. [{flag}] {json.dumps(assertion, ensure_ascii=False)}")


if __name__ == "__main__":
    main()

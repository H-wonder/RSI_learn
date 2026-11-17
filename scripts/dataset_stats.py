#!/usr/bin/env python3
"""Recompute the runtime data card for AutomationBench.

Run with the benchmark environment:
    uv run --project ../datasets/AutomationBench python scripts/dataset_stats.py

It imports the benchmark package, so the dataset's `.venv` must be synced.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter

from automationbench.domains import PUBLIC_DOMAINS, get_domain_dataset


def percentile(values: list[int], p: float) -> int:
    if not values:
        return 0
    values = sorted(values)
    k = max(0, min(len(values) - 1, int(round((len(values) - 1) * p))))
    return values[k]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", default="all")
    args = parser.parse_args()

    domains = PUBLIC_DOMAINS if args.domains == "all" else [
        d.strip() for d in args.domains.split(",") if d.strip()
    ]

    print("| domain | n | tools/task | assertions/task | prompt chars | initial_state bytes | negative |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    total_tasks = total_assertions = total_negative = 0
    assertion_types: Counter[str] = Counter()

    for domain in domains:
        ds = get_domain_dataset(domain)
        tools, asserts, prompts, states = [], [], [], []
        negative = 0
        for row in ds:
            info = json.loads(row["info"])
            tools.append(len(info.get("zapier_tools", [])))
            assertions = info.get("assertions", [])
            asserts.append(len(assertions))
            prompts.append(sum(len(m.get("content", "")) for m in row["prompt"]))
            states.append(len(json.dumps(info.get("initial_state", {}))))
            for a in assertions:
                assertion_types[a["type"]] += 1
                if "not" in a["type"].split("_"):
                    negative += 1
        n = len(ds)
        domain_assertions = sum(asserts)
        total_tasks += n
        total_assertions += domain_assertions
        total_negative += negative
        print(
            f"| {domain} | {n} | {statistics.mean(tools):.1f} | "
            f"{statistics.mean(asserts):.1f} | {statistics.mean(prompts):.0f} | "
            f"{statistics.mean(states):.0f} | {negative / domain_assertions:.1%} |"
        )

    print()
    print(f"- total tasks: {total_tasks}")
    print(f"- total assertions: {total_assertions}")
    print(f"- negative assertions: {total_negative} ({total_negative / total_assertions:.1%})")
    print(f"- distinct assertion types: {len(assertion_types)}")
    print()
    print("Top 15 assertion types:")
    print("| assertion type | count |")
    print("|---|---:|")
    for name, count in assertion_types.most_common(15):
        print(f"| {name} | {count} |")


if __name__ == "__main__":
    main()

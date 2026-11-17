#!/usr/bin/env python3
"""Pick an evenly spaced task sample per domain and write a CSV for run_batch.

Run with the benchmark environment:
    uv run --project ../datasets/AutomationBench python scripts/select_tasks.py \
        --per-domain 3 --out data/tasks/small.csv

The output CSV has: domain,task_name,example_id,n_tools,n_assertions,n_negative
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from automationbench.domains import PUBLIC_DOMAINS, get_domain_dataset

FIELDS = ["domain", "task_name", "example_id", "n_tools", "n_assertions", "n_negative"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-domain", type=int, default=3)
    parser.add_argument("--domains", default="all")
    parser.add_argument("--out", default="data/tasks/sample.csv")
    args = parser.parse_args()

    domains = PUBLIC_DOMAINS if args.domains == "all" else [
        d.strip() for d in args.domains.split(",") if d.strip()
    ]
    rows = []
    for domain in domains:
        ds = get_domain_dataset(domain)
        n = len(ds)
        k = min(args.per_domain, n)
        if k == 1:
            picks = [0]
        else:
            picks = sorted({round(i * (n - 1) / (k - 1)) for i in range(k)})
        for i in picks:
            row = ds[i]
            info = json.loads(row["info"])
            assertions = info.get("assertions", [])
            rows.append(
                {
                    "domain": domain,
                    "task_name": info.get("task_name", ""),
                    "example_id": row["example_id"],
                    "n_tools": len(info.get("zapier_tools", [])),
                    "n_assertions": len(assertions),
                    "n_negative": sum(1 for a in assertions if "not" in a["type"].split("_")),
                }
            )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} tasks to {out}")


if __name__ == "__main__":
    main()

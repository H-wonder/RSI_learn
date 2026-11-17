#!/usr/bin/env python3
"""Export the sampled annotation rows with full prompt/assertions for labeling.

Run with the benchmark environment:
    uv run --project ../datasets/AutomationBench python scripts/export_for_labeling.py

Writes a compact markdown workfile grouped by domain.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from automationbench.domains import get_domain_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation", default="data/annotation/tasks_to_label.csv")
    parser.add_argument("--out", default="data/annotation/workfile.md")
    parser.add_argument("--params-chars", type=int, default=180)
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.annotation, encoding="utf-8-sig")))
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_domain[row["domain"]].append(row)

    lines = []
    for domain, items in by_domain.items():
        ds = get_domain_dataset(domain)
        lines.append(f"\n# {domain} ({len(items)} tasks)\n")
        for row in items:
            idx = int(row["dataset_index"])
            data = ds[idx]
            info = json.loads(data["info"])
            user = ""
            for m in data["prompt"]:
                if m["role"] == "user":
                    user = m["content"]
                    break
            assertions = info.get("assertions", [])
            lines.append(f"## {info['task_name']}  (idx={idx}, example_id={data['example_id']})\n")
            lines.append(f"prompt: {user}\n")
            tools = info.get("zapier_tools", [])
            lines.append(f"tools ({len(tools)}): {', '.join(tools)}\n")
            lines.append(f"assertions ({len(assertions)}):")
            for a in assertions:
                atype = a["type"]
                params = {k: v for k, v in a.items() if k != "type"}
                text = json.dumps(params, ensure_ascii=False)
                if len(text) > args.params_chars:
                    text = text[: args.params_chars] + "..."
                lines.append(f"- {atype} {text}")
            lines.append("")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({len(rows)} tasks)")


if __name__ == "__main__":
    main()

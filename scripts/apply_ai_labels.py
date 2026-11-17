#!/usr/bin/env python3
"""Merge the label JSON files (data/annotation/ai_labels/*.json) into the CSV.

Existing columns are preserved; label columns are filled in place.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/annotation/tasks_to_label.csv")
    parser.add_argument("--labels-dir", default="data/annotation/ai_labels")
    args = parser.parse_args()

    labels: dict[str, dict] = {}
    for path in sorted(Path(args.labels_dir).glob("*.json")):
        labels.update(json.loads(path.read_text(encoding="utf-8")))

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8-sig")))
    filled = 0
    missing = []
    for row in rows:
        label = labels.get(row["task_name"])
        if not label:
            missing.append(row["task_name"])
            continue
        old_type = row.get("primary_type", "")
        row["primary_type"] = label["primary"]
        # P4 has a curated sub-type (P4a eligibility / P4b routing); preserve it
        # when re-applying AI labels, but clear it if the primary type changes.
        if row["primary_type"] == "P4":
            row["primary_subtype"] = label.get("subtype") or (
                row.get("primary_subtype", "") if old_type == "P4" else ""
            )
        else:
            row["primary_subtype"] = ""
        row["secondary_types"] = label["secondary"]
        row["evidence"] = label["evidence"]
        row["failure_mode"] = label["failure_mode"]
        filled += 1

    fieldnames = list(rows[0].keys())
    with open(args.csv, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"filled {filled}/{len(rows)} rows")
    if missing:
        print("missing labels:", ", ".join(missing))
    dist = Counter(row["primary_type"] for row in rows if row["primary_type"])
    print("primary distribution:")
    for key in sorted(dist):
        print(f"  {key}: {dist[key]}")


if __name__ == "__main__":
    main()

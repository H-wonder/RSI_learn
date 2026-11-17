#!/usr/bin/env python3
"""Analyze AutomationBench result JSONs and write a markdown report + issue CSV.

Usage:
    python scripts/analyze_results.py --dir results/small \
        --out-md reports/small.md --out-issues reports/small.issues.csv

The analyzer is offline and stdlib-only. It answers:
  - pass rate / partial credit overall and per domain
  - how close failing tasks were (partial credit buckets)
  - which assertion types fail most
  - what kind of failure it looks like (extra action, missing record, wrong value, ...)
  - one row per failed assertion for manual diagnosis
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

CATEGORY_ORDER = [
    "extra_or_unwanted_action",
    "missing_record",
    "missing_message_or_note",
    "wrong_value_or_state",
    "wrong_count",
    "missing_content",
    "other",
]


def domain_of(task: dict) -> str:
    name = task.get("name", "")
    return name.split(".", 1)[0] if "." in name else "unknown"


def failed_assertions(task: dict) -> list[dict]:
    return [
        a
        for a in (task.get("assertion_results") or [])
        if not a.get("excluded") and not a.get("passed")
    ]


def categorize(assertion_type: str) -> str:
    """Heuristic mapping from assertion type to a human failure category."""
    parts = set(assertion_type.split("_"))
    if "not" in parts:
        return "extra_or_unwanted_action"
    if "count" in parts and "equals" in parts:
        return "wrong_count"
    if assertion_type.endswith("_exists") or "_exists_" in assertion_type:
        return "missing_record"
    if parts & {"sent", "message", "messages", "in_channel", "comment", "thread"}:
        return "missing_message_or_note"
    if "equals" in parts or assertion_type.endswith("_has_priority") or assertion_type.endswith(
        "_has_tag"
    ):
        return "wrong_value_or_state"
    if "contains" in parts:
        return "missing_content"
    return "other"


def load_tasks(paths: list[Path]) -> tuple[list[dict], dict]:
    tasks_by_name: dict[str, dict] = {}
    meta = {"files": [], "models": set(), "domains": set(), "max_steps": set()}
    duplicates = 0
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        m = data.get("meta") or {}
        meta["files"].append(str(path))
        if m.get("model"):
            meta["models"].add(str(m["model"]))
        for d in m.get("domains") or []:
            meta["domains"].add(str(d))
        if m.get("max_steps") is not None:
            meta["max_steps"].add(m["max_steps"])
        for task in data.get("tasks") or []:
            name = task.get("name") or f"task_{task.get('id', '?')}"
            if name in tasks_by_name:
                duplicates += 1
                if float(task.get("score", 0)) > float(tasks_by_name[name].get("score", 0)):
                    tasks_by_name[name] = task
            else:
                tasks_by_name[name] = task
    meta["duplicates"] = duplicates
    return list(tasks_by_name.values()), meta


def pct(num: float, den: float) -> str:
    return f"{100 * num / den:.1f}%" if den else "-"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        action="append",
        help="directory with result JSON files (recursive); repeat to merge runs",
    )
    parser.add_argument("files", nargs="*", help="explicit result JSON files")
    parser.add_argument("--out-md", default="reports/report.md")
    parser.add_argument("--out-issues", default=None)
    parser.add_argument("--out-tasks", default=None)
    parser.add_argument("--title", default="AutomationBench Baseline Report")
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

    tasks, meta = load_tasks(paths)
    n = len(tasks)
    if n == 0:
        raise SystemExit("result files contain no tasks")

    scores = [float(t.get("score", 0.0)) for t in tasks]
    passed = [t for t in tasks if bool(t.get("passed")) or float(t.get("score", 0)) == 1.0]
    steps = [float(t.get("steps", 0) or 0) for t in tasks]
    in_tokens = sum(int(t.get("input_tokens", 0) or 0) for t in tasks)
    out_tokens = sum(int(t.get("output_tokens", 0) or 0) for t in tasks)
    cost = sum(float(t.get("cost", 0.0) or 0.0) for t in tasks)

    by_domain: dict[str, list[dict]] = defaultdict(list)
    for t in tasks:
        by_domain[domain_of(t)].append(t)

    failed_by_type: Counter[str] = Counter()
    task_failure_categories: dict[str, set[str]] = defaultdict(set)
    category_assertions: Counter[str] = Counter()
    issue_rows = []
    per_task_rows = []

    for t in tasks:
        name = t.get("name", "")
        dom = domain_of(t)
        fails = failed_assertions(t)
        for a in fails:
            atype = a.get("type", "unknown")
            cat = categorize(atype)
            failed_by_type[atype] += 1
            category_assertions[cat] += 1
            task_failure_categories[name].add(cat)
            issue_rows.append(
                {
                    "task": name,
                    "domain": dom,
                    "score": f"{float(t.get('score', 0)):.3f}",
                    "assertion_type": atype,
                    "category": cat,
                    "params": json.dumps(a.get("params", {}), ensure_ascii=False),
                    "note": "",
                }
            )
        per_task_rows.append(
            {
                "task": name,
                "domain": dom,
                "score": f"{float(t.get('score', 0)):.3f}",
                "passed": "1" if float(t.get("score", 0)) == 1.0 else "0",
                "assertions_passed": t.get("assertions_passed", ""),
                "assertions_total": t.get("assertions_total", ""),
                "steps": t.get("steps", ""),
                "input_tokens": t.get("input_tokens", ""),
                "output_tokens": t.get("output_tokens", ""),
                "cost": t.get("cost", ""),
                "failed_types": ";".join(sorted({a.get("type", "?") for a in fails})),
            }
        )

    lines = []
    lines.append(f"# {args.title}")
    lines.append("")
    lines.append(f"- generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- model(s): {', '.join(sorted(meta['models'])) or '-'}")
    lines.append(f"- files: {len(meta['files'])}")
    if meta["max_steps"]:
        lines.append(f"- max_steps: {', '.join(str(x) for x in sorted(meta['max_steps']))}")
    if meta["duplicates"]:
        lines.append(f"- duplicate task rows merged: {meta['duplicates']}")
    lines.append("")

    lines.append("## 1. Overall")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---:|")
    lines.append(f"| tasks | {n} |")
    lines.append(f"| pass rate (`score == 1`) | {pct(len(passed), n)} |")
    lines.append(f"| avg partial credit | {statistics.mean(scores):.3f} |")
    lines.append(f"| avg steps | {statistics.mean(steps):.1f} |")
    lines.append(f"| input tokens | {in_tokens:,} |")
    lines.append(f"| output tokens | {out_tokens:,} |")
    lines.append(f"| cost | {cost:.4f} |")
    lines.append("")

    lines.append("## 2. By domain")
    lines.append("")
    lines.append("| domain | n | pass | partial | avg steps |")
    lines.append("|---|---:|---:|---:|---:|")
    for dom in sorted(by_domain):
        group = by_domain[dom]
        d_pass = sum(1 for t in group if float(t.get("score", 0)) == 1.0)
        d_scores = [float(t.get("score", 0)) for t in group]
        d_steps = [float(t.get("steps", 0) or 0) for t in group]
        lines.append(
            f"| {dom} | {len(group)} | {pct(d_pass, len(group))} | "
            f"{statistics.mean(d_scores):.3f} | {statistics.mean(d_steps):.1f} |"
        )
    lines.append("")

    buckets = {"0": 0, "(0, 0.5)": 0, "[0.5, 1)": 0, "1": 0}
    for s in scores:
        if s == 0:
            buckets["0"] += 1
        elif s < 0.5:
            buckets["(0, 0.5)"] += 1
        elif s < 1:
            buckets["[0.5, 1)"] += 1
        else:
            buckets["1"] += 1
    lines.append("## 3. Partial credit distribution")
    lines.append("")
    lines.append("| bucket | tasks | share |")
    lines.append("|---|---:|---:|")
    for label, count in buckets.items():
        lines.append(f"| {label} | {count} | {pct(count, n)} |")
    lines.append("")

    affected = Counter()
    for cats in task_failure_categories.values():
        for c in cats:
            affected[c] += 1
    total_fail_assertions = sum(category_assertions.values())
    lines.append("## 4. Failure categories (heuristic)")
    lines.append("")
    lines.append("| category | failed assertions | share of failures | tasks affected | share of tasks |")
    lines.append("|---|---:|---:|---:|---:|")
    for cat in CATEGORY_ORDER:
        if category_assertions[cat] == 0 and affected[cat] == 0:
            continue
        lines.append(
            f"| {cat} | {category_assertions[cat]} | "
            f"{pct(category_assertions[cat], total_fail_assertions)} | "
            f"{affected[cat]} | {pct(affected[cat], n)} |"
        )
    lines.append("")
    lines.append(
        "> Categories are inferred from assertion type names. "
        "Use the issues CSV to verify and correct them."
    )
    lines.append("")

    lines.append("## 5. Top failed assertion types")
    lines.append("")
    lines.append("| assertion type | failures | category |")
    lines.append("|---|---:|---|")
    for atype, count in failed_by_type.most_common(20):
        lines.append(f"| `{atype}` | {count} | {categorize(atype)} |")
    lines.append("")

    lines.append("## 6. Failing tasks (score < 1)")
    lines.append("")
    lines.append("| task | domain | score | passed/total | steps | failed types |")
    lines.append("|---|---|---:|---:|---:|---|")
    failing = sorted(
        [t for t in tasks if float(t.get("score", 0)) < 1.0],
        key=lambda t: (float(t.get("score", 0)), t.get("name", "")),
    )
    for t in failing[:30]:
        types = sorted({a.get("type", "?") for a in failed_assertions(t)})
        lines.append(
            f"| {t.get('name', '')} | {domain_of(t)} | {float(t.get('score', 0)):.2f} | "
            f"{t.get('assertions_passed', '?')}/{t.get('assertions_total', '?')} | "
            f"{t.get('steps', '?')} | {', '.join(types[:4])} |"
        )
    if len(failing) > 30:
        lines.append(f"\n> showing 30 of {len(failing)} failing tasks")
    lines.append("")

    lines.append("## 7. Reading this report")
    lines.append("")
    lines.append(
        "- Only **scored** assertions count. Assertions already true in the initial state "
        "are excluded from the denominator (see `rubric/__init__.py`)."
    )
    lines.append(
        "- `extra_or_unwanted_action` = a `*_not_*` assertion failed: the agent did "
        "something it should not have done."
    )
    lines.append(
        "- `missing_record` = an `*_exists*` assertion failed: the expected record "
        "was not created or was created with the wrong key."
    )
    lines.append(
        "- `wrong_value_or_state` = an `*_equals*` assertion failed: the record exists "
        "but a field is wrong."
    )
    lines.append("")

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    issues_path = Path(args.out_issues) if args.out_issues else out_md.with_suffix(".issues.csv")
    issues_path.parent.mkdir(parents=True, exist_ok=True)
    with open(issues_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["task", "domain", "score", "assertion_type", "category", "params", "note"],
        )
        writer.writeheader()
        writer.writerows(issue_rows)

    if args.out_tasks:
        tasks_path = Path(args.out_tasks)
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        with open(tasks_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(per_task_rows[0].keys()))
            writer.writeheader()
            writer.writerows(per_task_rows)

    print(f"wrote {out_md}")
    print(f"wrote {issues_path} ({len(issue_rows)} failed assertions)")
    if args.out_tasks:
        print(f"wrote {args.out_tasks}")


if __name__ == "__main__":
    main()

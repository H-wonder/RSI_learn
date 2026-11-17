#!/usr/bin/env python3
"""Summarize the manual/AI annotation sheet: counts by domain and problem type."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

TYPES = ["P1", "P2", "P3", "P4a", "P4b", "P5", "P6", "P7", "P8", "P9"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/annotation/tasks_to_label.csv")
    parser.add_argument("--out", default="reports/annotation-distribution.md")
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8-sig")))
    by_domain: dict[str, Counter[str]] = defaultdict(Counter)
    primary: Counter[str] = Counter()
    secondary: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)

    for row in rows:
        ptype = (
            row.get("primary_subtype")
            or row.get("primary_type")
            or "unlabeled"
        ).strip()
        primary[ptype] += 1
        by_domain[row["domain"]][ptype] += 1
        for s in (row.get("secondary_types") or "").split(";"):
            s = s.strip()
            if s:
                secondary[s] += 1
        if ptype not in ("unlabeled",) and len(examples[ptype]) < 3:
            examples[ptype].append(row["task_name"])

    lines = ["# 问题分类标注分布", ""]
    lines.append(f"- total tasks: {len(rows)}")
    lines.append("- labels: AI 初标 + 用户复核；P4 的 P4a/P4b 子类由人工判定")
    lines.append("")
    lines.append("## 主类分布")
    lines.append("")
    lines.append("| type | count | share | example tasks |")
    lines.append("|---|---:|---:|---|")
    for ptype in TYPES + ["unlabeled"]:
        count = primary.get(ptype, 0)
        if not count:
            continue
        lines.append(
            f"| {ptype} | {count} | {100 * count / len(rows):.1f}% | "
            f"{', '.join(examples.get(ptype, []))} |"
        )
    lines.append("")
    lines.append("## 域 × 主类")
    lines.append("")
    header = "| domain | " + " | ".join(TYPES) + " | total |"
    lines.append(header)
    lines.append("|---|" + "---:|" * len(TYPES) + "---:|")
    for domain in sorted(by_domain):
        row = by_domain[domain]
        cells = " | ".join(str(row.get(t, 0) or "") for t in TYPES)
        lines.append(f"| {domain} | {cells} | {sum(row.values())} |")
    lines.append("")
    lines.append("## 次类分布")
    lines.append("")
    lines.append("| type | appears as secondary |")
    lines.append("|---|---:|")
    for ptype in TYPES:
        if secondary.get(ptype):
            lines.append(f"| {ptype} | {secondary[ptype]} |")
    lines.append("")
    lines.append("## 观察")
    lines.append("")
    lines.append("- P4 已拆成两个子类：P4a 资格筛选/规则判定（谁符合条件、是否越过阈值）")
    lines.append("  与 P4b 分支路由/优先级（去哪里、走哪条路径、什么优先级）。")
    lines.append("- P4a 16 题、P4b 9 题，合计仍是 25 题；拆开后能区分“集合选错”和“目的地选错”。")
    lines.append("- P1（单工具 CRUD）和 P6（模糊匹配）在 60 题样本里没有作为主类出现：")
    lines.append("  这两类可能更多作为**次类**，或者样本没有覆盖到。")
    lines.append("- P9（长链编排）只有 2 题，但它的“长”是跨度而非类别；")
    lines.append("  很多 P4a/P4b 任务其实也包含 5+ 步，需要在论文里说明分类口径。")
    lines.append("- P5 作为次类出现 53 次，建议在论文里作为横切约束层，而不是普通主类。")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

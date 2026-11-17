#!/usr/bin/env python3
"""Generate LaTeX table/figure snippets from the 60-task result CSVs."""

from __future__ import annotations

import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "tex"
OUT.mkdir(parents=True, exist_ok=True)

DOMAIN_ORDER = ["sales", "marketing", "operations", "support", "finance", "hr"]
TYPE_ORDER = [f"P{i}" for i in range(1, 10)]
TYPE_NAMES = {
    "P1": "P1 单工具 CRUD",
    "P2": "P2 多跳检索",
    "P3": "P3 跨应用同步",
    "P4": "P4 条件路由/规则",
    "P5": "P5 排除/冲突",
    "P6": "P6 模糊匹配",
    "P7": "P7 时间/日程",
    "P8": "P8 聚合/计算",
    "P9": "P9 长链编排",
}
CAT_NAMES = {
    "missing_record": "漏建记录",
    "missing_message_or_note": "漏发消息/通知",
    "extra_or_unwanted_action": "多做（负断言）",
    "wrong_value_or_state": "值/状态写错",
    "missing_content": "内容缺失",
    "wrong_count": "数量不对",
    "other": "其他",
}
CAT_ORDER = [
    "missing_record",
    "missing_message_or_note",
    "extra_or_unwanted_action",
    "wrong_value_or_state",
    "missing_content",
    "wrong_count",
    "other",
]


def esc_name(name: str) -> str:
    return name.replace("_", r"\_")


def read_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    tasks = read_rows(ROOT / "reports" / "medium-60.tasks.csv")
    ann = {r["task_name"]: r["primary_type"] for r in read_rows(ROOT / "data" / "annotation" / "tasks_to_label.csv")}
    issues = read_rows(ROOT / "reports" / "medium-60.issues.csv")

    n = len(tasks)
    scores = [float(t["score"]) for t in tasks]
    passes = [t for t in tasks if t["passed"] == "1"]
    steps = [float(t["steps"] or 0) for t in tasks]
    input_tokens = sum(int(t["input_tokens"] or 0) for t in tasks)
    output_tokens = sum(int(t["output_tokens"] or 0) for t in tasks)
    cost = sum(float(t["cost"] or 0) for t in tasks)

    # metrics macros
    macros = [
        rf"\newcommand{{\MetricN}}{{{n}}}",
        rf"\newcommand{{\MetricPass}}{{{100 * len(passes) / n:.1f}\%}}",
        rf"\newcommand{{\MetricPassCount}}{{{len(passes)}}}",
        rf"\newcommand{{\MetricPartial}}{{{statistics.mean(scores):.3f}}}",
        rf"\newcommand{{\MetricSteps}}{{{statistics.mean(steps):.1f}}}",
        rf"\newcommand{{\MetricInputTokens}}{{{input_tokens:,}}}",
        rf"\newcommand{{\MetricOutputTokens}}{{{output_tokens:,}}}",
        rf"\newcommand{{\MetricCost}}{{\${cost:,.2f}}}",
    ]
    (OUT / "metrics.tex").write_text("\n".join(macros) + "\n", encoding="utf-8")

    # domain table
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for t in tasks:
        by_domain[t["domain"]].append(t)
    lines = []
    for d in DOMAIN_ORDER:
        group = by_domain[d]
        p = sum(1 for t in group if t["passed"] == "1") / len(group)
        s = statistics.mean(float(t["score"]) for t in group)
        st = statistics.mean(float(t["steps"] or 0) for t in group)
        lines.append(f"{d} & {len(group)} & {100 * p:.1f}\\% & {s:.3f} & {st:.1f} \\\\")
    (OUT / "domain.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # type table
    by_type: dict[str, list[dict]] = defaultdict(list)
    for t in tasks:
        by_type[ann.get(t["task"], "unlabeled")].append(t)
    lines = []
    for ptype in TYPE_ORDER:
        group = by_type.get(ptype, [])
        if not group:
            continue
        p = sum(1 for t in group if t["passed"] == "1") / len(group)
        s = statistics.mean(float(t["score"]) for t in group)
        st = statistics.mean(float(t["steps"] or 0) for t in group)
        lines.append(f"{TYPE_NAMES[ptype]} & {len(group)} & {100 * p:.1f}\\% & {s:.3f} & {st:.1f} \\\\")
    (OUT / "type.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # failure categories
    cat_assert = Counter(i["category"] for i in issues)
    cat_tasks: dict[str, set[str]] = defaultdict(set)
    for i in issues:
        cat_tasks[i["category"]].add(i["task"])
    total_fail = sum(cat_assert.values())
    lines = []
    for cat in CAT_ORDER:
        if not cat_assert[cat]:
            continue
        lines.append(
            f"{CAT_NAMES[cat]} & {cat_assert[cat]} & {100 * cat_assert[cat] / total_fail:.1f}\\% & {len(cat_tasks[cat])} \\\\"
        )
    (OUT / "failure.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # top assertion types
    top = Counter(i["assertion_type"] for i in issues).most_common(10)
    lines = []
    for atype, count in top:
        lines.append(f"\\code{{{atype}}} & {count} \\\\")
    (OUT / "top_assertions.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # partial buckets
    buckets = {"0": 0, "(0,0.5)": 0, "[0.5,1)": 0, "1": 0}
    for s in scores:
        if s == 0:
            buckets["0"] += 1
        elif s < 0.5:
            buckets["(0,0.5)"] += 1
        elif s < 1:
            buckets["[0.5,1)"] += 1
        else:
            buckets["1"] += 1
    lines = [f"{{{k}}} & {v} & {100 * v / n:.1f}\\% \\\\" for k, v in buckets.items()]
    (OUT / "partial.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # per-task longtable rows
    lines = []
    for t in sorted(tasks, key=lambda x: (x["domain"], float(x["score"]))):
        ptype = ann.get(t["task"], "?")
        lines.append(
            f"\\code{{{t['task']}}} & {t['domain']} & {ptype} & {float(t['score']):.3f} & {t['steps']} \\\\"
        )
    (OUT / "per_task.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # figures
    domain_coords = " ".join(
        f"({d},{100 * sum(1 for t in by_domain[d] if t['passed'] == '1') / len(by_domain[d]):.1f})"
        for d in DOMAIN_ORDER
    )
    fig = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
  ybar, width=0.92\textwidth, height=6.2cm, ymin=0, ymax=40,
  ylabel={{通过率 (\%)}}, symbolic x coords={{{','.join(DOMAIN_ORDER)}}},
  xtick=data, nodes near coords, bar width=14pt,
  enlarge x limits=0.12, tick label style={{font=\small}},
]
\addplot coordinates {{{domain_coords}}};
\end{{axis}}
\end{{tikzpicture}}
"""
    (OUT / "fig_domain.tex").write_text(fig, encoding="utf-8")

    type_coords = []
    type_ticks = []
    for ptype in TYPE_ORDER:
        group = by_type.get(ptype, [])
        if not group:
            continue
        rate = 100 * sum(1 for t in group if t["passed"] == "1") / len(group)
        type_coords.append(f"({ptype},{rate:.1f})")
        type_ticks.append(ptype)
    fig = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
  ybar, width=0.92\textwidth, height=6.2cm, ymin=0, ymax=40,
  ylabel={{通过率 (\%)}}, symbolic x coords={{{','.join(type_ticks)}}},
  xtick=data, nodes near coords, bar width=14pt,
  enlarge x limits=0.12, tick label style={{font=\small}},
]
\addplot coordinates {{{' '.join(type_coords)}}};
\end{{axis}}
\end{{tikzpicture}}
"""
    (OUT / "fig_type.tex").write_text(fig, encoding="utf-8")

    # Also provide all row groups as macros.  Including a file *inside* a
    # tabular breaks booktabs' \bottomrule, so report.tex loads these macros in
    # the preamble and expands them inside the tables instead.
    def macro(name: str, filename: str) -> str:
        body = (OUT / filename).read_text(encoding="utf-8").strip()
        return f"\\newcommand{{\\{name}}}{{%\n{body}\n}}"

    rows_tex = "\n".join(
        [
            macro("DomainRows", "domain.tex"),
            macro("TypeRows", "type.tex"),
            macro("FailureRows", "failure.tex"),
            macro("TopAssertionRows", "top_assertions.tex"),
            macro("PartialRows", "partial.tex"),
            macro("PerTaskRows", "per_task.tex"),
        ]
    )
    (OUT / "rows.tex").write_text(rows_tex + "\n", encoding="utf-8")

    print("wrote", OUT)


if __name__ == "__main__":
    main()

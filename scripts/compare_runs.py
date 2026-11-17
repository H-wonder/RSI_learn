#!/usr/bin/env python3
"""Paired comparison of two AutomationBench runs on the same task set.

The intended use is the config-parity control:
    A = the first 60-task run (default reasoning effort, split over small + medium)
    B = the 60-task run with --reasoning-effort max

Both runs cover exactly the same 60 task names, so every task is a paired
observation. The script reports pass/partial differences, transition counts,
an exact McNemar test for the binary pass rate, and a paired bootstrap CI for
the partial-credit difference.

Usage:
    python scripts/compare_runs.py \
      --a-dir results/small --a-dir results/medium \
      --b-dir results/medium-max \
      --tasks-file data/tasks/medium_from_annotation.csv \
      --annotation data/annotation/tasks_to_label.csv \
      --out-md reports/compare-default-vs-max.md \
      --out-csv reports/compare-default-vs-max.csv \
      --out-tex reports/tex/compare.tex
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN_ORDER = ["sales", "marketing", "operations", "support", "finance", "hr"]
TYPE_ORDER = ["P1", "P2", "P3", "P4a", "P4b", "P5", "P6", "P7", "P8", "P9"]
TYPE_NAMES = {
    "P1": "P1 单工具 CRUD",
    "P2": "P2 多跳检索",
    "P3": "P3 跨应用同步",
    "P4a": "P4a 资格筛选/规则判定",
    "P4b": "P4b 分支路由/优先级",
    "P5": "P5 排除/冲突",
    "P6": "P6 模糊匹配",
    "P7": "P7 时间/日程",
    "P8": "P8 聚合/计算",
    "P9": "P9 长链编排",
}


def load_tasks(directories: list[Path]) -> dict[str, dict]:
    tasks: dict[str, dict] = {}
    for directory in directories:
        for path in sorted(directory.rglob("*.json")):
            if path.name == "manifest.json":
                continue
            for task in json.loads(path.read_text(encoding="utf-8")).get("tasks") or []:
                name = task.get("name") or ""
                if not name:
                    continue
                old = tasks.get(name)
                if old is None or float(task.get("score", 0)) > float(old.get("score", 0)):
                    tasks[name] = task
    return tasks


def read_tasks(path: Path) -> list[str]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [row["task_name"] for row in csv.DictReader(fh)]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return (100 * max(0.0, center - half), 100 * min(1.0, center + half))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value for discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / (2**n)
    return min(1.0, 2 * tail)


def bootstrap_ci(values: list[float], reps: int = 20000, seed: int = 20261117) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(reps):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    lo = means[int(0.025 * reps)]
    hi = means[int(0.975 * reps) - 1]
    return (lo, hi)


def pct(k: int, n: int) -> str:
    return f"{100 * k / n:.1f}%" if n else "-"


def pct_tex(k: int, n: int) -> str:
    return pct(k, n).replace("%", r"\%")


def esc(name: str) -> str:
    return name.replace("_", r"\verb|_|").replace("|", "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a-dir", action="append", required=True, help="run A; repeatable")
    parser.add_argument("--b-dir", action="append", required=True, help="run B; repeatable")
    parser.add_argument("--tasks-file", required=True)
    parser.add_argument("--annotation", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-tex")
    parser.add_argument("--a-label", default="medium 实验（默认 effort）")
    parser.add_argument("--b-label", default="medium-max 实验（max effort）")
    args = parser.parse_args()

    names = read_tasks(Path(args.tasks_file))
    a_all = load_tasks([Path(p) for p in args.a_dir])
    b_all = load_tasks([Path(p) for p in args.b_dir])
    missing_a = [n for n in names if n not in a_all]
    missing_b = [n for n in names if n not in b_all]
    if missing_a or missing_b:
        raise SystemExit(
            f"missing tasks: A={len(missing_a)} {missing_a[:5]} B={len(missing_b)} {missing_b[:5]}"
        )

    ann = {
        row["task_name"]: (row.get("primary_subtype") or row["primary_type"])
        for row in csv.DictReader(open(args.annotation, encoding="utf-8-sig"))
    }

    rows = []
    for name in names:
        a, b = a_all[name], b_all[name]
        rows.append(
            {
                "task": name,
                "domain": name.split(".", 1)[0],
                "type": ann.get(name, "?"),
                "score_a": float(a.get("score", 0)),
                "score_b": float(b.get("score", 0)),
                "passed_a": bool(a.get("passed")),
                "passed_b": bool(b.get("passed")),
                "steps_a": float(a.get("steps", 0) or 0),
                "steps_b": float(b.get("steps", 0) or 0),
                "out_a": int(a.get("output_tokens", 0) or 0),
                "out_b": int(b.get("output_tokens", 0) or 0),
                "cost_a": float(a.get("cost", 0) or 0),
                "cost_b": float(b.get("cost", 0) or 0),
                "refusal_a": bool(a.get("died_on_refusal")),
                "refusal_b": bool(b.get("died_on_refusal")),
            }
        )

    n = len(rows)
    pass_a = sum(r["passed_a"] for r in rows)
    pass_b = sum(r["passed_b"] for r in rows)
    scores_a = [r["score_a"] for r in rows]
    scores_b = [r["score_b"] for r in rows]
    deltas = [b - a for a, b in zip(scores_a, scores_b)]
    delta_mean = statistics.mean(deltas)
    delta_lo, delta_hi = bootstrap_ci(deltas)

    both_pass = sum(r["passed_a"] and r["passed_b"] for r in rows)
    fail_to_pass = sum((not r["passed_a"]) and r["passed_b"] for r in rows)
    pass_to_fail = sum(r["passed_a"] and (not r["passed_b"]) for r in rows)
    both_fail = sum((not r["passed_a"]) and (not r["passed_b"]) for r in rows)
    mcnemar_p = mcnemar_exact(fail_to_pass, pass_to_fail)

    improved = sum(d > 1e-9 for d in deltas)
    unchanged = sum(abs(d) <= 1e-9 for d in deltas)
    worsened = sum(d < -1e-9 for d in deltas)

    def group_stats(key: str, order: list[str]):
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            groups[r[key]].append(r)
        out = []
        for label in order:
            group = groups.get(label, [])
            if not group:
                continue
            out.append(
                {
                    "label": label,
                    "n": len(group),
                    "pass_a": sum(r["passed_a"] for r in group),
                    "pass_b": sum(r["passed_b"] for r in group),
                    "partial_a": statistics.mean(r["score_a"] for r in group),
                    "partial_b": statistics.mean(r["score_b"] for r in group),
                }
            )
        return out

    by_domain = group_stats("domain", DOMAIN_ORDER)
    by_type = group_stats("type", TYPE_ORDER)

    # ---------- markdown ----------
    lines = []
    lines.append("# 同一批 60 题：默认 effort vs max effort")
    lines.append("")
    lines.append(f"- A：{args.a_label}")
    lines.append(f"- B：{args.b_label}")
    lines.append(f"- n：{n}（逐题配对）")
    lines.append("")
    lines.append("## 1. 总体")
    lines.append("")
    lines.append("| 指标 | A | B | 变化 |")
    lines.append("|---|---:|---:|---:|")
    lines.append(
        f"| 通过率 | {pct(pass_a, n)} | {pct(pass_b, n)} | "
        f"+{100 * (pass_b - pass_a) / n:.1f} pp |"
    )
    lines.append(f"| 通过数 | {pass_a}/{n} | {pass_b}/{n} | {pass_b - pass_a:+d} |")
    lines.append(
        f"| 平均部分分 | {statistics.mean(scores_a):.3f} | {statistics.mean(scores_b):.3f} | "
        f"{delta_mean:+.3f}（95% bootstrap CI [{delta_lo:+.3f}, {delta_hi:+.3f}]） |"
    )
    lines.append(
        f"| 平均步数 | {statistics.mean(r['steps_a'] for r in rows):.1f} | "
        f"{statistics.mean(r['steps_b'] for r in rows):.1f} | "
        f"{statistics.mean(r['steps_b'] - r['steps_a'] for r in rows):+.1f} |"
    )
    lines.append(
        f"| 平均输出 token | {statistics.mean(r['out_a'] for r in rows):,.0f} | "
        f"{statistics.mean(r['out_b'] for r in rows):,.0f} | "
        f"{statistics.mean(r['out_b'] - r['out_a'] for r in rows):+,.0f} |"
    )
    lines.append(
        f"| 总成本 | ${sum(r['cost_a'] for r in rows):,.2f} | "
        f"${sum(r['cost_b'] for r in rows):,.2f} | "
        f"${sum(r['cost_b'] for r in rows) - sum(r['cost_a'] for r in rows):+,.2f} |"
    )
    lines.append(
        f"| refusal-stopped | {sum(r['refusal_a'] for r in rows)} | "
        f"{sum(r['refusal_b'] for r in rows)} | — |"
    )
    lines.append("")
    lines.append("## 2. 逐题变化")
    lines.append("")
    lines.append("| 类别 | 任务数 |")
    lines.append("|---|---:|")
    lines.append(f"| A 通过、B 通过 | {both_pass} |")
    lines.append(f"| A 失败、B 通过（提升） | {fail_to_pass} |")
    lines.append(f"| A 通过、B 失败（退化） | {pass_to_fail} |")
    lines.append(f"| A 失败、B 失败 | {both_fail} |")
    lines.append("")
    lines.append(
        f"McNemar 精确检验（通过/不通过）：p = {mcnemar_p:.4g}"
        f"（不一致对 {fail_to_pass} vs {pass_to_fail}）"
    )
    lines.append("")
    lines.append(
        f"部分分逐题变化：提升 {improved} 题，不变 {unchanged} 题，下降 {worsened} 题。"
    )
    lines.append("")
    lines.append("## 3. 分域")
    lines.append("")
    lines.append("| 域 | n | 通过 A | 通过 B | 部分分 A | 部分分 B | 部分分变化 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for g in by_domain:
        lines.append(
            f"| {g['label']} | {g['n']} | {pct(g['pass_a'], g['n'])} | "
            f"{pct(g['pass_b'], g['n'])} | {g['partial_a']:.3f} | {g['partial_b']:.3f} | "
            f"{g['partial_b'] - g['partial_a']:+.3f} |"
        )
    lines.append("")
    lines.append("## 4. 问题类型")
    lines.append("")
    lines.append("| 类型 | n | 通过 A | 通过 B | 部分分 A | 部分分 B | 部分分变化 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for g in by_type:
        lines.append(
            f"| {TYPE_NAMES.get(g['label'], g['label'])} | {g['n']} | "
            f"{pct(g['pass_a'], g['n'])} | {pct(g['pass_b'], g['n'])} | "
            f"{g['partial_a']:.3f} | {g['partial_b']:.3f} | "
            f"{g['partial_b'] - g['partial_a']:+.3f} |"
        )
    lines.append("")
    flips = sorted(
        [r for r in rows if (not r["passed_a"]) and r["passed_b"]],
        key=lambda r: r["task"],
    )
    lines.append("## 5. 从失败变为通过的任务")
    lines.append("")
    if flips:
        lines.append("| 任务 | 类型 | A 分数 | B 分数 |")
        lines.append("|---|---|---:|---:|")
        for r in flips:
            lines.append(f"| `{r['task']}` | {r['type']} | {r['score_a']:.2f} | {r['score_b']:.2f} |")
    else:
        lines.append("（无）")
    lines.append("")
    drops = sorted(
        [r for r in rows if r["passed_a"] and (not r["passed_b"])],
        key=lambda r: r["task"],
    )
    lines.append("## 6. 从通过变为失败的任务")
    lines.append("")
    if drops:
        lines.append("| 任务 | 类型 | A 分数 | B 分数 |")
        lines.append("|---|---|---:|---:|")
        for r in drops:
            lines.append(f"| `{r['task']}` | {r['type']} | {r['score_a']:.2f} | {r['score_b']:.2f} |")
    else:
        lines.append("（无）")
    lines.append("")

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_md}")

    # ---------- task CSV ----------
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "task",
                "domain",
                "type",
                "score_a",
                "score_b",
                "delta",
                "passed_a",
                "passed_b",
                "steps_a",
                "steps_b",
                "out_a",
                "out_b",
                "cost_a",
                "cost_b",
                "refusal_a",
                "refusal_b",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "task": r["task"],
                    "domain": r["domain"],
                    "type": r["type"],
                    "score_a": f"{r['score_a']:.4f}",
                    "score_b": f"{r['score_b']:.4f}",
                    "delta": f"{r['score_b'] - r['score_a']:+.4f}",
                    "passed_a": int(r["passed_a"]),
                    "passed_b": int(r["passed_b"]),
                    "steps_a": int(r["steps_a"]),
                    "steps_b": int(r["steps_b"]),
                    "out_a": r["out_a"],
                    "out_b": r["out_b"],
                    "cost_a": f"{r['cost_a']:.4f}",
                    "cost_b": f"{r['cost_b']:.4f}",
                    "refusal_a": int(r["refusal_a"]),
                    "refusal_b": int(r["refusal_b"]),
                }
            )
    print(f"wrote {out_csv}")

    # ---------- LaTeX ----------
    if args.out_tex:
        out_tex = Path(args.out_tex)
        out_tex.parent.mkdir(parents=True, exist_ok=True)
        lo_a, hi_a = wilson(pass_a, n)
        lo_b, hi_b = wilson(pass_b, n)
        macros = [
            rf"\newcommand{{\CmpN}}{{{n}}}",
            rf"\newcommand{{\CmpPassA}}{{{pct_tex(pass_a, n)}}}",
            rf"\newcommand{{\CmpPassB}}{{{pct_tex(pass_b, n)}}}",
            rf"\newcommand{{\CmpPassCountA}}{{{pass_a}}}",
            rf"\newcommand{{\CmpPassCountB}}{{{pass_b}}}",
            rf"\newcommand{{\CmpPassACI}}{{[{lo_a:.1f}, {hi_a:.1f}]\%}}",
            rf"\newcommand{{\CmpPassBCI}}{{[{lo_b:.1f}, {hi_b:.1f}]\%}}",
            rf"\newcommand{{\CmpPassDelta}}{{{{+}}{100 * (pass_b - pass_a) / n:.1f} pp}}",
            rf"\newcommand{{\CmpPartialA}}{{{statistics.mean(scores_a):.3f}}}",
            rf"\newcommand{{\CmpPartialB}}{{{statistics.mean(scores_b):.3f}}}",
            rf"\newcommand{{\CmpPartialDelta}}{{{delta_mean:+.3f}}}",
            rf"\newcommand{{\CmpPartialCI}}{{[{delta_lo:+.3f}, {delta_hi:+.3f}]}}",
            rf"\newcommand{{\CmpMcNemarP}}{{{mcnemar_p:.4g}}}",
            rf"\newcommand{{\CmpBothPass}}{{{both_pass}}}",
            rf"\newcommand{{\CmpFailToPass}}{{{fail_to_pass}}}",
            rf"\newcommand{{\CmpPassToFail}}{{{pass_to_fail}}}",
            rf"\newcommand{{\CmpBothFail}}{{{both_fail}}}",
            rf"\newcommand{{\CmpImproved}}{{{improved}}}",
            rf"\newcommand{{\CmpUnchanged}}{{{unchanged}}}",
            rf"\newcommand{{\CmpWorsened}}{{{worsened}}}",
            rf"\newcommand{{\CmpStepsA}}{{{statistics.mean(r['steps_a'] for r in rows):.1f}}}",
            rf"\newcommand{{\CmpStepsB}}{{{statistics.mean(r['steps_b'] for r in rows):.1f}}}",
            rf"\newcommand{{\CmpOutA}}{{{statistics.mean(r['out_a'] for r in rows):,.0f}}}",
            rf"\newcommand{{\CmpOutB}}{{{statistics.mean(r['out_b'] for r in rows):,.0f}}}",
            rf"\newcommand{{\CmpCostA}}{{\${sum(r['cost_a'] for r in rows):,.2f}}}",
            rf"\newcommand{{\CmpCostB}}{{\${sum(r['cost_b'] for r in rows):,.2f}}}",
        ]
        domain_rows = "\n".join(
            f"{g['label']} & {g['n']} & {pct_tex(g['pass_a'], g['n'])} & {pct_tex(g['pass_b'], g['n'])} "
            f"& {g['partial_a']:.3f} & {g['partial_b']:.3f} & {g['partial_b'] - g['partial_a']:+.3f} \\\\"
            for g in by_domain
        )
        type_rows = "\n".join(
            f"{TYPE_NAMES.get(g['label'], g['label'])} & {g['n']} & {pct_tex(g['pass_a'], g['n'])} "
            f"& {pct_tex(g['pass_b'], g['n'])} & {g['partial_a']:.3f} & {g['partial_b']:.3f} "
            f"& {g['partial_b'] - g['partial_a']:+.3f} \\\\"
            for g in by_type
        )
        flip_rows = "\n".join(
            f"\\code{{{r['task'].replace('_', chr(92) + '_')}}} & {r['type']} & "
            f"{r['score_a']:.2f} & {r['score_b']:.2f} \\\\"
            for r in flips
        ) or "（无） \\\\"
        macros.append(rf"\newcommand{{\CmpDomainRows}}{{%" + "\n" + domain_rows + "\n}")
        macros.append(rf"\newcommand{{\CmpTypeRows}}{{%" + "\n" + type_rows + "\n}")
        macros.append(rf"\newcommand{{\CmpFlipRows}}{{%" + "\n" + flip_rows + "\n}")
        out_tex.write_text("\n".join(macros) + "\n", encoding="utf-8")
        print(f"wrote {out_tex}")

        domain_labels = [g["label"] for g in by_domain]
        coords_a = " ".join(
            f"({g['label']},{100 * g['pass_a'] / g['n']:.1f})" for g in by_domain
        )
        coords_b = " ".join(
            f"({g['label']},{100 * g['pass_b'] / g['n']:.1f})" for g in by_domain
        )
        rates = [
            100 * g["pass_a"] / g["n"] for g in by_domain
        ] + [100 * g["pass_b"] / g["n"] for g in by_domain]
        ymax = max(40, int(max(rates, default=0) // 10 * 10) + 10)
        fig = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
  ybar, width=0.92\textwidth, height=6.2cm, ymin=0, ymax={ymax},
  ylabel={{通过率 (\%)}}, symbolic x coords={{{','.join(domain_labels)}}},
  xtick=data, bar width=9pt, enlarge x limits=0.12,
  tick label style={{font=\small}},
  legend style={{at={{(0.5,1.02)}}, anchor=south, legend columns=2, font=\small}},
]
\addplot coordinates {{{coords_a}}};
\addplot coordinates {{{coords_b}}};
\legend{{默认 effort, max effort}}
\end{{axis}}
\end{{tikzpicture}}
"""
        fig_path = out_tex.parent / "fig_compare_domain.tex"
        fig_path.write_text(fig, encoding="utf-8")
        print(f"wrote {fig_path}")


if __name__ == "__main__":
    main()

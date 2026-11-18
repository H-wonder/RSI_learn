#!/usr/bin/env python3
"""Generate LaTeX fragments for the task-2 PDF report.

Outputs (reports/tex/):
  task2_nodes.tex       node inventory of the five flows
  task2_assertions.tex  direct vs structured assertion tables
  task2_metrics.tex     headline macros

Data sources:
  results/medium-max/{sales,operations,support}.json  (direct, max effort)
  experiments/exp-004-structured/*.json               (structured runs)
  rsi-flow/.../FLOW_AGENT/flow-agent-*.json           (flow definitions)
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "tex"
OUT.mkdir(parents=True, exist_ok=True)

# The flow JSONs are committed under experiments/ so the appendices rebuild
# from a fresh clone; fall back to the rsi-flow working tree when present.
_LOCAL_FLOWS = ROOT / "experiments" / "exp-004-structured" / "flows"
FLOW_DIR = _LOCAL_FLOWS if _LOCAL_FLOWS.is_dir() else (
    ROOT.parent / "rsi-flow" / "flow-test" / "src" / "test"
    / "resources" / "flow" / "FLOW_AGENT")


def tex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def load_direct(domain: str, task: str) -> dict:
    # Compact per-task direct records are committed so the report can be
    # rebuilt from a fresh clone (results/ itself is gitignored).
    compact = (ROOT / "experiments" / "exp-004-structured"
               / f"direct-{domain}.json")
    if compact.exists():
        row = json.loads(compact.read_text(encoding="utf-8"))
        if row.get("name") == task:
            return row
    data = json.loads((ROOT / "results" / "medium-max" / f"{domain}.json")
                      .read_text(encoding="utf-8"))
    for row in data["tasks"]:
        if row["name"] == task:
            return row
    raise SystemExit(f"task not found in direct results: {task}")


def load_run(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


TASKS = [
    {
        "key": "sales",
        "domain": "sales",
        "task": "sales.multi_hop_lookup",
        "flow": "FLOW_AGENT_ULTRA",
        "structured": ["experiments/exp-004-structured/multi_hop_lookup-run1.json",
                       "experiments/exp-004-structured/multi_hop_lookup-run2.json",
                       "experiments/exp-004-structured/multi_hop_lookup-run3.json"],
        "label": "sales.multi\\_hop\\_lookup",
    },
    {
        "key": "ops",
        "domain": "operations",
        "task": "operations.generator_load_testing_schedule",
        "flow": "FLOW_AGENT_OPS",
        "structured": ["experiments/exp-004-structured/ops-run1.json"],
        "label": "operations.generator\\_load\\_testing\\_schedule",
    },
    {
        "key": "support",
        "domain": "support",
        "task": "support.zendesk_sf_case_sync",
        "flow": "FLOW_AGENT_SUPPORT",
        "structured": ["experiments/exp-004-structured/support-run2.json"],
        "label": "support.zendesk\\_sf\\_case\\_sync",
    },
]


def write_metrics() -> None:
    lines = []
    for spec in TASKS:
        direct = load_direct(spec["domain"], spec["task"])
        run = load_run(spec["structured"][-1])
        stem = spec["key"]
        lines.append(rf"\newcommand{{\Tii{stem.capitalize()}DirectScore}}{{{direct['score']:.3f}}}")
        lines.append(rf"\newcommand{{\Tii{stem.capitalize()}StructuredScore}}{{{run['score']['score']:.3f}}}")
    (OUT / "task2_metrics.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_nodes() -> None:
    files = [
        ("FLOW_AGENT_ULTRA", "flow-agent-ultra.json", "sales（S0–S7，3 次 LLM）"),
        ("FLOW_AGENT_OPS", "flow-agent-ops.json", "operations（全确定性）"),
        ("FLOW_AGENT_SUPPORT", "flow-agent-support.json", "support（1 次 LLM）"),
        ("FLOW_AGENT_ULTRA_NOREPAIR", "flow-agent-ultra-norepair.json", "消融：去掉 repair"),
        ("FLOW_AGENT_OPS_SEQ", "flow-agent-ops-seq.json", "消融：串行读取"),
    ]
    rows = []
    for flow_id, filename, desc in files:
        flow = json.loads((FLOW_DIR / filename).read_text(encoding="utf-8"))
        rows.append(r"\midrule")
        rows.append(
            rf"\multicolumn{{4}}{{l}}{{\textbf{{{tex_escape(flow_id)}}}: "
            rf"{len(flow['nodes'])} 节点 / {len(flow['routes'])} 路由，{tex_escape(desc)}}} \\")
        rows.append(r"\midrule")
        for node in flow["nodes"]:
            ref = node.get("reference", "")
            params = len(node.get("params") or [])
            results = ", ".join(r["name"] for r in node.get("results") or [])
            rows.append(
                rf"{tex_escape(node['id'])} & {tex_escape(ref)} & {params} & "
                rf"{tex_escape(results)} \\")
    body = "\n".join(rows)
    tex = rf"""
{{\scriptsize
\begin{{longtable}}{{p{{5.0cm}}p{{3.1cm}}p{{1.0cm}}p{{5.0cm}}}}
\toprule
节点 ID & 引用 & 参数数 & 结果变量 \\
\midrule
\endhead
\bottomrule
\endfoot
{body}
\end{{longtable}}
}}
"""
    (OUT / "task2_nodes.tex").write_text(tex, encoding="utf-8")


def assertion_label(assertion: dict) -> str:
    params = assertion.get("params") or {}
    keys = []
    for key in ("subject", "to", "ticket_id", "summary_contains",
                "body_contains", "priority", "origin", "account_id",
                "channel_name", "text_contains", "count", "collection"):
        if key in params:
            value = params[key]
            if isinstance(value, list):
                value = "/".join(str(v) for v in value)
            keys.append(f"{key}={value}")
    if not keys:
        return tex_escape(assertion.get("type", ""))
    return (tex_escape(assertion.get("type", "")) + r"\newline "
            + tex_escape("; ".join(keys)))


def write_assertions() -> None:
    blocks = []
    for spec in TASKS:
        direct = load_direct(spec["domain"], spec["task"])
        run = load_run(spec["structured"][-1])
        d_asserts = [a for a in direct["assertion_results"] if not a.get("excluded")]
        s_asserts = [a for a in run["score"]["assertion_results"] if not a.get("excluded")]
        rows = []
        for d, s in zip(d_asserts, s_asserts):
            rows.append(
                rf"\TiiMark{{{ 'P' if d['passed'] else 'F' }}} & "
                rf"\TiiMark{{{ 'P' if s['passed'] else 'F' }}} & "
                rf"{assertion_label(d)} \\")
        blocks.append(rf"""
\subsection*{{{tex_escape(spec['task'])}}}

{{\footnotesize
\begin{{longtable}}{{p{{1.5cm}}p{{1.5cm}}p{{10.8cm}}}}
\toprule
direct & structured & 断言（类型 + 关键参数） \\
\midrule
\endhead
\bottomrule
\endfoot
{chr(10).join(rows)}
\end{{longtable}}
}}
""")
    (OUT / "task2_assertions.tex").write_text("\n".join(blocks), encoding="utf-8")


if __name__ == "__main__":
    write_metrics()
    write_nodes()
    write_assertions()
    print("wrote task2 tex fragments to", OUT)

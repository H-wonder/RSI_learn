#!/usr/bin/env python3
"""Derive ablation variants from the task flows (task 2 attribution).

- FLOW_AGENT_ULTRA_NOREPAIR : same sales flow without the S6 repair rounds.
  If the first pass already scores 1.0, repair is not what produced the gain.

- FLOW_AGENT_OPS_SEQ       : the ops flow with the async strategy removed.
  Reads still happen, just sequentially; any change is latency, not accuracy.

The variants are generated, never hand-edited, so they stay in sync with the
base flows.
"""

from __future__ import annotations

import json
from pathlib import Path

SRC = Path(
    "/home/wonder/work/xinren/multi_agent/rsi-flow/"
    "flow-test/src/test/resources/flow/FLOW_AGENT"
)


def load(name: str) -> dict:
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def save(flow: dict, name: str) -> None:
    (SRC / name).write_text(
        json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {SRC / name} ({len(flow['nodes'])} nodes, "
          f"{len(flow['routes'])} routes)")


def no_repair() -> None:
    flow = load("flow-agent-ultra.json")
    flow["id"] = "FLOW_AGENT_ULTRA_NOREPAIR"
    flow["name"] = "S0-S7 without S6 repair (ablation)"
    keep = [n for n in flow["nodes"] if not n["id"].startswith("S6_")]
    removed = {n["id"] for n in flow["nodes"]} - {n["id"] for n in keep}
    flow["nodes"] = keep
    routes = [r for r in flow["routes"]
              if r["source"] not in removed and r["target"] not in removed]
    # both branches of the score check go straight to finalize
    routes = [r for r in routes if r["source"] != "S5_CHECK"]
    routes.append({"source": "S5_CHECK", "target": "S7_FINAL"})
    flow["routes"] = routes
    # S7 payload referenced passed_2, which no longer exists
    for n in flow["nodes"]:
        if n["id"] == "S7_FINAL":
            for p in n["params"]:
                if p["name"].endswith("_payloadJson"):
                    p["defaultValue"] = '{"passed":"{{passed}}"}'
    save(flow, "flow-agent-ultra-norepair.json")


def ops_sequential() -> None:
    flow = load("flow-agent-ops.json")
    flow["id"] = "FLOW_AGENT_OPS_SEQ"
    flow["name"] = "Generator load-test scheduling, sequential reads (ablation)"
    flow["strategies"] = []
    # Without a fork strategy the three reads must be chained explicitly,
    # otherwise only the first branch runs before the join.
    flow["routes"] = [
        r for r in flow["routes"]
        if r["target"] not in ("O_READ_ENG", "O_READ_FUEL")
        and not (r["source"] in ("O_READ_ENG", "O_READ_FUEL", "O_READ_UNITS")
                 and r["target"] == "O_JOIN")
    ]
    flow["routes"] += [
        {"source": "O_READ_UNITS", "target": "O_READ_ENG"},
        {"source": "O_READ_ENG", "target": "O_READ_FUEL"},
        {"source": "O_READ_FUEL", "target": "O_JOIN"},
    ]
    save(flow, "flow-agent-ops-seq.json")


if __name__ == "__main__":
    no_repair()
    ops_sequential()

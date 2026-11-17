#!/usr/bin/env python3
"""Run AutomationBench per domain, saving one JSON + one log per domain.

Why per domain: `--num-examples` slices the *combined* dataset, so running
several domains with N would give N tasks total, not N per domain.

Usage:
    python scripts/run_batch.py --name smoke --domains simple --per-domain 5 --dry-run
    python scripts/run_batch.py --name small --domains all --per-domain 3
    python scripts/run_batch.py --name small --tasks-file data/tasks/small.csv
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DOMAINS = ["sales", "marketing", "operations", "support", "finance", "hr"]
DEFAULT_DATASET = ROOT.parent / "datasets" / "AutomationBench"


def load_config(path: str | None) -> dict:
    if not path:
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def resolve_dataset(config: dict, cli_value: str | None) -> Path:
    raw = cli_value or config.get("dataset_dir") or str(DEFAULT_DATASET)
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve()


def split_domains(raw: str | list[str]) -> list[str]:
    if isinstance(raw, list):
        items = raw
    else:
        items = [x.strip() for x in raw.split(",") if x.strip()]
    if not items or items == ["all"]:
        return PUBLIC_DOMAINS
    return items


def read_tasks_file(path: Path) -> dict[str, list[str]]:
    """Read a CSV with `domain,task_name` columns (header optional)."""
    grouped: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2 or parts[0] == "domain":
            continue
        grouped.setdefault(parts[0], []).append(parts[1])
    return grouped


def build_command(
    dataset: Path,
    model: str,
    domain: str,
    out_json: Path,
    toolset: str,
    max_steps: int,
    max_concurrent: int,
    api_key_var: str,
    base_url: str | None,
    reasoning_effort: str | None,
    per_domain: int,
    task_names: list[str] | None,
) -> list[str]:
    cmd = [
        "uv",
        "run",
        "auto-bench",
        "--model",
        model,
        "--domains",
        domain,
        "--toolset",
        toolset,
        "--max-steps",
        str(max_steps),
        "--max-concurrent",
        str(max_concurrent),
        "--api-key-var",
        api_key_var,
        "--export-json",
        str(out_json),
    ]
    if base_url:
        cmd += ["--base-url", base_url]
    if reasoning_effort:
        cmd += ["--reasoning-effort", reasoning_effort]
    if task_names:
        cmd += ["--tasks", ",".join(task_names)]
    else:
        cmd += ["--num-examples", str(per_domain)]
    return cmd


def run_streaming(cmd: list[str], cwd: Path, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n\n")
        log.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            log.write(line)
            log.flush()
        return proc.wait()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="experiment name, e.g. small")
    parser.add_argument("--config", help="JSON config under configs/")
    parser.add_argument("--dataset-dir")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--reasoning-effort")
    parser.add_argument("--api-key-var")
    parser.add_argument("--toolset")
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--max-concurrent", type=int)
    parser.add_argument("--domains", help="comma separated, or 'all'")
    parser.add_argument("--per-domain", type=int)
    parser.add_argument("--tasks-file", help="CSV: domain,task_name")
    parser.add_argument("--out-root", default="results")
    parser.add_argument("--logs-root", default="logs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = args.config
    if config_path is None:
        candidate = ROOT / "configs" / f"{args.name}.json"
        if candidate.is_file():
            config_path = str(candidate)
    config = load_config(config_path)
    if config_path:
        print(f"config: {config_path}")
    dataset = resolve_dataset(config, args.dataset_dir)
    model = args.model or config.get("model") or "TBD"
    base_url = args.base_url or config.get("base_url")
    reasoning_effort = args.reasoning_effort or config.get("reasoning_effort")
    api_key_var = args.api_key_var or config.get("api_key_var") or "OPENAI_API_KEY"
    toolset = args.toolset or config.get("toolset") or "api"
    max_steps = args.max_steps or config.get("max_steps") or 50
    max_concurrent = args.max_concurrent or config.get("max_concurrent") or 5
    per_domain = args.per_domain or config.get("per_domain") or 3
    domains = split_domains(args.domains or config.get("domains") or "all")

    if not dataset.is_dir():
        raise SystemExit(f"dataset not found: {dataset}")
    if not shutil.which("uv"):
        raise SystemExit("uv not found; install it first")
    if not args.dry_run and model == "TBD":
        raise SystemExit("model is TBD: pass --model or edit configs/<name>.json")
    if not args.dry_run and not os.environ.get(api_key_var):
        raise SystemExit(f"{api_key_var} is not set (use --dry-run to only print commands)")

    tasks_by_domain = {}
    if args.tasks_file:
        tasks_by_domain = read_tasks_file(Path(args.tasks_file))
        domains = [d for d in domains if d in tasks_by_domain] or list(tasks_by_domain)

    out_dir = ROOT / args.out_root / args.name
    log_dir = ROOT / args.logs_root / args.name
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "name": args.name,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "base_url": base_url,
        "reasoning_effort": reasoning_effort,
        "toolset": toolset,
        "max_steps": max_steps,
        "max_concurrent": max_concurrent,
        "per_domain": per_domain,
        "tasks_file": args.tasks_file,
        "domains": domains,
        "runs": [],
    }

    failures = 0
    for domain in domains:
        out_json = out_dir / f"{domain}.json"
        log_path = log_dir / f"{domain}.log"
        task_names = tasks_by_domain.get(domain)
        cmd = build_command(
            dataset=dataset,
            model=model,
            domain=domain,
            out_json=out_json,
            toolset=toolset,
            max_steps=max_steps,
            max_concurrent=max_concurrent,
            api_key_var=api_key_var,
            base_url=base_url,
            reasoning_effort=reasoning_effort,
            per_domain=per_domain,
            task_names=task_names,
        )
        print(f"\n=== {args.name} / {domain} ===")
        print("$", " ".join(cmd))
        started = datetime.now(timezone.utc)
        if args.dry_run:
            rc = 0
        else:
            rc = run_streaming(cmd, dataset, log_path)
        finished = datetime.now(timezone.utc)
        status = "ok" if rc == 0 else f"failed({rc})"
        print(f"--- {domain}: {status}")
        if rc != 0:
            failures += 1
        manifest["runs"].append(
            {
                "domain": domain,
                "status": status,
                "returncode": rc,
                "command": cmd,
                "started_at": started.isoformat(),
                "finished_at": finished.isoformat(),
                "output": str(out_json),
                "log": str(log_path),
            }
        )
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nresults: {out_dir}")
    if failures:
        raise SystemExit(f"{failures} domain(s) failed")


if __name__ == "__main__":
    main()

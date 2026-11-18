#!/usr/bin/env bash
# Rebuild the task-2 PDF report from reports/task2-report.tex.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/build_task2_report.py

cd "$ROOT/reports"
# The TOC can oscillate by one page on the first passes; four runs converge.
xelatex -interaction=nonstopmode -halt-on-error task2-report.tex > /tmp/task2-build-1.log
xelatex -interaction=nonstopmode -halt-on-error task2-report.tex > /tmp/task2-build-2.log
xelatex -interaction=nonstopmode -halt-on-error task2-report.tex > /tmp/task2-build-3.log
xelatex -interaction=nonstopmode -halt-on-error task2-report.tex > /tmp/task2-build-4.log
cp task2-report.pdf ../Task2-Structured-Agent-Report.pdf
rm -f task2-report.pdf task2-report.aux task2-report.log task2-report.out task2-report.toc

echo "built: $ROOT/Task2-Structured-Agent-Report.pdf"

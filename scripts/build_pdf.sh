#!/usr/bin/env bash
# Rebuild the PDF report from reports/report.tex using local TeXLive.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/reports"

xelatex -interaction=nonstopmode -halt-on-error report.tex > /tmp/report-build-1.log
xelatex -interaction=nonstopmode -halt-on-error report.tex > /tmp/report-build-2.log
cp report.pdf AutomationBench-Baseline-Report.pdf

echo "built: $ROOT/reports/AutomationBench-Baseline-Report.pdf"

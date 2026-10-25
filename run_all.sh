#!/usr/bin/env bash
# Runs the whole pipeline in order. Takes about 75 minutes, mostly downloads.
set -euo pipefail
cd "$(dirname "$0")"
python3 code/01_fetch_bank.py
python3 code/02_parse_bank.py
python3 code/03_fetch_ncbi.py
python3 code/04_crosswalk.py
python3 code/05_external_check.py
python3 code/06_figures.py "$@"
python3 code/07_docs.py "$@"
echo "Done. Read data/processed/qa_report.txt first."

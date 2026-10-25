#!/usr/bin/env bash
# Rebuilds every output of this release.
#
# Default (offline): reproduces the released numbers exactly from the saved inputs in data/raw/
# (the archived CDC pages, the saved NCBI rows and the FDA documents). Takes about two minutes.
#
#   bash run_all.sh            # reproduce this release
#   bash run_all.sh --final    # same, without DRAFT stamps (after author verification)
#   bash run_all.sh --refresh  # download fresh copies from CDC, FDA and NCBI first (about 75 minutes).
#                              # CDC pages and NCBI results change over time, so numbers will differ
#                              # from this release; that is how a new version is made.
set -euo pipefail
cd "$(dirname "$0")"
FLAGS=()
REFRESH=0
for a in "$@"; do
  if [ "$a" = "--refresh" ]; then REFRESH=1; else FLAGS+=("$a"); fi
done
if [ "$REFRESH" = "1" ]; then
  rm -rf data/raw/isolates data/raw/panels
  python3 code/01_fetch_bank.py
  python3 code/01b_fetch_fda.py
  python3 code/02_parse_bank.py
  python3 code/03_fetch_ncbi.py
else
  python3 code/02_parse_bank.py      # unpacks data/raw/cdc_pages.tar.gz if the pages are not already unpacked
fi
python3 code/04_crosswalk.py > /dev/null
python3 code/05_external_check.py > /dev/null
python3 code/06_figures.py "${FLAGS[@]+"${FLAGS[@]}"}"
python3 code/07_docs.py "${FLAGS[@]+"${FLAGS[@]}"}"
echo "Done. Read data/processed/qa_report.txt first."

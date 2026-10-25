#!/usr/bin/env python3
"""
01b_fetch_fda.py - Download the FDA decision summaries behind the rapid panel target table.

PLAIN-LANGUAGE NOTE: Saves a copy of each FDA document listed in
reference/rapid_panel_targets.csv (plus the later modification summaries named
there) into data/raw/fda/, and logs each one in data/raw/PROVENANCE.txt. These
are the documents you check the target lists against. You do not need to open
this file.
"""
import csv
import datetime
import hashlib
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
FDA = os.path.join(RAW, "fda")


def main():
    os.makedirs(FDA, exist_ok=True)
    urls = set()
    for r in csv.DictReader(open(os.path.join(ROOT, "reference", "rapid_panel_targets.csv"))):
        urls.add(r["decision_summary_url"])
        for k in re.findall(r"modified (K\d{6})", r["fda_510k"]):
            urls.add(f"https://www.accessdata.fda.gov/cdrh_docs/reviews/{k}.pdf")
    for u in sorted(urls):
        name = u.rstrip("/").split("/")[-1]
        out = os.path.join(FDA, name)
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        b = urllib.request.urlopen(req, timeout=120).read()
        open(out, "wb").write(b)
        with open(os.path.join(RAW, "PROVENANCE.txt"), "a") as f:
            f.write(" | ".join([datetime.date.today().isoformat(), os.path.relpath(out, RAW), f"{len(b)} bytes",
                                f"sha256:{hashlib.sha256(b).hexdigest()}", u, "FDA decision summary"]) + "\n")
        print(name, len(b))


if __name__ == "__main__":
    main()

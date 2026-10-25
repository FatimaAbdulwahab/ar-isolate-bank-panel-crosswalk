#!/usr/bin/env python3
"""
01_fetch_bank.py - Download the CDC & FDA Antimicrobial Resistance Isolate Bank
panel list, every panel page, and every isolate page.

PLAIN-LANGUAGE NOTE: This script saves a copy of the Isolate Bank's public web
pages exactly as CDC shows them today. Nothing is changed. Each saved page is
logged in data/raw/PROVENANCE.txt with the date, size and a fingerprint
(SHA-256) so anyone can confirm later which version of the website was used.
You do not need to open this file.

Source: https://wwwn.cdc.gov/ARIsolateBank/  (U.S. federal government web
content; public domain in the United States, 17 U.S.C. 105).

The script is polite (one request at a time, a short pause between requests)
and resumable: pages already saved today are not downloaded again.
"""
import datetime
import hashlib
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROV = os.path.join(RAW, "PROVENANCE.txt")
BASE = "https://wwwn.cdc.gov/ARIsolateBank/"
UA = "Mozilla/5.0 (research crosswalk; contact abdulwahabfatima43@gmail.com)"
PAUSE = 0.6


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def log(path, url, note=""):
    with open(PROV, "a") as f:
        f.write(" | ".join([datetime.date.today().isoformat(), os.path.relpath(path, RAW),
                            f"{os.path.getsize(path)} bytes", f"sha256:{sha256(path)}", url, note]).rstrip(" |") + "\n")


def get(url, path, note="", tries=4):
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        return open(path, encoding="utf-8", errors="ignore").read()
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            data = urllib.request.urlopen(req, timeout=60).read()
            with open(path, "wb") as f:
                f.write(data)
            log(path, url, note)
            time.sleep(PAUSE)
            return data.decode("utf-8", errors="ignore")
        except Exception as e:  # network hiccup: wait and retry
            print(f"  retry {k+1} {url}: {e}", file=sys.stderr)
            time.sleep(3 * (k + 1))
    raise RuntimeError(f"could not fetch {url}")


def main():
    os.makedirs(os.path.join(RAW, "panels"), exist_ok=True)
    os.makedirs(os.path.join(RAW, "isolates"), exist_ok=True)
    allp = get(BASE + "Panel/AllIsolate", os.path.join(RAW, "AllIsolate.html"), "list of all panels")
    ids = sorted(set(int(x) for x in re.findall(r'PanelDetail(?:\.aspx)?\?ID=(\d+)', allp, flags=re.I)))
    print(f"{len(ids)} panel IDs on the All Isolate Panels page")
    pairs = set()
    for pid in ids:
        html = get(f"{BASE}Panel/PanelDetail?ID={pid}", os.path.join(RAW, "panels", f"panel_{pid}.html"), f"panel {pid}")
        for iso, p in re.findall(r'IsolateDetail(?:\.aspx)?\?IsolateID=(\d+)&(?:amp;)?PanelID=(\d+)', html, flags=re.I):
            pairs.add((int(iso), int(p)))
    isolates = sorted(set(i for i, _ in pairs))
    print(f"{len(pairs)} panel-isolate links, {len(isolates)} unique isolate IDs")
    with open(os.path.join(RAW, "panel_isolate_links.tsv"), "w") as f:
        f.write("panel_page_id\tisolate_page_id\n")
        for i, p in sorted(pairs, key=lambda x: (x[1], x[0])):
            f.write(f"{p}\t{i}\n")
    first_panel = {}
    for i, p in sorted(pairs):
        first_panel.setdefault(i, p)
    if "--reverse" in sys.argv:  # optional second worker that starts from the other end
        isolates = isolates[::-1]
    for n, iso in enumerate(isolates, 1):
        get(f"{BASE}Panel/IsolateDetail?IsolateID={iso}&PanelID={first_panel[iso]}",
            os.path.join(RAW, "isolates", f"isolate_{iso}.html"), f"isolate page {iso}")
        if n % 100 == 0:
            print(f"  {n}/{len(isolates)} isolate pages")
    print("done")


if __name__ == "__main__":
    main()

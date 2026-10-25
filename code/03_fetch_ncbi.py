#!/usr/bin/env python3
"""
03_fetch_ncbi.py - Download NCBI's own gene calls (AMRFinderPlus) for the
Isolate Bank genomes, and NCBI's reference gene catalog.

PLAIN-LANGUAGE NOTE: CDC lists genes for each Bank isolate using its own
method. NCBI separately runs AMRFinderPlus, the tool your Project 1 benchmark
relies on, on the same genomes. This script fetches NCBI's results for every
Bank BioSample so the two can be compared, plus NCBI's master list of
resistance genes and gene families (used to decide which gene belongs to which
rapid panel target). Every download is logged in data/raw/PROVENANCE.txt.
You do not need to open this file.

Sources (NCBI public data, no restrictions on use;
https://www.ncbi.nlm.nih.gov/home/about/policies/):
  https://ftp.ncbi.nlm.nih.gov/pathogen/Results/<group>/latest_snps/AMR/PDG*.amr.metadata.tsv
  https://ftp.ncbi.nlm.nih.gov/pathogen/Antimicrobial_resistance/AMRFinderPlus/database/latest/
The large NCBI tables are read as a stream and only rows for Bank BioSamples
are kept; the PDG run accession in the log pins the exact NCBI version.
"""
import csv
import datetime
import gzip
import hashlib
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
NCBI = os.path.join(RAW, "ncbi")
PROV = os.path.join(RAW, "PROVENANCE.txt")
PD = "https://ftp.ncbi.nlm.nih.gov/pathogen/Results/"
DB = "https://ftp.ncbi.nlm.nih.gov/pathogen/Antimicrobial_resistance/AMRFinderPlus/database/latest/"


def log(line):
    with open(PROV, "a") as f:
        f.write(line + "\n")


def save(url, out, note=""):
    b = urllib.request.urlopen(url, timeout=600).read()
    open(out, "wb").write(b)
    log(" | ".join([datetime.date.today().isoformat(), os.path.relpath(out, RAW), f"{len(b)} bytes",
                    f"sha256:{hashlib.sha256(b).hexdigest()}", url, note]).rstrip(" |"))
    return b


def groups_for(organisms):
    listing = urllib.request.urlopen(PD, timeout=120).read().decode()
    allg = sorted(set(re.findall(r'href="([A-Za-z_]+)/"', listing)))
    genera = {o.split()[0] for o in organisms if o and o[0].isupper()}
    alias = {"Escherichia": ["Escherichia_coli_Shigella"], "Shigella": ["Escherichia_coli_Shigella"],
             "Candida": ["Candidozyma_auris"], "Candidozyma": ["Candidozyma_auris"]}
    out = set()
    for g in genera:
        out.update(alias.get(g, []))
        out.update(x for x in allg if x.split("_")[0] == g)
    return sorted(out)


def stream_group(group, keep):
    url = f"{PD}{group}/latest_snps/AMR/"
    try:
        html = urllib.request.urlopen(url, timeout=120).read().decode()
    except Exception as e:
        log(f"{datetime.date.today()} | {group} | no AMR directory ({e}) | {url}")
        return 0
    m = re.search(r'href="(PDG\d+\.\d+\.amr\.metadata\.tsv)"', html)
    if not m:
        return 0
    src = url + m.group(1)
    out = os.path.join(NCBI, f"{group}.bank_rows.tsv")
    h = hashlib.sha256()
    nbytes = nrows = nkept = 0
    with urllib.request.urlopen(src, timeout=1800) as r, open(out, "w") as fo:
        buf = b""
        bs_col = None
        while True:
            chunk = r.read(1 << 22)
            if not chunk:
                lines = [buf] if buf.strip() else []
            else:
                h.update(chunk)
                nbytes += len(chunk)
                buf += chunk
                lines = buf.split(b"\n")
                buf = lines.pop()
            for ln in lines:
                s = ln.decode("utf-8", "replace")
                if bs_col is None:
                    bs_col = s.split("\t").index("biosample_acc")
                    fo.write(s + "\n")
                    continue
                nrows += 1
                f = s.split("\t")
                if len(f) > bs_col and f[bs_col] in keep:
                    fo.write(s + "\n")
                    nkept += 1
            if not chunk:
                break
    log(" | ".join([datetime.date.today().isoformat(), os.path.relpath(out, RAW),
                    f"source {nbytes} bytes, {nrows} rows, kept {nkept} Bank rows",
                    f"source sha256:{h.hexdigest()}", src]))
    print(f"  {group}: {nrows} NCBI isolates scanned, {nkept} Bank BioSamples found", flush=True)
    return nkept


def main():
    os.makedirs(NCBI, exist_ok=True)
    isos = list(csv.DictReader(open(os.path.join(ROOT, "data", "processed", "bank_isolates.tsv")), delimiter="\t"))
    keep = {r["biosample"] for r in isos if r["biosample"]}
    ver = save(DB + "version.txt", os.path.join(NCBI, "amrfinder_db_version.txt")).decode().strip()
    for fn in ["ReferenceGeneCatalog.txt", "ReferenceGeneHierarchy.txt"]:
        save(DB + fn, os.path.join(NCBI, fn), f"AMRFinderPlus database {ver}")
    groups = groups_for([r["organism"] for r in isos])
    print(f"{len(keep)} Bank BioSamples; scanning {len(groups)} NCBI groups", flush=True)
    for g in groups:
        stream_group(g, keep)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
fetch_crossref.py - Download the Crossref record for every DOI the preprint cites.

PLAIN-LANGUAGE NOTE: Reference details (authors, title, journal, volume, pages) are
taken from the publisher's own registration at Crossref, not typed from memory.
Records reused from the Project 1 preprint are copied from its crossref_raw.json.
Output: crossref_raw.json. You do not need to open this file.
"""
import json, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = json.load(open(os.path.join(HERE, "crossref_p1.json")))
REUSE = ["feldgarden2021", "feldgarden2019", "bcid2_2022", "verigene2015", "timbrook2017", "ellington2017",
         "jacoby2009", "bush2020", "szakacs2014", "vanA2025", "osmrsa2002", "tamma2017", "wilson1927", "ncbi2025",
         "poirel2012", "pitout2015", "bevan2017", "su2019", "banerjee2021", "hunter2007", "mckinney2010", "waskom2021",
         "gordon2014", "idsa2024"]
NEW = {"lutgring2018": "10.1128/jcm.01415-17", "garcia2011": "10.1016/S1473-3099(11)70126-8",
       "lister2009": "10.1128/cmr.00040-09", "potron2013": "10.1016/j.ijantimicag.2012.11.007",
       "zankari2012": "10.1093/jac/dks261", "gupta2014": "10.1128/aac.01310-13",
       "cohen1960": "10.1177/001316446002000104", "courvalin2006": "10.1086/491711",
       "cetinkaya2000": "10.1128/CMR.13.4.686"}

if __name__ == "__main__":
    out = {k: P1[k] for k in REUSE}
    for k, doi in NEW.items():
        u = f"https://api.crossref.org/works/{doi}?mailto=abdulwahabfatima43@gmail.com"
        out[k] = json.load(urllib.request.urlopen(u, timeout=60))["message"]
        print(k, out[k]["DOI"], (out[k].get("title") or [""])[0][:70])
        time.sleep(0.3)
    json.dump(out, open(os.path.join(HERE, "crossref_raw.json"), "w"), indent=1)

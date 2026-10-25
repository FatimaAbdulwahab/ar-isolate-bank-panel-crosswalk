#!/usr/bin/env python3
"""
02_parse_bank.py - Turn the saved Isolate Bank pages into tables.

PLAIN-LANGUAGE NOTE: This reads the web pages saved by 01_fetch_bank.py and
writes four tables, copying CDC's values exactly (no reinterpretation here):
  data/processed/bank_panels.tsv          one row per panel
  data/processed/bank_isolates.tsv        one row per isolate (AR Bank number)
  data/processed/bank_mic_long.tsv        one row per isolate x drug (CDC MIC and S/I/R)
  data/processed/bank_mechanisms_long.tsv one row per isolate x gene CDC lists
You do not need to open this file.
"""
import csv
import glob
import html as H
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "processed")
BASE = "https://wwwn.cdc.gov/ARIsolateBank/"


def clean(s):
    s = re.sub(r"<sup>.*?</sup>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = H.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def span(t, sid):
    m = re.search(r'id="MainContent_%s"[^>]*>(.*?)</span>' % sid, t, flags=re.S)
    return clean(m.group(1)) if m else ""


def parse_panels():
    t = open(os.path.join(RAW, "AllIsolate.html"), encoding="utf-8", errors="ignore").read()
    body = t[t.find('id="dataTable"'):]
    rows = []
    listed = set()
    for tr in re.findall(r"<tr><td style='width: 669px!important;'>(.*?)</tr>", body, flags=re.S):
        m = re.search(r'PanelDetail\.aspx\?ID=(\d+)"><strong>(.*?)</strong></a>\s*\((\d+)\)', tr, flags=re.S)
        if not m:
            continue
        pid, name, n = int(m.group(1)), clean(m.group(2)), int(m.group(3))
        desc = re.search(r"<p[^>]*>(.*?)</p>", tr, flags=re.S)
        desc = clean(desc.group(1)) if desc else ""
        code = re.search(r"Panel ID:\s*([A-Za-z0-9\-]+)", desc)
        if not code:
            code = re.search(r"\(([A-Za-z0-9\-]+)\)\s*$", name)
        rows.append(dict(panel_page_id=pid, panel_name=name, panel_code=code.group(1) if code else f"panel{pid}",
                         n_isolates_listed=n, listed_on_all_panels_page=True,
                         description=re.sub(r"\s*Panel ID:.*$", "", desc)))
        listed.add(pid)
    # panel pages reached only through links inside descriptions
    for f in sorted(glob.glob(os.path.join(RAW, "panels", "panel_*.html"))):
        pid = int(re.search(r"panel_(\d+)", f).group(1))
        if pid in listed:
            continue
        pt = open(f, encoding="utf-8", errors="ignore").read()
        h1 = re.findall(r"<h1>\s*(.*?)\s*</h1>", pt[pt.find("IsolateInfoDownload"):], flags=re.S)
        code = re.search(r"Panel ID:</b>\s*([A-Za-z0-9\-]+)", pt)
        rows.append(dict(panel_page_id=pid, panel_name=clean(h1[-1]) if h1 else "",
                         panel_code=code.group(1) if code else f"panel{pid}",
                         n_isolates_listed="", listed_on_all_panels_page=False,
                         description="reached through a link in another panel's description"))
    return rows


def parse_isolate(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    pid = int(re.search(r"isolate_(\d+)", path).group(1))
    m = re.search(r"AR Bank #\s*(\d+)\s*</b>\s*<span[^>]*>\s*(.*?)</span>", t, flags=re.S)
    arbank = m.group(1) if m else ""
    organism = clean(m.group(2)) if m else ""
    bios = re.search(r'id="MainContent_lblSeqAcc".*?>(SAM[NDE][A-Z]?\d+)<', t, flags=re.S)
    panels = re.findall(r'<a href ="PanelDetail\.aspx\?ID=(\d+)">(.*?)</a>', t[:t.find('id="tabComponent"')], flags=re.S)
    panel_ids, panel_names = [], []
    for p, n in panels:
        if p not in panel_ids:
            panel_ids.append(p)
            panel_names.append(clean(n))
    note = ""
    mn = re.search(r"(MICs obtained by.*?)</div>", t, flags=re.S)
    if mn:
        note = clean(mn.group(1))
    # Free text CDC places between the (usually empty) characteristics label and the MIC note,
    # e.g. "Disk Diffusion FOX: 21 mm, R*" on the DTD panel or the vancomycin-variable note.
    page_note, fox_mm, fox_int = "", "", ""
    ci = t.find("lblIsolateCharacteristicsResult")
    cj = t.find("MICs obtained", ci) if ci > 0 else -1
    if ci > 0 and cj > 0:
        page_note = clean(t[t.find("</span>", ci):cj])
        fm = re.search(r"Disk Diffusion FOX:\s*(\d+)\s*mm,\s*([SIR])", page_note)
        if fm:
            fox_mm, fox_int = fm.group(1), fm.group(2)
    rec = dict(isolate_page_id=pid, ar_bank_number=arbank, organism=organism,
               study_id=span(t, "lblStudyIDResult"), biosample=bios.group(1) if bios else "",
               source=span(t, "lblSourceResult"), mlst=span(t, "lblmlstresult"),
               mcim=span(t, "lblmCIMResult"), carba_np=span(t, "lblCarbaResult"),
               collection_year=span(t, "lblCollectionYearResult"), location=span(t, "lblLocationResult"),
               characteristics=span(t, "lblIsolateCharacteristicsResult"),
               cdc_page_note=page_note, cefoxitin_disk_mm=fox_mm, cefoxitin_disk_int=fox_int,
               panel_page_ids=";".join(panel_ids), panel_names=" | ".join(panel_names),
               ast_method_note=note,
               isolate_url=f"{BASE}Panel/IsolateDetail?IsolateID={pid}&PanelID={panel_ids[0] if panel_ids else ''}")
    # MIC table
    mic = []
    i = t.find('id="mic"')
    seg = t[i:t.find('id="mmr"', i)] if i > 0 else ""
    interp = re.search(r"Interpretation \(INT\) derived from\s*(.*?)<", seg, flags=re.S)
    rec["int_standard"] = clean(interp.group(1)) if interp else ""
    foot = {}
    for k, v in re.findall(r"<sup>\s*(\d+)\s*</sup>\s*([^<]{3,200})", seg[seg.find("</tbody>"):] if "</tbody>" in seg else ""):
        foot[k] = clean(v)
    tb = seg[seg.find("<tbody>"):seg.find("</tbody>")] if "<tbody>" in seg else ""
    for tr in re.findall(r"<tr>(.*?)</tr>", tb, flags=re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)
        if len(tds) < 2:
            continue
        sup = re.findall(r"<sup>\s*(\d+)\s*</sup>", tds[0])
        mic.append(dict(ar_bank_number=arbank, biosample=rec["biosample"], organism=organism,
                        drug_cdc=clean(tds[0]), mic_cdc=clean(tds[1]),
                        int_cdc=clean(tds[2]) if len(tds) > 2 else "",
                        footnote="; ".join(foot.get(s, s) for s in sup)))
    # Mechanisms
    mech = []
    j = t.find('id="mmr"')
    mseg = t[j:t.find('id="propagation"', j)] if j > 0 else ""
    disc = re.search(r"Disclaimer:</b></span><br />\s*<p>(.*?)</p>", mseg, flags=re.S)
    rec["mechanism_method_note"] = clean(disc.group(1)) if disc else ""
    for cat, genes in re.findall(r"<tr><td>(.*?)</td><td>(.*?)</td></tr>", mseg, flags=re.S):
        cat = clean(cat)
        for g in [x.strip() for x in clean(genes).split(",") if x.strip()]:
            mech.append(dict(ar_bank_number=arbank, biosample=rec["biosample"], organism=organism,
                             category_cdc=cat, gene_cdc=g))
    rec["n_drugs"] = len(mic)
    rec["n_mechanisms"] = len(mech)
    return rec, mic, mech


def write(path, rows, cols=None):
    cols = cols or (list(rows[0].keys()) if rows else [])
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def unpack_if_needed():
    """The repository ships the saved CDC pages as one archive (GitHub limits file counts)."""
    arc = os.path.join(RAW, "cdc_pages.tar.gz")
    if not os.path.isdir(os.path.join(RAW, "isolates")) and os.path.exists(arc):
        import tarfile
        with tarfile.open(arc) as t:
            t.extractall(RAW, filter="data")


def main():
    unpack_if_needed()
    os.makedirs(OUT, exist_ok=True)
    panels = parse_panels()
    write(os.path.join(OUT, "bank_panels.tsv"), panels)
    isos, mics, mechs = [], [], []
    for f in sorted(glob.glob(os.path.join(RAW, "isolates", "isolate_*.html")),
                    key=lambda x: int(re.search(r"(\d+)", os.path.basename(x)).group(1))):
        r, m, k = parse_isolate(f)
        isos.append(r); mics += m; mechs += k
    # membership from the panel pages themselves (authoritative list of who is in each panel)
    links = list(csv.DictReader(open(os.path.join(RAW, "panel_isolate_links.tsv")), delimiter="\t"))
    by_iso = {}
    for l in links:
        by_iso.setdefault(int(l["isolate_page_id"]), []).append(l["panel_page_id"])
    pname = {str(p["panel_page_id"]): (p["panel_code"] or p["panel_name"]) for p in panels}
    for r in isos:
        r["panels_from_panel_pages"] = ";".join(sorted(set(by_iso.get(r["isolate_page_id"], [])), key=int))
        r["panel_codes"] = ";".join(pname.get(p, p) for p in r["panels_from_panel_pages"].split(";") if p)
    isos.sort(key=lambda r: r["ar_bank_number"])
    write(os.path.join(OUT, "bank_isolates.tsv"), isos)
    write(os.path.join(OUT, "bank_mic_long.tsv"), mics)
    write(os.path.join(OUT, "bank_mechanisms_long.tsv"), mechs)
    print(f"panels {len(panels)}  isolates {len(isos)}  MIC rows {len(mics)}  gene rows {len(mechs)}")
    print(f"isolates with BioSample: {sum(1 for r in isos if r['biosample'])}")


if __name__ == "__main__":
    main()

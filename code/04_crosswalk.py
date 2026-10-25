#!/usr/bin/env python3
"""
04_crosswalk.py - Build the Isolate Bank to rapid panel target crosswalk.

PLAIN-LANGUAGE NOTE: This is the heart of the project. For every Bank isolate
it takes the genes CDC lists, decides which rapid blood culture panel target
each gene belongs to (using NCBI's gene family tree, so "KPC-3" counts as KPC
and "OXA-232" counts as OXA-48-like), then writes:
  reference/cdc_gene_to_target.csv         every CDC gene name and the target it maps to
  data/processed/crosswalk_isolates.tsv    one row per isolate: genes, targets, key results, hard-case flag
  data/processed/panel_target_grid.csv     how many isolates in each Bank panel carry each target
  data/processed/product_target_coverage.csv  for each cleared panel's target: which Bank isolates exercise it
  data/processed/hard_cases.csv            isolates where gene and growth result part ways
"Hard case" uses CDC's own posted S/I/R (the Bank's reference interpretation).
You do not need to open this file.
"""
import csv
import json
import os
import re
from collections import defaultdict

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
REF = os.path.join(ROOT, "reference")
NCBI = os.path.join(ROOT, "data", "raw", "ncbi")

# Hierarchy nodes (NCBI ReferenceGeneHierarchy) that define each rapid panel target group
NODE_TO_TARGET = {
    "mecA": "mecA", "mecC": "mecC", "vanA": "vanA", "vanB": "vanB",
    "blaKPC": "KPC", "blaNDM": "NDM", "blaVIM": "VIM", "blaIMP": "IMP", "blaCTX-M": "CTX-M",
    "blaOXA-48_fam": "OXA-48-like", "blaOXA-23_fam": "OXA-23-like", "blaOXA-24_fam": "OXA-24/40-like",
    "blaOXA-58_fam": "OXA-58-like", "blaOXA-143_fam": "OXA-143-like", "blaSME": "SME",
    "mcr-1": "mcr-1", "mcr-2": "mcr-2", "mcr-3": "mcr-3",
}
TARGET_ORDER = ["mecA", "mecC", "vanA", "vanB", "KPC", "NDM", "OXA-48-like", "VIM", "IMP", "CTX-M",
                "OXA-23-like", "OXA-24/40-like", "OXA-58-like", "OXA-143-like", "SME", "mcr-1", "mcr-2", "mcr-3"]
CARBA_TARGETS = {"KPC", "NDM", "OXA-48-like", "VIM", "IMP", "OXA-23-like", "OXA-24/40-like", "OXA-58-like",
                 "OXA-143-like", "SME"}
# Drug that each target is expected to affect (CDC drug names); first is primary
TARGET_DRUGS = {
    "mecA": ["Oxacillin", "Cefoxitin"], "mecC": ["Oxacillin", "Cefoxitin"],
    "vanA": ["Vancomycin"], "vanB": ["Vancomycin"],
    "CTX-M": ["Ceftriaxone", "Cefotaxime", "Ceftazidime"],
    "mcr-1": ["Colistin"], "mcr-2": ["Colistin"], "mcr-3": ["Colistin"],
}
for t in CARBA_TARGETS:
    TARGET_DRUGS[t] = ["Meropenem", "Imipenem", "Ertapenem", "Doripenem"]
KEY_DRUGS = ["Meropenem", "Imipenem", "Ertapenem", "Doripenem", "Ceftriaxone", "Cefotaxime", "Ceftazidime",
             "Oxacillin", "Cefoxitin", "Vancomycin", "Colistin"]
ENTEROBACTERALES = ("Escherichia", "Klebsiella", "Enterobacter", "Citrobacter", "Serratia", "Proteus",
                    "Morganella", "Providencia", "Salmonella", "Shigella", "Raoultella", "Kluyvera",
                    "Cronobacter", "Pantoea", "Hafnia", "Leclercia", "Pluralibacter", "Kosakonia")
MORGANELLACEAE = ("Proteus", "Morganella", "Providencia")
FUNGI = ("Candida", "Candidozyma", "Aspergillus", "Trichophyton", "Kodameae", "Saccharomyces", "Cryptococcus",
         "Rhodotorula", "Pichia", "Clavispora", "Meyerozyma", "Nakaseomyces", "Wickerhamomyces", "Fusarium",
         "Kluyveromyces", "Debaryomyces", "Cyberlindnera", "Diutina", "Yarrowia")


def organism_group(org):
    g = (org or "").split(" ")[0]
    if g in ENTEROBACTERALES:
        return "Enterobacterales"
    if g == "Pseudomonas":
        return "Pseudomonas"
    if g == "Acinetobacter":
        return "Acinetobacter"
    if g == "Staphylococcus":
        return "Staphylococcus aureus" if org.startswith("Staphylococcus aureus") else "Staphylococcus, other"
    if g == "Enterococcus":
        return "Enterococcus"
    if g in FUNGI:
        return "Fungi"
    if g == "Neisseria":
        return "Neisseria"
    return "Other bacteria"


SCOPE = {"Enterobacterales", "Pseudomonas", "Acinetobacter", "Staphylococcus aureus", "Staphylococcus, other",
         "Enterococcus"}
GP_TARGETS = {"mecA", "mecC", "vanA", "vanB"}


def target_applies(t, grp):
    if t in ("mecA", "mecC"):
        return grp.startswith("Staphylococcus")
    if t in ("vanA", "vanB"):
        return grp == "Enterococcus"
    return grp in ("Enterobacterales", "Pseudomonas", "Acinetobacter")


def load_hierarchy():
    h = pd.read_csv(os.path.join(NCBI, "ReferenceGeneHierarchy.txt"), sep="\t", dtype=str).fillna("")
    parent = dict(zip(h.node_id, h.parent_node_id))
    subclass = dict(zip(h.node_id, h.subclass))
    syn = {}
    for nid, s in zip(h.node_id, h.synonyms):
        for x in s.split(","):
            if x.strip():
                syn[x.strip()] = nid
    ver = h.db_version.iloc[0]
    return parent, subclass, syn, ver


def target_of(sym, parent):
    seen, n = set(), sym
    while n and n not in seen:
        if n in NODE_TO_TARGET:
            return NODE_TO_TARGET[n], n
        seen.add(n)
        n = parent.get(n, "")
    return "", ""


def cdc_to_symbol(name, parent, syn):
    """CDC writes allele names like 'KPC-3', 'OXA-232', 'CTX-M-15', 'mecA'. NCBI uses 'blaKPC-3'."""
    n = name.strip().rstrip("*").strip()
    cands = [n, "bla" + n, "bla" + n.upper(), n.replace("bla", "bla", 1)]
    if n.lower().startswith("bla"):
        cands.insert(0, "bla" + n[3:])
    for c in cands:
        if c in parent:
            return c, "exact"
        if c in syn:
            return syn[c], "synonym"
    low = {k.lower(): k for k in parent}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()], "case-insensitive"
    # fall back to the family when the allele is new or untyped (e.g. 'KPC', 'OXA-48-like')
    m = re.match(r"^(?:bla)?(KPC|NDM|VIM|IMP|CTX-M|SME|GES|OXA)[-_]?", n, flags=re.I)
    if m:
        fam = "bla" + m.group(1).upper()
        if fam in parent:
            return fam, "family name only"
    m = re.match(r"^(mcr-\d+)", n)
    if m and m.group(1) in parent:
        return m.group(1), "family name only"
    return "", "not in NCBI catalog"


def main():
    parent, subclass, syn, refver = load_hierarchy()
    iso = pd.read_csv(os.path.join(PROC, "bank_isolates.tsv"), sep="\t", dtype=str).fillna("")
    mic = pd.read_csv(os.path.join(PROC, "bank_mic_long.tsv"), sep="\t", dtype=str).fillna("")
    mech = pd.read_csv(os.path.join(PROC, "bank_mechanisms_long.tsv"), sep="\t", dtype=str).fillna("")
    panels = pd.read_csv(os.path.join(PROC, "bank_panels.tsv"), sep="\t", dtype=str).fillna("")
    prod = pd.read_csv(os.path.join(REF, "rapid_panel_targets.csv"), dtype=str).fillna("")

    # ---- gene name map
    gmap = []
    for name in sorted(mech.gene_cdc.unique()):
        sym, how = cdc_to_symbol(name, parent, syn)
        tgt, node = target_of(sym, parent) if sym else ("", "")
        flag = ""
        if tgt == "OXA-48-like" and subclass.get(sym, "") and "CARBAPENEM" not in subclass.get(sym, ""):
            flag = "OXA-48 family variant NCBI does not list as carbapenem-hydrolyzing"
        if not sym and re.search(r"KPC|NDM|VIM|IMP|OXA|CTX|SME|mec|van|mcr|MBL", name, flags=re.I):
            flag = "[VERIFY] name resembles a panel target family but is not in the NCBI catalog; author to rule"
        if name.lower().startswith("vanhax"):
            sym, how, node, tgt = "vanA", "operon name (vanH-vanA-vanX)", "vanA", "vanA"
            flag = ("[VERIFY] vanA operon without its vanR/vanS regulators (CDC note); a panel detects vanA "
                    "but the isolate can test vancomycin susceptible (vancomycin-variable enterococcus)")
        if name.lower().startswith("blaz-mecc") or name.lower() == "blaz-mecc":
            # NCBI: blaZ-mecC is the blaZ carried on the mecC element (SCCmec type XI). CDC's own custom
            # panel BOR-33 is titled "AR-1306 & AR-1307 S.aureus mecC+", so CDC treats these isolates as mecC
            # positive. Counted as mecC here; the AMRFinderPlus check (05) tests whether mecC itself is present.
            flag = ("[VERIFY] CDC lists only blaZ-mecC (the blaZ on the mecC element); CDC's custom panel BOR-33 "
                    "names these isolates mecC+, so they are counted as mecC. Author to rule")
            tgt = "mecC"
        gmap.append(dict(gene_cdc=name, ncbi_symbol=sym, match=how, hierarchy_node=node, target_group=tgt,
                         ncbi_subclass=subclass.get(sym, ""), flag=flag, refgene_db_version=refver,
                         n_isolates=int(mech[mech.gene_cdc == name].ar_bank_number.nunique())))
    gmap = pd.DataFrame(gmap)
    gmap.to_csv(os.path.join(REF, "cdc_gene_to_target.csv"), index=False)
    g2t = dict(zip(gmap.gene_cdc, gmap.target_group))
    g2flag = dict(zip(gmap.gene_cdc, gmap.flag))

    # ---- per isolate
    mic["drug_key"] = mic.drug_cdc.str.strip()
    micd = {(r.ar_bank_number, r.drug_key): (r.mic_cdc, r.int_cdc) for r in mic.itertuples()}
    genes_by = mech.groupby("ar_bank_number").gene_cdc.apply(list).to_dict()
    cats_by = mech.groupby("ar_bank_number").apply(
        lambda d: dict(d.groupby("category_cdc").gene_cdc.apply(list))).to_dict()
    rows, hard = [], []
    for r in iso.itertuples():
        a = r.ar_bank_number
        grp = organism_group(r.organism)
        genes = genes_by.get(a, [])
        tg = defaultdict(list)
        for g in genes:
            if g2t.get(g):
                tg[g2t[g]].append(g)
        d = dict(ar_bank_number=a, organism=r.organism, organism_group=grp, biosample=r.biosample,
                 bank_panels=r.panel_codes, n_bank_panels=len([x for x in r.panel_codes.split(";") if x]),
                 in_scope_for_panel_targets=grp in SCOPE, has_mechanism_list=bool(genes),
                 n_genes_listed=len(genes))
        for t in TARGET_ORDER:
            d[f"{t}"] = ";".join(tg.get(t, []))
        d["panel_targets_carried"] = ";".join(t for t in TARGET_ORDER if tg.get(t))
        for p in prod["product"].unique():
            sub = prod[prod["product"] == p]
            hit = []
            for rt, groups in zip(sub.reported_target, sub.target_groups):
                gs = [x for x in groups.split(";") if x != "MREJ"]
                if "MREJ" in groups.split(";") and grp != "Staphylococcus aureus":
                    continue  # the MRSA call needs S. aureus; MREJ itself cannot be read from a gene list
                if any(tg.get(x) and target_applies(x, grp) for x in gs):
                    hit.append(rt)
            d[f"expected_positive::{p}"] = ";".join(hit)
        for dr in KEY_DRUGS:
            m, i = micd.get((a, dr), ("", ""))
            d[f"{dr.lower()}_mic"] = m
            d[f"{dr.lower()}_int"] = i
        # ---- hard cases (CDC posted interpretation)
        reasons = []
        if grp in SCOPE:
            for t in TARGET_ORDER:
                if not tg.get(t) or not target_applies(t, grp):
                    continue
                drugs = [x for x in TARGET_DRUGS[t] if not (x == "Imipenem" and grp == "Enterobacterales"
                                                             and r.organism.split(" ")[0] in MORGANELLACEAE)]
                ints = {x: micd.get((a, x), ("", ""))[1] for x in drugs}
                ints = {x: v for x, v in ints.items() if v in ("S", "I", "R", "SDD", "NS")}
                if not ints:
                    continue
                prim = next((x for x in drugs if x in ints), None)
                if all(v != "R" for v in ints.values()):
                    flags = [g2flag.get(g, "") for g in tg[t] if g2flag.get(g)]
                    reasons.append(dict(direction="target gene present, matching drug(s) not resistant",
                                        target=t, genes=";".join(tg[t]), drugs_checked=";".join(
                                            f"{x}={micd[(a, x)][0]} {v}" for x, v in ints.items()),
                                        primary_drug=prim, note="; ".join(sorted(set(flags)))))
            # resistant without any panel target of that class
            if grp in ("Enterobacterales", "Pseudomonas", "Acinetobacter"):
                cr = {x: micd.get((a, x), ("", "")) for x in ["Meropenem", "Imipenem", "Ertapenem", "Doripenem"]
                      if not (x == "Imipenem" and r.organism.split(" ")[0] in MORGANELLACEAE)}
                rdr = [x for x, (m, i) in cr.items() if i == "R"]
                if rdr and not any(tg.get(t) for t in CARBA_TARGETS):
                    other = [g for g in cats_by.get(a, {}).get("Beta-lactam", [])] + \
                            [f"porin: {g}" for g in cats_by.get(a, {}).get("Truncated Porin", [])]
                    reasons.append(dict(direction="carbapenem resistant, no panel carbapenemase target",
                                        target="(any carbapenemase target)", genes="",
                                        drugs_checked=";".join(f"{x}={cr[x][0]} R" for x in rdr),
                                        primary_drug=rdr[0], note="other CDC-listed mechanisms: " +
                                        (", ".join(other) if other else "none listed")))
            if grp == "Enterobacterales":
                er = {x: micd.get((a, x), ("", "")) for x in ["Ceftriaxone", "Cefotaxime", "Ceftazidime"]}
                rdr = [x for x, (m, i) in er.items() if i == "R"]
                if rdr and not tg.get("CTX-M") and not any(tg.get(t) for t in CARBA_TARGETS):
                    other = cats_by.get(a, {}).get("Beta-lactam", [])
                    reasons.append(dict(direction="3rd-generation cephalosporin resistant, no CTX-M or carbapenemase target",
                                        target="CTX-M", genes="",
                                        drugs_checked=";".join(f"{x}={er[x][0]} R" for x in rdr),
                                        primary_drug=rdr[0], note="other CDC-listed beta-lactamases: " +
                                        (", ".join(other) if other else "none listed")))
            if grp.startswith("Staphylococcus"):
                sr = {x: micd.get((a, x), ("", "")) for x in ["Oxacillin", "Cefoxitin"]}
                rdr = [x for x, (m, i) in sr.items() if i == "R"]
                if rdr and not tg.get("mecA") and not tg.get("mecC"):
                    reasons.append(dict(direction="oxacillin/cefoxitin resistant, no mecA or mecC",
                                        target="mecA/mecC", genes="", drugs_checked=";".join(
                                            f"{x}={sr[x][0]} R" for x in rdr), primary_drug=rdr[0],
                                        note="other CDC-listed beta-lactam genes: " + ", ".join(
                                            cats_by.get(a, {}).get("Beta-lactam", [])) if cats_by.get(a, {}).get(
                                            "Beta-lactam") else "none listed"))
            if grp == "Enterococcus":
                v = micd.get((a, "Vancomycin"), ("", ""))
                if v[1] == "R" and not tg.get("vanA") and not tg.get("vanB"):
                    vanc = any(g.lower().startswith("vanc") for g in genes_by.get(a, []))
                    reasons.append(dict(direction=("vancomycin resistant by intrinsic vanC, no vanA or vanB (panel negative is expected)"
                                                   if vanc else "vancomycin resistant, no vanA or vanB"),
                                        target="vanA/vanB",
                                        genes="", drugs_checked=f"Vancomycin={v[0]} R", primary_drug="Vancomycin",
                                        note="other CDC-listed genes: " + ", ".join(genes_by.get(a, []))))
        d["hard_case"] = bool(reasons)
        d["hard_case_types"] = " | ".join(sorted({x["direction"] for x in reasons}))
        d["isolate_url"] = r.isolate_url
        rows.append(d)
        for x in reasons:
            hard.append(dict(ar_bank_number=a, organism=r.organism, organism_group=grp, biosample=r.biosample,
                             bank_panels=r.panel_codes, **x, isolate_url=r.isolate_url))
    xw = pd.DataFrame(rows)
    xw.to_csv(os.path.join(PROC, "crosswalk_isolates.tsv"), sep="\t", index=False)
    hc = pd.DataFrame(hard)
    hc.to_csv(os.path.join(PROC, "hard_cases.csv"), index=False)

    # ---- panel x target grid
    pcode = {r.panel_page_id: (r.panel_code or r.panel_name) for r in panels.itertuples()}
    pname = {(r.panel_code or r.panel_name): r.panel_name for r in panels.itertuples()}
    plist = {(r.panel_code or r.panel_name): r.listed_on_all_panels_page for r in panels.itertuples()}
    grid = []
    for code in sorted(set(c for s in xw.bank_panels for c in s.split(";") if c)):
        sub = xw[xw.bank_panels.str.split(";").apply(lambda L: code in L)]
        row = dict(panel_code=code, panel_name=pname.get(code, code),
                   listed_on_all_panels_page=plist.get(code, ""), n_isolates=len(sub),
                   n_in_scope=int(sub.in_scope_for_panel_targets.sum()),
                   n_hard_cases=int(sub.hard_case.sum()))
        for t in TARGET_ORDER:
            row[t] = int((sub[t] != "").sum())
        row["organisms"] = "; ".join(f"{o} ({n})" for o, n in sub.organism.value_counts().items())
        grid.append(row)
    grid = pd.DataFrame(grid).sort_values(["n_in_scope", "n_isolates"], ascending=False)
    grid.to_csv(os.path.join(PROC, "panel_target_grid.csv"), index=False)

    # ---- product x reported target coverage
    cov = []
    for r in prod.itertuples():
        col = f"expected_positive::{r.product}"
        sub = xw[xw[col].str.split(";").apply(lambda L: r.reported_target in L)]
        cov.append(dict(product=r.product, fda_510k=r.fda_510k, reported_target=r.reported_target,
                        target_groups=r.target_groups, n_bank_isolates=len(sub),
                        n_bank_panels=len(set(c for s in sub.bank_panels for c in s.split(";") if c)),
                        bank_panels=";".join(sorted(set(c for s in sub.bank_panels for c in s.split(";") if c))),
                        n_species=sub.organism.nunique(),
                        n_hard_cases=int(sub.hard_case.sum()),
                        ar_bank_numbers=";".join(sub.ar_bank_number)))
    pd.DataFrame(cov).to_csv(os.path.join(PROC, "product_target_coverage.csv"), index=False)

    # ---- stats
    st = dict(refgene_db_version=refver, n_panels=len(panels),
              n_panels_listed=int((panels.listed_on_all_panels_page == "True").sum()),
              n_isolates=len(xw), n_with_biosample=int((xw.biosample != "").sum()),
              n_with_mechanism_list=int(xw.has_mechanism_list.sum()),
              n_in_scope=int(xw.in_scope_for_panel_targets.sum()),
              n_by_group=xw.organism_group.value_counts().to_dict(),
              n_in_scope_carrying_any_target=int((xw.in_scope_for_panel_targets & (xw.panel_targets_carried != "")).sum()),
              n_carrying=dict((t, int((xw[t] != "").sum())) for t in TARGET_ORDER),
              n_hard_cases=int(xw.hard_case.sum()),
              n_hard_by_type=hc.direction.value_counts().to_dict() if len(hc) else {},
              n_cdc_gene_names=len(gmap), n_cdc_gene_names_unmapped=int((gmap.ncbi_symbol == "").sum()),
              n_cdc_gene_names_with_target=int((gmap.target_group != "").sum()))
    old = json.load(open(os.path.join(ROOT, "paper", "stats.json"))) if os.path.exists(
        os.path.join(ROOT, "paper", "stats.json")) else {}
    old.update(dict(crosswalk=st))
    json.dump(old, open(os.path.join(ROOT, "paper", "stats.json"), "w"), indent=1)
    print(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()

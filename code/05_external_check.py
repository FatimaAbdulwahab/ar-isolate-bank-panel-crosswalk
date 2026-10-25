#!/usr/bin/env python3
"""
05_external_check.py - Test the Project 1 benchmark against the Isolate Bank's
posted reference results.

PLAIN-LANGUAGE NOTE: Project 1 measured, across U.S. clinical isolates, how
often a rapid panel target gene (found by NCBI's AMRFinderPlus) goes with a
resistant laboratory result. The Isolate Bank is an outside yardstick: CDC
tested every isolate by reference broth microdilution, the gold-standard
method. This script repeats Project 1's exact rules on the Bank isolates and
puts the two sets of numbers side by side. It runs three checks:
  A. Gene calls: does NCBI's AMRFinderPlus find the same panel targets that
     CDC lists for each Bank isolate?
  B. Gene versus reference result: with Project 1's breakpoints and rules,
     what are sensitivity, specificity, PPV and NPV in the Bank, and do they
     fall inside Project 1's 95% ranges?
  C. Same isolate, two labs: for Bank isolates that also appear in the
     Project 1 benchmark (with the submitting lab's own results), how often
     do the two S/I/R calls agree?
Isolates that are in both datasets are left out of check B, so B is a truly
independent test. Outputs go to data/processed/external_check_*.csv and
paper/stats.json. You do not need to open this file.
"""
import csv
import glob
import json
import math
import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
REF = os.path.join(ROOT, "reference")
NCBI = os.path.join(ROOT, "data", "raw", "ncbi")

# ---- Project 1 rules, copied unchanged from us-rapid-panel-amr-concordance v1.0 code/04_build.py
CARBA = ["meropenem", "imipenem", "ertapenem", "doripenem"]
CEPH3 = ["ceftriaxone", "cefotaxime", "ceftazidime"]
PLAN = {
    "mecA": ("Staphylococcus aureus", ["oxacillin", "cefoxitin"], "oxacillin or cefoxitin", "methicillin"),
    "mecC": ("Staphylococcus aureus", ["oxacillin", "cefoxitin"], "oxacillin or cefoxitin", "methicillin"),
    "vanA": ("Enterococcus", ["vancomycin"], None, "vancomycin"),
    "vanB": ("Enterococcus", ["vancomycin"], None, "vancomycin"),
    "KPC": ("Enterobacterales", CARBA, "any carbapenem", "carbapenem"),
    "NDM": ("Enterobacterales", CARBA, "any carbapenem", "carbapenem"),
    "OXA-48-like": ("Enterobacterales", CARBA, "any carbapenem", "carbapenem"),
    "VIM": ("Enterobacterales", CARBA, "any carbapenem", "carbapenem"),
    "IMP": ("Enterobacterales", CARBA, "any carbapenem", "carbapenem"),
    "CTX-M": ("Enterobacterales", CEPH3, "any of ceftriaxone, cefotaxime, ceftazidime",
              "extended-spectrum cephalosporin"),
}
CLASS_SETS = {
    "methicillin": ("mecA or mecC", ["mecA", "mecC"]),
    "vancomycin": ("vanA or vanB", ["vanA", "vanB"]),
    "carbapenem": ("any panel carbapenemase (KPC, NDM, OXA-48-like, VIM, IMP)", ["KPC", "NDM", "OXA-48-like", "VIM", "IMP"]),
}
STD_DILUTIONS = {0.002, 0.004, 0.008, 0.015, 0.016, 0.03, 0.03125, 0.06, 0.0625, 0.12, 0.125, 0.25, 0.5}


def organism_category(name):
    n = (name or "").lower()
    if n.startswith("staphylococcus aureus"):
        return "Staphylococcus aureus"
    if n.startswith("enterococcus faecalis"):
        return "Enterococcus faecalis"
    if n.startswith("enterococcus faecium"):
        return "Enterococcus faecium"
    if n.startswith("escherichia coli") or n.startswith("shigella"):
        return "Escherichia coli"
    if n.startswith(("klebsiella pneumoniae", "klebsiella quasipneumoniae", "klebsiella variicola",
                     "klebsiella quasivariicola", "klebsiella africana")):
        return "Klebsiella pneumoniae complex"
    if n.startswith(("klebsiella oxytoca", "klebsiella michiganensis", "klebsiella grimontii",
                     "klebsiella pasteurii", "klebsiella huaxiensis", "klebsiella spallanzanii")):
        return "Klebsiella oxytoca complex"
    if n.startswith("klebsiella aerogenes") or n.startswith("enterobacter aerogenes"):
        return "Klebsiella aerogenes"
    if n.startswith("enterobacter"):
        return "Enterobacter cloacae complex"
    if n.startswith("citrobacter"):
        return "Citrobacter freundii complex"
    if n.startswith("serratia"):
        return "Serratia spp."
    if n.startswith(("morganella", "providencia", "proteus")):
        return "Morganella / Providencia"
    if n.startswith("salmonella"):
        return "Salmonella enterica"
    if n.startswith("klebsiella"):
        return "Klebsiella, other"
    return "Other Enterobacterales"


def bp_group(org):
    if org == "Staphylococcus aureus":
        return "Staphylococcus_aureus"
    if org.startswith("Enterococcus"):
        return "Enterococcus"
    return "Enterobacterales"


def interpret_mic(sign, val, s_bp, r_bp, between):
    if val is None:
        return "NI"
    sign = {"=": "==", "": "=="}.get(sign, sign)
    if sign == "==":
        lo = hi = val
    elif sign == "<=":
        lo, hi = 0.0, val
    elif sign == "<":
        lo, hi = 0.0, val / 2.0
    elif sign == ">=":
        lo, hi = val, math.inf
    elif sign == ">":
        lo, hi = val * 2.0, math.inf
    else:
        return "NI"

    def cat(m):
        if m <= s_bp + 1e-9:
            return "S"
        if m >= r_bp - 1e-9:
            return "R"
        return "I" if between == "I" else "NI"
    a, b = cat(lo), cat(hi if hi != math.inf else 1e9)
    return a if a == b else "NI"


def wilson(k, n, z=1.959964):
    if n == 0:
        return (None, None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(p, 4), round(max(0, c - h), 6), round(min(1, c + h), 6))


def two_by_two(rows):
    tp = sum(1 for g, p in rows if g and p)
    fp = sum(1 for g, p in rows if g and not p)
    fn = sum(1 for g, p in rows if not g and p)
    tn = sum(1 for g, p in rows if not g and not p)
    out = {"n": len(rows), "gene_pos_R": tp, "gene_pos_notR": fp, "gene_neg_R": fn, "gene_neg_notR": tn}
    for name, k, n in [("ppv", tp, tp + fp), ("npv", tn, tn + fn), ("sensitivity", tp, tp + fn),
                       ("specificity", tn, tn + fp)]:
        p, lo, hi = wilson(k, n)
        out[name], out[name + "_lo95"], out[name + "_hi95"] = p, lo, hi
    out["categorical_agreement"] = round((tp + tn) / len(rows), 4) if rows else None
    return out


# ---- helpers for this project
def parse_mic(s):
    s = (s or "").strip().replace("≤", "<=").replace("≥", ">=").replace(" ", "")
    m = re.match(r"^(<=|>=|<|>|=)?(\d*\.?\d+)$", s)
    if not m:
        return None, None
    return (m.group(1) or "=="), float(m.group(2))


def load_breakpoints():
    bps = {}
    for d in csv.DictReader(open(os.path.join(REF, "breakpoints_from_project1.csv"))):
        if d["method"] != "MIC":
            continue
        bps[(d["bp_group"], d["drug"])] = (float(d["susceptible"].lstrip("<=>")),
                                           float(d["resistant"].lstrip("<=>")), d["non_resistant_category_between"])
    return bps


def load_p1_crosswalk():
    xw = {}
    for d in csv.DictReader(open(os.path.join(REF, "project1_gene_panel_crosswalk.csv"))):
        xw[d["amrfinder_symbol"]] = (d["panel_target"], d["match_flag"])
    return xw


def load_ncbi():
    frames = []
    for f in glob.glob(os.path.join(NCBI, "*.bank_rows.tsv")):
        d = pd.read_csv(f, sep="\t", dtype=str).fillna("")
        if len(d):
            d["pd_group"] = os.path.basename(f).split(".")[0]
            frames.append(d)
    if not frames:
        return pd.DataFrame(columns=["biosample_acc", "AMR_genotypes"])
    d = pd.concat(frames, ignore_index=True)
    d = d.sort_values("target_acc").drop_duplicates("biosample_acc", keep="last")
    return d


def main():
    xw = pd.read_csv(os.path.join(PROC, "crosswalk_isolates.tsv"), sep="\t", dtype=str).fillna("")
    mic = pd.read_csv(os.path.join(PROC, "bank_mic_long.tsv"), sep="\t", dtype=str).fillna("")
    ncbi = load_ncbi()
    p1xw = load_p1_crosswalk()
    bps = load_breakpoints()
    p1_bs = set(open(os.path.join(REF, "project1_benchmark_biosamples.txt")).read().split())
    p1tab = pd.read_csv(os.path.join(REF, "project1_concordance_table.csv"), dtype=str).fillna("")

    # scope: organisms Project 1 covers
    def p1_org(o):
        g = o.split(" ")[0]
        if o.startswith(("Staphylococcus aureus", "Enterococcus faecalis", "Enterococcus faecium")):
            return organism_category(o)
        from_crosswalk = xw.loc[xw.organism == o, "organism_group"]
        if len(from_crosswalk) and from_crosswalk.iloc[0] == "Enterobacterales":
            return organism_category(o)
        return ""
    xw["p1_organism"] = xw.organism.map(p1_org)
    sc = xw[(xw.p1_organism != "") & (xw.biosample != "")].copy()
    gen = dict(zip(ncbi.biosample_acc, ncbi.AMR_genotypes))
    sc["in_ncbi"] = sc.biosample.isin(gen)
    sc["in_project1_benchmark"] = sc.biosample.isin(p1_bs)
    ver_col = next((c for c in ["AMRFinderPlus_version", "amrfinder_version"] if c in ncbi.columns), None)

    targets = list(PLAN)
    for t in targets:
        sc[f"ncbi_{t}"] = False
        sc[f"ncbi_{t}_alleles"] = ""
    for i, r in sc.iterrows():
        toks = [x.strip().strip('"') for x in gen.get(r.biosample, "").split(",") if x.strip() and x != "NULL"]
        for t in targets:
            hits = [tok for tok in toks if p1xw.get(tok.split("=")[0], ("", ""))[0] == t]
            sc.at[i, f"ncbi_{t}"] = bool(hits)
            sc.at[i, f"ncbi_{t}_alleles"] = ";".join(hits)

    # ---- A. gene-call agreement (CDC list vs AMRFinderPlus)
    A, Adisc = [], []
    base = sc[sc.in_ncbi & (sc.has_mechanism_list == "True")]
    for t in targets:
        fam = PLAN[t][0]
        sub = base[base.p1_organism.map(lambda o: (o == fam) or (fam == "Enterococcus" and o.startswith("Enterococcus"))
                                         or (fam == "Enterobacterales" and not o.startswith(("Staph", "Enterococcus"))))]
        cdc = sub[t] != ""
        nc = sub[f"ncbi_{t}"].astype(bool)
        both, conly, nonly, neither = int((cdc & nc).sum()), int((cdc & ~nc).sum()), int((~cdc & nc).sum()), int((~cdc & ~nc).sum())
        n = len(sub)
        po = (both + neither) / n if n else None
        pe = (((both + conly) * (both + nonly)) + ((neither + nonly) * (neither + conly))) / (n * n) if n else None
        kappa = round((po - pe) / (1 - pe), 4) if n and pe is not None and pe < 1 else None
        A.append(dict(panel_target=t, organism_scope=fam, n_isolates=n, both=both, cdc_only=conly,
                      ncbi_only=nonly, neither=neither, percent_agreement=round(po, 4) if po is not None else None,
                      cohens_kappa=kappa))
        for _, r in sub[cdc != nc].iterrows():
            Adisc.append(dict(ar_bank_number=r.ar_bank_number, organism=r.organism, biosample=r.biosample,
                              panel_target=t, cdc_listed=r[t], amrfinderplus=r[f"ncbi_{t}_alleles"],
                              direction="CDC only" if r[t] else "AMRFinderPlus only", isolate_url=r.isolate_url))
    pd.DataFrame(A).to_csv(os.path.join(PROC, "external_check_A_gene_calls.csv"), index=False)
    pd.DataFrame(Adisc).to_csv(os.path.join(PROC, "external_check_A_discrepancies.csv"), index=False)

    # ---- reinterpret CDC MICs with Project 1 breakpoints
    mic["drug"] = mic.drug_cdc.str.lower().str.strip()
    mic = mic[mic.drug.isin(set(CARBA + CEPH3 + ["oxacillin", "cefoxitin", "vancomycin"]))]
    org_of = dict(zip(sc.ar_bank_number, sc.p1_organism))
    cat, qa = {}, []
    for r in mic.itertuples():
        if r.ar_bank_number not in org_of:
            continue
        org = org_of[r.ar_bank_number]
        bp = bps.get((bp_group(org), r.drug))
        if bp is None or (r.drug == "imipenem" and org == "Morganella / Providencia"):
            continue
        sign, val = parse_mic(r.mic_cdc)
        c = interpret_mic(sign, val, *bp) if val is not None else "NI"
        cat[(r.ar_bank_number, r.drug)] = c
        qa.append(dict(ar_bank_number=r.ar_bank_number, organism=org, drug=r.drug, mic_cdc=r.mic_cdc,
                       int_cdc=r.int_cdc, reinterpreted_project1=c,
                       agree=(c == r.int_cdc) if r.int_cdc in ("S", "I", "R") and c in ("S", "I", "R") else ""))
    qa = pd.DataFrame(qa)
    qa.to_csv(os.path.join(PROC, "external_check_reinterpretation.csv"), index=False)

    def pheno(a, drugs, comp):
        cs = [cat.get((a, d)) for d in drugs]
        cs = [c for c in cs if c in ("S", "I", "R")]
        if not cs:
            return None
        return any(c == "R" for c in cs)

    # ---- B. gene vs reference result, independent isolates only
    indep = sc[sc.in_ncbi & ~sc.in_project1_benchmark]
    analyses = []
    for t, (fam, drugs, comp, cls) in PLAN.items():
        for d in drugs:
            analyses.append((t, [t], fam, [d], d, "gene"))
        if comp:
            analyses.append((t, [t], fam, drugs, comp, "gene"))
    for cls, (label, tset) in CLASS_SETS.items():
        fam, drugs, comp, _ = PLAN[tset[0]]
        for d in drugs:
            analyses.append((label, tset, fam, [d], d, "class"))
        if comp:
            analyses.append((label, tset, fam, drugs, comp, "class"))
    pooled = {"Staphylococcus aureus": "Staphylococcus aureus", "Enterococcus": "Enterococcus faecalis + faecium",
              "Enterobacterales": "Enterobacterales (excluding Salmonella)"}
    B, members = [], []
    for tl, tset, fam, drugs, dl, level in analyses:
        if fam == "Staphylococcus aureus":
            sub = indep[indep.p1_organism == "Staphylococcus aureus"]
        elif fam == "Enterococcus":
            sub = indep[indep.p1_organism.str.startswith("Enterococcus")]
        else:
            sub = indep[~indep.p1_organism.str.startswith(("Staphylococcus", "Enterococcus")) &
                        (indep.p1_organism != "Salmonella enterica")]
        rows = []
        for r in sub.itertuples():
            p = pheno(r.ar_bank_number, drugs, dl)
            if p is None:
                continue
            g = any(sc.at[r.Index, f"ncbi_{x}"] for x in tset)
            rows.append((bool(g), p))
            if bool(g) != p:
                members.append(dict(ar_bank_number=r.ar_bank_number, organism=r.organism, panel_target=tl,
                                    drug=dl, amrfinderplus_target_detected=bool(g), reference_resistant=p,
                                    direction="gene detected, not resistant" if g else "gene not detected, resistant",
                                    mics="; ".join(f"{d}={dict(zip(mic[mic.ar_bank_number == r.ar_bank_number].drug, mic[mic.ar_bank_number == r.ar_bank_number].mic_cdc)).get(d, '')}" for d in drugs),
                                    isolate_url=r.isolate_url))
        if not rows:
            continue
        res = dict(panel_target=tl, drug=dl, organism=pooled[fam], level=level)
        res.update({f"bank_{k}": v for k, v in two_by_two(rows).items()})
        pm = p1tab[(p1tab.analysis_version == "main") & (p1tab.isolate_subset == "all U.S. human clinical isolates")
                   & (p1tab.panel_target == tl) & (p1tab.drug == dl) & (p1tab.organism == pooled[fam])]
        if len(pm):
            pr = pm.iloc[0]
            for k in ["n", "ppv", "ppv_lo95", "ppv_hi95", "npv", "npv_lo95", "npv_hi95", "sensitivity",
                      "sensitivity_lo95", "sensitivity_hi95", "specificity", "specificity_lo95", "specificity_hi95"]:
                res[f"project1_{k}"] = pr[k]
            for k in ["sensitivity", "specificity"]:
                bv, lo, hi = res[f"bank_{k}"], pr[f"{k}_lo95"], pr[f"{k}_hi95"]
                if bv is None or lo == "":
                    res[f"{k}_vs_project1"] = "not estimable"
                else:
                    blo, bhi = res[f"bank_{k}_lo95"], res[f"bank_{k}_hi95"]
                    overlap = not (bhi < float(lo) or blo > float(hi))
                    res[f"{k}_vs_project1"] = ("Bank estimate inside Project 1 95% range" if float(lo) <= bv <= float(hi)
                                               else "ranges overlap" if overlap else
                                               ("Bank lower, ranges do not overlap" if bv < float(lo)
                                                else "Bank higher, ranges do not overlap"))
        B.append(res)
    B = pd.DataFrame(B)
    B.to_csv(os.path.join(PROC, "external_check_B_concordance.csv"), index=False)
    pd.DataFrame(members).drop_duplicates().to_csv(os.path.join(PROC, "external_check_B_discordant_isolates.csv"), index=False)

    # ---- C. same isolate, two labs
    C = []
    p1long = os.path.join(REF, "project1_benchmark_isolate_drug_long.tsv")
    if os.path.exists(p1long):
        p1d = pd.read_csv(p1long, sep="\t", dtype=str).fillna("")
        ov = sc[sc.in_project1_benchmark]
        bs2a = dict(zip(ov.biosample, ov.ar_bank_number))
        p1d = p1d[p1d.biosample_acc.isin(bs2a)]
        for r in p1d.itertuples():
            a = bs2a[r.biosample_acc]
            c = cat.get((a, r.drug))
            if c in ("S", "I", "R") and r.final_category in ("S", "I", "R"):
                C.append(dict(ar_bank_number=a, biosample=r.biosample_acc, drug=r.drug,
                              project1_method=f"{r.method} {r.sign}{r.value} {r.units}".strip(),
                              project1_platform=r.platform, project1_category=r.final_category,
                              bank_mic=mic[(mic.ar_bank_number == a) & (mic.drug == r.drug)].mic_cdc.iloc[0]
                              if len(mic[(mic.ar_bank_number == a) & (mic.drug == r.drug)]) else "",
                              bank_category=c, agree=c == r.final_category,
                              major_or_very_major=(c == "R" and r.final_category == "S") or (c == "S" and r.final_category == "R")))
    C = pd.DataFrame(C)
    C.to_csv(os.path.join(PROC, "external_check_C_same_isolate.csv"), index=False)

    sc.drop(columns=[c for c in sc.columns if c.startswith("expected_positive::")]).to_csv(
        os.path.join(PROC, "external_check_isolates.tsv"), sep="\t", index=False)

    st = dict(
        n_bank_isolates_in_project1_organisms=int(len(sc)),
        n_with_ncbi_amrfinderplus=int(sc.in_ncbi.sum()),
        n_without_ncbi=int((~sc.in_ncbi).sum()),
        n_overlap_with_project1_benchmark=int(sc.in_project1_benchmark.sum()),
        n_independent_with_ncbi=int(len(indep)),
        amrfinderplus_versions=sorted(ncbi[ver_col].unique().tolist()) if ver_col else [],
        reinterpretation_agreement_with_cdc_int=round(float(qa[qa.agree != ""].agree.astype(bool).mean()), 4) if len(qa[qa.agree != ""]) else None,
        n_reinterpreted=int(len(qa)),
        n_reinterpretation_disagreements=int((qa.agree == False).sum()),
        gene_call_agreement={r["panel_target"]: dict(n=r["n_isolates"], both=r["both"], cdc_only=r["cdc_only"],
                                                     ncbi_only=r["ncbi_only"], kappa=r["cohens_kappa"])
                             for r in A},
        n_same_isolate_pairs=int(len(C)),
        same_isolate_agreement=round(float(C.agree.mean()), 4) if len(C) else None,
        same_isolate_major_or_very_major=int(C.major_or_very_major.sum()) if len(C) else 0,
    )
    if len(B):
        key = B[B.drug.isin(["meropenem", "oxacillin", "vancomycin", "ceftriaxone", "any carbapenem",
                             "oxacillin or cefoxitin"])]
        st["concordance_headline"] = key[["panel_target", "drug", "organism", "bank_n", "bank_sensitivity",
                                          "bank_specificity", "bank_ppv", "bank_npv"] +
                                         [c for c in ["sensitivity_vs_project1", "specificity_vs_project1"] if c in key]
                                         ].to_dict("records")
    s = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
    s["external_check"] = st
    json.dump(s, open(os.path.join(ROOT, "paper", "stats.json"), "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in st.items() if k != "concordance_headline"}, indent=1, default=str))


if __name__ == "__main__":
    main()

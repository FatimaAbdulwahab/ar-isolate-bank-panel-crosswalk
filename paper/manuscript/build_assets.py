#!/usr/bin/env python3
"""
build_assets.py - Write every number, table and figure the preprint uses.

PLAIN-LANGUAGE NOTE: The manuscript (preprint.tex) never contains a typed-in
result. It reads numbers.tex (one macro per number) and the tables/ and
figures/ folders, all written here from the verified pipeline outputs in
data/processed/, reference/ and paper/stats.json. Re-run this, then compile,
after any rebuild of the data. You do not need to open this file.

Usage: python3 paper/manuscript/build_assets.py
"""
import json
import math
import os
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import seaborn as sns

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROC = os.path.join(ROOT, "data", "processed")
REF = os.path.join(ROOT, "reference")
FIG = os.path.join(HERE, "figures")
TAB = os.path.join(HERE, "tables")
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)

S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
X, E = S["crosswalk"], S["external_check"]
xw = pd.read_csv(os.path.join(PROC, "crosswalk_isolates.tsv"), sep="\t", dtype=str).fillna("")
iso = pd.read_csv(os.path.join(PROC, "bank_isolates.tsv"), sep="\t", dtype=str).fillna("")
mic = pd.read_csv(os.path.join(PROC, "bank_mic_long.tsv"), sep="\t", dtype=str).fillna("")
hc = pd.read_csv(os.path.join(PROC, "hard_cases.csv"), dtype=str).fillna("")
grid = pd.read_csv(os.path.join(PROC, "panel_target_grid.csv"), dtype=str).fillna("")
cov = pd.read_csv(os.path.join(PROC, "product_target_coverage.csv"), dtype=str).fillna("")
prod = pd.read_csv(os.path.join(REF, "rapid_panel_targets.csv"), dtype=str).fillna("")
gmap = pd.read_csv(os.path.join(REF, "cdc_gene_to_target.csv"), dtype=str).fillna("")
A = pd.read_csv(os.path.join(PROC, "external_check_A_gene_calls.csv"))
Am = pd.read_csv(os.path.join(PROC, "external_check_A_by_cdc_method.csv"))
Ad = pd.read_csv(os.path.join(PROC, "external_check_A_discrepancies.csv"), dtype=str).fillna("")
B = pd.read_csv(os.path.join(PROC, "external_check_B_concordance.csv"))
C = pd.read_csv(os.path.join(PROC, "external_check_C_cdc_consistency.csv"), dtype=str).fillna("")
RI = pd.read_csv(os.path.join(PROC, "external_check_reinterpretation.csv"), dtype=str).fillna("")
EI = pd.read_csv(os.path.join(PROC, "external_check_isolates.tsv"), sep="\t", dtype=str).fillna("")
panels = pd.read_csv(os.path.join(PROC, "bank_panels.tsv"), sep="\t", dtype=str).fillna("")

# ----------------------------------------------------------------------------- style
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                                                         "#e87ba4", "#008300", "#6250d6", "#e34948")
GRAY = "#b9b8b2"
SEQ = ["#f4f8fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
sns.set_theme(context="paper", style="whitegrid", font="DejaVu Sans",
              rc={"axes.edgecolor": "#cfcec9", "grid.color": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                  "ytick.color": INK2, "axes.titlesize": 9, "axes.labelsize": 8.5, "xtick.labelsize": 7.5,
                  "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "axes.titleweight": "bold",
                  "axes.titlelocation": "left", "figure.dpi": 150, "savefig.dpi": 300,
                  "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})

TARGETS = ["mecA", "mecC", "vanA", "vanB", "KPC", "NDM", "OXA-48-like", "VIM", "IMP", "CTX-M",
           "OXA-23-like", "OXA-24/40-like", "OXA-58-like", "SME", "mcr-1", "mcr-2", "mcr-3"]
PRODUCT_SHORT = {
    "BIOFIRE Blood Culture Identification 2 (BCID2) Panel": "BioFire BCID2",
    "ePlex BCID-GP Panel": "ePlex BCID-GP",
    "ePlex BCID-GN Panel": "ePlex BCID-GN",
    "Verigene Gram-Positive Blood Culture Nucleic Acid Test (BC-GP)": "Verigene BC-GP",
    "Verigene Gram-Negative Blood Culture Nucleic Acid Test (BC-GN)": "Verigene BC-GN",
    "LIAISON PLEX Gram-Positive Blood Culture Assay": "LIAISON PLEX GP",
    "LIAISON PLEX Gram-Negative Blood Culture Assay": "LIAISON PLEX GN",
}
HB = X["n_hard_by_type"]
K_TGT = "target gene present, matching drug(s) not resistant"
K_CARB = "carbapenem resistant, no panel carbapenemase target"
K_PSA = ("carbapenem-resistant P. aeruginosa without a carbapenemase (chromosomal mechanisms; panel negative is "
         "expected)")
K_ESC = "3rd-generation cephalosporin resistant, no CTX-M or carbapenemase target"
K_OXA = "oxacillin/cefoxitin resistant, no mecA or mecC"
K_VANC = "vancomycin resistant by intrinsic vanC, no vanA or vanB (panel negative is expected)"


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)


def pct(v, d=1):
    return "--" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{100 * float(v):.{d}f}\\%"


def ci(lo, hi):
    if lo is None or (isinstance(lo, float) and math.isnan(lo)):
        return "--"
    return f"{100 * float(lo):.1f}--{100 * float(hi):.1f}"


def tex(s):
    s = str(s)
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"),
                 ("<=", r"$\le$"), (">=", r"$\ge$"), ("ß", r"$\beta$"), ("β", r"$\beta$"), ("–", "--")]:
        s = s.replace(a, b)
    s = re.sub(r"(?<!\$)>(?!\$)", r"$>$", s)
    s = re.sub(r"(?<![\$\\])<(?![\$=])", r"$<$", s)
    return s


def italic_species(s):
    return re.sub(r"\b(Staphylococcus aureus|Escherichia coli|Klebsiella pneumoniae|Enterobacter cloacae( complex)?|"
                  r"Klebsiella oxytoca|Proteus mirabilis|Pseudomonas aeruginosa|Enterococcus faecalis|"
                  r"Enterococcus faecium|Enterococcus gallinarum|Enterococcus casseliflavus|Serratia marcescens|"
                  r"Acinetobacter baumannii|Klebsiella aerogenes|Citrobacter freundii)\b",
                  lambda m: r"\textit{" + m.group(0).replace(" complex", "") + "}" +
                  (" complex" if m.group(0).endswith("complex") else ""), s)


N = {}


def nv(k, v):
    N[k] = v


def fmt_int(v):
    return f"{int(v):,}"


# ----------------------------------------------------------------------------- numbers: collection
nv("access-date", "24 October 2026")
nv("n-isolates", fmt_int(X["n_isolates"]))
nv("n-panels", X["n_panels"])
nv("n-panels-listed", X["n_panels_listed"])
nv("n-panels-linked", X["n_panels"] - X["n_panels_listed"])
nv("n-biosample", fmt_int(X["n_with_biosample"]))
nv("n-no-biosample", X["n_isolates"] - X["n_with_biosample"])
nv("n-mech", X["n_with_mechanism_list"])
nv("n-inscope", X["n_in_scope"])
nv("n-inscope-target", X["n_in_scope_carrying_any_target"])
nv("pct-inscope-target", pct(X["n_in_scope_carrying_any_target"] / X["n_in_scope"]))
nv("n-products", X["n_products"])
nv("n-510k", X["n_fda_510k"])
nv("refgene", X["refgene_db_version"])
nv("n-gene-names", X["n_cdc_gene_names"])
nv("n-gene-names-unmapped", X["n_cdc_gene_names_unmapped"])
nv("n-gene-names-mapped", X["n_cdc_gene_names"] - X["n_cdc_gene_names_unmapped"])
nv("n-gene-names-target", X["n_cdc_gene_names_with_target"])
nv("n-fox-disk", X["n_with_cefoxitin_disk"])
nv("n-mic-rows", fmt_int(len(mic)))
nv("n-gene-rows", fmt_int(len(pd.read_csv(os.path.join(PROC, "bank_mechanisms_long.tsv"), sep="\t", dtype=str))))
nv("n-provenance", fmt_int(sum(1 for _ in open(os.path.join(ROOT, "data", "raw", "PROVENANCE.txt")))))
nv("n-isolate-pages", fmt_int(len(iso)))
for g, k in [("Enterobacterales", "ent"), ("Pseudomonas", "psa"), ("Staphylococcus aureus", "sau"),
             ("Fungi", "fungi"), ("Neisseria", "neis"), ("Acinetobacter", "aci"), ("Enterococcus", "ent2"),
             ("Other bacteria", "oth"), ("Staphylococcus, other", "cons")]:
    nv(f"n-grp-{k}", X["n_by_group"].get(g, 0))
for t, v in X["n_carrying"].items():
    nv(f"n-carry-{t.lower().replace('/', '').replace('-like', 'like')}", v)
# number of panels and species carrying each target
for t in TARGETS:
    sub = xw[xw[t] != ""]
    nv(f"n-panels-{t.lower().replace('/', '').replace('-like', 'like')}",
       len(set(c for s in sub.bank_panels for c in s.split(";") if c)))
# multi-target isolates
xw["n_targets"] = xw.panel_targets_carried.map(lambda s: len([t for t in s.split(";") if t]))
insc = xw[xw.in_scope_for_panel_targets == "True"]
nv("n-multi-target", int((insc.n_targets >= 2).sum()))
nv("n-max-targets", int(insc.n_targets.max()))
# methods and CLSI editions
mg = X["n_by_cdc_gene_method"]
nv("n-meth-resfinder2016", mg.get("ResFinder (database of June 2016)", 0))
nv("n-meth-argannot2018", mg.get("ARG-ANNOT + ResFinder (2018-06-08)", 0))
nv("n-meth-resfinder3", mg.get("ResFinder 3.0", 0))
nv("n-meth-resgan", sum(v for k, v in mg.items() if k.startswith("ResGANNCBI")))
nv("n-meth-notstated", mg.get("method not stated", 0))
ed = X["int_standards"]
nv("n-clsi-2025", ed.get("CLSI 2025 M100 S35", 0))
nv("n-clsi-2026", ed.get("CLSI 2026 M100 Ed36", 0) + ed.get("CLSI 2026 M100 S36", 0))
nv("n-clsi-2024", ed.get("CLSI 2024 M100 S34", 0))
nv("n-clsi-2020", ed.get("CLSI 2020 M100 S30", 0))
nv("n-clsi-fungal", ed.get("CLSI M27 M44S ED3:2022", 0))
nv("n-clsi-m45", ed.get("M45 2016 S3", 0))
nv("n-no-int-std", int((iso.int_standard == "").sum()))
nv("n-fda-footnote", int((mic.footnote.str.contains("FDA break")).sum()))
nv("n-fda-footnote-isolates", mic[mic.footnote.str.contains("FDA break")].ar_bank_number.nunique())
# hard cases
nv("n-hard", X["n_hard_cases"])
nv("n-hard-tgt", HB.get(K_TGT, 0))
nv("n-hard-carb", HB.get(K_CARB, 0))
nv("n-hard-psa", HB.get(K_PSA, 0))
nv("n-hard-esc", HB.get(K_ESC, 0))
nv("n-hard-oxa", HB.get(K_OXA, 0))
nv("n-hard-vanc", HB.get(K_VANC, 0))
nv("n-hard-carb-total", HB.get(K_CARB, 0) + HB.get(K_PSA, 0))
nv("n-hard-informative", len(set(hc[~hc.direction.isin([K_PSA, K_VANC])].ar_bank_number)))
nv("n-expected-neg", len(set(hc[hc.direction.isin([K_PSA, K_VANC])].ar_bank_number)))
for t, v in X["n_gene_present_not_R_by_target"].items():
    nv(f"n-tgtnotr-{t.lower().replace('-like', 'like')}", v)
nv("n-dtd-disk-r", int(((xw.cefoxitin_disk_int == "R") & (xw.mecA != "")).sum()))
nv("n-dtd-disk-s", int(((xw.cefoxitin_disk_int == "S") & (xw.mecA != "")).sum()))
psa = xw[xw.organism.str.startswith("Pseudomonas aeruginosa")]
nv("n-psa", len(psa))
nv("n-psa-target", int((psa.panel_targets_carried != "").sum()))
# ----------------------------------------------------------------------------- numbers: external check
nv("n-p1org", E["n_bank_isolates_in_project1_organisms"])
nv("n-ncbi", E["n_with_ncbi_amrfinderplus"])
nv("n-no-ncbi", E["n_without_ncbi"])
nv("n-overlap", E["n_overlap_with_project1_benchmark"])
nv("n-overlap-cdc", E["n_overlap_submitted_by_cdc"])
nv("n-indep", E["n_independent_with_ncbi"])
nv("amrfinder-versions", ", ".join(E["amrfinderplus_versions"]))
nv("n-meth-incl", E["n_cdc_method_groups"].get("includes NCBI database", 0))
nv("n-meth-without", E["n_cdc_method_groups"].get("without NCBI database", 0))
nv("n-meth-ns", E["n_cdc_method_groups"].get("not stated", 0))
nv("reint-agree", pct(E["reinterpretation_agreement_with_cdc_int"]))
nv("n-reint", fmt_int(E["n_reinterpreted"]))
nv("n-reint-comp", fmt_int(E["n_reinterpreted_comparable"]))
nv("n-reint-dis", E["n_reinterpretation_disagreements"])
nv("n-cons-pairs", E["n_cdc_consistency_pairs"])
nv("cons-agree", pct(E["cdc_consistency_agreement"]))
nv("n-cons-dis", int((C.agree == "False").sum()))
nv("n-cons-major", E["cdc_consistency_major_or_very_major"])
ga = E["gene_call_agreement"]
for t, d in ga.items():
    k = t.lower().replace("-like", "like")
    nv(f"ga-{k}-n", d["n"]); nv(f"ga-{k}-both", d["both"]); nv(f"ga-{k}-cdconly", d["cdc_only"])
    nv(f"ga-{k}-ncbionly", d["ncbi_only"]); nv(f"ga-{k}-kappa", f"{d['kappa']:.2f}")
nv("ga-disagree-total", int(A.cdc_only.sum() + A.ncbi_only.sum()))
ind = Am[Am.cdc_method_group.str.contains("independent")]
nv("ga-ind-disagree", int(ind.cdc_only.sum() + ind.ncbi_only.sum()))
nv("ga-ind-pos", int(ind.both.sum()))
inc = Am[Am.cdc_method_group.str.contains("included")]
nv("ga-inc-disagree", int(inc.cdc_only.sum() + inc.ncbi_only.sum()))
nv("ga-inc-pos", int(inc.both.sum()))


def brow(t, d):
    r = B[(B.panel_target == t) & (B.drug == d)]
    return r.iloc[0] if len(r) else None


def frac(r, num, den):
    return f"{int(r[num])}/{int(sum(r[x] for x in den))}"


CARBCLASS = "any panel carbapenemase (KPC, NDM, OXA-48-like, VIM, IMP)"
for key, t, d in [("meca-ox", "mecA", "oxacillin"), ("meca-oxfox", "mecA", "oxacillin or cefoxitin"),
                  ("meca-fox", "mecA", "cefoxitin"),
                  ("vana", "vanA", "vancomycin"), ("vanb", "vanB", "vancomycin"), ("van", "vanA or vanB", "vancomycin"),
                  ("kpc-mero", "KPC", "meropenem"), ("kpc-any", "KPC", "any carbapenem"),
                  ("ndm-mero", "NDM", "meropenem"), ("ndm-any", "NDM", "any carbapenem"),
                  ("oxa-mero", "OXA-48-like", "meropenem"), ("oxa-any", "OXA-48-like", "any carbapenem"),
                  ("oxa-erta", "OXA-48-like", "ertapenem"),
                  ("vim-mero", "VIM", "meropenem"), ("imp-mero", "IMP", "meropenem"),
                  ("carb-mero", CARBCLASS, "meropenem"), ("carb-any", CARBCLASS, "any carbapenem"),
                  ("ctx-cro", "CTX-M", "ceftriaxone"), ("ctx-caz", "CTX-M", "ceftazidime"),
                  ("mec-class", "mecA or mecC", "oxacillin or cefoxitin")]:
    r = brow(t, d)
    if r is None:
        continue
    nv(f"b-{key}-n", int(r.bank_n))
    nv(f"b-{key}-ppv", pct(r.bank_ppv)); nv(f"b-{key}-ppv-ci", ci(r.bank_ppv_lo95, r.bank_ppv_hi95))
    nv(f"b-{key}-ppv-frac", frac(r, "bank_gene_pos_R", ["bank_gene_pos_R", "bank_gene_pos_notR"]))
    nv(f"b-{key}-sens", pct(r.bank_sensitivity)); nv(f"b-{key}-sens-ci", ci(r.bank_sensitivity_lo95, r.bank_sensitivity_hi95))
    nv(f"b-{key}-sens-frac", frac(r, "bank_gene_pos_R", ["bank_gene_pos_R", "bank_gene_neg_R"]))
    nv(f"b-{key}-spec", pct(r.bank_specificity)); nv(f"b-{key}-spec-ci", ci(r.bank_specificity_lo95, r.bank_specificity_hi95))
    nv(f"b-{key}-spec-frac", frac(r, "bank_gene_neg_notR", ["bank_gene_neg_notR", "bank_gene_pos_notR"]))
    nv(f"b-{key}-npv", pct(r.bank_npv))
    nv(f"b-{key}-genepos-notr", int(r.bank_gene_pos_notR))
    nv(f"b-{key}-geneneg-r", int(r.bank_gene_neg_R))
    for m in ["ppv", "sensitivity", "specificity", "npv"]:
        v = r.get(f"project1_{m}")
        nv(f"p1-{key}-{m}", pct(v) if pd.notna(v) else "--")
        lo, hi = r.get(f"project1_{m}_lo95"), r.get(f"project1_{m}_hi95")
        nv(f"p1-{key}-{m}-ci", ci(lo, hi) if pd.notna(lo) else "--")

# ----------------------------------------------------------------------------- mechanisms behind carbapenem R
hier = pd.read_csv(os.path.join(ROOT, "data", "raw", "ncbi", "ReferenceGeneHierarchy.txt"), sep="\t", dtype=str).fillna("")
parent = dict(zip(hier.node_id, hier.parent_node_id))
sym = dict(zip(gmap.gene_cdc, gmap.ncbi_symbol))
subc = dict(zip(gmap.gene_cdc, gmap.ncbi_subclass))
mech = pd.read_csv(os.path.join(PROC, "bank_mechanisms_long.tsv"), sep="\t", dtype=str).fillna("")


def in_family(s, fam):
    seen = set()
    while s and s not in seen:
        if s == fam:
            return True
        seen.add(s)
        s = parent.get(s, "")
    return False


def carb_mech(a, org):
    g = mech[mech.ar_bank_number == a]
    bl = g[g.category_cdc == "Beta-lactam"].gene_cdc.tolist()
    por = g[g.category_cdc == "Truncated Porin"].gene_cdc.tolist()
    noncarba = [x for x in bl if "CARBAPENEM" in subc.get(x, "") and not in_family(sym.get(x, ""), "blaOXA-51_fam")]
    oxa51 = [x for x in bl if in_family(sym.get(x, ""), "blaOXA-51_fam")]
    ceph = [x for x in bl if subc.get(x, "") == "CEPHALOSPORIN"]
    if noncarba:
        return "Carbapenemase not on any panel", ", ".join(noncarba)
    if org.startswith("Acinetobacter") and oxa51:
        return "Intrinsic OXA-51-like (Acinetobacter)", ", ".join(oxa51)
    if por and ceph:
        return "Porin truncation with ESBL or AmpC", ", ".join(ceph[:3] + por[:2])
    if ceph:
        return "ESBL or AmpC only", ", ".join(ceph[:3])
    if por:
        return "Porin truncation only", ", ".join(por[:2])
    return "No mechanism listed by CDC", ""


cm = hc[hc.direction == K_CARB].copy()
cm[["mech_class", "mech_genes"]] = [carb_mech(a, o) for a, o in zip(cm.ar_bank_number, cm.organism)]
cm.to_csv(os.path.join(TAB, "carb_nontarget_mechanisms.csv"), index=False)
mc = cm.mech_class.value_counts()
CMKEY = {"Carbapenemase not on any panel": "noncarba", "Intrinsic OXA-51-like (Acinetobacter)": "oxa51",
         "Porin truncation with ESBL or AmpC": "porinplus", "ESBL or AmpC only": "esblonly",
         "Porin truncation only": "porinonly", "No mechanism listed by CDC": "none"}
for k, v in mc.items():
    nv("cm-" + CMKEY[k], v)
nv("cm-noncarba-genes", ", ".join(sorted(set(", ".join(cm[cm.mech_class == "Carbapenemase not on any panel"]
                                                    .mech_genes).split(", ")) - {""})))

# ----------------------------------------------------------------------------- illustrative verification sets
listed = set(panels[panels.listed_on_all_panels_page == "True"].panel_code)
ver_rows = []
for p, short in PRODUCT_SHORT.items():
    col = f"expected_positive::{p}"
    rts = prod[prod["product"] == p].reported_target.tolist()
    pool = xw[(xw[col] != "") & xw.bank_panels.str.split(";").apply(lambda L: any(c in listed for c in L))].copy()
    pool["hits"] = pool[col].str.split(";")
    unc, chosen = set(rts), []
    while unc:
        pool["gain"] = pool.hits.apply(lambda h: len(unc & set(h)))
        cand = pool[pool.gain > 0]
        if cand.empty:
            break
        cand = cand.assign(hc=(cand.hard_case == "True").astype(int)).sort_values(
            ["gain", "hc", "ar_bank_number"], ascending=[False, True, True])
        r = cand.iloc[0]
        chosen.append((r.ar_bank_number, r.organism, sorted(unc & set(r.hits), key=rts.index)))
        unc -= set(r.hits)
    hard_pos = xw[(xw[col] != "") & (xw.hard_case_types.str.contains("target gene present"))]
    ver_rows.append(dict(product=short, n_targets=len(rts), n_isolates=len(chosen), chosen=chosen,
                         uncovered=sorted(unc), hard_pos=hard_pos.ar_bank_number.tolist()))
nv("ver-bcid2-n", [v for v in ver_rows if v["product"] == "BioFire BCID2"][0]["n_isolates"])
nv("ver-bcid2-t", [v for v in ver_rows if v["product"] == "BioFire BCID2"][0]["n_targets"])
nv("ver-liaisongn-n", [v for v in ver_rows if v["product"] == "LIAISON PLEX GN"][0]["n_isolates"])
nv("ver-liaisongn-t", [v for v in ver_rows if v["product"] == "LIAISON PLEX GN"][0]["n_targets"])
nv("ver-max", max(v["n_isolates"] for v in ver_rows))
nv("ver-min", min(v["n_isolates"] for v in ver_rows))
nv("ver-uncovered", sum(len(v["uncovered"]) for v in ver_rows))

# ============================================================================= TABLES
def write(name, body):
    open(os.path.join(TAB, name), "w").write(body)


# Table I: data sources
write("tab_sources.tex", r"""\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}p{0.27\linewidth}>{\raggedright\arraybackslash}X@{}}
\toprule
Source & Content used, version and terms \\
\midrule
CDC \& FDA AR Isolate Bank web site & All panel pages and """ + N["n-isolate-pages"] + r""" isolate pages (AR Bank number, species, BioSample, CDC gene list and calling method, reference broth microdilution MICs and S/I/R, page notes); accessed 24 Oct 2026; U.S.\ government work \\
FDA 510(k) decision summaries & """ + str(X["n_fda_510k"]) + r""" summaries for """ + str(X["n_products"]) + r""" cleared blood culture panels with resistance targets; U.S.\ government works \\
NCBI Pathogen Detection & AMRFinderPlus genotypes for Bank BioSamples (versions """ + N["amrfinder-versions"] + r"""), streamed from the latest analysis of each organism group; no restrictions on use \\
AMRFinderPlus Reference Gene Hierarchy & Database """ + X["refgene_db_version"] + r"""; gene-to-family tree used to assign targets \\
Project 1 benchmark v1.0.0 & Breakpoint table (CLSI M100-Ed35, checked against FDA STIC), gene-to-target crosswalk, concordance table and isolate list \\
\bottomrule
\end{tabularx}
""")

# Table II: panel targets by product
rows = []
for p, short in PRODUCT_SHORT.items():
    sub = prod[prod["product"] == p]
    k = sub.fda_510k.iloc[0].replace("(modified ", "; ").replace(")", "")
    rows.append(f"{short} & {k} & " + ", ".join(tex(t) for t in sub.reported_target) + r" \\")
write("tab_products.tex", r"""\begin{tabularx}{\linewidth}{@{}l>{\raggedright\arraybackslash}p{0.2\linewidth}>{\raggedright\arraybackslash}X@{}}
\toprule
Panel & FDA 510(k) & Resistance targets reported \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabularx}
""")

# Table III: collection by organism group
order = ["Enterobacterales", "Pseudomonas", "Acinetobacter", "Staphylococcus aureus", "Staphylococcus, other",
         "Enterococcus", "Neisseria", "Fungi", "Other bacteria"]
lab = {"Staphylococcus aureus": r"\textit{S.~aureus}", "Staphylococcus, other": "Other staphylococci",
       "Pseudomonas": r"\textit{Pseudomonas}", "Acinetobacter": r"\textit{Acinetobacter}",
       "Enterococcus": r"\textit{Enterococcus}", "Neisseria": r"\textit{Neisseria}"}
rows = []
for g in order:
    s = xw[xw.organism_group == g]
    rows.append(f"{lab.get(g, g)} & {len(s)} & {(s.biosample != '').sum()} & {(s.has_mechanism_list == 'True').sum()} & "
                f"{'yes' if g in ('Enterobacterales', 'Pseudomonas', 'Acinetobacter', 'Staphylococcus aureus', 'Staphylococcus, other', 'Enterococcus') else 'no'} & "
                f"{(s.panel_targets_carried != '').sum()} & {(s.hard_case == 'True').sum()} \\\\")
rows.append(r"\midrule")
rows.append(f"Total & {len(xw):,} & {(xw.biosample != '').sum()} & {(xw.has_mechanism_list == 'True').sum()} & "
            f"{X['n_in_scope']} & {(xw.panel_targets_carried != '').sum()} & {(xw.hard_case == 'True').sum()} \\\\")
write("tab_collection.tex", r"""\begin{tabular}{@{}lrrrcrr@{}}
\toprule
Organism group & Isolates & BioSample & Gene list & In scope & Target & Hard case \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
""")

# Table IV: targets
prod_by_group = {}
for r in prod.itertuples():
    for g in r.target_groups.split(";"):
        prod_by_group.setdefault(g, set()).add(PRODUCT_SHORT[r.product])
pabbr = {"BioFire BCID2": "B2", "ePlex BCID-GP": "eP", "ePlex BCID-GN": "eN", "Verigene BC-GP": "VP",
         "Verigene BC-GN": "VN", "LIAISON PLEX GP": "LP", "LIAISON PLEX GN": "LN"}
rows = []
for t in TARGETS:
    s = xw[xw[t] != ""]
    alle = sorted({a for v in s[t] for a in v.split(";") if a})
    shown = ", ".join(alle[:6]) + (f", +{len(alle) - 6} more" if len(alle) > 6 else "")
    rows.append(f"{tex(t)} & {len(s)} & {len(set(c for v in s.bank_panels for c in v.split(';') if c))} & "
                f"{s.organism.str.split().str[:2].str.join(' ').nunique()} & "
                f"{', '.join(pabbr[p] for p in PRODUCT_SHORT.values() if p in prod_by_group.get(t, set()))} & "
                f"{tex(shown)} \\\\")
write("tab_targets.tex", r"""\begin{tabularx}{\textwidth}{@{}lrrrl>{\raggedright\arraybackslash}X@{}}
\toprule
Target group & Isolates & Bank panels & Species & Panels reporting it$^{a}$ & CDC allele names (examples) \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\multicolumn{6}{@{}p{\textwidth}@{}}{\footnotesize $^{a}$B2, BioFire BCID2; eP/eN, ePlex BCID-GP/GN; VP/VN, Verigene BC-GP/GN; LP/LN, LIAISON PLEX Gram-Positive/Gram-Negative. OXA-143-like is reported by LIAISON PLEX GN but no Bank isolate carries it. The MRSA result of BCID2 additionally requires the SCC\textit{mec} right-extremity junction (MREJ), which a gene list cannot show.}\\
\end{tabularx}
""")

# Table V: verification sets
rows = []
for v in ver_rows:
    items = "; ".join(f"{a} ({', '.join(tex(x) for x in t)})" for a, _, t in v["chosen"])
    hp = ", ".join(v["hard_pos"][:8]) + (f", +{len(v['hard_pos']) - 8}" if len(v["hard_pos"]) > 8 else "")
    rows.append(f"{v['product']} & {v['n_targets']} & {v['n_isolates']} & {items} & {hp or '--'} \\\\")
write("tab_verification.tex", r"""\begin{tabularx}{\textwidth}{@{}lrr>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}p{0.2\textwidth}@{}}
\toprule
Panel & Targets & Isolates & Smallest covering set: AR Bank number (targets exercised) & Target present, drug not resistant (AR Bank) \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabularx}
""")

# Table VI: hard cases summary
hrows = [
    (r"Target gene present, matching drug(s) not resistant", HB.get(K_TGT, 0),
     ", ".join(f"{k} {v}" for k, v in X["n_gene_present_not_R_by_target"].items()), "Panel positive, AST not resistant"),
    (r"Carbapenem resistant, no panel carbapenemase (Enterobacterales, \textit{Acinetobacter})", HB.get(K_CARB, 0),
     "; ".join(f"{k} {v}" for k, v in mc.items()), "Panel negative, AST resistant"),
    (r"Third-generation cephalosporin resistant, no CTX-M or carbapenemase", HB.get(K_ESC, 0),
     "Other ESBL (SHV, TEM), plasmid or chromosomal AmpC", "CTX-M negative, AST resistant"),
    (r"Oxacillin or cefoxitin resistant, no \textit{mecA}/\textit{mecC}", HB.get(K_OXA, 0), "No mechanism listed",
     "Panel negative, AST resistant"),
    (r"Carbapenem-resistant \textit{P.~aeruginosa}, no carbapenemase", HB.get(K_PSA, 0),
     "Chromosomal (OprD, efflux, AmpC)", "Expected negative"),
    (r"Vancomycin resistant by intrinsic \textit{vanC}", HB.get(K_VANC, 0), r"\textit{E.~gallinarum}, \textit{E.~casseliflavus}",
     "Expected negative"),
]
write("tab_hardcases.tex", r"""\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{0.34\textwidth}r>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}p{0.17\textwidth}@{}}
\toprule
Category & Isolates & Breakdown & What a laboratory sees \\
\midrule
""" + "\n".join(f"{a} & {b} & {tex(c) if '$' not in c and 'textit' not in c else c} & {d} \\\\" for a, b, c, d in hrows) + r"""
\bottomrule
\end{tabularx}
""")

# Table VII: the gene-present-not-R isolates
g = hc[hc.direction == K_TGT].sort_values(["target", "ar_bank_number"])
rows = []
for r in g.itertuples():
    d = r.drugs_checked.replace(";", "; ")
    rows.append(f"{r.ar_bank_number} & {italic_species(tex(r.organism))} & {tex(r.target)} & {tex(r.genes)} & {tex(d)} \\\\")
write("tab_tgtnotr.tex", r"""\begin{tabularx}{\textwidth}{@{}llll>{\raggedright\arraybackslash}X@{}}
\toprule
AR Bank & Organism & Target & CDC gene & CDC reference results (MIC in mg/L or disk in mm, CDC S/I/R) \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabularx}
""")

# Table VIII: check A
rows = []
for r in A.itertuples():
    k = r.panel_target.lower().replace("-like", "like")
    i = Am[(Am.panel_target == r.panel_target) & Am.cdc_method_group.str.contains("independent")].iloc[0]
    rows.append(f"{tex(r.panel_target)} & {r.n_isolates} & {r.both} & {r.cdc_only} & {r.ncbi_only} & "
                f"{r.cohens_kappa:.2f} & {i.n_isolates} & {i.both} & {int(i.cdc_only + i.ncbi_only)} \\\\")
write("tab_checkA.tex", r"""\begin{tabular}{@{}lrrrrrrrr@{}}
\toprule
 & \multicolumn{5}{c}{All isolates with both calls} & \multicolumn{3}{c}{CDC method without NCBI database} \\
\cmidrule(lr){2-6}\cmidrule(l){7-9}
Target & $n$ & Both & CDC only & NCBI only & $\kappa$ & $n$ & Both & Disagree \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
""")

# Table IX: check B
keyrows = [("mecA", "oxacillin"), ("mecA", "cefoxitin"), ("mecA", "oxacillin or cefoxitin"), ("vanA", "vancomycin"),
           ("vanB", "vancomycin"), ("KPC", "meropenem"), ("KPC", "any carbapenem"), ("NDM", "meropenem"),
           ("NDM", "any carbapenem"), ("OXA-48-like", "meropenem"), ("OXA-48-like", "any carbapenem"),
           ("VIM", "meropenem"), ("IMP", "meropenem"), ("CTX-M", "ceftriaxone"), ("CTX-M", "ceftazidime"),
           ("mecA or mecC", "oxacillin or cefoxitin"), ("vanA or vanB", "vancomycin"), (CARBCLASS, "meropenem"),
           (CARBCLASS, "any carbapenem")]
rows = []
for t, d in keyrows:
    r = brow(t, d)
    if r is None:
        continue
    tl = "Any of 5 carbapenemases" if t == CARBCLASS else tex(t)
    p1 = lambda m: (pct(r[f'project1_{m}']) if pd.notna(r.get(f'project1_{m}')) else "--")
    rows.append(f"{tl} & {tex(d)} & {int(r.bank_n)} & {int(r.bank_gene_pos_R)}/{int(r.bank_gene_pos_R + r.bank_gene_pos_notR)} & "
                f"{pct(r.bank_ppv)} & {p1('ppv')} & {int(r.bank_gene_pos_R)}/{int(r.bank_gene_pos_R + r.bank_gene_neg_R)} & "
                f"{pct(r.bank_sensitivity)} & {p1('sensitivity')} & {pct(r.bank_specificity)} & {p1('specificity')} \\\\")
    if t == "CTX-M" and d == "ceftazidime":
        rows.append(r"\midrule")
write("tab_checkB.tex", r"""\begin{tabular}{@{}llrrrrrrrrr@{}}
\toprule
 & & & \multicolumn{3}{c}{PPV} & \multicolumn{3}{c}{Sensitivity} & \multicolumn{2}{c}{Specificity} \\
\cmidrule(lr){4-6}\cmidrule(lr){7-9}\cmidrule(l){10-11}
Target & Drug & $n$ & Bank & Bank & P1 & Bank & Bank & P1 & Bank & P1 \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
""")

# Table X: interpretation differences
rows = []
for r in RI[RI.agree == "False"].itertuples():
    rows.append(f"{r.ar_bank_number} & {italic_species(tex(r.organism))} & {tex(r.drug)} & {tex(r.mic_cdc)} & {r.int_cdc} & "
                f"{r.reinterpreted_project1} \\\\")
write("tab_reint.tex", r"""\begin{tabular}{@{}lllrcc@{}}
\toprule
AR Bank & Organism group & Drug & MIC & CDC & Project 1 rules \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
""")

# ============================================================================= FIGURES
# Fig 1: design schematic
fig, ax = plt.subplots(figsize=(7.1, 3.1))
ax.set_xlim(0, 104); ax.set_ylim(0, 42); ax.axis("off")


def box(x, y, w, h, title, body, col):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=col + "1f", ec=col, lw=1.1))
    ax.text(x + 1.2, y + h - 1.6, title, fontsize=6.9, fontweight="bold", color=INK, va="top")
    ax.text(x + 1.2, y + h - 5.4, body, fontsize=5.8, color=INK2, va="top", linespacing=1.35)


def arrow(x1, y1, x2, y2):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.0, shrinkA=2, shrinkB=2))


box(1, 28, 28, 13, "CDC & FDA AR Isolate Bank",
    f"{X['n_panels']} panels, {X['n_isolates']:,} isolate pages\nCDC gene lists, BioSample,\nreference BMD MICs and S/I/R", BLUE)
box(1, 14.5, 28, 11.5, "FDA decision summaries",
    f"{X['n_fda_510k']} 510(k) summaries,\n{X['n_products']} blood culture panels", ORANGE)
box(1, 1, 28, 11.5, "NCBI Pathogen Detection",
    f"AMRFinderPlus calls for\n{E['n_with_ncbi_amrfinderplus']} Bank genomes", AQUA)
box(36, 21, 31, 20, "Crosswalk",
    "CDC gene names \u2192 NCBI symbols\n\u2192 NCBI family tree \u2192 target group\n"
    "expected positives for each panel\nhard-case rules on CDC S/I/R", VIOLET)
box(36, 1, 31, 17, "External check of Project 1",
    "A. CDC vs AMRFinderPlus gene calls\nB. Project 1 rules on Bank BMD\nC. CDC NCBI deposit vs web page", MAGENTA)
box(74, 21, 29, 20, "Outputs (CC BY 4.0)",
    "isolate table\npanel \u00d7 target grid\npanel-target coverage\nhard cases, gene-name map\nQA report, provenance log", GREEN)
box(74, 1, 29, 17, "Project 1 benchmark",
    "breakpoints (CLSI M100-Ed35),\ngene-to-target crosswalk,\nU.S. concordance estimates", YELLOW)
arrow(29.5, 34.5, 35.5, 31); arrow(29.5, 20, 35.5, 27); arrow(29.5, 8, 35.5, 9.5); arrow(29.5, 31, 35.5, 12)
arrow(67.5, 31, 73.5, 31); arrow(73.5, 9.5, 67.5, 9.5)
save(fig, "fig1_design")

# Fig 2: collection composition
fig, axs = plt.subplots(1, 3, figsize=(7.1, 2.6), gridspec_kw={"width_ratios": [1.0, 1.0, 1.0], "wspace": 0.95})
oc = xw.groupby("organism_group").agg(total=("ar_bank_number", "size"),
                                      target=("panel_targets_carried", lambda s: (s != "").sum())).reindex(order)
oc["no target"] = oc.total - oc.target
lbl = [o.replace("Staphylococcus aureus", "S. aureus").replace("Staphylococcus, other", "Other staph.") for o in oc.index]
axs[0].barh(lbl, oc.target, color=BLUE, height=0.7, label="carries a panel target")
axs[0].barh(lbl, oc["no target"], left=oc.target, color=GRAY, height=0.7, label="no panel target")
axs[0].invert_yaxis(); axs[0].set_xlabel("Isolates"); axs[0].set_title("a  Organism groups\n ")
fig.legend(loc="lower left", bbox_to_anchor=(0.02, -0.1), ncol=2, frameon=False, fontsize=6.4)
axs[0].grid(axis="y", visible=False)
mo = pd.Series({"ResFinder 2016": mg.get("ResFinder (database of June 2016)", 0),
                "ARG-ANNOT+ResF. 2018": mg.get("ARG-ANNOT + ResFinder (2018-06-08)", 0),
                "ResFinder 3.0": mg.get("ResFinder 3.0", 0),
                "ResGANNCBI 2021": mg.get("ResGANNCBI incl. NCBI database (2021-05-07)", 0),
                "ResGANNCBI 2022": sum(v for k, v in mg.items() if "2022" in k),
                "Not stated": mg.get("method not stated", 0)})
axs[1].barh(mo.index, mo.values, color=[ORANGE, ORANGE, ORANGE, AQUA, AQUA, GRAY], height=0.7)
axs[1].invert_yaxis(); axs[1].set_xlabel("Isolates with a gene list"); axs[1].set_xlim(0, mo.max() * 1.3); axs[1].set_title("b  CDC gene-calling\n    method")
axs[1].grid(axis="y", visible=False)
for i, v in enumerate(mo.values):
    axs[1].text(v + 4, i, str(v), va="center", fontsize=6.3, color=INK2)
edl = pd.Series({"CLSI M100 2025": ed.get("CLSI 2025 M100 S35", 0),
                 "CLSI M100 2026": ed.get("CLSI 2026 M100 Ed36", 0) + ed.get("CLSI 2026 M100 S36", 0),
                 "CLSI M100 2024": ed.get("CLSI 2024 M100 S34", 0), "CLSI M100 2020": ed.get("CLSI 2020 M100 S30", 0),
                 "CLSI M27/M44S": ed.get("CLSI M27 M44S ED3:2022", 0), "CLSI M45 2016": ed.get("M45 2016 S3", 0),
                 "None stated": int((iso.int_standard == "").sum())})
axs[2].barh(edl.index, edl.values, color=[BLUE] * 4 + [GRAY] * 3, height=0.7)
axs[2].invert_yaxis(); axs[2].set_xlabel("Isolates"); axs[2].set_xlim(0, edl.max() * 1.3); axs[2].set_title("c  Interpretive standard\n    on the CDC page")
axs[2].grid(axis="y", visible=False)
for i, v in enumerate(edl.values):
    axs[2].text(v + 8, i, str(v), va="center", fontsize=6.3, color=INK2)
save(fig, "fig2_collection")

# Fig 3: heatmap
g3 = grid.copy()
for t in TARGETS + ["n_in_scope", "n_isolates"]:
    g3[t] = g3[t].astype(int)
g3 = g3[g3.n_in_scope > 0]
g3 = g3.assign(_o=g3[TARGETS].gt(0).dot(range(len(TARGETS), 0, -1))).sort_values(["_o", "n_isolates"],
                                                                                  ascending=[False, False])
def short_name(n, c):
    n = re.sub(r"\s*\((Custom)\)", " (custom)", n)
    n = re.sub(r"\s*\(([A-Za-z0-9\-]+)\)\s*$", "", n) if not n.endswith("(custom)") else n
    n = n.replace("Staphylococcus", "Staph.").replace("Enterobacterales", "Enterobact.")
    return (n[:44].rstrip() + "...") if len(n) > 46 else n
ylab = [f"{c}  {short_name(n, c)}  (n={k})" for n, c, k in zip(g3.panel_name, g3.panel_code, g3.n_isolates)]
mat = g3[TARGETS].values
fig, ax = plt.subplots(figsize=(7.1, 0.205 * len(g3) + 1.5))
cmap = matplotlib.colors.ListedColormap(SEQ)
norm = matplotlib.colors.BoundaryNorm([0, 0.5, 1.5, 3.5, 6.5, 10.5, 15.5, 22.5, 40], cmap.N)
sns.heatmap(mat, ax=ax, cmap=cmap, norm=norm, linewidths=0.8, linecolor="white", cbar=True,
            annot=np.where(mat > 0, mat.astype(str), ""), fmt="", annot_kws={"fontsize": 6.2},
            cbar_kws={"label": "Isolates carrying the target", "shrink": 0.5, "ticks": [1, 3, 6, 10, 15, 22, 30]},
            xticklabels=TARGETS, yticklabels=ylab)
for txt in ax.texts:
    if not txt.get_text():
        continue
    v = float(txt.get_text())
    txt.set_color("white" if v >= 11 else INK)
ax.xaxis.tick_top(); ax.set_xticklabels(TARGETS, rotation=50, ha="left", fontsize=7)
ax.set_yticklabels(ylab, fontsize=6.6); ax.tick_params(length=0)
ax.set_xlabel(""); ax.set_ylabel("")
save(fig, "fig3_heatmap")

# Fig 4: product x target coverage, as a matrix of target groups by panel
TG4 = ["mecA", "mecC", "vanA", "vanB", "KPC", "NDM", "OXA-48-like", "VIM", "IMP", "CTX-M", "OXA-23-like",
       "OXA-24/40-like", "OXA-58-like", "OXA-143-like", "SME", "mcr-1", "mcr-2", "mcr-3"]
cols4 = list(PRODUCT_SHORT.values())
M = np.full((len(TG4), len(cols4)), np.nan)
for r in prod.itertuples():
    c = cols4.index(PRODUCT_SHORT[r.product])
    for gname in r.target_groups.split(";"):
        if gname in TG4:
            M[TG4.index(gname), c] = int((xw[gname] != "").sum()) if gname in xw.columns else 0
fig, ax = plt.subplots(figsize=(7.1, 3.35))
cmap4 = matplotlib.colors.ListedColormap(SEQ[1:])
norm4 = matplotlib.colors.BoundaryNorm([0, 0.5, 2.5, 9.5, 20.5, 40.5, 80.5, 200], cmap4.N)
ann = np.where(np.isnan(M), "", np.where(M == 0, "0", np.nan_to_num(M).astype(int).astype(str)))
sns.heatmap(np.ma.masked_invalid(M).T, ax=ax, cmap=cmap4, norm=norm4, linewidths=1.2, linecolor="white",
            annot=ann.T, fmt="", annot_kws={"fontsize": 7}, cbar_kws={"label": "Bank isolates carrying the target",
                                                                        "shrink": 0.7, "ticks": [1, 5, 15, 30, 60, 120]},
            xticklabels=TG4, yticklabels=cols4)
ax.set_facecolor("#f1f0ec"); ax.grid(False)
for txt in ax.texts:
    t = txt.get_text()
    if t:
        v = float(t)
        txt.set_color("white" if v >= 41 else (RED if v == 0 else INK))
ax.xaxis.tick_top(); ax.set_xticklabels(TG4, rotation=45, ha="left", fontsize=7)
ax.set_yticklabels(cols4, fontsize=7.2, rotation=0); ax.tick_params(length=0)
for k, col in enumerate(cols4):
    ax.text(len(TG4) + 0.2, k + 0.5, "", va="center")
save(fig, "fig4_products")

# Fig 5: meropenem MIC by carbapenemase target, Enterobacterales
def mic_val(s):
    m = re.match(r"^(<=|>=|<|>)?\s*([\d.]+)$", s.strip())
    if not m:
        return None, None
    return m.group(1) or "=", float(m.group(2))
ent = xw[(xw.organism_group == "Enterobacterales")].copy()
ent = ent[ent.meropenem_mic != ""]
def carb_label(r):
    ts = [t for t in ["KPC", "NDM", "OXA-48-like", "VIM", "IMP", "SME"] if r[t] != ""]
    if len(ts) > 1:
        return "Two or more"
    return ts[0] if ts else "None of the targets"
ent["group"] = ent.apply(carb_label, axis=1)
ent["sign"], ent["val"] = zip(*ent.meropenem_mic.map(mic_val))
levels = [0.06, 0.12, 0.25, 0.5, 1, 2, 4, 8, 16]
def bin_of(sign, v):
    if v is None:
        return None
    if sign in (">", ">="):
        return 16
    return min(levels, key=lambda L: abs(math.log2(L) - math.log2(v)))
ent["bin"] = [bin_of(s, v) for s, v in zip(ent.sign, ent.val)]
grp_order = ["KPC", "NDM", "OXA-48-like", "VIM", "IMP", "SME", "Two or more", "None of the targets"]
fig, axs = plt.subplots(2, 4, figsize=(7.1, 3.2), sharex=True)
for ax, gname in zip(axs.flat, grp_order):
    s = ent[ent.group == gname]
    cnt = s["bin"].value_counts().reindex(levels, fill_value=0)
    cols = [AQUA if L <= 1 else (YELLOW if L == 2 else RED) for L in levels]
    ax.bar(range(len(levels)), cnt.values, color=cols, width=0.78)
    ax.set_title(f"{gname}  (n={len(s)})", fontsize=7.4)
    ax.grid(axis="x", visible=False)
    ax.axvline(4.5, color=INK2, lw=0.6, ls=":"); ax.axvline(5.5, color=INK2, lw=0.6, ls=":")
for ax in axs[1]:
    ax.set_xticks(range(len(levels)))
    ax.set_xticklabels(["≤0.06", "0.12", "0.25", "0.5", "1", "2", "4", "8", "≥16"], rotation=60, fontsize=6.2)
    ax.set_xlabel("Meropenem MIC (mg/L)", fontsize=7)
for ax in axs[:, 0]:
    ax.set_ylabel("Isolates", fontsize=7)
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (AQUA, YELLOW, RED)]
fig.legend(handles, ["S (≤1)", "I (2)", "R (≥4)"], loc="upper right", ncol=3, frameon=False, fontsize=6.6,
           bbox_to_anchor=(0.99, 1.04))
fig.tight_layout()
save(fig, "fig5_meropenem")
nv("n-ent-mero", len(ent))
for gname in grp_order:
    s = ent[ent.group == gname]
    k = re.sub(r"[^a-z0-9]", "", gname.lower())[:10]
    nv(f"mero-{k}-n", len(s))
    nv(f"mero-{k}-notr", int((s["bin"] < 4).sum()))
    nv(f"mero-{k}-s", int((s["bin"] <= 1).sum()))

# Fig 6: hard cases
fig, axs = plt.subplots(1, 2, figsize=(7.1, 2.75), gridspec_kw={"width_ratios": [1.05, 1.0], "wspace": 1.15})
cats = [("Target present,\ndrug not resistant", HB.get(K_TGT, 0), ORANGE),
        ("Carbapenem R, no panel\ncarbapenemase", HB.get(K_CARB, 0), RED),
        ("3GC R, no CTX-M or\ncarbapenemase", HB.get(K_ESC, 0), YELLOW),
        ("Oxacillin/cefoxitin R,\nno mecA/mecC", HB.get(K_OXA, 0), VIOLET),
        ("Carbapenem-R P. aeruginosa,\nno carbapenemase (expected)", HB.get(K_PSA, 0), GRAY),
        ("Vancomycin R, intrinsic\nvanC (expected)", HB.get(K_VANC, 0), GRAY)]
axs[0].barh([c[0] for c in cats], [c[1] for c in cats], color=[c[2] for c in cats], height=0.68)
axs[0].invert_yaxis(); axs[0].set_xlabel("Isolates"); axs[0].set_title("a  Hard-case categories")
axs[0].tick_params(axis="y", labelsize=6.4); axs[0].grid(axis="y", visible=False)
for i, c in enumerate(cats):
    axs[0].text(c[1] + 1, i, str(c[1]), va="center", fontsize=6.4, color=INK2)
mcs = mc.reindex(["Carbapenemase not on any panel", "Intrinsic OXA-51-like (Acinetobacter)",
                  "Porin truncation with ESBL or AmpC", "ESBL or AmpC only", "Porin truncation only",
                  "No mechanism listed by CDC"]).fillna(0).astype(int)
axs[1].barh([m.replace(" (Acinetobacter)", "\n(Acinetobacter)").replace(" with ", "\nwith ") for m in mcs.index],
            mcs.values, color=[RED, VIOLET, BLUE, AQUA, YELLOW, GRAY], height=0.68)
axs[1].invert_yaxis(); axs[1].set_xlabel("Isolates")
axs[1].set_title(f"b  Mechanisms CDC lists in the {HB.get(K_CARB, 0)}\n    carbapenem-R isolates without a target")
axs[1].tick_params(axis="y", labelsize=6.4); axs[1].grid(axis="y", visible=False)
for i, v in enumerate(mcs.values):
    axs[1].text(v + 0.3, i, str(v), va="center", fontsize=6.4, color=INK2)
save(fig, "fig6_hardcases")

# Fig 7: check A
a7 = A.copy()
fig, axs = plt.subplots(1, 2, figsize=(7.1, 2.4), gridspec_kw={"width_ratios": [1.7, 1.0], "wspace": 0.45})
xs = np.arange(len(a7))
axs[0].bar(xs, a7.both, color=BLUE, width=0.62, label="both find it")
axs[0].bar(xs, a7.cdc_only, bottom=a7.both, color=ORANGE, width=0.62, label="CDC only")
axs[0].bar(xs, a7.ncbi_only, bottom=a7.both + a7.cdc_only, color=AQUA, width=0.62, label="AMRFinderPlus only")
axs[0].set_xticks(xs)
axs[0].set_xticklabels([f"{t}  κ={k:.2f}" for t, k in zip(a7.panel_target, a7.cohens_kappa)], fontsize=6.0,
                       rotation=40, ha="right", rotation_mode="anchor")
axs[0].set_ylabel("Isolates with the target"); axs[0].set_title("a  Target calls, CDC vs NCBI AMRFinderPlus")
axs[0].legend(frameon=False, fontsize=6.2, loc="upper left"); axs[0].grid(axis="x", visible=False)
axs[0].set_ylim(0, a7[["both", "cdc_only", "ncbi_only"]].sum(axis=1).max() * 1.18)
mm = Am.groupby("cdc_method_group")[["both", "cdc_only", "ncbi_only"]].sum()
mm = mm.reindex(["CDC method without NCBI database (independent)", "CDC method included NCBI database",
                 "CDC method not stated"])
lab7 = ["Independent", "Used NCBI\ndatabase", "Not stated"]
axs[1].barh(lab7, mm.both, color=BLUE, height=0.6)
axs[1].barh(lab7, mm.cdc_only + mm.ncbi_only, left=mm.both, color=RED, height=0.6)
for i, (b, d) in enumerate(zip(mm.both, mm.cdc_only + mm.ncbi_only)):
    axs[1].text(b + d + 4, i, f"{d} of {b + d} differ", va="center", fontsize=6.2, color=INK2)
axs[1].invert_yaxis(); axs[1].set_xlim(0, mm.both.max() * 1.55)
axs[1].set_xlabel("Target-positive calls (all targets)"); axs[1].set_title("b  By CDC calling method")
axs[1].grid(axis="y", visible=False)
save(fig, "fig7_checkA")

# Fig 8: check B forest
rows8 = [("mecA", "oxacillin or cefoxitin", "mecA | oxacillin or cefoxitin"), ("vanA", "vancomycin", "vanA | vancomycin"),
         ("vanB", "vancomycin", "vanB | vancomycin"), ("KPC", "meropenem", "KPC | meropenem"),
         ("KPC", "any carbapenem", "KPC | any carbapenem"), ("NDM", "meropenem", "NDM | meropenem"),
         ("OXA-48-like", "meropenem", "OXA-48-like | meropenem"), ("OXA-48-like", "any carbapenem", "OXA-48-like | any carbapenem"),
         ("VIM", "meropenem", "VIM | meropenem"), ("IMP", "meropenem", "IMP | meropenem"),
         ("CTX-M", "ceftriaxone", "CTX-M | ceftriaxone"), ("CTX-M", "ceftazidime", "CTX-M | ceftazidime")]
rows8b = [("mecA or mecC", "oxacillin or cefoxitin", "mecA or mecC | oxacillin or cefoxitin"),
          ("vanA or vanB", "vancomycin", "vanA or vanB | vancomycin"),
          (CARBCLASS, "meropenem", "any of 5 carbapenemases | meropenem"),
          (CARBCLASS, "any carbapenem", "any of 5 carbapenemases | any carbapenem"),
          ("CTX-M", "ceftriaxone", "CTX-M | ceftriaxone")]
fig, axs = plt.subplots(2, 1, figsize=(6.2, 5.0), gridspec_kw={"height_ratios": [len(rows8), len(rows8b)], "hspace": 0.4})
for ax, rr, m, title, (nk1, nk2) in [(axs[0], rows8, "ppv", "a  Gene present: share resistant (PPV)",
                                      ("bank_gene_pos_R", "bank_gene_pos_notR")),
                                     (axs[1], rows8b, "sensitivity", "b  Resistant: share with a target (sensitivity)",
                                      ("bank_gene_pos_R", "bank_gene_neg_R"))]:
    labels = []
    for i, (t, d, l) in enumerate(rr):
        r = brow(t, d)
        labels.append(f"{l} ({int(r[nk1] + r[nk2])})")
        for off, src, col in [(-0.17, "project1", ORANGE), (0.17, "bank", BLUE)]:
            v, lo, hi = r.get(f"{src}_{m}"), r.get(f"{src}_{m}_lo95"), r.get(f"{src}_{m}_hi95")
            if pd.isna(v):
                continue
            ax.plot([lo, hi], [i + off, i + off], color=col, lw=1.6, solid_capstyle="round")
            ax.plot(v, i + off, "o", color=col, ms=4.6, mec="white", mew=0.9)
    ax.set_yticks(range(len(rr))); ax.set_yticklabels(labels, fontsize=6.6); ax.invert_yaxis()
    ax.set_xlim(-0.02, 1.02); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0", "25", "50", "75", "100%"])
    ax.set_title(title, fontsize=7.8); ax.grid(axis="y", visible=False)
axs[0].plot([], [], "o-", color=ORANGE, label="Project 1 (U.S. clinical)")
axs[0].plot([], [], "o-", color=BLUE, label="Isolate Bank (CDC BMD)")
axs[1].legend(*axs[0].get_legend_handles_labels(), loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2,
              frameon=False, fontsize=7)
save(fig, "fig8_checkB")

# ----------------------------------------------------------------------------- write numbers.tex
with open(os.path.join(HERE, "numbers.tex"), "w") as f:
    f.write("% Auto-generated by build_assets.py from paper/stats.json and data/processed. Do not edit.\n\\makeatletter\n")
    for k in sorted(N):
        f.write(f"\\expandafter\\def\\csname nv@{k}\\endcsname{{{N[k]}}}\n")
    f.write("\\makeatother\n")
json.dump(N, open(os.path.join(HERE, "numbers.json"), "w"), indent=1, default=str)
print(f"{len(N)} numbers, tables and figures written")

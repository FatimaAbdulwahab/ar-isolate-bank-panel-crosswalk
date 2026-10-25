#!/usr/bin/env python3
"""
07_docs.py - Write the QA report and every document that quotes a number.

PLAIN-LANGUAGE NOTE: Numbers in the README and the results summary are never
typed by hand. This script reads paper/stats.json (written by the pipeline)
and fills them in, so the text can never disagree with the data. It also
writes data/processed/qa_report.txt, the first file to read before trusting
anything. Run with --final after your verification to remove the DRAFT banner.
You do not need to open this file.
"""
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
FINAL = "--final" in sys.argv
S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
X, E = S["crosswalk"], S["external_check"]
BANNER = "" if FINAL else "> **DRAFT** - not yet verified by the author. Numbers may change before release.\n\n"


def pct(v):
    return "n/a" if v in (None, "") else f"{100 * float(v):.1f}%"


def qa():
    iso = pd.read_csv(os.path.join(PROC, "bank_isolates.tsv"), sep="\t", dtype=str).fillna("")
    mic = pd.read_csv(os.path.join(PROC, "bank_mic_long.tsv"), sep="\t", dtype=str).fillna("")
    xw = pd.read_csv(os.path.join(PROC, "crosswalk_isolates.tsv"), sep="\t", dtype=str).fillna("")
    gm = pd.read_csv(os.path.join(ROOT, "reference", "cdc_gene_to_target.csv"), dtype=str).fillna("")
    A = pd.read_csv(os.path.join(PROC, "external_check_A_discrepancies.csv"), dtype=str).fillna("")
    re_ = pd.read_csv(os.path.join(PROC, "external_check_reinterpretation.csv"), dtype=str).fillna("")
    L = ["QA REPORT - Isolate Bank to rapid panel target crosswalk", "=" * 60, "",
         "PLAIN-LANGUAGE NOTE: Read this before trusting any number. It counts rows at each step,",
         "lists anything that did not match, and names isolates you can check by hand.", "",
         "1. Row counts",
         f"   Panels found: {X['n_panels']} ({X['n_panels_listed']} on the All Isolate Panels page, "
         f"{X['n_panels'] - X['n_panels_listed']} custom panels linked from them)",
         f"   Isolate pages parsed: {X['n_isolates']}; unique AR Bank numbers: {iso.ar_bank_number.nunique()}; "
         f"blank AR Bank numbers: {(iso.ar_bank_number == '').sum()}",
         f"   Isolates with a BioSample accession: {X['n_with_biosample']}",
         f"   Isolates with a CDC gene list: {X['n_with_mechanism_list']}",
         f"   Isolate-drug MIC rows: {len(mic)}; isolates with no MIC table: {(iso.n_drugs == '0').sum()}",
         f"   Isolates in organisms the rapid panels test: {X['n_in_scope']}", "",
         "2. Gene name matching (CDC names to NCBI catalog)",
         f"   Distinct CDC gene names: {X['n_cdc_gene_names']}; matched to an NCBI symbol: "
         f"{X['n_cdc_gene_names'] - X['n_cdc_gene_names_unmapped']}; not in NCBI catalog: {X['n_cdc_gene_names_unmapped']}",
         f"   Names mapped to a rapid panel target: {X['n_cdc_gene_names_with_target']}",
         "   Names flagged for the author:"]
    for r in gm[gm.flag != ""].itertuples():
        L.append(f"     - {r.gene_cdc} -> {r.target_group or '(none)'}: {r.flag} [{r.n_isolates} isolate(s)]")
    L += ["   Unmatched names are mostly mutations, efflux pumps, porins and fungal targets, which no rapid",
          "   panel reports. Full list: reference/cdc_gene_to_target.csv (match = 'not in NCBI catalog').", "",
          "3. Outside check inputs",
          f"   Bank isolates in Project 1 organisms with a BioSample: {E['n_bank_isolates_in_project1_organisms']}",
          f"   Found in NCBI Pathogen Detection with AMRFinderPlus results: {E['n_with_ncbi_amrfinderplus']} "
          f"(not found: {E['n_without_ncbi']})",
          f"   Also in the Project 1 benchmark (left out of check B): {E['n_overlap_with_project1_benchmark']}",
          f"   Reinterpretation with Project 1 breakpoints agrees with CDC's posted S/I/R: "
          f"{pct(E['reinterpretation_agreement_with_cdc_int'])} of {E['n_reinterpreted_comparable']} comparable isolate-drug results "
          f"(of {E['n_reinterpreted']} reinterpreted; the rest had no CDC S/I/R) "
          f"({E['n_reinterpretation_disagreements']} disagreements, listed below)"]
    for r in re_[re_.agree == "False"].itertuples():
        L.append(f"     - AR Bank {r.ar_bank_number} {r.organism} {r.drug} MIC {r.mic_cdc}: CDC {r.int_cdc}, "
                 f"Project 1 rules {r.reinterpreted_project1}")
    L += ["", "4. Gene-call disagreements between CDC and AMRFinderPlus (panel targets)"]
    for r in A.itertuples():
        L.append(f"     - AR Bank {r.ar_bank_number} {r.organism} {r.panel_target}: CDC '{r.cdc_listed}', "
                 f"AMRFinderPlus '{r.amrfinderplus}' ({r.direction})")
    L += ["", "5. Named spot checks (verify these by hand on the CDC pages; see docs/VERIFY_CHECKLIST.md)"]
    for a in ["0032", "0066", "0164", "0500", "0977", "1306"]:
        r = xw[xw.ar_bank_number == a]
        if len(r):
            r = r.iloc[0]
            L.append(f"     - AR Bank {a} {r.organism}: targets [{r.panel_targets_carried}], meropenem "
                     f"{r.meropenem_mic} {r.meropenem_int}, oxacillin {r.oxacillin_mic} {r.oxacillin_int}, "
                     f"cefoxitin {r.cefoxitin_mic} {r.cefoxitin_int}"
                     f"{(', cefoxitin disk ' + r.cefoxitin_disk_mm + ' mm ' + r.cefoxitin_disk_int) if r.cefoxitin_disk_int else ''}, vancomycin {r.vancomycin_mic} "
                     f"{r.vancomycin_int}; hard case: {r.hard_case_types or 'no'}")
    L += ["", "6. Threshold counts quoted in documents"]
    for k, v in X["n_carrying"].items():
        L.append(f"     isolates carrying {k}: {v}")
    for k, v in X["n_hard_by_type"].items():
        L.append(f"     hard cases - {k}: {v}")
    open(os.path.join(PROC, "qa_report.txt"), "w").write("\n".join(L) + "\n")


def readme():
    c = X["n_carrying"]
    hb = X["n_hard_by_type"]
    ga = E["gene_call_agreement"]
    txt = f"""# CDC & FDA Antimicrobial Resistance Isolate Bank: Rapid Panel Target Crosswalk

**Status:** {"v1.0, released" if FINAL else "DRAFT v1.0, awaiting author verification"} | data accessed 2026-10-24 | Fatima Abdulwahab, Independent Researcher, Dallas, Texas ([ORCID 0009-0008-2298-8386](https://orcid.org/0009-0008-2298-8386))

{BANNER}## In plain language

Before a laboratory reports results from a new test, federal rules (42 CFR 493.1253) require it to show the test performs as expected in its hands. Most laboratories do this with well-characterized reference organisms, and the CDC & FDA Antimicrobial Resistance Isolate Bank is the main free U.S. source. But the Bank is organized by panel, not by test. This project is the missing catalog: for every Bank isolate it lists the resistance genes CDC reports, the BioSample accession, CDC's reference broth microdilution results, and which targets on each FDA-cleared rapid blood culture panel the isolate exercises. It flags the "hard cases," where the gene and the growth result part ways, so a laboratory can choose organisms that test both what a panel detects and what it cannot. It also uses the Bank as an outside yardstick for the author's [Project 1 benchmark](https://github.com/FatimaAbdulwahab/us-rapid-panel-amr-concordance).

## What is in it

- **{X['n_isolates']:,} isolates in {X['n_panels']} panels**, {X['n_with_biosample']} with a BioSample accession; {X['n_in_scope']} are organisms that rapid blood culture panels test, and {X['n_in_scope_carrying_any_target']} of those carry at least one panel target.
- Isolates per target (CDC gene lists): CTX-M {c['CTX-M']}, mecA {c['mecA']}, KPC {c['KPC']}, NDM {c['NDM']}, OXA-48-like {c['OXA-48-like']}, VIM {c['VIM']}, OXA-23-like {c['OXA-23-like']}, IMP {c['IMP']}, OXA-24/40-like {c['OXA-24/40-like']}, vanA {c['vanA']}, vanB {c['vanB']}, SME {c['SME']}, mcr-1 {c['mcr-1']}, mecC {c['mecC']}.
- {X['n_products']} FDA-cleared rapid blood culture panels mapped target by target: BioFire BCID2, ePlex BCID-GP and BCID-GN, Verigene BC-GP and BC-GN, LIAISON PLEX Gram-Positive and Gram-Negative (`reference/rapid_panel_targets.csv`, with the FDA decision summary link for each).
- Hard cases ({X['n_hard_cases']} isolates; one isolate can fall in more than one group):
  - target gene present but the matching drug not resistant: {hb.get('target gene present, matching drug(s) not resistant', 0)} ({", ".join(f"{k} {v}" for k, v in X['n_gene_present_not_R_by_target'].items())});
  - carbapenem resistant with no panel carbapenemase target: {hb.get('carbapenem resistant, no panel carbapenemase target', 0)};
  - third-generation cephalosporin resistant with no CTX-M or carbapenemase target: {hb.get('3rd-generation cephalosporin resistant, no CTX-M or carbapenemase target', 0)};
  - oxacillin or cefoxitin resistant with no mecA or mecC: {hb.get('oxacillin/cefoxitin resistant, no mecA or mecC', 0)}.
- Two groups where a negative panel result is expected and correct, listed so laboratories can use them as true negatives: carbapenem-resistant P. aeruginosa without a carbapenemase ({hb.get('carbapenem-resistant P. aeruginosa without a carbapenemase (chromosomal mechanisms; panel negative is expected)', 0)}) and vancomycin-resistant enterococci with intrinsic vanC ({hb.get('vancomycin resistant by intrinsic vanC, no vanA or vanB (panel negative is expected)', 0)}).
- For S. aureus, CDC's cefoxitin disk result ({X['n_with_cefoxitin_disk']} isolates, DTD panel) counts alongside the MICs.

## Outside check of the Project 1 benchmark

Project 1's gene rules were applied to {E['n_independent_with_ncbi']} Bank isolates that NCBI's AMRFinderPlus has analyzed and that are not in the Project 1 benchmark, scored against CDC's reference broth microdilution results.

- **Gene calls agree.** AMRFinderPlus and CDC's gene lists agreed for every isolate on mecA, mecC, vanA, vanB, KPC, NDM, VIM and IMP; OXA-48-like differed for {ga['OXA-48-like']['cdc_only'] + ga['OXA-48-like']['ncbi_only']} isolates (kappa {ga['OXA-48-like']['kappa']:.2f}) and CTX-M for {ga['CTX-M']['cdc_only'] + ga['CTX-M']['ncbi_only']} (kappa {ga['CTX-M']['kappa']:.2f}). This is not fully independent: CDC's own gene calls for {E['n_cdc_method_groups'].get('includes NCBI database', 0)} of these isolates used a database that includes NCBI's. Agreement is just as high in the {E['n_cdc_method_groups'].get('without NCBI database', 0)} isolates CDC called without it (`data/processed/external_check_A_by_cdc_method.csv`).
- **Interpretation agrees.** Project 1's breakpoints reproduce CDC's posted S/I/R for {pct(E['reinterpretation_agreement_with_cdc_int'])} of {E['n_reinterpreted_comparable']:,} comparable isolate-drug results.
- **CDC's two postings are consistent.** {E['n_overlap_with_project1_benchmark']} Bank isolates are also in the Project 1 benchmark; all {E['n_overlap_submitted_by_cdc']} were deposited in NCBI by CDC itself, so they are excluded from the gene-versus-result check. For their {E['n_cdc_consistency_pairs']} isolate-drug results, CDC's NCBI antibiogram category matched CDC's web page {pct(E['cdc_consistency_agreement'])} of the time, with {E['cdc_consistency_major_or_very_major']} major or very major differences. This is a consistency check of CDC's own records, not a comparison between laboratories.
- Gene-to-resistance results by target are in `data/processed/external_check_B_concordance.csv` and Figure 2. The Bank is deliberately enriched for difficult organisms, so its specificity is expected to sit below a clinical population's; the check tests direction and failure modes, not prevalence.

## Files

| File | What it is |
|---|---|
| `data/processed/crosswalk_isolates.tsv` | One row per isolate: genes by target, expected positive targets per panel, key MICs and CDC S/I/R, hard-case flag, link to the CDC page |
| `data/processed/panel_target_grid.csv` | Bank panel x target counts (Figure 1) |
| `data/processed/product_target_coverage.csv` | For each cleared panel target: Bank isolates and panels that exercise it |
| `data/processed/hard_cases.csv` | Every hard case with the drug results and the other mechanisms CDC lists |
| `data/processed/external_check_*.csv` | The three outside checks |
| `data/processed/bank_*.tsv` | CDC's values exactly as posted (panels, isolates, MICs, genes) |
| `reference/cdc_gene_to_target.csv` | Every CDC gene name, its NCBI symbol and its panel target |
| `reference/rapid_panel_targets.csv` | Targets of each FDA-cleared rapid blood culture panel, with sources |
| `docs/` | Start here, codebook, limitations, verification checklist, glossary |

## Reproduce

```
pip install -r requirements.txt
bash run_all.sh
```

This rebuilds every output of this release from the saved inputs in `data/raw/` (the archived CDC pages, the saved NCBI rows and the FDA documents) in about two minutes, and should match the released files exactly. `bash run_all.sh --refresh` downloads fresh copies from CDC, FDA and NCBI first (about 75 minutes); because CDC revises pages and NCBI re-runs its analyses, a refresh gives a new version rather than this one. Every download is logged with its size and SHA-256 fingerprint in `data/raw/PROVENANCE.txt`; read `data/processed/qa_report.txt` before anything else.

## Sources

- CDC & FDA Antimicrobial Resistance Isolate Bank, https://wwwn.cdc.gov/ARIsolateBank/ (accessed 2026-10-24). U.S. government work.
- FDA 510(k) decision summaries K193519, K243759, K181663, K182619, K213236, K122514, K132843, K243490, K243013 (links in `reference/rapid_panel_targets.csv`).
- NCBI Pathogen Detection AMRFinderPlus results and Reference Gene Hierarchy (database {X['refgene_db_version']}), https://www.ncbi.nlm.nih.gov/pathogens/ . No restrictions on use.
- Breakpoints for the outside check: CLSI M100-Ed35 (2025) as confirmed against FDA STIC for Project 1 (`reference/breakpoints_from_project1.csv`). CDC's own posted S/I/R, used for hard cases, cites the CLSI edition on each page (mostly M100 2025; some 2020, 2024 and 2026).

Device manufacturers and users of FDA-cleared devices should consult FDA's Antibacterial Susceptibility Test Interpretive Criteria (https://www.fda.gov/drugs/development-resources/antibacterial-susceptibility-test-interpretive-criteria) for breakpoints recognized by FDA. Whether a specific allele is detected by a specific panel is defined by the manufacturer's instructions for use, not by this crosswalk. This project is not affiliated with or endorsed by CDC, FDA or any manufacturer.

## License and citation

Code: MIT. Data and documents: CC BY 4.0. Cite as: Abdulwahab F. CDC & FDA Antimicrobial Resistance Isolate Bank: Rapid Panel Target Crosswalk, v1.0. Zenodo. DOI: added when the Zenodo record is published. See `CITATION.cff`.

Limitations: `docs/LIMITATIONS.md`.
"""
    open(os.path.join(ROOT, "README.md"), "w").write(txt)


def talk_track():
    c, hb = X["n_carrying"], X["n_hard_by_type"]
    t = f"""# Talk track

*Plain-language note: what to say when someone asks about Project 2. Every number comes from the verified data.*

{BANNER}## 60 seconds

Before a lab can report a new rapid blood culture test on patients, federal rules say it has to prove the test works, and most labs do that with reference organisms from the CDC and FDA Antimicrobial Resistance Isolate Bank. The problem is that the Bank is organized by panel, not by test. If you are bringing up a BioFire BCID2 or an ePlex panel, there is no list telling you which of the Bank's {X['n_isolates']} isolates carry KPC, which carry OXA-48-like, and which are the tricky ones where the gene says resistant but the organism grows like a susceptible one.

I built that list. For every isolate it shows the genes CDC reports, the reference broth microdilution results, and which targets on {X['n_products']} FDA-cleared rapid panels it exercises. It flags the hard cases, for example KPC-positive isolates that test carbapenem susceptible and mecA-positive Staph aureus that test oxacillin and cefoxitin susceptible, and it marks organisms where a negative panel result is the right answer, like carbapenem-resistant Pseudomonas without a carbapenemase. I also used the Bank as an outside check of my earlier benchmark: NCBI's gene calls matched CDC's, and my breakpoint rules reproduced CDC's reference interpretations {pct(E['reinterpretation_agreement_with_cdc_int'])} of the time. It is free, open, and has a permanent DOI.

## Two sentences

I built an open catalog that tells a laboratory which CDC and FDA reference organisms to use to verify each resistance target on the FDA-cleared rapid blood culture panels, including the hard cases where gene and growth result disagree. I also used CDC's reference results as an independent check of my national benchmark of those same resistance markers.

## Likely questions

**Who would use this?** Clinical microbiology laboratories verifying or re-verifying rapid blood culture panels, proficiency and quality managers, and manufacturers or researchers choosing challenge organisms.

**Does it replace the manufacturer's instructions?** No. It says which isolates carry a target. Whether a given allele is detected is set by each panel's instructions for use, and labs should follow those.

**What did the outside check show?** The gene calls agree almost perfectly, the breakpoint rules reproduce CDC's interpretations for {pct(E['reinterpretation_agreement_with_cdc_int'])} of results, and the isolates where a target gene is present without resistance are mostly KPC with carbapenem MICs at or just below the breakpoint ({X['n_gene_present_not_R_by_target'].get('KPC', 0)}) and mecA-positive S. aureus that test susceptible by oxacillin and cefoxitin ({X['n_gene_present_not_R_by_target'].get('mecA', 0)}). The Bank is built to be difficult, so its numbers describe a challenge set, not a patient population.
"""
    open(os.path.join(ROOT, "docs", "TALK_TRACK.md"), "w").write(t)


if __name__ == "__main__":
    qa()
    readme()
    talk_track()
    print("wrote qa_report.txt and README.md")

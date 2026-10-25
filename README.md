# CDC & FDA Antimicrobial Resistance Isolate Bank: Rapid Panel Target Crosswalk

**Status:** v1.0, released | data accessed 2026-10-24 | Fatima Abdulwahab, Independent Researcher, Dallas, Texas ([ORCID 0009-0008-2298-8386](https://orcid.org/0009-0008-2298-8386))

## In plain language

Before a laboratory reports results from a new test, federal rules (42 CFR 493.1253) require it to show the test performs as expected in its hands. Most laboratories do this with well-characterized reference organisms, and the CDC & FDA Antimicrobial Resistance Isolate Bank is the main free U.S. source. But the Bank is organized by panel, not by test. This project is the missing catalog: for every Bank isolate it lists the resistance genes CDC reports, the BioSample accession, CDC's reference broth microdilution results, and which targets on each FDA-cleared rapid blood culture panel the isolate exercises. It flags the "hard cases," where the gene and the growth result part ways, so a laboratory can choose organisms that test both what a panel detects and what it cannot. It also uses the Bank as an outside yardstick for the author's [Project 1 benchmark](https://github.com/FatimaAbdulwahab/us-rapid-panel-amr-concordance).

## What is in it

- **1,087 isolates in 39 panels**, 975 with a BioSample accession; 825 are organisms that rapid blood culture panels test, and 529 of those carry at least one panel target.
- Isolates per target (CDC gene lists): CTX-M 168, mecA 113, KPC 95, NDM 77, OXA-48-like 38, VIM 36, OXA-23-like 28, IMP 26, OXA-24/40-like 18, vanA 11, vanB 10, SME 9, mcr-1 7, mecC 2.
- 7 FDA-cleared rapid blood culture panels mapped target by target: BioFire BCID2, ePlex BCID-GP and BCID-GN, Verigene BC-GP and BC-GN, LIAISON PLEX Gram-Positive and Gram-Negative (`reference/rapid_panel_targets.csv`, with the FDA decision summary link for each).
- Hard cases (169 isolates; one isolate can fall in more than one group):
  - target gene present but the matching drug not resistant: 14 (KPC 6, mecA 3, VIM 2, SME 1, vanA 1, vanB 1);
  - carbapenem resistant with no panel carbapenemase target: 38;
  - third-generation cephalosporin resistant with no CTX-M or carbapenemase target: 58;
  - oxacillin or cefoxitin resistant with no mecA or mecC: 1.
- Two groups where a negative panel result is expected and correct, listed so laboratories can use them as true negatives: carbapenem-resistant P. aeruginosa without a carbapenemase (68) and vancomycin-resistant enterococci with intrinsic vanC (7).
- For S. aureus, CDC's cefoxitin disk result (30 isolates, DTD panel) counts alongside the MICs.

## Outside check of the Project 1 benchmark

Project 1's gene rules were applied to 538 Bank isolates that NCBI's AMRFinderPlus has analyzed and that are not in the Project 1 benchmark, scored against CDC's reference broth microdilution results.

- **Gene calls agree.** AMRFinderPlus and CDC's gene lists agreed for every isolate on mecA, mecC, vanA, vanB, KPC, NDM, VIM and IMP; OXA-48-like differed for 4 isolates (kappa 0.93) and CTX-M for 4 (kappa 0.98). This is not fully independent: CDC's own gene calls for 231 of these isolates used a database that includes NCBI's. Agreement is just as high in the 240 isolates CDC called without it (`data/processed/external_check_A_by_cdc_method.csv`).
- **Interpretation agrees.** Project 1's breakpoints reproduce CDC's posted S/I/R for 99.8% of 2,851 comparable isolate-drug results.
- **CDC's two postings are consistent.** 24 Bank isolates are also in the Project 1 benchmark; all 24 were deposited in NCBI by CDC itself, so they are excluded from the gene-versus-result check. For their 120 isolate-drug results, CDC's NCBI antibiogram category matched CDC's web page 97.5% of the time, with 0 major or very major differences. This is a consistency check of CDC's own records, not a comparison between laboratories.
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
- NCBI Pathogen Detection AMRFinderPlus results and Reference Gene Hierarchy (database 2026-08-07.1), https://www.ncbi.nlm.nih.gov/pathogens/ . No restrictions on use.
- Breakpoints for the outside check: CLSI M100-Ed35 (2025) as confirmed against FDA STIC for Project 1 (`reference/breakpoints_from_project1.csv`). CDC's own posted S/I/R, used for hard cases, cites the CLSI edition on each page (mostly M100 2025; some 2020, 2024 and 2026).

Device manufacturers and users of FDA-cleared devices should consult FDA's Antibacterial Susceptibility Test Interpretive Criteria (https://www.fda.gov/drugs/development-resources/antibacterial-susceptibility-test-interpretive-criteria) for breakpoints recognized by FDA. Whether a specific allele is detected by a specific panel is defined by the manufacturer's instructions for use, not by this crosswalk. This project is not affiliated with or endorsed by CDC, FDA or any manufacturer.

## License and citation

Code: MIT. Data and documents: CC BY 4.0. Cite as: Abdulwahab F. CDC & FDA Antimicrobial Resistance Isolate Bank: Rapid Panel Target Crosswalk, v1.0. Zenodo. DOI: added when the Zenodo record is published. See `CITATION.cff`.

Limitations: `docs/LIMITATIONS.md`.

# Verification checklist

*Plain-language note: the record of what was checked before release, and how. Ticked items were done on 2026-10-24. Anyone can repeat them: each says exactly what to open and what you should see.*

Open the main table first: `data/processed/crosswalk_isolates.tsv` in Excel or Google Sheets (File > Import, tab-separated). Turn on a filter on the header row. To find an isolate, filter `ar_bank_number`.

## A. Spot checks against CDC's own pages

For each isolate, open the CDC link, then compare. The "MIC" tab has results, the "MMR" tab has genes, and any disk result is printed above the MIC table.

- [x] **AR Bank 0032, Enterobacter cloacae** (an easy-looking KPC that is a hard case). https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=32&PanelID=9 . BioSample SAMN04014873, KPC-3 under Beta-lactam, meropenem 0.25 S, cefoxitin >16 R. Table: `KPC` = KPC-3, `meropenem_mic` = 0.25, `meropenem_int` = S, `hard_case_types` = "target gene present, matching drug(s) not resistant".
- [x] **AR Bank 0066, Klebsiella pneumoniae**. https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=66&PanelID=9 . CDC lists OXA-232 and CTX-M-15; meropenem >8 R. Table: `OXA-48-like` = OXA-232, `CTX-M` = CTX-M-15, not a hard case.
- [x] **AR Bank 0164, Enterobacter cloacae complex** (resistant with no panel target). https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=164&PanelID=8 . CDC lists NMC-A, a carbapenemase no cleared panel targets; meropenem >8 R. Table: no targets; hard case "carbapenem resistant, no panel carbapenemase target".
- [x] **AR Bank 0500, Enterococcus faecium**. https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=500&PanelID=10 . CDC lists "vanHAX (lacks VanRs)" and notes it is a vancomycin-variable enterococcus; vancomycin 1 S. Table: `vanA` = vanHAX(lacks VanRs), hard case "target gene present...".
- [x] **AR Bank 0977, Staphylococcus aureus** (mecA, oxacillin susceptible, cefoxitin disk resistant). DTD panel: https://wwwn.cdc.gov/ARIsolateBank/Panel/PanelDetail?ID=1157 . CDC lists mecA; oxacillin <=0.25 S, cefoxitin MIC 4 S, and above the MIC table "Disk Diffusion FOX: 21 mm, R". Table: `cefoxitin_disk_mm` = 21, `cefoxitin_disk_int` = R, **not** a hard case, because the cefoxitin disk detects the resistance.
- [x] **AR Bank 1306, Staphylococcus aureus** (mecC). https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=10597&PanelID=13 . CDC gene list shows blaZ-mecC; cefoxitin 16 R, oxacillin 2 S. Table: `mecC` = blaZ-mecC.
- [x] **AR Bank 0504, Klebsiella pneumoniae** (CDC bracket note). CDC writes "OXA-48(c)". Table: `OXA-48-like` = OXA-48(c), not a hard case; `reference/cdc_gene_to_target.csv` shows the "(c)" was ignored.
- [x] **Panel count.** https://wwwn.cdc.gov/ARIsolateBank/Panel/AllIsolate lists 34 panels; `data/processed/bank_panels.tsv` has 34 rows with `listed_on_all_panels_page` = True.
- [x] **All values.** A second, separately written reader of the saved pages matched all 20,546 MIC rows and 8,298 gene rows, and all saved pages match the fingerprints in `data/raw/PROVENANCE.txt`.

## B. Rapid panel targets against FDA

`reference/rapid_panel_targets.csv`, column `verify_status`, records what was checked for each row.

- [x] ePlex BCID-GN (K182619, K213236): CTX-M, IMP, KPC, NDM, OXA (OXA-23 and OXA-48 groups only), VIM. Confirmed by the author in both FDA summaries.
- [x] BIOFIRE BCID2 (K193519), ePlex BCID-GP (K181663), Verigene BC-GP (K122514), LIAISON PLEX Gram-Positive (K243490) and Gram-Negative (K243013): targets checked against the FDA decision summary text.
- [x] Verigene BC-GN (K132843): the FDA summary lists "OXA" without naming groups; the crosswalk uses OXA-23 and OXA-48 groups from its analytical studies and says so (Limitations 5). The package insert would settle it.

## C. Rulings applied in this release

1. **blaZ-mecC counted as mecC** (AR Bank 1306, 1307). CDC's custom panel names them mecC+, and NCBI AMRFinderPlus finds mecC in both.
2. **vanHAX without vanR/vanS counted as vanA** (AR Bank 0500), kept as a hard case. CDC's own page calls it a vancomycin-variable enterococcus.
3. **Generic "MBL" entries left unmapped** (4 isolates): no enzyme is named, so no target can be assigned.
4. **Intermediate counts as not resistant** for hard cases, as in Project 1. Six KPC isolates whose carbapenem MICs are all 2 mg/L or lower are hard cases.
5. **Expected panel negatives are their own categories:** vancomycin-resistant enterococci with intrinsic vanC (7), and carbapenem-resistant P. aeruginosa without a carbapenemase (68), where porin loss, efflux and AmpC are the usual causes and no panel targets them.
6. **CDC's posted S/I/R for the crosswalk, Project 1's breakpoints for the outside check.** The six places they differ are listed in `data/processed/qa_report.txt`, section 3.
7. **Cefoxitin disk counts as a drug result** for mecA and mecC where CDC posts one (30 isolates). Four mecA isolates (0977, 0981, 0991, 0992) are disk resistant and so are not hard cases.
8. **The MRSA (MREJ) call is assumed** for every mecA- or mecC-positive S. aureus, and this is stated as a limitation (Limitations 4).
9. **Republishing CDC values:** only facts printed on CDC's public pages, each with a link; the project states it is not affiliated with CDC or FDA.

## D. Outside check

- [x] `data/processed/external_check_A_gene_calls.csv`: mecA both = 103, cdc_only = 0, ncbi_only = 0. OXA-48-like: 4 CDC-only (all OXA-232), kappa 0.93.
- [x] `data/processed/external_check_A_by_cdc_method.csv`: agreement is as high in isolates CDC called without NCBI's database as in those called with it.
- [x] AR Bank 0066 (SAMN04014907) in NCBI's isolate browser: blaCTX-M-15 and blaOXA-1 but no blaOXA-232, although CDC lists OXA-232.
- [x] `data/processed/external_check_C_cdc_consistency.csv`: all 24 overlapping isolates were deposited in NCBI by CDC, so this is a consistency check of CDC's two postings, worded that way everywhere.

## E. Reproduce

- [x] Running `bash run_all.sh` rebuilds every table, `paper/stats.json` and the QA report identically from the saved inputs in `data/raw/`. `bash run_all.sh --refresh` downloads new copies and will give a new version, not this one.

## F. Your words

- [ ] Optional: rewrite the "In plain language" paragraph of `README.md` and read `docs/TALK_TRACK.md` aloud, changing anything you would not say. Either can be updated in a later version.

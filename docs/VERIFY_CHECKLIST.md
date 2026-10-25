# Verification checklist

*Plain-language note: nothing is published until you have done this. It takes about 1 hour 30 minutes in one sitting. Each item says exactly what to open and what you should see. Tick each box. Write "OK" or what you found.*

Open the main table first: `data/processed/crosswalk_isolates.tsv` in Excel or Google Sheets (File > Import, tab-separated). Turn on a filter on the header row. To find an isolate, filter `ar_bank_number`.

## A. Spot checks against CDC's own pages (25 minutes)

For each isolate, open the CDC link, then compare. Click the "MIC" tab for results and the "MMR" tab for genes.

- [ ] **AR Bank 0032, Enterobacter cloacae** (an easy-looking KPC that is a hard case). https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=32&PanelID=9 . You should see BioSample SAMN04014873, KPC-3 under Beta-lactam, meropenem 0.25 S, cefoxitin >16 R. In the table: `KPC` = KPC-3, `meropenem_mic` = 0.25, `meropenem_int` = S, `hard_case_types` = "target gene present, matching drug(s) not resistant".
- [ ] **AR Bank 0066, Klebsiella pneumoniae**. https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=66&PanelID=9 . CDC lists OXA-232 and CTX-M-15; meropenem >8 R. Table: `OXA-48-like` = OXA-232, `CTX-M` = CTX-M-15, not a hard case.
- [ ] **AR Bank 0164, Enterobacter cloacae complex** (resistant with no panel target). https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=164&PanelID=8 . CDC lists NMC-A (a carbapenemase no cleared panel targets); meropenem >8 R. Table: no targets in `panel_targets_carried`; hard case "carbapenem resistant, no panel carbapenemase target".
- [ ] **AR Bank 0500, Enterococcus faecium**. https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=500&PanelID=10 . CDC lists "vanHAX (lacks VanRs)", vancomycin 1 S. Table: `vanA` = vanHAX(lacks VanRs), hard case "target gene present...".
- [ ] **AR Bank 0977, Staphylococcus aureus** (mecA, oxacillin susceptible). Find it in the DTD panel: https://wwwn.cdc.gov/ARIsolateBank/Panel/PanelDetail?ID=1157 . CDC lists mecA; oxacillin <=0.25 S, cefoxitin 4 S. Table matches; hard case.
- [ ] **AR Bank 1306, Staphylococcus aureus** (mecC). https://wwwn.cdc.gov/ARIsolateBank/Panel/IsolateDetail?IsolateID=10597&PanelID=13 . CDC gene list shows blaZ-mecC; cefoxitin 16 R, oxacillin 2 S. Table: `mecC` = blaZ-mecC.
- [ ] **Panel count.** Open https://wwwn.cdc.gov/ARIsolateBank/Panel/AllIsolate . Count the panels on the "Panels" list. You should count 34. Open `data/processed/bank_panels.tsv`: 34 rows say `True` under `listed_on_all_panels_page`.

## B. Rapid panel targets against FDA (25 minutes)

Open `reference/rapid_panel_targets.csv`. For each panel, open the FDA link in the `decision_summary_url` column and find the "Indications for use" or "Intended use" paragraph (usually page 1 or 2). Confirm the targets match. Then remove `[VERIFY]` from `verify_status` and write "confirmed by author against FDA decision summary on <date>".

- [ ] BIOFIRE BCID2 (K193519): mecA/C, mecA/C and MREJ (MRSA), vanA/B, CTX-M, KPC, NDM, OXA-48-like, VIM, IMP, mcr-1.
- [ ] ePlex BCID-GP (K181663): mecA, mecC, vanA, vanB.
- [ ] ePlex BCID-GN (K182619): CTX-M, IMP, KPC, NDM, OXA (OXA-23 and OXA-48 groups only), VIM.
- [ ] Verigene BC-GP (K122514): mecA, vanA, vanB.
- [ ] Verigene BC-GN (K132843): CTX-M, KPC, NDM, VIM, IMP, OXA. **Judgment call:** the summary does not name OXA groups; its studies used OXA-23 and OXA-48 strains. If you have the Verigene BC-GN package insert, check which OXA groups it claims. Keep "OXA-23-like;OXA-48-like" or correct it.
- [ ] LIAISON PLEX Gram-Positive (K243490): mecA/mecC, vanA, vanB.
- [ ] LIAISON PLEX Gram-Negative (K243013): CTX-M, IMP, KPC, MCR (MCR-1, -2, -3), NDM, OXA (OXA-23, OXA-24/40/143, OXA-48, OXA-58), SME, VIM.
- [ ] Are there other FDA-cleared blood culture panels with resistance targets you use or know (for example a newer BioFire or Qiagen panel)? If so, tell Claude the name; it will be added.

## C. Your rulings (20 minutes)

Each needs a one-word answer. Tell Claude your choices; it rebuilds in a few minutes.

1. **blaZ-mecC as mecC.** CDC lists only "blaZ-mecC" for AR Bank 1306 and 1307 but titles their custom panel "S. aureus mecC+". NCBI's AMRFinderPlus finds mecC itself in both. Count them as mecC? *(Suggested: yes.)*
2. **vanHAX without vanR/vanS as vanA.** AR Bank 0500. A panel would detect vanA; the isolate tests vancomycin S. Count as vanA and keep as a hard case? *(Suggested: yes; this is exactly the vancomycin-variable enterococcus a laboratory should know about.)*
3. **Generic "MBL" entries** (4 isolates): CDC writes "MBL" without naming the enzyme. Leave unmapped (no panel target)? *(Suggested: yes, and note it.)*
4. **Intermediate as not resistant** for hard cases, same as Project 1? *(Suggested: yes.)* With this rule, 6 KPC isolates whose carbapenem MICs are all 2 mg/L or lower count as hard cases.
5. **VanC enterococci** (7 isolates, vancomycin R by intrinsic vanC): keep them as a separate "panel negative is expected" category? *(Suggested: yes.)*
6. **Six interpretation differences** between CDC's posted S/I/R and Project 1's breakpoints (listed in `data/processed/qa_report.txt`, section 3), mostly Morganella/Providencia meropenem at 2 to 4 mg/L. The crosswalk uses CDC's posted calls; the outside check uses Project 1's. Keep that split? *(Suggested: yes.)*
7. **Republishing CDC values.** CDC's isolate pages say the *material* (the organisms) may not be redistributed. This project republishes only the facts printed on CDC's public web pages, with a link to each page; U.S. government web content is public domain. Comfortable? *(Suggested: yes; the README says the project is not affiliated with CDC or FDA.)*

## D. Outside check (15 minutes)

- [ ] Open `data/processed/external_check_A_gene_calls.csv`. mecA row: both = 103, cdc_only = 0, ncbi_only = 0.
- [ ] Check one disagreement yourself: go to https://www.ncbi.nlm.nih.gov/pathogens/isolates/ and search SAMN04014907 (AR Bank 0066). In the "AMR genotypes" column you should see blaCTX-M-15 and blaOXA-1 but no blaOXA-232, although CDC lists OXA-232. This is a real difference between the two methods, not a build error.
- [ ] Open `paper/figures/fig2_external_check.png`. Does the explanation in the footer match how you would describe it?
- [ ] Open `data/processed/external_check_C_same_isolate.csv`: 120 rows, `agree` mostly True. Filter `agree` = False and read the 3 rows. Do these look like ordinary one-dilution differences?

## E. Reproduce (5 minutes of your time)

Ask Claude in a new chat: "Clone github.com/FatimaAbdulwahab/ar-isolate-bank-panel-crosswalk, run run_all.sh, and tell me the numbers in section 1 and 6 of qa_report.txt." Compare them with this release's `data/processed/qa_report.txt`. Small differences are expected only if CDC has changed a page since 2026-10-24.

## F. Your words (15 minutes)

- [ ] Rewrite the "In plain language" paragraph of `README.md` so it sounds like you. Claude can do this with you line by line.
- [ ] Read `docs/TALK_TRACK.md` out loud once. Change anything you would not say.

When everything is ticked, tell Claude: "I have verified Project 2." It will remove the DRAFT stamps, run the publish check and publish.

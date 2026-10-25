# Build spec

*Plain-language note: the one-page plan this build followed. Each line has a plain meaning in italics underneath.*

```
PROJECT:        Reference Isolate Verification Crosswalk (Project 2). Archetypes: dataset + validation study.
QUESTION:       Which CDC & FDA AR Isolate Bank isolates exercise which FDA-cleared rapid blood culture panel
                resistance targets, which are hard cases where genotype and phenotype part ways, and does the
                Project 1 benchmark hold up against the Bank's reference broth microdilution results?
SOURCES:        CDC & FDA AR Isolate Bank web pages (all panels, all isolate pages), accessed 2026-10-24,
                U.S. government work. FDA 510(k) decision summaries K193519, K243759, K181663, K182619, K213236,
                K122514, K132843, K243490, K243013. NCBI Pathogen Detection latest_snps AMR metadata (per-group
                PDG runs logged in PROVENANCE.txt) and AMRFinderPlus Reference Gene Hierarchy 2026-08-07.1;
                no restrictions on use. Project 1 v1.0 breakpoints, gene crosswalk and concordance table.
UNIT:           One Isolate Bank isolate (AR Bank number). Analysis unit for the outside check: isolate x
                target x drug, Project 1 rules.
MEASURES:       Target carriage per isolate (CDC gene list -> NCBI hierarchy -> target group); expected positive
                targets per cleared panel; hard-case rules on CDC's posted S/I/R; CDC vs AMRFinderPlus gene-call
                agreement (kappa); sensitivity, specificity, PPV, NPV with Wilson 95% ranges vs Project 1;
                same-isolate categorical agreement.
OUTPUTS:        data/processed/crosswalk_isolates.tsv, panel_target_grid.csv, product_target_coverage.csv,
                hard_cases.csv, external_check_*.csv, bank_*.tsv; reference/cdc_gene_to_target.csv,
                rapid_panel_targets.csv; paper/figures/fig1, fig2; paper/stats.json; qa_report.txt.
VENUES:         GitHub -> Zenodo (crosswalk DOI, target June 2027 in plan; ready now). External check ->
                preprint (medRxiv) after the crosswalk DOI exists.
VERIFY POINTS:  CDC spot checks; FDA target lists (Verigene BC-GN OXA groups); blaZ-mecC as mecC; vanHAX as
                vanA; generic MBL; I as not resistant; VanC category; CDC vs Project 1 interpretation split;
                republishing CDC web values.
LICENSE:        Code MIT; data and documents CC BY 4.0.
ASSUMPTIONS:    Proceeding on the defaults offered to the author on 2026-10-24 (all 39 panels listed, bacteria
                in rapid panel scope mapped; seven cleared panels; Project 1 breakpoints plus CDC posted S/I/R;
                hard-case definition as offered; MIT + CC BY 4.0).
```

*Question: the one thing this answers. Unit: every row in the main table is one Bank isolate. Measures: what is counted and how. Venues: GitHub, then a DOI on Zenodo, then the preprint. Verify points: the decisions in your checklist.*

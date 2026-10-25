# Codebook

*Plain-language note: this lists every column in the main files, what it means, and where it comes from. Open it when a column name is unclear. Values copied from CDC are exactly as CDC posts them; nothing is reinterpreted unless the column says so.*

## data/processed/crosswalk_isolates.tsv (one row per Isolate Bank isolate)

| Column | Meaning | Source / rule |
|---|---|---|
| ar_bank_number | CDC AR Bank number (4 digits, as on the CDC page) | CDC isolate page |
| organism | Species as CDC lists it | CDC isolate page |
| organism_group | Enterobacterales, Pseudomonas, Acinetobacter, Staphylococcus aureus, Staphylococcus other, Enterococcus, Neisseria, Fungi, Other bacteria | Genus name |
| biosample | NCBI BioSample accession | CDC isolate page |
| bank_panels | Codes of every Bank panel that lists this isolate, separated by `;` | CDC panel pages |
| n_bank_panels | Number of those panels | Count |
| in_scope_for_panel_targets | True if the organism group is one that rapid blood culture panels report resistance genes for (Enterobacterales, Pseudomonas, Acinetobacter, staphylococci, enterococci) | Rule in `code/04_crosswalk.py` |
| has_mechanism_list | True if CDC posts a gene list for the isolate | CDC isolate page |
| n_genes_listed | Number of gene entries CDC lists | Count |
| mecA ... mcr-3 (one column per target) | CDC gene names that map to that target, `;`-separated; blank if none | CDC gene list mapped through `reference/cdc_gene_to_target.csv` |
| panel_targets_carried | All targets present | Derived |
| expected_positive::<panel> | Targets that panel reports which this isolate should be positive for, given its genes and organism (MRSA call only for S. aureus) | `reference/rapid_panel_targets.csv` |
| <drug>_mic, <drug>_int | CDC's posted reference broth microdilution MIC (mg/L) and CDC's posted S/I/R for meropenem, imipenem, ertapenem, doripenem, ceftriaxone, cefotaxime, ceftazidime, oxacillin, cefoxitin, vancomycin, colistin | CDC isolate page (CDC states interpretations are from CLSI M100 2025 unless footnoted as FDA) |
| hard_case | True if any hard-case rule fires | See below |
| hard_case_types | Which rules fired | See below |
| isolate_url | Link to the CDC isolate page | Constructed from the CDC page ID |

**Hard-case rules** (CDC's posted S/I/R; intermediate counts as not resistant; imipenem not used for Proteus, Morganella, Providencia):
1. *Target gene present, matching drug(s) not resistant*: e.g. KPC with no carbapenem R; mecA with oxacillin and cefoxitin not R; vanA/vanB with vancomycin not R; CTX-M with ceftriaxone, cefotaxime and ceftazidime not R; mcr with colistin not R.
2. *Carbapenem resistant, no panel carbapenemase target* (Enterobacterales, Pseudomonas, Acinetobacter): any carbapenem R and none of KPC, NDM, VIM, IMP, OXA-48-like, OXA-23-like, OXA-24/40-like, OXA-58-like, OXA-143-like, SME.
3. *Third-generation cephalosporin resistant, no CTX-M or carbapenemase target* (Enterobacterales).
4. *Oxacillin/cefoxitin resistant, no mecA or mecC* (staphylococci).
5. *Vancomycin resistant, no vanA or vanB* (enterococci); labelled "by intrinsic vanC, panel negative is expected" when CDC lists vanC.

## data/processed/hard_cases.csv
One row per isolate per rule: `direction` (the rule), `target`, `genes`, `drugs_checked` (drug=MIC S/I/R), `primary_drug`, `note` (other CDC-listed mechanisms or a mapping flag), plus identifiers and link.

## data/processed/panel_target_grid.csv
One row per Bank panel: code, name, whether it is on the All Isolate Panels page, isolate count, in-scope count, hard-case count, the number of isolates carrying each target, and the species mix.

## data/processed/product_target_coverage.csv
One row per cleared panel per reported target: number of Bank isolates expected positive, number of Bank panels and species they come from, hard cases among them, and their AR Bank numbers.

## data/processed/bank_panels.tsv, bank_isolates.tsv, bank_mic_long.tsv, bank_mechanisms_long.tsv
CDC's values as posted. `bank_mic_long`: drug_cdc, mic_cdc, int_cdc, footnote (CDC's footnote text, e.g. "Based on FDA break points"). `bank_mechanisms_long`: category_cdc, gene_cdc. `bank_isolates` also keeps study ID, source, MLST, CDC's notes on MIC method and gene-calling method.

## reference/cdc_gene_to_target.csv
| Column | Meaning |
|---|---|
| gene_cdc | Gene name exactly as CDC writes it |
| ncbi_symbol | Matching NCBI AMRFinderPlus symbol (blank if none) |
| match | exact, synonym, case-insensitive, family name only, operon name, or not in NCBI catalog |
| hierarchy_node | NCBI family node that set the target |
| target_group | Rapid panel target group, blank if not a panel target |
| ncbi_subclass | NCBI drug subclass for the gene |
| flag | Notes and `[VERIFY]` items for the author |
| n_isolates | Bank isolates listing this name |

## reference/rapid_panel_targets.csv
One row per reported target per FDA-cleared panel: product, manufacturer, 510(k) number, FDA decision summary link, the target as the panel reports it, the target groups it covers, organism scope, a note on wording, and verification status.

## Outside check files
- `external_check_isolates.tsv`: Bank isolates in Project 1 organisms, with NCBI AMRFinderPlus target calls (`ncbi_<target>`, `ncbi_<target>_alleles`), `in_ncbi`, `in_project1_benchmark`.
- `external_check_A_gene_calls.csv`: per target, isolates where both, CDC only, NCBI only or neither found it; percent agreement; Cohen's kappa.
- `external_check_A_discrepancies.csv`: each disagreeing isolate.
- `external_check_reinterpretation.csv`: CDC MIC reinterpreted with Project 1 breakpoints next to CDC's S/I/R.
- `external_check_B_concordance.csv`: Project 1's analysis rows recomputed on independent Bank isolates (`bank_*`) next to Project 1's main estimates (`project1_*`), with a plain comparison of the 95% ranges for sensitivity and specificity.
- `external_check_B_discordant_isolates.csv`: isolates behind every gene/phenotype disagreement in check B.
- `external_check_C_same_isolate.csv`: Bank isolates also in Project 1: the submitting lab's category vs CDC's reference category for the same drug.

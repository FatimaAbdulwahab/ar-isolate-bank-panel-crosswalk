# Next steps

*Plain-language note: what comes after v1.0, so v1.0 is understood as a first step.*

1. **Preprint of the outside check** (medRxiv). The analysis is done (`external_check_*`); the manuscript reuses Figure 2 and the stats file. Natural title: "An external reference-method check of rapid blood culture panel resistance markers using the CDC & FDA Antimicrobial Resistance Isolate Bank."
2. **Lookup page.** Add the crosswalk to Project 1's GitHub Pages site: pick a panel (for example BCID2), get the Bank isolates that exercise each target and the hard cases, with CDC links.
3. **Yearly refresh.** The Bank adds isolates and revises MICs. Re-run `run_all.sh` once a year and release v1.1 with a new Zenodo version.
4. **Allele-level detectability.** With manufacturers' instructions for use, mark alleles each panel claims or excludes.
5. **More panels.** Add newly cleared blood culture panels with resistance targets as FDA clears them.

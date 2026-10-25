# Limitations

*Plain-language note: the honest list of what this project cannot tell you. Any paper or post about it must stay inside these limits.*

1. **The crosswalk says which targets an isolate carries, not that a given panel will detect it.** Allele-level detection (for example a rare OXA-48 variant, or IMP alleles a primer set may miss) is defined by each manufacturer's instructions for use. The crosswalk tells a laboratory which organisms are candidates; the instructions for use decide whether each is a valid positive.
2. **Gene lists come from CDC's 2021-era analysis.** CDC states its genes were called with ARG-ANNOT, ResFinder and NCBI databases accessed 2021-05-07, without point mutations. Newer genes, and anything CDC's method did not report, are missing from CDC's lists. The outside check (AMRFinderPlus) catches some of these; a few OXA-232 and CTX-M-15 calls differ between the two (likely genes on small plasmids absent from the public assembly).
3. **MREJ cannot be read from a gene list.** The BCID2 "MRSA" result needs both mecA/C and the SCCmec junction (MREJ). The crosswalk marks S. aureus mecA/C carriers as expected MRSA positives; MREJ variants that the assay may not detect are not assessed.
4. **Organism identification is CDC's.** Species names are taken as posted. A few names on CDC pages are older (for example Enterobacter aerogenes) and are grouped by Project 1's rules.
5. **The Bank is not a patient population.** It is built to contain unusual, difficult and multi-mechanism organisms. Prevalence-dependent numbers (PPV, NPV, and sensitivity of a single gene) in the outside check describe this collection, not what a laboratory will see in its patients.
6. **Small numbers for some targets.** vanA, vanB, VIM, IMP and mecC have 2 to 36 isolates; their ranges are wide.
7. **CDC's posted interpretation is used for hard cases.** CDC interprets with CLSI M100 2025, or FDA where footnoted. A laboratory using different breakpoints may classify some isolates differently; the crosswalk keeps the MIC so users can reinterpret.
8. **Not every isolate is in NCBI Pathogen Detection.** 31 Bank isolates in Project 1's organisms had no AMRFinderPlus result, and 112 Bank isolates have no BioSample listed. They stay in the crosswalk but not in the outside check.
9. **Website snapshot.** The Bank adds isolates and revises MICs (each page has a change history). This release reflects pages downloaded on 2026-10-24; the provenance log fingerprints each page.
10. **Scope.** Fungal, gonococcal, C. difficile and enteric-pathogen panels are listed but not mapped, because cleared rapid blood culture panels do not report resistance genes for those organisms.
11. **No physical isolates were tested.** Everything here comes from published CDC, FDA and NCBI data.

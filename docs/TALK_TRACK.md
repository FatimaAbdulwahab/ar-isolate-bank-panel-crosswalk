# Talk track

*Plain-language note: what to say when someone asks about Project 2. Every number comes from the verified data.*

## 60 seconds

Before a lab can report a new rapid blood culture test on patients, federal rules say it has to prove the test works, and most labs do that with reference organisms from the CDC and FDA Antimicrobial Resistance Isolate Bank. The problem is that the Bank is organized by panel, not by test. If you are bringing up a BioFire BCID2 or an ePlex panel, there is no list telling you which of the Bank's 1087 isolates carry KPC, which carry OXA-48-like, and which are the tricky ones where the gene says resistant but the organism grows like a susceptible one.

I built that list. For every isolate it shows the genes CDC reports, the reference broth microdilution results, and which targets on 7 FDA-cleared rapid panels it exercises. It flags the hard cases, for example KPC-positive isolates that test carbapenem susceptible and mecA-positive Staph aureus that test oxacillin and cefoxitin susceptible, and it marks organisms where a negative panel result is the right answer, like carbapenem-resistant Pseudomonas without a carbapenemase. I also used the Bank as an outside check of my earlier benchmark: NCBI's gene calls matched CDC's, and my breakpoint rules reproduced CDC's reference interpretations 99.8% of the time. It is free, open, and has a permanent DOI.

## Two sentences

I built an open catalog that tells a laboratory which CDC and FDA reference organisms to use to verify each resistance target on the FDA-cleared rapid blood culture panels, including the hard cases where gene and growth result disagree. I also used CDC's reference results as an independent check of my national benchmark of those same resistance markers.

## Likely questions

**Who would use this?** Clinical microbiology laboratories verifying or re-verifying rapid blood culture panels, proficiency and quality managers, and manufacturers or researchers choosing challenge organisms.

**Does it replace the manufacturer's instructions?** No. It says which isolates carry a target. Whether a given allele is detected is set by each panel's instructions for use, and labs should follow those.

**What did the outside check show?** The gene calls agree almost perfectly, the breakpoint rules reproduce CDC's interpretations for 99.8% of results, and the isolates where a target gene is present without resistance are mostly KPC with carbapenem MICs at or just below the breakpoint (6) and mecA-positive S. aureus that test susceptible by oxacillin and cefoxitin (3). The Bank is built to be difficult, so its numbers describe a challenge set, not a patient population.

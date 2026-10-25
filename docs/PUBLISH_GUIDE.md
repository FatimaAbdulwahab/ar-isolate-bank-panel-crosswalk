# Publish guide

*Plain-language note: how to put Project 2 on GitHub and get its permanent DOI from Zenodo. The package you have is the final, verified version. Total time: about 25 minutes. Or skip Parts 1 and 2 by giving Claude two upload tokens (Part 0).*

## Copy-ready text

**Repository name:** `ar-isolate-bank-panel-crosswalk`

**Repository description:** Open crosswalk of CDC & FDA AR Isolate Bank isolates to FDA-cleared rapid blood culture panel resistance targets, with hard cases and an external check of the Project 1 benchmark.

**Author:** Abdulwahab, Fatima. ORCID 0009-0008-2298-8386. Independent Researcher, Dallas, Texas, USA.

**Keywords:** antimicrobial resistance; AR Isolate Bank; rapid diagnostics; blood culture identification panel; test verification; CLIA; reference organisms; carbapenemase; mecA; AMRFinderPlus

**License:** data and documents CC BY 4.0; code MIT

**Release notes (v1.0.0):** First public release. Isolate-level crosswalk of the CDC & FDA AR Isolate Bank to the resistance targets of seven FDA-cleared rapid blood culture panels, panel-by-target grid, hard-case list, external check of the Project 1 benchmark, codebook, QA report and provenance log. CDC pages accessed 2026-10-24.

## Part 0 (optional): let Claude upload for you (8 min)

1. **GitHub token.** https://github.com/settings/tokens/new . Note: "crosswalk upload". Expiration: 7 days. Tick **repo**. Click **Generate token** and copy it.
2. **Zenodo token.** https://zenodo.org/account/settings/applications/tokens/new/ . Name: "crosswalk upload". Tick **deposit:write** and **deposit:actions**. Click **Create** and copy it.
3. Paste both into the chat. A token is a temporary password that lets Claude upload for you; Claude never writes it into a file.
4. Afterwards delete both: https://github.com/settings/tokens and https://zenodo.org/account/settings/applications/ .

## Part 1: GitHub (10 min)

1. Go to https://github.com/new . Owner: FatimaAbdulwahab. Name and description: paste from above. **Public**. Leave "Add a README" unticked. Click **Create repository**.
2. Unzip the project zip Claude gave you.
3. On the empty repository page click **uploading an existing file** and drag in everything inside the unzipped folder. If GitHub says too many files, upload in batches: first the loose files, then `code` and `docs`, then `data`, then `paper`, `reference`, `tools`, `zenodo`. Commit message: `v1.0.0 release`. Click **Commit changes**.
4. The repository page now shows the README titled "CDC & FDA Antimicrobial Resistance Isolate Bank: Rapid Panel Target Crosswalk".

## Part 2: Zenodo DOI (10 min)

1. Log in at https://zenodo.org with ORCID.
2. Click your name (top right), then **GitHub**. Click **Sync now**. Find `ar-isolate-bank-panel-crosswalk` and flip its switch **On**.
3. On GitHub open the repository, click **Releases**, **Draft a new release**. Tag: `v1.0.0` (Create new tag). Title: `v1.0.0`. Paste the release notes. Click **Publish release**.
4. Within about five minutes the record appears under Zenodo **Uploads**. Open it, click **Edit**. Paste the description and keywords from `zenodo/crosswalk.json`. Resource type: **Dataset**. License: **Creative Commons Attribution 4.0**. Under "Related works" add the three links from `zenodo/crosswalk.json`. Click **Publish**. Copy the DOI.

## Part 3: The same day (10 min)

1. Send the DOI to Claude. Claude puts it in `README.md`, `CITATION.cff` and `LICENSE-DATA.md` and gives you the updated files.
2. Add a row to `docs/evidence_log.csv`: date, "Isolate Bank to panel target crosswalk", "dataset", "Zenodo + GitHub", the DOI, "live". Save the Zenodo page as PDF (browser **Print**, **Save as PDF**).
3. Optional: add the DOI to ORCID (https://orcid.org/my-orcid , **Works**, **Add**, **Search & link**, **DataCite**).

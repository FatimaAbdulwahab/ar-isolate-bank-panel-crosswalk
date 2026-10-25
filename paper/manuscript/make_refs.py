#!/usr/bin/env python3
"""
make_refs.py - Build references.tex for the preprint.

PLAIN-LANGUAGE NOTE: Every journal reference is formatted from its Crossref
record (crossref_raw.json, fetched by DOI), so author names, titles, volumes and
pages come from the publisher's registration, not from memory. References are
numbered in the order they are first cited in preprint.tex.
"""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
CR = json.load(open(os.path.join(HERE, "crossref_raw.json")))

MANUAL = {
    "cdc10yr": r"Centers for Disease Control and Prevention. \textit{CDC \& FDA Antimicrobial Resistance Isolate Bank: 10 Facts for 10 Years}. "
               r"CDC, Atlanta, GA, revised January 2026. \url{https://www.cdc.gov/antimicrobial-resistance/media/pdfs/10-Facts-for-10-Years-508.pdf}.",
    "arbankweb": r"Centers for Disease Control and Prevention and U.S. Food and Drug Administration. CDC \& FDA Antimicrobial Resistance "
                 r"Isolate Bank. \url{https://wwwn.cdc.gov/ARIsolateBank/}. Accessed 24 October 2026.",
    "clia": r"Code of Federal Regulations. Title 42, \S\,493.1253, Standard: Establishment and verification of performance "
            r"specifications. \url{https://www.ecfr.gov/current/title-42/section-493.1253}.",
    "clsi2025": r"Clinical and Laboratory Standards Institute. \textit{Performance Standards for Antimicrobial Susceptibility "
                r"Testing}. CLSI supplement M100, 35th edition. Clinical and Laboratory Standards Institute, Wayne, PA, 2025.",
    "clsim52": r"Clinical and Laboratory Standards Institute. \textit{Verification of Commercial Microbial Identification and "
               r"Antimicrobial Susceptibility Testing Systems}. CLSI guideline M52, 1st edition. Clinical and Laboratory Standards "
               r"Institute, Wayne, PA, 2015.",
    "fdastic": r"U.S. Food and Drug Administration. Antibacterial Susceptibility Test Interpretive Criteria. "
               r"\url{https://www.fda.gov/drugs/development-resources/antibacterial-susceptibility-test-interpretive-criteria}. "
               r"Accessed 24 October 2026.",
    "fda_bcid2": r"U.S. Food and Drug Administration. 510(k) decision summaries K193519 and K243759, BIOFIRE Blood Culture "
                 r"Identification 2 (BCID2) Panel. \url{https://www.accessdata.fda.gov/cdrh_docs/reviews/K193519.pdf}.",
    "fda_eplexgp": r"U.S. Food and Drug Administration. 510(k) decision summary K181663, ePlex Blood Culture Identification "
                   r"Gram-Positive (BCID-GP) Panel. \url{https://www.accessdata.fda.gov/cdrh_docs/reviews/K181663.pdf}.",
    "fda_eplexgn": r"U.S. Food and Drug Administration. 510(k) decision summaries K182619 and K213236, ePlex Blood Culture "
                   r"Identification Gram-Negative (BCID-GN) Panel. \url{https://www.accessdata.fda.gov/cdrh_docs/reviews/K182619.pdf}.",
    "fda_vergp": r"U.S. Food and Drug Administration. 510(k) summary K122514, Verigene Gram-Positive Blood Culture Nucleic Acid "
                 r"Test (BC-GP). \url{https://www.accessdata.fda.gov/cdrh_docs/pdf12/K122514.pdf}.",
    "fda_vergn": r"U.S. Food and Drug Administration. 510(k) decision summary K132843, Verigene Gram-Negative Blood Culture "
                 r"Nucleic Acid Test (BC-GN). \url{https://www.accessdata.fda.gov/cdrh_docs/reviews/K132843.pdf}.",
    "fda_lpgp": r"U.S. Food and Drug Administration. 510(k) decision summary K243490, LIAISON PLEX Gram-Positive Blood Culture "
                r"Assay. \url{https://www.accessdata.fda.gov/cdrh_docs/reviews/K243490.pdf}.",
    "fda_lpgn": r"U.S. Food and Drug Administration. 510(k) decision summary K243013, LIAISON PLEX Gram-Negative Blood Culture "
                r"Assay. \url{https://www.accessdata.fda.gov/cdrh_docs/reviews/K243013.pdf}.",
    "ncbipd": r"National Center for Biotechnology Information. Pathogen Detection. "
              r"\url{https://www.ncbi.nlm.nih.gov/pathogens/}. Data accessed 24 October 2026.",
    "project1": r"Fatima Abdulwahab. U.S. Rapid Panel Resistance Marker Concordance Benchmark, version 1.0.0. "
                r"\url{https://github.com/FatimaAbdulwahab/us-rapid-panel-amr-concordance}, 2026.",
    "thiswork": r"Fatima Abdulwahab. CDC \& FDA Antimicrobial Resistance Isolate Bank: Rapid Panel Target Crosswalk, version 1.0.0. "
                r"\url{https://github.com/FatimaAbdulwahab/ar-isolate-bank-panel-crosswalk}, 2026. Archived on Zenodo.",
}


def tex_escape(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"), ("$", r"\$"),
                 ("β", r"$\beta$"), ("–", "--"), ("—", "---"), ("’", "'"), ("‘", "`")]:
        s = s.replace(a, b)
    return s


def authors(m):
    au = m.get("author", [])
    names = [tex_escape(f"{a.get('given', '')} {a.get('family', '')}".strip()) for a in au if a.get("family")]
    if not names:
        return ""
    if len(names) > 3:
        return names[0] + " et al."
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return names[0] + " and " + names[1]
    return ", ".join(names[:-1]) + ", and " + names[-1]


def year(m):
    for k in ["published-print", "journal-issue", "issued"]:
        v = m.get(k, {})
        if isinstance(v, dict) and "date-parts" in v:
            return v["date-parts"][0][0]
        if k == "journal-issue" and isinstance(v, dict) and "published-print" in v:
            return v["published-print"]["date-parts"][0][0]
    return ""


def fmt(key):
    if key in MANUAL:
        return MANUAL[key]
    m = CR[key]
    title = tex_escape((m.get("title") or [""])[0])
    title = re.sub(r"(Staphylococcus aureus|Escherichia coli|Klebsiella pneumoniae|Enterococcus faecium|Pseudomonas aeruginosa|vanA)",
                   r"\\textit{\1}", title)
    jr = tex_escape((m.get("short-container-title") or m.get("container-title") or [""])[0])
    vol = tex_escape(m.get("volume", ""))
    iss = tex_escape(m.get("issue", "")).replace("Supplement\\_", "Suppl.~")
    pg = m.get("page") or m.get("article-number") or ""
    loc = (f"{vol}" + (f"({iss})" if iss else "") + (f":{re.sub(r'^(\\d+)-(\\d+)$', r'\\1--\\2', pg)}" if pg else "")) if vol else (
        re.sub(r'^(\d+)-(\d+)$', r'\1--\2', pg) if pg else "")
    doi = m["DOI"]
    au = authors(m)
    return (f"{au}{'' if au.endswith('.') else '.'} {title}. \\textit{{{jr}}}, {loc}, {year(m)}. "
            f"\\href{{https://doi.org/{doi}}}{{doi:{tex_escape(doi)}}}").replace(", , ", ", ")


if __name__ == "__main__":
    tex = open(os.path.join(HERE, "preprint.tex")).read()
    tex = re.sub(r"(?m)(?<!\\)%.*$", "", tex)
    order = []
    for grp in re.findall(r"\\cite\{([^}]+)\}", tex):
        for k in grp.split(","):
            k = k.strip()
            if k and k not in order:
                order.append(k)
    missing = [k for k in order if k not in CR and k not in MANUAL]
    if missing:
        raise SystemExit(f"cited but not defined: {missing}")
    unused = [k for k in list(CR) + list(MANUAL) if k not in order]
    with open(os.path.join(HERE, "references.tex"), "w") as f:
        f.write("% Auto-generated by make_refs.py from Crossref records (crossref_raw.json). Do not edit.\n")
        f.write("\\begin{thebibliography}{%d}\n" % len(order))
        for k in order:
            f.write(f"\\bibitem{{{k}}} {fmt(k)}\n\n")
        f.write("\\end{thebibliography}\n")
    print(f"{len(order)} references written; unused entries: {unused}")

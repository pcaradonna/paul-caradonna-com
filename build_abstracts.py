#!/usr/bin/env python3
"""
build_abstracts.py
Extracts abstracts for all papers in the website:
  1. CrossRef API (for papers with a real DOI)
  2. pdftotext fallback (for preprints / missing CrossRef abstracts)
Outputs: data/abstracts.json
"""

import json, re, subprocess, time, urllib.request, urllib.error, html
from pathlib import Path

# ── Paper data (id, doi, pdf path) ───────────────────────────────────────────
# Extracted from the papers array in index.html
PAPERS = [
    {"id": 0,  "doi": "10.1002/aps3.70026",              "pdf": "pdfs/benkendorf-caradonna-2025-aps.pdf"},
    {"id": 1,  "doi": None,                               "pdf": "pdfs/dorian-caradonna-2025-consbio.pdf"},
    {"id": 2,  "doi": "10.1111/oik.11151",                "pdf": "pdfs/cahill-caradonna-2025-oikos.pdf"},
    {"id": 3,  "doi": "10.1111/1365-2656.14205",          "pdf": "pdfs/fitzgerald-caradonna-2025-jae.pdf"},
    {"id": 4,  "doi": "10.1002/ecs2.70100",               "pdf": "pdfs/zink-caradonna-2024-ecosphere.pdf"},
    {"id": 5,  "doi": "10.1002/ece3.70026",               "pdf": "pdfs/vanvalkenburg-caradonna-2024-ee.pdf"},
    {"id": 6,  "doi": "10.1016/j.tree.2024.01.003",       "pdf": "pdfs/peralta-caradonna-2024-tree.pdf"},
    {"id": 7,  "doi": "10.1894/0038-4909-68.1.13",        "pdf": "pdfs/ingold-caradonna-2024-swnat.pdf"},
    {"id": 8,  "doi": None,                               "pdf": "pdfs/caradonna-dorf-2023-psb.pdf"},
    {"id": 9,  "doi": None,                               "pdf": None},
    {"id": 10, "doi": None,                               "pdf": "pdfs/sandacz-caradonna-2023-fcosc.pdf"},
    {"id": 11, "doi": "10.1002/ajb2.16112",               "pdf": "pdfs/iler-caradonna-2023-ajb.pdf"},
    {"id": 12, "doi": "10.1111/1365-2656.13799",          "pdf": "pdfs/ogilvie-caradonna-2022-jae.pdf"},
    {"id": 13, "doi": "10.1093/ee/nvac061",               "pdf": "pdfs/fitzgerald-ogilvie-caradonna-2022-ee.pdf"},
    {"id": 14, "doi": "10.1002/ecs2.4154",                "pdf": "pdfs/bain-caradonna-2022-ecosphere.pdf"},
    {"id": 15, "doi": "10.1111/1365-2656.13779",          "pdf": "pdfs/semmler-caradonna-2022-jae.pdf"},
    {"id": 16, "doi": None,                               "pdf": "pdfs/finkelstein-caradonna-2022-jpe.pdf"},
    {"id": 17, "doi": "10.1098/rsbl.2022.0016",           "pdf": "pdfs/finkelstein-caradonna-2022-biolletts.pdf"},
    {"id": 18, "doi": "10.1111/ele.13653",                "pdf": "pdfs/caradonna-burkle-2021-ecollett.pdf"},
    {"id": 19, "doi": "10.1146/annurev-ecolsys-011921-015133", "pdf": "pdfs/iler-caradonna-2021-annurev.pdf"},
    {"id": 20, "doi": "10.1002/ecs2.3828",                "pdf": "pdfs/iler-caradonna-2021-ecosphere.pdf"},
    {"id": 21, "doi": "10.1007/s00442-021-05040-0",       "pdf": "pdfs/endres-caradonna-iler-2021-oecologia.pdf"},
    {"id": 22, "doi": "10.1093/ee/nvab055",               "pdf": "pdfs/gruver-caradonna-2021-ee.pdf"},
    {"id": 23, "doi": "10.1007/s10530-021-02677-z",       "pdf": "pdfs/hui-caradonna-2021-biolinv.pdf"},
    {"id": 24, "doi": "10.1111/oik.07526",                "pdf": "pdfs/caradonna-waser-2020-oikos.pdf"},
    {"id": 25, "doi": "10.1111/oik.07303",                "pdf": "pdfs/schwarz-caradonna-2020-oikos.pdf"},
    {"id": 26, "doi": None,                               "pdf": "pdfs/gruver-caradonna-2020-gle.pdf"},
    {"id": 27, "doi": "10.1073/pnas.1918584117",          "pdf": "pdfs/cordes-caradonna-2020-pnas.pdf"},
    {"id": 28, "doi": "10.1038/s41467-020-17894-y",       "pdf": "pdfs/bramon-mora-caradonna-2020-natcomm.pdf"},
    {"id": 29, "doi": "10.1111/1365-2745.13190",          "pdf": "pdfs/iler-caradonna-2019-jecol.pdf"},
    {"id": 30, "doi": "10.1002/ecs2.2645",                "pdf": "pdfs/cameron-caradonna-2019-ecosphere.pdf"},
    {"id": 31, "doi": "10.1086/702551",                   "pdf": "pdfs/forrest-caradonna-2019-amnat.pdf"},
    {"id": 32, "doi": "10.1086/699827",                   "pdf": "pdfs/waser-caradonna-price-2018-amnat.pdf"},
    {"id": 33, "doi": "10.1111/1365-2435.13151",          "pdf": "pdfs/caradonna-cunningham-iler-2018-funeco.pdf"},
    {"id": 34, "doi": "10.1002/bes2.1384",                "pdf": "pdfs/ellison-caradonna-2018-besa.pdf"},
    {"id": 35, "doi": "10.1111/ele.12740",                "pdf": "pdfs/caradonna-petry-2017-ecollett.pdf"},
    {"id": 36, "doi": "10.1111/1365-2745.12482",          "pdf": "pdfs/caradonna-bain-2016-jecol.pdf"},
    {"id": 37, "doi": "10.1890/14-0547.1",                "pdf": "pdfs/caradonna-inouye-2015-ecology.pdf"},
    {"id": 38, "doi": "10.1111/oik.01303",                "pdf": "pdfs/rafferty-caradonna-2015-oikos.pdf"},
    {"id": 39, "doi": "10.1073/pnas.1323073111",          "pdf": "pdfs/caradonna-iler-inouye-2014-pnas.pdf"},
    {"id": 40, "doi": "10.1002/ece3.722",                 "pdf": "pdfs/rafferty-caradonna-2013-ecoevo.pdf"},
    {"id": 41, "doi": "10.1890/12-0255.1",                "pdf": "pdfs/mckinney-caradonna-2012-ecology.pdf"},
    {"id": 42, "doi": None,                               "pdf": "pdfs/caradonna-ackerman-2012-cjs.pdf"},
    {"id": 43, "doi": "10.32942/X2S63Z",                  "pdf": "pdfs/dormann-caradonna-2025-ecoevorxiv.pdf"},
    {"id": 44, "doi": "10.1098/rspb.2025.0643",           "pdf": "pdfs/bain-caradonna-2025-procb.pdf"},
    {"id": 45, "doi": "10.1101/2025.10.08.680666",        "pdf": "pdfs/sakhalkar-caradonna-2025-biorxiv.pdf"},
    {"id": 46, "doi": "10.1002/fee.2863",                 "pdf": "pdfs/caradonna-2025-fee-curiosity.pdf"},
    {"id": 47, "doi": "10.64898/2025.12.19.695174",       "pdf": "pdfs/kirschke-caradonna-2025-biorxiv.pdf"},
    {"id": 48, "doi": "10.1101/2025.10.29.685396",        "pdf": "pdfs/godtfredsen-caradonna-2025-biorxiv.pdf"},
    {"id": 49, "doi": "10.64898/2026.02.11.705202",       "pdf": "pdfs/simpson-caradonna-2026-biorxiv.pdf"},
    {"id": 50, "doi": None,                               "pdf": "pdfs/murphy-caradonna-2026-fee.pdf"},
    {"id": 51, "doi": "10.1002/ecs2.70566",               "pdf": "pdfs/dorian-caradonna-2026-ecosphere.pdf"},
    {"id": 52, "doi": None,                               "pdf": "pdfs/catchen-caradonna-2026-biorxiv.pdf"},
    {"id": 53, "doi": "10.64898/2026.05.20.726591",       "pdf": "pdfs/iler-caradonna-petry-2026-biorxiv.pdf"},
]

BASE_DIR = Path(__file__).parent


def clean_abstract(text):
    """Strip JATS XML tags and normalize whitespace."""
    text = re.sub(r'<jats:[^>]+>', ' ', text)
    text = re.sub(r'</jats:[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_crossref(doi):
    """Return abstract string from CrossRef, or None."""
    url = f"https://api.crossref.org/works/{doi}"
    req = urllib.request.Request(url, headers={"User-Agent": "paul-caradonna-website/1.0 (mailto:pcaradonna@chicagobotanic.org)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        abstract = data.get("message", {}).get("abstract", "")
        return clean_abstract(abstract) if abstract else None
    except Exception as e:
        print(f"    CrossRef error for {doi}: {e}")
        return None


def extract_pdf_abstract(pdf_rel_path):
    """Extract abstract section from PDF using pdftotext."""
    pdf_path = BASE_DIR / pdf_rel_path
    if not pdf_path.exists():
        return None
    try:
        result = subprocess.run(
            ["pdftotext", "-l", "3", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=15
        )
        text = result.stdout
    except Exception as e:
        print(f"    pdftotext error: {e}")
        return None

    # Find "Abstract" header and grab text until the next major section
    match = re.search(
        r'\bAbstract[:\s]*\n?([\s\S]{80,2000}?)(?=\n\s*(?:Introduction|Keywords|Background|1[\.\s]|Plain[\s_]Language|\Z))',
        text, re.IGNORECASE
    )
    if match:
        abstract = re.sub(r'\s+', ' ', match.group(1)).strip()
        # Truncate at "Keywords" if it snuck in
        abstract = re.split(r'\s*Keywords?[:\s]', abstract, flags=re.IGNORECASE)[0].strip()
        return abstract if len(abstract) > 50 else None

    # Broader fallback: just grab text after "Abstract" label
    match2 = re.search(r'\bAbstract[:\s]*\n?([\s\S]{80,1500})', text, re.IGNORECASE)
    if match2:
        abstract = re.sub(r'\s+', ' ', match2.group(1)[:1200]).strip()
        abstract = re.split(r'\s*Keywords?[:\s]', abstract, flags=re.IGNORECASE)[0].strip()
        return abstract if len(abstract) > 50 else None

    return None


def main():
    output_path = BASE_DIR / "data" / "abstracts.json"

    # Load existing results so we can resume if interrupted
    if output_path.exists():
        with open(output_path) as f:
            abstracts = json.load(f)
        print(f"Resuming — {len(abstracts)} abstracts already saved.\n")
    else:
        abstracts = {}

    total = len(PAPERS)
    for i, paper in enumerate(PAPERS):
        pid = str(paper["id"])
        if pid in abstracts:
            print(f"[{i+1}/{total}] id:{pid} — already done, skipping")
            continue

        print(f"[{i+1}/{total}] id:{pid}", end="  ")

        abstract = None

        # 1. Try CrossRef
        if paper["doi"]:
            print(f"CrossRef ({paper['doi']})...", end=" ")
            abstract = fetch_crossref(paper["doi"])
            if abstract:
                print("✓")
            else:
                print("no abstract")
            time.sleep(0.3)  # be polite to the API

        # 2. Fall back to PDF
        if not abstract and paper["pdf"]:
            print(f"    → pdftotext fallback...", end=" ")
            abstract = extract_pdf_abstract(paper["pdf"])
            print("✓" if abstract else "failed")

        if abstract:
            abstracts[pid] = abstract
        else:
            abstracts[pid] = ""  # mark as attempted

        # Save after each paper so progress isn't lost
        with open(output_path, "w") as f:
            json.dump(abstracts, f, indent=2, ensure_ascii=False)

    filled = sum(1 for v in abstracts.values() if v)
    print(f"\nDone. {filled}/{total} abstracts collected → data/abstracts.json")


if __name__ == "__main__":
    main()

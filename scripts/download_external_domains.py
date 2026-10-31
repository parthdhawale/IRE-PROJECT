"""Download a small, diverse sample of non-legal documents for the family-classification
go/no-go test (legal vs. scientific vs. financial vs. literature).

Writes data/cache/external_domains.parquet (columns: domain, doc_id, text) and
results/notes/external_domains_samples.md (a few example titles per domain, for a manual check
that each domain is actually what it claims to be -- the Gutenberg source in particular mixes
historical/political documents in with fiction, so literature is filtered by Library of Congress
classification (locc starting with "P" = language & literature) to exclude those.

Sources (chosen for reliable, low-friction HTTPS access -- see results/notes/phase1.md and the
LegalBench-RAG download for what unreliable sources look like):
- scientific: gfissore/arxiv-abstracts-2021 (title + abstract, diverse across arXiv categories)
- financial:  winterForestStump/10-K_sec_filings (real SEC 10-K sections: Business, Risk Factors)
- literature: sedthh/gutenberg_english, filtered to locc starting with "P"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config  # noqa: E402

MAX_K = 200
BUFFER = 300  # collect a bit more than MAX_K, since literature needs post-hoc filtering
EXCERPT_CHARS = 2000  # stored excerpt length; classification later truncates further if needed


def literature_docs(seed: int, n: int) -> list[dict]:
    ds = load_dataset("sedthh/gutenberg_english", split="train", streaming=True)
    ds = ds.shuffle(seed=seed, buffer_size=20000)
    docs = []
    for rec in ds:
        meta = json.loads(rec["METADATA"])
        locc = (meta.get("locc") or "").strip()
        if not locc.startswith("P"):
            continue  # not language & literature (locc) -- excludes the political/legal texts
        docs.append({"domain": "literature", "doc_id": f"gutenberg_{meta.get('text_id')}",
                    "text": rec["TEXT"][:EXCERPT_CHARS]})
        if len(docs) >= n:
            break
    return docs


def scientific_docs(seed: int, n: int) -> list[dict]:
    ds = load_dataset("gfissore/arxiv-abstracts-2021", split="train", streaming=True)
    ds = ds.shuffle(seed=seed, buffer_size=20000)
    docs = []
    for rec in ds:
        text = f"{rec['title']}\n{rec['abstract']}"
        docs.append({"domain": "scientific", "doc_id": f"arxiv_{rec['id']}",
                    "text": text[:EXCERPT_CHARS]})
        if len(docs) >= n:
            break
    return docs


def financial_docs(seed: int, n: int) -> list[dict]:
    ds = load_dataset("winterForestStump/10-K_sec_filings", split="001", streaming=True)
    ds = ds.shuffle(seed=seed, buffer_size=20000)
    docs = []
    for rec in ds:
        text = f"{rec['company_name']}\n{rec['Business'] or ''}\n{rec['Risk Factors'] or ''}"
        if len(text.strip()) < 100:
            continue  # skip filings with empty/near-empty sections
        docs.append({"domain": "financial", "doc_id": f"sec10k_{rec['cik']}",
                    "text": text[:EXCERPT_CHARS]})
        if len(docs) >= n:
            break
    return docs


def main() -> None:
    cfg = load_config()
    cache = Path(cfg["paths"]["cache"])
    out = cache / "external_domains.parquet"
    if out.exists():
        print(f"{out} already exists, skipping (delete it to force a re-download)")
        return

    seed = cfg["seed"]
    print("downloading literature (filtered to locc startswith 'P')...")
    lit = literature_docs(seed, BUFFER)
    print(f"  got {len(lit)} literature docs")
    print("downloading scientific abstracts...")
    sci = scientific_docs(seed, BUFFER)
    print(f"  got {len(sci)} scientific docs")
    print("downloading financial filings...")
    fin = financial_docs(seed, BUFFER)
    print(f"  got {len(fin)} financial docs")

    df = pd.DataFrame(lit + sci + fin)
    cache.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)

    notes = Path(cfg["paths"]["notes"])
    notes.mkdir(parents=True, exist_ok=True)
    lines = ["# External domain samples (family-classification go/no-go test)", "",
             f"Counts: {df.groupby('domain').size().to_dict()}", "",
             "First 70 chars of 5 examples per domain, for a manual sanity check:", ""]
    for domain, g in df.groupby("domain"):
        lines.append(f"## {domain}")
        for text in g["text"].head(5):
            lines.append(f"- {text[:70].replace(chr(10), ' ')}")
        lines.append("")
    (notes / "external_domains_samples.md").write_text("\n".join(lines))
    print(f"wrote {out} ({len(df)} docs) and external_domains_samples.md")


if __name__ == "__main__":
    main()

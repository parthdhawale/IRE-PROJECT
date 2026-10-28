"""Phase 0: span sanity checks + corpus statistics table.

Writes results/tables/corpus_stats.md and results/tables/cuad_types.csv.
Exits non-zero if any gold span fails the round-trip check.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config  # noqa: E402
from trr.data.cuad_types import cuad_type, exhibit_title  # noqa: E402
from trr.data.load import load_corpus, load_queries  # noqa: E402
from trr.data.sanity import check_subset  # noqa: E402


def main() -> None:
    cfg = load_config()
    raw, tables = cfg["paths"]["raw"], Path(cfg["paths"]["tables"])
    tables.mkdir(parents=True, exist_ok=True)
    n_mini = cfg["data"]["mini_per_subset"]

    corpus_rows, query_rows, all_ok = [], [], True
    cuad_docs = []
    for subset in cfg["data"]["subsets"]:
        docs = load_corpus(raw, subset)
        full = load_queries(raw, subset, "full", n_mini)
        mini = load_queries(raw, subset, "mini", n_mini)
        check = check_subset(docs, full)
        all_ok &= check["ok"]
        lens = np.array([len(d.text) for d in docs])
        corpus_rows.append({
            "subset": subset, "docs": len(docs), "total_chars": int(lens.sum()),
            "min": int(lens.min()), "median": int(np.median(lens)),
            "mean": int(lens.mean()), "max": int(lens.max()),
            "chunks_500": int(np.ceil(lens / cfg["chunking"]["chunk_chars"]).sum()),
        })
        snippets_per_q = [len(q.gold) for q in full]
        query_rows.append({
            "subset": subset, "queries_full": len(full), "queries_mini": len(mini),
            "docs_touched_mini": len({d for q in mini for d in q.gold_docs}),
            "multi_doc_queries": check.get("multi_doc_queries", 0),
            "snippets": check["snippets"], "mean_snippets_per_q": round(float(np.mean(snippets_per_q)), 2),
            "round_trip": f"{check['round_trip']:.1%}", "ok": check["ok"],
        })
        if subset == "cuad":
            cuad_docs = [d.doc_id for d in docs]

    cdf, qdf = pd.DataFrame(corpus_rows), pd.DataFrame(query_rows)
    total = {"subset": "ALL", **{c: int(cdf[c].sum()) for c in ["docs", "total_chars", "chunks_500"]}}
    cdf = pd.concat([cdf, pd.DataFrame([total])], ignore_index=True)
    qtotal = {"subset": "ALL", **{c: int(qdf[c].sum()) for c in
              ["queries_full", "queries_mini", "docs_touched_mini", "multi_doc_queries", "snippets"]}}
    qdf = pd.concat([qdf, pd.DataFrame([qtotal])], ignore_index=True)

    types = pd.DataFrame({"doc_id": cuad_docs,
                          "title": [exhibit_title(d) for d in cuad_docs],
                          "cuad_type": [cuad_type(d) for d in cuad_docs]})
    types.to_csv(tables / "cuad_types.csv", index=False)
    type_counts = Counter(types["cuad_type"])
    tdf = pd.DataFrame(sorted(type_counts.items(), key=lambda kv: -kv[1]), columns=["cuad_type", "docs"])

    md = ["# Corpus statistics (LegalBench-RAG)", "",
          "## Documents (characters)", "", cdf.astype(object).fillna("").to_markdown(index=False), "",
          "## Queries", "",
          f"Mini = {n_mini} queries per subset, selected as in legalbenchrag/benchmark.py. "
          "The retrieval pool for every query is the full subset corpus.", "",
          qdf.astype(object).fillna("").to_markdown(index=False), "",
          "## CUAD contract types (parsed from file names, evaluation only)", "",
          tdf.to_markdown(index=False), ""]
    (tables / "corpus_stats.md").write_text("\n".join(md))
    print("\n".join(md))
    if not all_ok:
        sys.exit("span sanity check FAILED - see table above")


if __name__ == "__main__":
    main()

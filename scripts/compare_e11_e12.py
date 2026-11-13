"""E11 vs E12 query by query on CLERC: do lexical and dense document choice fail on different queries?

    python scripts/compare_e11_e12.py

Reads the per-query test run files of both experiments (results/runs/<method>_test_clerc_clerc.jsonl;
same pool, split and queries) and reports, at document recall@1:
- for each pair of methods, how many queries both / only one / neither get right, and the share
  that at least one gets right (the ceiling of any per-query choice between the two);
- an EXPLORATORY probe (not pre-registered, not a method claim): reciprocal rank fusion of the two
  ranked case lists (each pipeline stores its top `clerc.doc_list` cases), scored like the runs,
  with a paired bootstrap against full-query BM25 doc-first that resamples gold cases.
IR idea: fusion can only help where the two rankers disagree; the overlap counts say how much room
there is, and plain RRF says how much of it a rank-only fusion captures.
Writes results/tables/e11_e12_compare_clerc.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config  # noqa: E402
from trr.eval.experiment import doc_level_ci  # noqa: E402
from trr.eval.metrics import document_ranking_metrics  # noqa: E402

METHODS = {   # short name -> run name (E11 lexical, E12 dense)
    "bm25_docfirst": "mixed_docfirst_bm25",
    "bm25_chunks": "mixed_bm25",
    "band_selected": "band_band_df5_mx25_k16_b3_r10_bm25",
    "band_none": "band_none_df5_mx25_k16_r10_bm25",
    "emb_selected": "emb_band_k32_b3_mean",
    "emb_none": "emb_none_k32_mean",
    "dense_chunks": "mixed_dense",
}
PAIRS = [("bm25_docfirst", "emb_none"), ("bm25_docfirst", "emb_selected"), ("band_selected", "emb_selected"),
         ("bm25_docfirst", "band_none"), ("bm25_docfirst", "bm25_chunks"), ("emb_none", "dense_chunks")]
FUSE = [("bm25_docfirst", "emb_none"), ("bm25_docfirst", "emb_selected"), ("band_selected", "emb_selected")]
BASE = "bm25_docfirst"


def ranked_cases(rec: dict) -> list[str]:
    """The pipeline's ranked cases, else the cases of a flat retriever's hits in first-seen order."""
    docs = rec.get("diag", {}).get("docs")
    if docs:
        return docs
    return list(dict.fromkeys(h["doc_id"] for h in rec["hits"]))


def load_run(name: str, runs: Path, n: int) -> dict[str, dict]:
    lines = (runs / f"{name}_test_clerc_clerc.jsonl").read_text().splitlines()[1:]   # line 0 = header
    out = {}
    for line in lines:
        r = json.loads(line)
        out[r["qid"]] = {"qid": r["qid"], "subset": r["subset"], "gold_docs": r["gold_docs"],
                         "ranked": ranked_cases(r)[:n]}
    return out


def scored(recs: dict[str, dict], n: int) -> dict[str, dict]:
    for r in recs.values():
        r.update(document_ranking_metrics(r["ranked"], set(r["gold_docs"]), [1, n]))
    return recs


def rrf(lists: list[list[str]], k: int) -> list[str]:
    """Reciprocal rank fusion: score(d) = sum over lists of 1 / (k + rank of d)."""
    score: dict[str, float] = {}
    for ranked in lists:
        for i, d in enumerate(ranked):
            score[d] = score.get(d, 0.0) + 1.0 / (k + i + 1)
    return sorted(score, key=lambda d: -score[d])   # stable: ties keep the first list's order


def main() -> None:
    cfg = load_config()
    n, rrf_k = cfg["clerc"]["doc_list"], cfg["hybrid"]["rrf_k"]
    runs = Path(cfg["paths"]["runs"])
    data = {m: scored(load_run(name, runs, n), n) for m, name in METHODS.items()}
    qids = sorted(data[BASE])
    for m, recs in data.items():   # the two experiments must have scored the same queries and gold
        assert sorted(recs) == qids, m
        assert all(recs[q]["gold_docs"] == data[BASE][q]["gold_docs"] for q in qids), m
    hit = {m: pd.Series({q: data[m][q]["rdoc_recall@1"] for q in qids}).astype(bool) for m in data}

    rows = []
    for a, b in PAIRS:
        A, B = hit[a], hit[b]
        rows.append({"a": a, "b": b, "a r@1": A.mean(), "b r@1": B.mean(), "both": int((A & B).sum()),
                     "only a": int((A & ~B).sum()), "only b": int((~A & B).sum()),
                     "either r@1": (A | B).mean()})
    overlap = pd.DataFrame(rows)

    rows = []
    for a, b in FUSE:
        fused = {q: {**data[a][q], "ranked": rrf([data[a][q]["ranked"], data[b][q]["ranked"]], rrf_k)[:n]}
                 for q in qids}
        fused = scored(fused, n)
        row = {"fused": f"rrf({a}, {b})"}
        for metric in ("rdoc_recall@1", f"rdoc_recall@{n}", "rdoc_mrr"):
            row[metric] = sum(fused[q][metric] for q in qids) / len(qids)
        mean, lo, hi, _ = doc_level_ci(list(fused.values()), list(data[BASE].values()), "rdoc_recall@1", cfg)
        row.update({"r@1 - bm25_docfirst": mean, "lo": lo, "hi": hi, "real": "yes" if lo > 0 or hi < 0 else "no"})
        rows.append(row)
    fusion = pd.DataFrame(rows)

    out = Path(cfg["paths"]["tables"]) / "e11_e12_compare_clerc.md"
    out.write_text(
        f"# E11 vs E12 on CLERC, query by query ({len(qids)} test queries)\n\n"
        "## Who gets the case right at recall@1\n\n" + overlap.to_markdown(index=False, floatfmt=".3f") +
        f"\n\n## Exploratory: plain RRF (k={rrf_k}) of two top-{n} case lists (not pre-registered)\n\n"
        "CI = paired bootstrap resampling gold cases, against full-query BM25 doc-first.\n\n" +
        fusion.to_markdown(index=False, floatfmt=".3f") + "\n")
    print(out.read_text())


if __name__ == "__main__":
    main()

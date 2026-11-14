"""E13 error analysis: held-out passage queries on CLERC, query by query and by error type.

    python scripts/analyse_e13.py [--docs PATH]

Reads the per-query test runs of both sides (results/runs/<method>_test_clerc_heldout_q<N>_clerc.jsonl),
the held-out query file and the pool texts, and reports at document recall@1, per query length:
- for pairs of methods, how many queries both / only one / neither get right (the "either" share is
  the ceiling of any per-query choice between the two);
- on the queries where the rare band fires (no clusters), its recall@1 against full-query BM25;
- recall@1 by how many *names* of the query are still in the rest of its case. A name = a capitalised
  word found in at most `name_max_cases` pool cases (parties, places, witnesses). IR idea: in known-item
  search the rare shared words are the evidence; a query with none has only topic words to go on;
- what the wrong top case is: a near-duplicate text of the gold (>= `dup_containment` of the smaller
  case's word 8-grams in the other), another opinion of the same dispute (shares >= `sibling_min_names`
  names with the gold), or a different dispute (usually on the same legal topic). The same name rule
  on random case pairs gives the rate at which it fires by chance.
Writes results/tables/e13_analysis_clerc_heldout.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config  # noqa: E402
from trr.data import clerc  # noqa: E402

METHODS = {   # short name -> run name (selected settings from the E13 dev search)
    "bm25_docfirst": "mixed_docfirst_bm25",
    "bm25_chunks": "mixed_bm25",
    "band_selected": "band_band_df2_mx50_k8_b3_r2_bm25",
    "band_none": "band_none_df2_mx50_k8_r2_bm25",
    "emb_selected": "emb_band_k8_b3_maxp",
    "emb_none": "emb_none_k8_maxp",
    "dense_chunks": "mixed_dense",
}
PAIRS = [("bm25_docfirst", "emb_none"), ("band_selected", "emb_selected"), ("bm25_docfirst", "band_none"),
         ("bm25_docfirst", "bm25_chunks"), ("emb_none", "dense_chunks")]
ERRORS = ["bm25_docfirst", "emb_none"]          # doc-first methods: their top case is the chosen case
CAPITALISED = re.compile(r"\b[A-Z][A-Za-z'\-]{2,}\b")
WORD = re.compile(r"\w+")


def load_run(name: str, runs: Path, length: int) -> dict[str, dict]:
    lines = (runs / f"{name}_test_clerc_heldout_q{length}_clerc.jsonl").read_text().splitlines()[1:]
    out = {}
    for line in lines:
        r = json.loads(line)
        docs = r.get("diag", {}).get("docs") or list(dict.fromkeys(h["doc_id"] for h in r["hits"]))
        out[r["qid"]] = {"gold": r["gold_docs"][0], "top": docs[0] if docs else None, "hit": r["doc_recall@1"] == 1.0,
                         "fallback": r.get("diag", {}).get("fallback")}
    return out


def caps(text: str) -> set[str]:
    return set(CAPITALISED.findall(text))


def main() -> None:
    cfg = load_config()
    a = cfg["clerc"]["heldout"]["analysis"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=Path, default=clerc.pool_dir(cfg) / "docs.parquet")
    args = ap.parse_args()
    runs, lengths = Path(cfg["paths"]["runs"]), cfg["clerc"]["heldout"]["lengths"]

    docs = pd.read_parquet(args.docs)
    text = {f"clerc/{c}": t for c, t in zip(docs.case_id, docs.text)}
    names_of = {d: caps(t) for d, t in text.items()}
    case_df = Counter(w for s in names_of.values() for w in s)          # cases containing the word
    rare = {d: {w for w in s if case_df[w] <= a["name_max_cases"]} for d, s in names_of.items()}
    q = pd.read_parquet(clerc.heldout_dir(cfg) / "queries.parquet").set_index("qid")

    @lru_cache(maxsize=None)
    def shingles(d: str) -> frozenset:
        w, n = WORD.findall(text[d].lower()), a["dup_shingle"]
        return frozenset(hash(tuple(w[i:i + n])) for i in range(len(w) - n + 1))

    def kind(gold: str, wrong: str) -> str:
        sg, sw = shingles(gold), shingles(wrong)
        if len(sg & sw) >= a["dup_containment"] * min(len(sg), len(sw)):
            return "near-duplicate text"
        return "same dispute" if len(rare[gold] & rare[wrong]) >= a["sibling_min_names"] else "different dispute"

    rng = np.random.default_rng(cfg["seed"])
    ids = sorted(text)
    pairs = rng.choice(len(ids), size=(a["random_pairs"], 2))
    chance = np.mean([len(rare[ids[i]] & rare[ids[j]]) >= a["sibling_min_names"] for i, j in pairs if i != j])

    overlap, by_names, errors, band = [], [], [], []
    for length in lengths:
        data = {m: load_run(name, runs, length) for m, name in METHODS.items()}
        qids = sorted(data["bm25_docfirst"])
        for m, recs in data.items():     # both sides scored the same queries with the same gold
            assert sorted(recs) == qids and all(recs[i]["gold"] == data["bm25_docfirst"][i]["gold"] for i in qids), m
        hit = {m: pd.Series({i: data[m][i]["hit"] for i in qids}) for m in data}
        for x, y in PAIRS:
            X, Y = hit[x], hit[y]
            overlap.append({"words": length, "a": x, "b": y, "a r@1": X.mean(), "b r@1": Y.mean(),
                            "both": int((X & Y).sum()), "only a": int((X & ~Y).sum()),
                            "only b": int((~X & Y).sum()), "either r@1": (X | Y).mean()})

        fired = [i for i in qids if data["band_none"][i]["fallback"] is False]   # a word in exactly one case
        band.append({"words": length, "band fired": len(fired), "share": len(fired) / len(qids),
                     "rare band r@1": hit["band_none"][fired].mean(), "full-query BM25 r@1": hit["bm25_docfirst"][fired].mean(),
                     "full-query BM25 r@1, rest": hit["bm25_docfirst"].drop(fired).mean()})

        n_names = {}
        for i in qids:      # rare names of the query that are still in the rest of its own case
            row, gold = q.loc[i], data["bm25_docfirst"][i]["gold"]
            s, e, full = int(row["start"]), int(row[f"end_{length}"]), int(row[f"end_{max(lengths)}"])
            rest = text[gold][:s] + text[gold][full:]
            n_names[i] = len({w for w in caps(text[gold][s:e]) if case_df[w] <= a["name_max_cases"]} & caps(rest))
        bucket = pd.Series({i: "0" if n == 0 else "1-2" if n <= 2 else "3+" for i, n in n_names.items()})
        for b in ("0", "1-2", "3+"):
            sel = bucket[bucket == b].index
            by_names.append({"words": length, "names in query": b, "queries": len(sel),
                             **{f"{m} r@1": hit[m][sel].mean() for m in ("bm25_docfirst", "band_selected",
                                                                           "emb_none", "emb_selected")}})

        for m in ERRORS:
            wrong = [(r["gold"], r["top"]) for r in data[m].values() if not r["hit"] and r["top"]]
            c = Counter(kind(g, w) for g, w in wrong)
            errors.append({"words": length, "method": m, "errors": len(wrong),
                           **{k: c[k] / len(wrong) for k in ("near-duplicate text", "same dispute", "different dispute")}})

    out = Path(cfg["paths"]["tables"]) / "e13_analysis_clerc_heldout.md"
    out.write_text(
        f"# E13 error analysis: held-out passage queries on CLERC ({len(qids)} test queries per length)\n\n"
        f"Name = capitalised word in at most {a['name_max_cases']} of {len(ids)} pool cases.\n\n"
        "## Who gets the case right at recall@1\n\n" + pd.DataFrame(overlap).to_markdown(index=False, floatfmt=".3f") +
        "\n\n## When the rare band fires (no clusters; the query has a word found in exactly one case)\n\n"
        "Otherwise it falls back to full-query BM25, so the two agree on the rest.\n\n" +
        pd.DataFrame(band).to_markdown(index=False, floatfmt=("g", "g", ".3f", ".3f", ".3f", ".3f")) +
        "\n\n## Recall@1 by the number of names the query shares with the rest of its case\n\n" +
        pd.DataFrame(by_names).to_markdown(index=False, floatfmt=".3f") +
        "\n\n## What the wrong top case is (share of errors)\n\n"
        f"Near-duplicate = at least {a['dup_containment']} of the smaller case's word {a['dup_shingle']}-grams "
        f"in the other; same dispute = at least {a['sibling_min_names']} shared names. The name rule fires on "
        f"{chance:.3f} of {a['random_pairs']} random case pairs.\n\n" +
        pd.DataFrame(errors).to_markdown(index=False, floatfmt=".3f") + "\n")
    print(out.read_text())


if __name__ == "__main__":
    main()

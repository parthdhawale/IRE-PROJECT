"""Draw the dev / test query split (trr.eval.splits) and report its size per subset.

    python scripts/make_query_split.py   # -> results/tables/query_split.md (+ .csv of qid -> side)

The split is deterministic (leak-safe routing folds, fixed seed), so any script can recompute it;
the CSV is a record of exactly which queries were dev and which were test.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config, set_seeds  # noqa: E402
from trr.data.load import load_corpus, load_queries  # noqa: E402
from trr.eval.splits import split_queries  # noqa: E402
from trr.routing.prep import legalbench_doc_folds  # noqa: E402


def main() -> None:
    cfg = load_config()
    set_seeds(cfg["seed"])
    raw, subsets, dev_folds = cfg["paths"]["raw"], cfg["data"]["subsets"], cfg["eval"]["dev_folds"]
    docs = [d for s in subsets for d in load_corpus(raw, s)]
    _, _, folds = legalbench_doc_folds(cfg, docs)
    queries = [q for s in subsets for q in load_queries(raw, s, "full")]
    side = split_queries(queries, folds, dev_folds)
    rows = pd.DataFrame({"qid": [q.qid for q in queries], "subset": [q.subset for q in queries],
                         "doc_id": [next(iter(q.gold_docs)) for q in queries],
                         "side": [side[q.qid] for q in queries]})
    summary = (rows.groupby(["subset", "side"]).agg(queries=("qid", "size"), documents=("doc_id", "nunique"))
               .unstack("side").fillna(0).astype(int))
    summary.columns = [f"{side}_{what}" for what, side in summary.columns]
    summary.loc["all"] = summary.sum()
    summary["dev_share_of_queries"] = (summary.dev_queries / (summary.dev_queries + summary.test_queries)).round(3)
    out = Path(cfg["paths"]["tables"]) / "query_split.md"
    out.write_text("# Dev / test query split (by gold document)\n\n"
                   f"Dev = queries whose gold document is in routing fold(s) {dev_folds} of {cfg['routing']['n_folds']} "
                   "(leak-safe: stratified by group, near-duplicates together); test = the rest.\n\n"
                   + summary.to_markdown() + "\n")
    rows.to_csv(out.with_suffix(".csv"), index=False)
    print(summary.to_string())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

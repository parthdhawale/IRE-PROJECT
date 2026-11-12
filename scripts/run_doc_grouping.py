"""Document grouping per level: is an UNSEEN document filed into the right group?

The indexing-time half of a group-first retriever: a new document must land in its group
without retraining. Same pool, groups, leak-safe folds and levels as scripts/run_routing.py
(flat reference, coarse gated at top-1, fine = CUAD contract types gated at top-3). In each fold
every classifier -- including the mid-frequency band and each group's word distribution -- is fit
on training documents only and ranks the groups for each held-out document.

Writes results/runs/doc_grouping.jsonl, results/tables/doc_grouping.md, results/notes/doc_grouping.md.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import git_hash, load_config, set_seeds  # noqa: E402
from trr.routing.evaluate import build_levels, end_to_end, gate_report, level_ranks, summarise  # noqa: E402
from trr.routing.prep import load_setup  # noqa: E402

NAMES = ["centroid", "vocab_lr", "band_lr", "nb_band", "nb_all", "centroid_full", "nb_band_bin", "cnb_band"]


def main() -> None:
    cfg = load_config()
    set_seeds(cfg["seed"])
    rc = cfg["routing"]
    S = load_setup(cfg, full_vectors=True)   # centroid_full needs whole-document vectors
    item_doc = np.arange(len(S.docs))

    levels = build_levels(S.doc_subset, S.doc_group, item_doc)
    results = {}
    for lv in levels:
        results[lv.name] = level_ranks(lv, NAMES, cfg, S.d_fold, S.doc_vecs, S.doc_tokens,
                                       S.d_fold, S.doc_vecs, S.doc_tokens, S.doc_vecs_full, S.doc_vecs_full)
        print(f"level {lv.name} done", flush=True)
    routers = list(results["flat"][0])

    runs = Path(cfg["paths"]["runs"])
    runs.mkdir(parents=True, exist_ok=True)
    with open(runs / "doc_grouping.jsonl", "w") as fh:
        fh.write(json.dumps({"_header": True, "git": git_hash(), "config": cfg}) + "\n")
        for i, doc_id in enumerate(S.doc_ids):
            fh.write(json.dumps({"doc_id": doc_id, "subset": str(S.doc_subset[i]), "group": str(S.doc_group[i]),
                                 "fold": int(S.d_fold[i]),
                                 **{f"{lv}_rank_{n}": int(results[lv][0][n][i]) for lv in results for n in routers},
                                 **{f"{lv}_top1_{n}": results[lv][1][n][i] for lv in results for n in routers}}) + "\n")

    rows = []
    for lv in levels:
        ci_b = rc["gates"].get(lv.name, {"b": rc["go_b"]})["b"]
        rows += summarise(lv.name, results[lv.name][0], lv.item_gold != "", S.doc_subset, item_doc,
                          rc["top_b"], ci_b, cfg)
    table = pd.DataFrame(rows).fillna("")
    gate_lines, _ = gate_report(table, rc["gates"])
    fine_b = rc["gates"]["fine"]["b"]
    e2e = end_to_end(results, S.doc_subset, fine_b)

    cuad = S.doc_subset == "cuad"
    fine_ranks, fine_top1 = results["fine"]
    per_type = (pd.DataFrame({"type": S.doc_group[cuad], **{n: fine_ranks[n][cuad] for n in routers}})
                .groupby("type").agg(docs=("type", "size"),
                                     **{f"{n}@1": (n, lambda r: round(float((r == 1).mean()), 2)) for n in routers})
                .sort_values("docs", ascending=False))
    fine_all = table[(table.level == "fine") & (table.subset == "ALL")].set_index("router")
    best_fine = fine_all[f"acc@{fine_b}"].astype(float).idxmax()
    miss = cuad & (fine_ranks[best_fine] > 1)
    confusions = Counter(zip(S.doc_group[miss], fine_top1[best_fine][miss])).most_common(10)

    md = table.to_markdown(index=False)
    tables, notes = Path(cfg["paths"]["tables"]), Path(cfg["paths"]["notes"])
    (tables / "doc_grouping.md").write_text("# Grouping of held-out documents, per level\n\n" + md + "\n\n"
                                            + "## Fine level, per contract type (top-1)\n\n" + per_type.to_markdown() + "\n")
    note = [
        "# Document grouping go/no-go, per level: are unseen documents filed correctly?\n", *gate_lines, "",
        f"End-to-end for CUAD documents (coarse top-1 correct AND contract type in fine top-{fine_b}): "
        + ", ".join(f"`{n}` {v:.3f}" for n, v in e2e.items()) + "\n",
        "## Setup\n",
        f"- {len(S.docs)} documents; same groups, {rc['n_folds']} leak-safe folds and levels as the query "
        "routing gate. Each document is classified once, by classifiers fit only on the other folds.",
        f"- Band = words in {rc['band_low']:.0%}-{rc['band_high']:.0%} of the training documents, recomputed "
        "per fold and per level from training documents only.",
        "- nb_band / nb_all: multinomial Naive Bayes on band / all words; band_lr / vocab_lr: logistic "
        "regression on band / discriminative words; centroid: embedding of the first "
        f"{rc['excerpt_chars']} characters; fused: reciprocal rank fusion of centroid and nb_band.",
        "- Gate values were set after the flat results had been seen (see routing_gate.md for the reasoning).\n",
        "## Results\n", md, "",
        "## Fine level, per contract type (top-1)\n", per_type.to_markdown(), "",
        f"## Most frequent fine-level confusions ({best_fine}, top-1)\n",
        *[f"- {n}x `{g}` -> `{p}`" for (g, p), n in confusions],
    ]
    (notes / "doc_grouping.md").write_text("\n".join(note) + "\n")
    print(md)
    print("\n".join(gate_lines))
    print("end-to-end CUAD:", e2e)


if __name__ == "__main__":
    main()

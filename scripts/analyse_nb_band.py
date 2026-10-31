"""Where and why does nb_band misfile held-out documents?

Refits nb_band exactly as scripts/run_doc_grouping.py does (same setup, folds and levels) and,
for every document filed under the wrong group at top-1, explains the decision. Naive Bayes is
additive in log space, so a document's preference for its predicted group over its gold group is
    sum_w count(w) * (log P(w | predicted) - log P(w | gold))    (+ the log-prior difference)
and the largest terms are the words that pulled it the wrong way.

Writes results/notes/nb_band_failures.md.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config, set_seeds  # noqa: E402
from trr.routing.evaluate import build_levels, make_router  # noqa: E402
from trr.routing.prep import load_setup  # noqa: E402

TOP_WORDS = 8
EXAMPLES = 15


def explain_level(level, S, cfg) -> pd.DataFrame:
    """One row per scored document: gold, predicted, length, and the words behind a miss."""
    rc, rows = cfg["routing"], []
    for f in range(rc["n_folds"]):
        tr = np.flatnonzero((S.d_fold != f) & (level.doc_labels != ""))
        te = np.flatnonzero((S.d_fold == f) & (level.item_gold != ""))
        router = make_router("nb_band", rc, cfg["seed"]).fit([S.doc_tokens[i] for i in tr], list(level.doc_labels[tr]))
        x = router.vec.transform([S.doc_tokens[i] for i in te])
        logp, prior = router.nb.feature_log_prob_, router.nb.class_log_prior_
        pred = router.scores([S.doc_tokens[i] for i in te]).argmax(axis=1)
        vocab = np.array(router.vec.get_feature_names_out())
        for row, i in enumerate(te):
            g, p = router.groups.index(level.item_gold[i]), pred[row]
            words = ""
            if g != p:
                xi = x[row].toarray().ravel()
                contrib = xi * (logp[p] - logp[g])
                top = np.argsort(-contrib)[:TOP_WORDS]
                words = ", ".join(f"{vocab[j]}({int(xi[j])})" for j in top if contrib[j] > 0)
            rows.append({"doc_id": S.doc_ids[i], "gold": level.item_gold[i], "pred": router.groups[p],
                         "hit": g == p, "band_tokens": int(x[row].sum()),
                         "prior_gap": round(float(prior[p] - prior[g]), 2), "pulled_by": words})
    return pd.DataFrame(rows)


def main() -> None:
    cfg = load_config()
    set_seeds(cfg["seed"])
    S = load_setup(cfg)
    levels = {lv.name: lv for lv in build_levels(S.doc_subset, S.doc_group, np.arange(len(S.docs)))}
    import json
    grouping = [json.loads(line) for line in open(Path(cfg["paths"]["runs"]) / "doc_grouping.jsonl")][1:]
    centroid_hit = {r["doc_id"]: {lv: r[f"{lv}_rank_centroid"] == 1 for lv in ("coarse", "fine")} for r in grouping}

    out = ["# Where nb_band misfiles held-out documents\n",
           "Same setup, folds and band as run_doc_grouping.py. For each miss, `pulled_by` lists the band words "
           "with the largest count * (log P(w|predicted) - log P(w|gold)), i.e. the words that pushed the "
           "document toward the wrong group (count in parentheses). `prior_gap` = log P(predicted) - log P(gold), "
           "the push from group size alone.\n"]
    for name in ("coarse", "fine"):
        df = explain_level(levels[name], S, cfg)
        miss = df[~df.hit]
        df["centroid_hit"] = [centroid_hit[d][name] for d in df.doc_id]
        both = (~df.hit & ~df.centroid_hit).sum()
        df["length_tercile"] = pd.qcut(df.band_tokens, 3, labels=["short", "medium", "long"])
        by_len = df.groupby("length_tercile", observed=True).hit.agg(["size", "mean"]).round(3)
        out += [f"## {name} level: {len(miss)} misses of {len(df)} documents (top-1 accuracy {df.hit.mean():.3f})\n",
                f"- Also missed by centroid: {both} of {len(miss)}; nb_band-only misses: {len(miss) - both}.",
                f"- Mean prior_gap on misses: {miss.prior_gap.mean():.2f} (positive = pushed toward the larger group).\n",
                "### Most frequent confusions (gold -> predicted)\n",
                *[f"- {n}x `{g}` -> `{p}`" for (g, p), n in Counter(zip(miss.gold, miss.pred)).most_common(12)], "",
                "### Accuracy by document length (band tokens)\n", by_len.to_markdown(), ""]
        if name == "fine":
            per = df.groupby("gold").agg(docs=("hit", "size"), nb_band=("hit", "mean"), centroid=("centroid_hit", "mean"))
            out += ["### Per contract type (top-1)\n", per.round(2).sort_values("nb_band").to_markdown(), ""]
        ex = miss.sort_values("prior_gap").head(EXAMPLES)
        out += [f"### Example misses ({name})\n",
                ex[["doc_id", "gold", "pred", "band_tokens", "prior_gap", "pulled_by"]].to_markdown(index=False), ""]
        print(f"{name}: {len(miss)} misses, {both} shared with centroid", flush=True)
    path = Path(cfg["paths"]["notes"]) / "nb_band_failures.md"
    path.write_text("\n".join(out) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()

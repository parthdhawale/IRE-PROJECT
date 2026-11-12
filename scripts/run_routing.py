"""Query routing per level of the group hierarchy: does a query reach its gold document's group?

Mixed pool of all 714 LegalBench-RAG documents. Levels (src/trr/routing/evaluate.py):
flat (28 groups, reference), coarse (4 subsets, gated at top-1) and fine (25 CUAD contract types,
trained and scored on CUAD only, gated at top-3), plus end-to-end for CUAD queries.
Leak-safe protocol: 5 document-level folds (stratified, near-duplicates kept together); routers
are fit on training-fold documents and scored on queries whose gold document is held out.
Queries are never used for fitting.

    python scripts/run_routing.py            # gates
    python scripts/run_routing.py --sweep    # + band_lr sensitivity to band edges (flat level)
    python scripts/run_routing.py --question-only   # strip the "Consider ...;" header from queries

Writes results/runs/routing_full.jsonl, results/tables/routing.md, results/notes/routing_gate.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import git_hash, load_config, set_seeds  # noqa: E402
from trr.data.load import load_queries  # noqa: E402
from trr.routing.evaluate import build_levels, end_to_end, gate_report, level_ranks, summarise  # noqa: E402
from trr.routing.prep import cached_embeddings, load_setup  # noqa: E402
from trr.routing.routers import VocabLRRouter, band_selector, gold_rank, tokenize_words  # noqa: E402

NAMES = ["centroid", "vocab_lr", "band_lr", "nb_band", "nb_all", "centroid_full", "nb_band_bin", "cnb_band"]


def question_only(text: str) -> str:
    """Drop the benchmark's header ("Consider the NDA between X and Y; ...") and keep the question,
    to test routing without the document-type and party names the header gives away."""
    return text.split(";", 1)[1].strip() if ";" in text else text


def band_sweep(cfg, S, level, q_fold, q_tokens, q_subset) -> pd.DataFrame:
    """band_lr at the flat level for every (low, high) pair -- reported only, never used to pick."""
    rc, rows = cfg["routing"], []
    for low in rc["band_sweep_low"]:
        for high in rc["band_sweep_high"]:
            r = np.zeros(len(q_fold), dtype=int)
            for f in range(rc["n_folds"]):
                tr, te = np.flatnonzero(S.d_fold != f), np.flatnonzero(q_fold == f)
                router = VocabLRRouter(band_selector(low, high), rc["lr_c"], rc["lr_max_iter"], cfg["seed"]).fit(
                    [S.doc_tokens[i] for i in tr], list(level.doc_labels[tr]))
                r[te] = gold_rank(router.scores([q_tokens[i] for i in te]), router.groups, list(level.item_gold[te]))
            hit = r <= rc["go_b"]
            rows.append({"low": low, "high": high, "acc@1": round(float((r <= 1).mean()), 3),
                         f"acc@{rc['go_b']}": round(float(hit.mean()), 3),
                         **{f"{s}@{rc['go_b']}": round(float(hit[q_subset == s].mean()), 3)
                            for s in cfg["data"]["subsets"]},
                         "fixed": "<- band used" if (low, high) == (rc["band_low"], rc["band_high"]) else ""})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true", help="also run the band_lr band-edge sweep")
    ap.add_argument("--question-only", action="store_true", help="route on the question without its header")
    args = ap.parse_args()
    cfg = load_config()
    set_seeds(cfg["seed"])
    rc, raw, subsets = cfg["routing"], cfg["paths"]["raw"], cfg["data"]["subsets"]
    S = load_setup(cfg, full_vectors=True)   # centroid_full needs whole-document vectors

    queries = [q for s in subsets for q in load_queries(raw, s, "full")]
    mini = {q.qid for s in subsets for q in load_queries(raw, s, "mini", cfg["data"]["mini_per_subset"])}
    index = {d: i for i, d in enumerate(S.doc_ids)}
    item_doc = np.array([index[sorted(q.gold_docs)[0]] for q in queries])
    texts = [question_only(q.text) if args.question_only else q.text for q in queries]
    suffix = "_qonly" if args.question_only else ""
    qkey = {"model": S.emb.model_name, "prefix": S.emb.query_prefix, "n": len(queries)}
    if args.question_only:
        qkey["question_only"] = True  # keeps the original cache key unchanged
    q_vecs = cached_embeddings("queries", texts, S.emb.encode_queries, qkey, S.cache)
    q_tokens = tokenize_words(texts)
    q_fold, q_subset = S.d_fold[item_doc], S.doc_subset[item_doc]
    is_mini = np.array([q.qid in mini for q in queries])

    levels = build_levels(S.doc_subset, S.doc_group, item_doc)
    results = {}
    for lv in levels:
        results[lv.name] = level_ranks(lv, NAMES, cfg, S.d_fold, S.doc_vecs, S.doc_tokens, q_fold, q_vecs, q_tokens,
                                       S.doc_vecs_full, q_vecs)
        print(f"level {lv.name} done", flush=True)
    routers = list(results["flat"][0])

    runs = Path(cfg["paths"]["runs"])
    runs.mkdir(parents=True, exist_ok=True)
    with open(runs / f"routing_full{suffix}.jsonl", "w") as fh:
        fh.write(json.dumps({"_header": True, "git": git_hash(), "config": cfg}) + "\n")
        for i, q in enumerate(queries):
            fh.write(json.dumps({"qid": q.qid, "subset": str(q_subset[i]), "mini": bool(is_mini[i]),
                                 "gold_doc": S.doc_ids[item_doc[i]], "fold": int(q_fold[i]),
                                 **{f"{lv}_rank_{n}": int(results[lv][0][n][i]) for lv in results for n in routers},
                                 **{f"{lv}_top1_{n}": results[lv][1][n][i] for lv in results for n in routers}}) + "\n")

    rows = []
    for split, mask in [("full", np.ones(len(queries), bool)), ("mini", is_mini)]:
        for lv in levels:
            ci_b = rc["gates"].get(lv.name, {"b": rc["go_b"]})["b"]
            rows += [{"split": split, **r} for r in
                     summarise(lv.name, results[lv.name][0], mask & (lv.item_gold != ""), q_subset, item_doc,
                               rc["top_b"], ci_b, cfg)]
    table = pd.DataFrame(rows).fillna("")
    gate_lines, _ = gate_report(table[table.split == "full"], rc["gates"])
    fine_b = rc["gates"]["fine"]["b"]
    e2e = end_to_end(results, q_subset, fine_b)
    fine_rows = table[(table.split == "full") & (table.level == "fine") & (table.subset == "ALL")]
    best_fine = fine_rows.set_index("router")[f"acc@{fine_b}"].astype(float).idxmax()
    fr, ft = results["fine"][0][best_fine], results["fine"][1][best_fine]
    miss = (q_subset == "cuad") & (fr > 1)
    gold_fine = levels[2].item_gold
    confusions = Counter(zip(gold_fine[miss], ft[miss])).most_common(10)

    md = table.to_markdown(index=False)
    tables, notes = Path(cfg["paths"]["tables"]), Path(cfg["paths"]["notes"])
    sweep_md = ""
    if args.sweep:
        sweep_md = band_sweep(cfg, S, levels[0], q_fold, q_tokens, q_subset).to_markdown(index=False)
    title = "# Query routing per level (leak-safe document folds)" + (", question only" if suffix else "")
    (tables / f"routing{suffix}.md").write_text(title + "\n\n" + md + "\n"
                                       + (f"\n## band_lr band-edge sweep (flat)\n\n{sweep_md}\n" if sweep_md else ""))
    note = [
        "# Query routing go/no-go, per level\n", *gate_lines, "",
        f"End-to-end for CUAD queries (coarse top-1 correct AND contract type in fine top-{fine_b}): "
        + ", ".join(f"`{n}` {v:.3f}" for n, v in e2e.items()) + "\n",
        "## Setup\n",
        f"- Mixed pool: {len(S.docs)} documents. flat = {len(set(S.doc_group))} groups (reference only); "
        f"coarse = 4 subsets; fine = {len(set(S.doc_group[S.doc_subset == 'cuad']))} CUAD contract types "
        "(CUAD types with < "
        f"{rc['min_group_docs']} docs merged into cuad/Other), trained on CUAD documents only.",
        f"- {rc['n_folds']} document-level folds, stratified by group; {S.n_dup} near-duplicate clusters kept "
        "inside one fold. Every level's routers are fit on training-fold documents only and scored on "
        "queries whose gold document is held out. Queries are never used for fitting.",
        f"- Routers: centroid ({S.emb.model_name}, first {rc['excerpt_chars']} chars), vocab_lr "
        f"(top-{rc['vocab_per_group']} discriminative words + logistic regression), band_lr (band words "
        f"{rc['band_low']:.0%}-{rc['band_high']:.0%} of training docs + logistic regression), nb_band / nb_all "
        f"(multinomial Naive Bayes on band / all words, alpha={rc['nb_alpha']}), fused (reciprocal rank fusion "
        f"of centroid and nb_band, k={rc['fuse_rrf_k']}, ties to centroid).",
        "- Gate values were set after the flat (single-level) v1/v2 results had been seen: coarse top-1 "
        "because a coarse miss can mean searching the wrong 21% of the corpus, fine top-3 because three "
        "CUAD types cover ~4-14% of it.",
        "- CI: 95% bootstrap over gold documents (queries of one document are correlated).\n",
        "## Results\n", md, "",
        f"## Most frequent fine-level confusions ({best_fine}, top-1)\n",
        *[f"- {n}x `{g}` -> `{p}`" for (g, p), n in confusions],
    ]
    (notes / f"routing_gate{suffix}.md").write_text("\n".join(note) + "\n")
    print("\n".join(gate_lines))
    print("end-to-end CUAD:", e2e)


if __name__ == "__main__":
    main()

"""E11: the band pipeline -- dev search first, then ONE scored test run.

    python scripts/run_band_pipeline.py --stage dev            # grid on dev queries, picks a setting
    python scripts/run_band_pipeline.py --stage test           # selected + default settings and baselines on test
    --dataset clerc (default) | clerc_heldout [--qlen N] [--intact] | legalbench
    --dense-baselines (LegalBench only): + Parth's final method and dense doc-first (chunk embeddings: GPU)
    --smoke N: N documents per subset (a quick check that the script runs; tables get "_smoke<N>")

Every query searches ONE mixed pool of all documents. Dev / test split by gold document
(LegalBench: trr.eval.splits; CLERC: trr.data.clerc.split_by_gold). The dev stage only needs the
document choice (doc recall@1, the selection metric), so it skips the passage step; the test stage
runs whole retrievers through the shared harness (eval/run.py).

CLERC has document-level gold only: document ranking metrics (recall@1/@10, MRR, nDCG@10 over the
ranked cases) and DRM are reported; character metrics are not. CLERC has no class labels, so
cluster quality is reported as sizes, cohesion and names instead of NMI / ARI.

Outputs (results/tables, <tag> = _<dataset>[_smoke<N>]): band_dev<tag>.{csv,md} + band_selected<tag>.json
(dev); band_test<tag>.{csv,md} + band_test_ci<tag>.csv (test). Per-query run files go to
results/runs/<method>_test<tag>_<subset>.jsonl with config and git hash.
"""

from __future__ import annotations

import argparse
import copy
import json
import statistics
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import git_hash, load_config, set_seeds  # noqa: E402
from trr.eval.experiment import (DATASETS, DEV, TEST, add_document_metrics, doc_level_ci, human_groups,  # noqa: E402
                                 load_data, question_only, run_tags, summarise, use_dataset)
from trr.eval.run import aggregate, run_subset  # noqa: E402
from trr.retrievers.band_pipeline import POOL, BandIndex, BandPipelineRetriever, count_terms  # noqa: E402
from trr.retrievers.chunk_store import ChunkStore  # noqa: E402
from trr.retrievers.flat import BM25Retriever  # noqa: E402
from trr.routing.routers import tokenize_words  # noqa: E402

GRID_KEYS = ["min_df", "max_frac", "k", "rare_below", "b"]


# ---- dev search: document choice only --------------------------------------------------------
def cluster_quality(ix: BandIndex, docs, groups: dict[str, str] | None) -> dict:
    """Never used to choose a setting. Always: mid-band vocabulary size, cluster sizes and cohesion
    (mean cosine of a document to its own centroid: how tight the clusters are). With human labels
    (LegalBench): NMI / ARI against the subsets and the groups."""
    labels = ix.clusters.labels[:len(docs)]
    sizes = np.bincount(labels, minlength=ix.clusters.n_clusters)
    sims = ix.clusters.similarities(ix.doc_tokens)
    out = {"vocab": len(ix.clusters.vocab), "largest": int(sizes.max()), "smallest": int(sizes.min()),
           "cohesion": float(sims[np.arange(len(labels)), labels].mean())}
    if groups is not None:
        subset, group = [d.subset for d in docs], [groups[d.doc_id] for d in docs]
        out.update({"nmi_subset": normalized_mutual_info_score(subset, labels),
                    "ari_subset": adjusted_rand_score(subset, labels),
                    "nmi_group": normalized_mutual_info_score(group, labels),
                    "ari_group": adjusted_rand_score(group, labels)})
    return out


def score_document_choice(ret: BandPipelineRetriever, queries, words) -> list[dict]:
    """Per query: was the chosen document gold, was the gold cluster searched, rare words used?"""
    ix, out = ret.ix, []
    for q, w in zip(queries, words):
        if ret.needs_gold:
            ret.set_gold(q.gold_docs)
        clusters = ret.chosen_clusters(w)
        doc, rare = ret.choose_document(w, clusters)
        searched = sum(len(ix.cluster_docs[c]) for c in clusters)
        out.append({"qid": q.qid, "subset": q.subset, "gold_doc": sorted(q.gold_docs)[0],
                    "correct": int(doc in q.gold_docs),
                    "in_cluster": int(any(ix.doc_cluster[g] in clusters for g in q.gold_docs)),
                    "fallback": int(not rare), "searched_share": searched / len(ix.docs)})
    return out


def stage_dev(cfg, docs, queries, tag: str, sel_tag: str) -> None:
    bc, subsets, tables = cfg["band_clusters"], cfg["data"]["subsets"], Path(cfg["paths"]["tables"])
    groups = human_groups(cfg, docs)
    dev = queries[DEV]
    doc_tokens, words = tokenize_words([d.text for d in docs]), tokenize_words([q.text for q in dev])
    counts = count_terms(doc_tokens)                     # shared by every clustering of the grid
    print(f"dev: {len(dev)} queries, pool {len(docs)} documents", flush=True)
    rows, order, per_clustering = [], 0, len(bc["sweep_rare_below"]) * (len(bc["sweep_b"]) + 1)
    for min_df, max_frac, k in product(bc["sweep_min_df"], bc["sweep_max_frac"], bc["sweep_k"]):
        t0 = time.perf_counter()
        try:
            ix = BandIndex(cfg, docs, min_df, max_frac, k, doc_tokens=doc_tokens, counts=counts)
        except ValueError as e:                        # e.g. min_df=20 on a small (smoke) pool
            print(f"min_df={min_df} max_frac={max_frac} k={k}: skipped ({e})", flush=True)
            continue
        build = time.perf_counter() - t0
        quality = cluster_quality(ix, docs, groups)
        for rare_below in bc["sweep_rare_below"]:
            for router, b in [("band", b) for b in bc["sweep_b"]] + [("oracle", 1)]:
                ret = BandPipelineRetriever(None, ix, router, b, rare_below)
                rows.append(summarise(score_document_choice(ret, dev, words), subsets, order=order, router=router,
                                      min_df=min_df, max_frac=max_frac, k=k, rare_below=rare_below,
                                      b=b if router == "band" else np.nan, build_s=build, **quality))
                order += 1
        print(f"min_df={min_df} max_frac={max_frac} k={k}: built in {build:.1f}s, "
              f"best r@1 {max(r['doc_recall@1'] for r in rows[-per_clustering:]):.3f}", flush=True)
    # without clusters ("none"): independent of the clustering, once per rare_below; r0 = plain doc-first
    for rare_below in [0] + bc["sweep_rare_below"]:
        ret = BandPipelineRetriever(None, ix, "none", 1, rare_below)
        rows.append(summarise(score_document_choice(ret, dev, words), subsets, order=order, router="none",
                              rare_below=rare_below))
        order += 1
    df = pd.DataFrame(rows)

    band = df[df.router == "band"].copy()
    # pre-registered rule: most correct dev queries; ties -> smaller k, then smaller b, then grid order
    best = band.sort_values(["correct", "k", "b", "order"], ascending=[False, True, True, True]).iloc[0]
    selected = {key: (float(best[key]) if key == "max_frac" else int(best[key])) for key in GRID_KEYS}
    default = {key: bc[key] for key in GRID_KEYS}
    tied = int((band.correct == best.correct).sum())
    json.dump({"selected": selected, "default": default, "dev_doc_recall@1": float(best["doc_recall@1"]),
               "settings_tied_at_best": tied, "git": git_hash(), "smoke": "smoke" in tag, "dataset": cfg["dataset"]},
              open(tables / f"band_selected{sel_tag}.json", "w"), indent=2)
    df.to_csv(tables / f"band_dev{tag}.csv", index=False)

    top = band.sort_values("correct", ascending=False).head(15)
    cols = GRID_KEYS + ["doc_recall@1", "in_cluster", "fallback", "searched"] + [f"r1_{s}" for s in subsets]
    md = [f"# E11 dev search on {cfg['dataset']}: band pipeline document choice ({len(dev)} dev queries"
          f"{', SMOKE' if 'smoke' in tag else ''})", "",
          f"Selected (most correct dev queries; ties -> smaller k, then b): `{selected}`, dev doc recall@1 "
          f"{best['doc_recall@1']:.3f}; {tied} setting(s) tied at the best. Pre-registered default: `{default}`.", "",
          "## Top 15 band settings", "", top[cols].round(3).to_markdown(index=False), "",
          "## Without clusters (router none; rare_below 0 = plain full-query doc-first)", "",
          df[df.router == "none"][["rare_below", "doc_recall@1", "fallback"] + [f"r1_{s}" for s in subsets]]
          .round(3).to_markdown(index=False), "",
          "## Oracle routing (gold document's cluster), best per clustering", "",
          df[df.router == "oracle"].sort_values("correct", ascending=False)
          .drop_duplicates(["min_df", "max_frac", "k"])[["min_df", "max_frac", "k", "rare_below", "doc_recall@1"]]
          .round(3).to_markdown(index=False), "",
          "## Cluster quality per clustering (cohesion; NMI / ARI only where human labels exist)", "",
          df[df.router == "oracle"].drop_duplicates(["min_df", "max_frac", "k"])
          [[c for c in ["min_df", "max_frac", "k", "vocab", "cohesion", "nmi_subset", "ari_subset", "nmi_group",
                        "ari_group", "largest", "smallest", "build_s"] if c in df]].round(3).to_markdown(index=False), ""]
    (tables / f"band_dev{tag}.md").write_text("\n".join(md))
    print(f"selected {selected} (dev r@1 {best['doc_recall@1']:.3f}, {tied} tied); wrote band_dev{tag}.md", flush=True)


# ---- test run --------------------------------------------------------------------------------
def warm_local_indexes(ret: BandPipelineRetriever, queries) -> float:
    """Build, before timing, the cluster-local indexes the queries will touch (an index-time cost,
    reported separately) so per-query latency is the query-time work only."""
    t0 = time.perf_counter()
    for q in queries:
        if ret.needs_gold:
            ret.set_gold(q.gold_docs)
        ret.ix.local(ret.chosen_clusters(tokenize_words([q.text])[0]))
    return time.perf_counter() - t0


def add_one_document_ms(cfg, ix: BandIndex, n: int) -> dict:
    """Extendibility, measured: the median time to place one new document in a cluster and update
    its centroid, and to compute its row of term counts (what BM25 needs from it) -- versus
    re-clustering from scratch. Appending that row to the stored scipy matrix is a copy here; an
    inverted index with append-only segments (as in Lucene) adds it in time proportional to the
    document."""
    bc, place, row = cfg["band_clusters"], [], []
    for i in range(min(n, len(ix.docs))):
        clusters = copy.deepcopy(ix.clusters)
        t0 = time.perf_counter()
        clusters.add([ix.doc_tokens[i]])
        place.append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        ix.counter.transform([ix.doc_tokens[i]])
        row.append(time.perf_counter() - t0)
    t0 = time.perf_counter()
    BandIndex(cfg, ix.docs, ix.min_df, ix.max_frac, ix.k, doc_tokens=ix.doc_tokens)
    return {"place_ms": statistics.median(place) * 1000, "count_row_ms": statistics.median(row) * 1000,
            "recluster_s": time.perf_counter() - t0, "kmeans_restarts": bc["kmeans_n_init"]}


def stage_test(cfg, docs, queries, tag: str, sel_tag: str, dense: bool) -> None:
    bc, subsets, ks = cfg["band_clusters"], cfg["data"]["subsets"], cfg["eval"]["ks"]
    tables = Path(cfg["paths"]["tables"])
    sel_file = tables / f"band_selected{sel_tag}.json"
    if not sel_file.exists():
        sys.exit(f"{sel_file} missing: run --stage dev first")
    chosen = json.load(open(sel_file))
    test = queries[TEST]
    split = f"test{tag}"
    groups, legalbench = human_groups(cfg, docs), cfg["dataset"] == "legalbench"
    dense = dense and legalbench                         # Parth's router needs LegalBench's labelled groups
    doc_list = cfg["clerc"]["doc_list"]
    print(f"test: {len(test)} queries, pool {len(docs)} documents; selected {chosen['selected']}", flush=True)

    t0 = time.perf_counter()
    store = ChunkStore(cfg)
    for s in subsets:
        store.add([d for d in docs if d.subset == s])
    store.merge(POOL, subsets, embeddings=dense)
    store.bm25(POOL)                                   # chunk BM25 index, built before any query is timed
    timing = {"chunks": len(store.subsets[POOL].texts), "chunk_index_s": time.perf_counter() - t0}
    doc_tokens = tokenize_words([d.text for d in docs])

    indexes, quality = {}, {}
    for name in ("selected", "default"):
        p = chosen[name]
        key = (p["min_df"], p["max_frac"], p["k"])
        if key not in indexes:
            t0 = time.perf_counter()
            indexes[key] = BandIndex(cfg, docs, *key, doc_tokens=doc_tokens)
            timing[f"band_index_{name}_s"] = time.perf_counter() - t0
            quality[name] = {**cluster_quality(indexes[key], docs, groups),
                             "names": [" ".join(n) for n in indexes[key].clusters.names(5)]}
    sel, dft = chosen["selected"], chosen["default"]
    ix_sel = indexes[(sel["min_df"], sel["max_frac"], sel["k"])]
    ix_dft = indexes[(dft["min_df"], dft["max_frac"], dft["k"])]

    def band(ix, p, router):
        return BandPipelineRetriever(store, ix, router, p["b"], p["rare_below"], doc_list=doc_list)

    main = band(ix_sel, sel, "band")
    docfirst = BandPipelineRetriever(store, ix_sel, "none", 1, 0, doc_list=doc_list)   # no rare band
    docfirst.name = "mixed_docfirst_bm25"
    flat = BM25Retriever(store)
    flat.name = "mixed_bm25"
    methods = [(main, test), (band(ix_dft, dft, "band"), test), (band(ix_sel, sel, "none"), test),
               (band(ix_sel, sel, "oracle"), test), (docfirst, test), (flat, test)]
    main_q = None
    if legalbench:   # the question-only test removes LegalBench's header; CLERC queries have none
        qonly = question_only(test)
        main_q = band(ix_sel, sel, "band")
        docfirst_q = BandPipelineRetriever(store, ix_sel, "none", 1, 0, doc_list=doc_list)
        main_q.name, docfirst_q.name = main.name + "_qonly", "mixed_docfirst_bm25_qonly"
        methods += [(main_q, qonly), (docfirst_q, qonly)]
    if dense:
        from trr.retrievers.group_first import GroupFirstRetriever, GroupRouter
        gr = GroupRouter(cfg, store, docs, level="coarse")
        methods += [(GroupFirstRetriever(store, gr, "centroid_full", 2, "docfirst_local_rrf"), test),
                    (GroupFirstRetriever(store, gr, "none", 1, "docfirst"), test)]
    if len({m.name for m, _ in methods}) < len(methods):   # selected == default: run it once
        seen = set()
        methods = [(m, qs) for m, qs in methods if not (m.name in seen or seen.add(m.name))]

    records, frames = {}, []
    for ret, qs in methods:
        if isinstance(ret, BandPipelineRetriever):
            timing[f"warm_{ret.name}_s"] = warm_local_indexes(ret, qs)
        recs = []
        for s in subsets:
            sub = [q for q in qs if q.subset == s]
            if sub:
                recs += run_subset(ret, sub, s, ks, cfg, split, pool=POOL)
        add_document_metrics(recs, doc_list)
        records[ret.name] = recs
        agg = aggregate(recs, ret.name, ks)
        ms = sum(r["latency_ms"] for r in recs)
        agg["qps"] = len(recs) / (ms / 1000) if ms else np.nan
        if isinstance(ret, BandPipelineRetriever):
            ix = ret.ix
            agg["in_cluster"] = np.mean([any(ix.doc_cluster[g] in r["diag"]["clusters"] for g in r["gold_docs"])
                                         for r in recs])
            agg["fallback"] = np.mean([r["diag"]["fallback"] for r in recs])
        rdoc = pd.DataFrame(recs).groupby("subset")[[c for c in recs[0] if c.startswith("rdoc_")]].mean().mean()
        for c, v in rdoc.items():
            agg[c] = v                                   # macro over subsets, same on every row
        frames.append(agg)
        a1 = agg[(agg.subset == "ALL") & (agg.k == 1)].iloc[0]
        print(f"{ret.name:45s} r@1={a1.doc_recall:.3f} r@{doc_list}={rdoc[f'rdoc_recall@{doc_list}']:.3f} "
              f"MRR={rdoc['rdoc_mrr']:.3f} DRM@1={a1.drm:.3f} p50={a1.lat_p50_ms:.1f}ms", flush=True)
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(tables / f"band_test{tag}.csv", index=False)

    timing["add_one_document"] = add_one_document_ms(cfg, ix_sel, bc["add_doc_trials"])
    ci_rows = []
    mains = {main.name} | ({main_q.name} if main_q else set())
    pairs = [(main.name, m.name) for m, _ in methods if m.name not in mains]
    if main_q:
        pairs.append((main_q.name, "mixed_docfirst_bm25_qonly"))
    for (a, b), metric in product(pairs, bc["ci_metrics"]):
        mean, lo, hi, per = doc_level_ci(records[a], records[b], metric, cfg)
        ci_rows.append({"a": a, "b": b, "metric": metric, **{s: per.get(s, np.nan) for s in subsets},
                        "macro": mean, "lo": lo, "hi": hi, "real": "yes" if lo > 0 or hi < 0 else "no"})
    ci = pd.DataFrame(ci_rows)
    ci.to_csv(tables / f"band_test_ci{tag}.csv", index=False)

    view = df[df.subset == "ALL"]
    passage = ["drm", "ndcg", "char_r"] if legalbench else ["drm"]   # span metrics need span gold
    wide = view.pivot_table(index="method", columns="k", values=passage, sort=False)
    wide = wide[[c for c in wide.columns if c[1] in (1, 8, 10)]]
    wide.columns = [f"{m}@{k}" for m, k in wide.columns]
    doc_cols = ["rdoc_recall@1", f"rdoc_recall@{doc_list}", "rdoc_mrr", f"rdoc_ndcg@{doc_list}"]
    extra = view[view.k == 1].set_index("method")[[c for c in doc_cols + ["in_cluster", "fallback", "lat_p50_ms",
                                                                          "lat_p95_ms", "qps"] if c in view]]
    per_subset = df[df.k == 1].pivot_table(index="method", columns="subset", values="doc_recall", sort=False)
    md = [f"# E11 test run on {cfg['dataset']}: band pipeline vs baselines ({len(test)} test queries"
          f"{', SMOKE' if 'smoke' in tag else ''})", "",
          f"Selected on dev: `{sel}`; pre-registered default: `{dft}`. One mixed pool of {len(docs)} documents. "
          f"Macro over subsets. git {git_hash()}.", "",
          "## Main metrics (macro over subsets; rdoc_* = the ranked list of documents)", "",
          extra.join(wide).round(3).to_markdown(), "",
          "## Document recall@1 per subset", "", per_subset.round(3).to_markdown(), "",
          "## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)", "",
          ci.round(3).to_markdown(index=False), "",
          "## Cluster quality and names", ""]
    for name, q in quality.items():
        labels = (f", NMI/ARI vs subsets {q['nmi_subset']:.3f}/{q['ari_subset']:.3f}, vs groups "
                  f"{q['nmi_group']:.3f}/{q['ari_group']:.3f}" if "nmi_subset" in q else "")
        md += [f"**{name}**: vocab {q['vocab']}, cohesion {q['cohesion']:.3f}, sizes {q['smallest']}..{q['largest']}"
               f"{labels}", ""]
        md += [f"{i}. {n}" for i, n in enumerate(q["names"])] + [""]
    md += ["## Timing (index and extendibility)", "", "```", json.dumps(timing, indent=2), "```", ""]
    (tables / f"band_test{tag}.md").write_text("\n".join(md))
    print(f"wrote band_test{tag}.md", flush=True)


def main() -> None:
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["dev", "test"])
    ap.add_argument("--dataset", default="clerc", choices=list(DATASETS))
    ap.add_argument("--qlen", type=int, default=None, help="clerc_heldout: query length in words")
    ap.add_argument("--intact", action="store_true", help="clerc_heldout: passages left in (sanity)")
    ap.add_argument("--smoke", type=int, default=None, help="documents per subset (local check)")
    ap.add_argument("--dense-baselines", action="store_true", help="needs chunk embeddings (GPU)")
    args = ap.parse_args()
    set_seeds(cfg["seed"])
    use_dataset(cfg, args.dataset, args.qlen, args.intact)
    tag, sel_tag = run_tags(cfg, args.smoke)
    h = cfg["clerc"]["heldout"]
    if args.stage == "dev" and args.dataset == "clerc_heldout" and (h["length"] != h["main_length"] or args.intact):
        sys.exit("clerc_heldout selects once: --stage dev only at the main length, held out")
    docs, queries = load_data(cfg, args.smoke)
    if args.stage == "dev":
        stage_dev(cfg, docs, queries, tag, sel_tag)
    else:
        stage_test(cfg, docs, queries, tag, sel_tag, args.dense_baselines)


if __name__ == "__main__":
    main()

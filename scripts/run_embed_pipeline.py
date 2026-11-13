"""E12: the embedding pipeline -- dev search first, then ONE scored test run.

    python scripts/run_embed_pipeline.py --stage dev     # grid on dev queries, picks a setting
    python scripts/run_embed_pipeline.py --stage test    # selected + default settings and baselines on test
    --dataset clerc (default) | legalbench;  --smoke N: N documents per subset (tables get "_smoke<N>")

Same pool, dev / test split, selection rule and test-once as E11 (run_band_pipeline.py), so the two
pipelines compare query by query. Every chunk is embedded once (cached in data/cache, GPU on Kaggle).
The dev stage only scores the document choice (doc recall@1); the test stage runs whole retrievers
through the shared harness. Query vectors are encoded in one batch before timing; their cost per
query is reported separately.

Outputs (results/tables, <tag> = _<dataset>[_smoke<N>]): embed_dev<tag>.{csv,md} + embed_selected<tag>.json;
embed_test<tag>.{csv,md} + embed_test_ci<tag>.csv; per-query runs in results/runs/.
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
from trr.clustering.band_clusters import _unit_rows  # noqa: E402
from trr.config import git_hash, load_config, set_seeds  # noqa: E402
from trr.eval.experiment import (DEV, TEST, add_document_metrics, doc_level_ci, human_groups,  # noqa: E402
                                 load_data, summarise, use_dataset)
from trr.eval.run import aggregate, run_subset  # noqa: E402
from trr.retrievers.chunk_store import ChunkStore  # noqa: E402
from trr.retrievers.embed_pipeline import POOL, EmbedIndex, EmbedPipelineRetriever  # noqa: E402
from trr.retrievers.flat import DenseRetriever  # noqa: E402

GRID_KEYS = ["k", "b", "doc_score"]


def build_store(cfg, docs) -> tuple[ChunkStore, float]:
    """The mixed pool with every chunk embedded (cached in data/cache): (store, seconds)."""
    t0 = time.perf_counter()
    store = ChunkStore(cfg)
    for s in cfg["data"]["subsets"]:
        store.add([d for d in docs if d.subset == s])
    store.merge(POOL, cfg["data"]["subsets"], embeddings=True)
    return store, time.perf_counter() - t0


def encode(store, queries) -> tuple[dict[str, np.ndarray], float]:
    """Query text -> unit vector, in one batch: (vectors, milliseconds per query)."""
    texts = list(dict.fromkeys(q.text for q in queries))
    t0 = time.perf_counter()
    vecs = store.embedder.encode_queries(texts) if texts else []
    return dict(zip(texts, vecs)), (time.perf_counter() - t0) * 1000 / max(len(texts), 1)


def cluster_quality(ix: EmbedIndex, docs, groups) -> dict:
    """Never used to choose a setting: sizes, cohesion (mean cosine of a document to its own
    centroid) and, with human labels (LegalBench), NMI / ARI against subsets and groups."""
    labels = ix.clusters.labels[:len(docs)]
    sizes = np.bincount(labels, minlength=ix.clusters.n_clusters)
    sims = ix.clusters.similarities(ix.doc_vecs)
    out = {"largest": int(sizes.max()), "smallest": int(sizes.min()),
           "cohesion": float(sims[np.arange(len(labels)), labels].mean())}
    if groups is not None:
        subset, group = [d.subset for d in docs], [groups[d.doc_id] for d in docs]
        out.update({"nmi_subset": normalized_mutual_info_score(subset, labels),
                    "ari_subset": adjusted_rand_score(subset, labels),
                    "nmi_group": normalized_mutual_info_score(group, labels),
                    "ari_group": adjusted_rand_score(group, labels)})
    return out


def score_document_choice(ret: EmbedPipelineRetriever, queries, qvecs) -> list[dict]:
    ix, out = ret.ix, []
    for q in queries:
        v = qvecs[q.text]
        if ret.needs_gold:
            ret.set_gold(q.gold_docs)
        clusters = ret.chosen_clusters(v)
        doc = ret.rank_documents(v, clusters, 1)[0]
        out.append({"qid": q.qid, "subset": q.subset, "correct": int(doc in q.gold_docs),
                    "in_cluster": int(any(ix.doc_cluster[g] in clusters for g in q.gold_docs)), "fallback": 0,
                    "searched_share": sum(len(ix.cluster_docs[c]) for c in clusters) / len(ix.docs)})
    return out


def stage_dev(cfg, docs, queries, tag: str) -> None:
    ec, subsets, tables = cfg["embed_clusters"], cfg["data"]["subsets"], Path(cfg["paths"]["tables"])
    groups, dev = human_groups(cfg, docs), queries[DEV]
    store, embed_s = build_store(cfg, docs)
    qvecs, _ = encode(store, dev)
    print(f"dev: {len(dev)} queries, pool {len(docs)} documents, chunks embedded in {embed_s:.0f}s", flush=True)
    rows, order = [], 0
    for k in ec["sweep_k"]:
        t0 = time.perf_counter()
        ix = EmbedIndex(cfg, store, docs, k)
        build, quality = time.perf_counter() - t0, cluster_quality(ix, docs, groups)
        for how in ec["sweep_doc_score"]:
            for router, b in [("band", b) for b in ec["sweep_b"]] + [("oracle", 1)]:
                ret = EmbedPipelineRetriever(store, ix, router, b, how)
                rows.append(summarise(score_document_choice(ret, dev, qvecs), subsets, order=order, router=router,
                                      k=k, b=b if router == "band" else np.nan, doc_score=how, build_s=build,
                                      **quality))
                order += 1
        print(f"k={k}: built in {build:.1f}s, best r@1 {max(r['doc_recall@1'] for r in rows if r['k'] == k):.3f}",
              flush=True)
    for how in ec["sweep_doc_score"]:     # without clusters: flat dense document choice
        ret = EmbedPipelineRetriever(store, ix, "none", 1, how)
        rows.append(summarise(score_document_choice(ret, dev, qvecs), subsets, order=order, router="none",
                              doc_score=how))
        order += 1
    df = pd.DataFrame(rows)

    band = df[df.router == "band"]
    # same rule as E11: most correct dev queries; ties -> smaller k, then smaller b, then grid order
    best = band.sort_values(["correct", "k", "b", "order"], ascending=[False, True, True, True]).iloc[0]
    selected = {"k": int(best.k), "b": int(best.b), "doc_score": str(best.doc_score)}
    default = {key: ec[key] for key in GRID_KEYS}
    tied = int((band.correct == best.correct).sum())
    json.dump({"selected": selected, "default": default, "dev_doc_recall@1": float(best["doc_recall@1"]),
               "settings_tied_at_best": tied, "git": git_hash(), "smoke": "smoke" in tag, "dataset": cfg["dataset"],
               "embed_s": embed_s}, open(tables / f"embed_selected{tag}.json", "w"), indent=2)
    df.to_csv(tables / f"embed_dev{tag}.csv", index=False)
    cols = GRID_KEYS + ["doc_recall@1", "in_cluster", "searched"] + [f"r1_{s}" for s in subsets]
    md = [f"# E12 dev search on {cfg['dataset']}: embedding pipeline document choice ({len(dev)} dev queries"
          f"{', SMOKE' if 'smoke' in tag else ''})", "",
          f"Selected (most correct dev queries; ties -> smaller k, then b): `{selected}`, dev doc recall@1 "
          f"{best['doc_recall@1']:.3f}; {tied} setting(s) tied at the best. Pre-registered default: `{default}`.", "",
          "## Band (routed) settings", "", band.sort_values("correct", ascending=False)[cols].round(3)
          .to_markdown(index=False), "",
          "## Without clusters (router none = flat dense document choice)", "",
          df[df.router == "none"][["doc_score", "doc_recall@1"]].round(3).to_markdown(index=False), "",
          "## Oracle routing (gold document's cluster)", "",
          df[df.router == "oracle"][["k", "doc_score", "doc_recall@1"]].round(3).to_markdown(index=False), "",
          "## Cluster quality per k", "",
          df[df.router == "oracle"].drop_duplicates("k")[[c for c in ["k", "cohesion", "nmi_subset", "ari_subset",
              "nmi_group", "ari_group", "largest", "smallest", "build_s"] if c in df]].round(3)
          .to_markdown(index=False), ""]
    (tables / f"embed_dev{tag}.md").write_text("\n".join(md))
    print(f"selected {selected} (dev r@1 {best['doc_recall@1']:.3f}, {tied} tied); wrote embed_dev{tag}.md",
          flush=True)


def add_one_document_ms(cfg, store, ix: EmbedIndex, n: int) -> dict:
    """Extendibility, measured: the median time to embed one document's chunks with the fixed model,
    form its document vector and place it in a cluster -- versus re-clustering from scratch."""
    sc, embed, place = store.subsets[POOL], [], []
    for i in range(min(n, len(ix.docs))):
        texts = [sc.texts[r] for r in ix.rows[i]]
        t0 = time.perf_counter()
        vecs = store.embedder.encode(texts)
        embed.append(time.perf_counter() - t0)
        clusters = copy.deepcopy(ix.clusters)
        t0 = time.perf_counter()
        clusters.add(_unit_rows(vecs.mean(axis=0, keepdims=True)))
        place.append(time.perf_counter() - t0)
    t0 = time.perf_counter()
    EmbedIndex(cfg, store, ix.docs, ix.k)
    return {"embed_doc_ms": statistics.median(embed) * 1000, "place_ms": statistics.median(place) * 1000,
            "recluster_s": time.perf_counter() - t0}


def stage_test(cfg, docs, queries, tag: str) -> None:
    ec, subsets, ks = cfg["embed_clusters"], cfg["data"]["subsets"], cfg["eval"]["ks"]
    tables, doc_list = Path(cfg["paths"]["tables"]), cfg["clerc"]["doc_list"]
    sel_file = tables / f"embed_selected{tag}.json"
    if not sel_file.exists():
        sys.exit(f"{sel_file} missing: run --stage dev first")
    chosen, test, split = json.load(open(sel_file)), queries[TEST], f"test{tag}"
    groups = human_groups(cfg, docs)
    store, embed_s = build_store(cfg, docs)
    qvecs, encode_ms = encode(store, test)
    timing = {"chunks": len(store.subsets[POOL].texts), "embed_and_index_s": embed_s,
              "query_encode_ms_per_query": encode_ms}
    print(f"test: {len(test)} queries; selected {chosen['selected']}", flush=True)

    indexes, quality = {}, {}
    for name in ("selected", "default"):
        k = chosen[name]["k"]
        if k not in indexes:
            t0 = time.perf_counter()
            indexes[k] = EmbedIndex(cfg, store, docs, k)
            timing[f"embed_index_{name}_s"] = time.perf_counter() - t0
            quality[name] = cluster_quality(indexes[k], docs, groups)
    sel, dft = chosen["selected"], chosen["default"]
    ix_sel = indexes[sel["k"]]

    def emb(p, router, ix=ix_sel):
        return EmbedPipelineRetriever(store, ix, router, p["b"], p["doc_score"], doc_list=doc_list)

    main = emb(sel, "band")
    flat = DenseRetriever(store)
    flat.name = "mixed_dense"
    methods = [main, emb(dft, "band", indexes[dft["k"]]), emb(sel, "none"), emb(sel, "oracle"), flat]
    seen, unique = set(), []
    for m in methods:                                    # selected == default: run it once
        if m.name not in seen:
            seen.add(m.name)
            unique.append(m)
    records, frames = {}, []
    for ret in unique:
        ret._qvecs = qvecs                               # one batch encode serves every method
        recs = []
        for s in subsets:
            sub = [q for q in test if q.subset == s]
            if sub:
                recs += run_subset(ret, sub, s, ks, cfg, split, pool=POOL)
        add_document_metrics(recs, doc_list)
        records[ret.name] = recs
        agg = aggregate(recs, ret.name, ks)
        ms = sum(r["latency_ms"] for r in recs)
        agg["qps"] = len(recs) / (ms / 1000) if ms else np.nan
        rdoc = pd.DataFrame(recs).groupby("subset")[[c for c in recs[0] if c.startswith("rdoc_")]].mean().mean()
        for c, v in rdoc.items():
            agg[c] = v
        if isinstance(ret, EmbedPipelineRetriever):
            agg["in_cluster"] = np.mean([any(ret.ix.doc_cluster[g] in r["diag"]["clusters"] for g in r["gold_docs"])
                                         for r in recs])
        frames.append(agg)
        print(f"{ret.name:32s} r@1={rdoc['rdoc_recall@1']:.3f} r@{doc_list}={rdoc[f'rdoc_recall@{doc_list}']:.3f} "
              f"MRR={rdoc['rdoc_mrr']:.3f} p50={agg.lat_p50_ms.iloc[0]:.1f}ms", flush=True)
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(tables / f"embed_test{tag}.csv", index=False)

    timing["add_one_document"] = add_one_document_ms(cfg, store, ix_sel, ec["add_doc_trials"])
    ci_rows = []
    for b, metric in product([m.name for m in unique if m.name != main.name], cfg["band_clusters"]["ci_metrics"]):
        mean, lo, hi, per = doc_level_ci(records[main.name], records[b], metric, cfg)
        ci_rows.append({"a": main.name, "b": b, "metric": metric, **{s: per.get(s, np.nan) for s in subsets},
                        "macro": mean, "lo": lo, "hi": hi, "real": "yes" if lo > 0 or hi < 0 else "no"})
    ci = pd.DataFrame(ci_rows)
    ci.to_csv(tables / f"embed_test_ci{tag}.csv", index=False)

    view = df[(df.subset == "ALL") & (df.k == 1)].set_index("method")
    drm = df[df.subset == "ALL"].pivot_table(index="method", columns="k", values="drm", sort=False)[[1, 8]]
    drm.columns = ["drm@1", "drm@8"]
    cols = ["rdoc_recall@1", f"rdoc_recall@{doc_list}", "rdoc_mrr", f"rdoc_ndcg@{doc_list}", "in_cluster",
            "lat_p50_ms", "lat_p95_ms", "qps"]
    md = [f"# E12 test run on {cfg['dataset']}: embedding pipeline vs baselines ({len(test)} test queries"
          f"{', SMOKE' if 'smoke' in tag else ''})", "",
          f"Selected on dev: `{sel}`; pre-registered default: `{dft}`. One mixed pool of {len(docs)} documents. "
          f"git {git_hash()}.", "",
          "## Main metrics (rdoc_* = the ranked list of documents)", "",
          view[[c for c in cols if c in view]].join(drm).round(3).to_markdown(), "",
          "## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)", "",
          ci.round(3).to_markdown(index=False), "", "## Cluster quality", ""]
    md += [f"**{name}**: " + ", ".join(f"{k} {v:.3f}" if isinstance(v, float) else f"{k} {v}" for k, v in q.items())
           for name, q in quality.items()]
    md += ["", "## Timing (index and extendibility)", "", "```", json.dumps(timing, indent=2), "```", ""]
    (tables / f"embed_test{tag}.md").write_text("\n".join(md))
    print(f"wrote embed_test{tag}.md", flush=True)


def main() -> None:
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["dev", "test"])
    ap.add_argument("--dataset", default="clerc", choices=["clerc", "legalbench"])
    ap.add_argument("--smoke", type=int, default=None, help="documents per subset (a quick check)")
    args = ap.parse_args()
    set_seeds(cfg["seed"])
    use_dataset(cfg, args.dataset)
    tag = f"_{args.dataset}" + (f"_smoke{args.smoke}" if args.smoke else "")
    docs, queries = load_data(cfg, args.smoke)
    (stage_dev if args.stage == "dev" else stage_test)(cfg, docs, queries, tag)


if __name__ == "__main__":
    main()

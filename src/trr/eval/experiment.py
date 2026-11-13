"""Shared experiment plumbing for the pipeline run scripts (E11 band, E12 embedding).

Dataset switch, loading with the dev / test split, a small smoke slice, per-setting summaries of
the dev search, document ranking metrics on run records, and the paired bootstrap that resamples
gold documents. Kept in one place so both pipelines are scored identically.
"""

from __future__ import annotations

import dataclasses
from collections import defaultdict

import numpy as np
import pandas as pd

from trr.data.clerc import load_clerc
from trr.data.load import load_corpus, load_queries
from trr.eval.metrics import document_ranking_metrics, paired_cluster_bootstrap_macro_ci
from trr.eval.splits import DEV, TEST, split_queries
from trr.retrievers.query_split import split_query
from trr.routing.groups import assign_groups
from trr.routing.prep import legalbench_doc_folds


def use_dataset(cfg: dict, dataset: str) -> None:
    """Point the shared config at one dataset. CLERC: one subset "clerc", its own chunking (fixed
    windows: its texts have no line breaks), a k grid scaled to its pool, document-level CI metrics."""
    cfg["dataset"] = dataset
    if dataset == "clerc":
        c = cfg["clerc"]
        cfg["chunking"], cfg["data"]["subsets"] = c["chunking"], ["clerc"]
        cfg["band_clusters"]["sweep_k"], cfg["band_clusters"]["ci_metrics"] = c["sweep_k"], c["ci_metrics"]


def load_data(cfg: dict, smoke: int | None):
    """(docs, {DEV: queries, TEST: queries}). The split is drawn on the whole collection first, so a
    smoke run sees exactly the same dev / test sides, only fewer of them."""
    if cfg["dataset"] == "clerc":
        docs, queries, side = load_clerc(cfg)
    else:
        raw, subsets = cfg["paths"]["raw"], cfg["data"]["subsets"]
        docs = [d for s in subsets for d in load_corpus(raw, s)]
        _, _, folds = legalbench_doc_folds(cfg, docs)
        queries = [q for s in subsets for q in load_queries(raw, s, "full")]
        side = split_queries(queries, folds, cfg["eval"]["dev_folds"])
    if smoke:
        docs, queries = smoke_slice(cfg, docs, queries, side, smoke)
    return docs, {sd: [q for q in queries if side[q.qid] == sd] for sd in (DEV, TEST)}


def smoke_slice(cfg, docs, queries, side, n_docs):
    """Per subset: the first documents with a dev or a test query (half each), padded with other
    documents up to n_docs, and the first queries per side on the kept documents."""
    keep = set()
    for s in cfg["data"]["subsets"]:
        sub = [d.doc_id for d in docs if d.subset == s]
        for sd in (DEV, TEST):
            gold = list(dict.fromkeys(g for q in queries if q.subset == s and side[q.qid] == sd for g in q.gold_docs))
            keep |= set(gold[:max(1, n_docs // 4)])
        keep |= set([d for d in sub if d not in keep][:max(0, n_docs - sum(d in keep for d in sub))])
    per = cfg["band_clusters"]["smoke_queries"]
    out, seen = [], defaultdict(int)
    for q in queries:
        if q.gold_docs <= keep and seen[(q.subset, side[q.qid])] < per:
            seen[(q.subset, side[q.qid])] += 1
            out.append(q)
    return [d for d in docs if d.doc_id in keep], out


def question_only(queries):
    """The same queries with the header ("Consider the NDA between X and Y;") removed."""
    return [dataclasses.replace(q, text=split_query(q.text)[1]) for q in queries]


def human_groups(cfg, docs) -> dict[str, str] | None:
    """LegalBench's human labels (subsets / CUAD types) for evaluation; CLERC has none."""
    return assign_groups(docs, cfg["routing"]["min_group_docs"]) if cfg["dataset"] == "legalbench" else None


def summarise(recs: list[dict], subsets: list[str], **setting) -> dict:
    df = pd.DataFrame(recs)
    row = {**setting, "queries": len(df), "correct": int(df.correct.sum()), "doc_recall@1": df.correct.mean(),
           "in_cluster": df.in_cluster.mean(), "fallback": df.fallback.mean(), "searched": df.searched_share.mean()}
    for s in subsets:
        row[f"r1_{s}"] = df[df.subset == s].correct.mean() if (df.subset == s).any() else np.nan
    return row


def doc_level_ci(recs_a, recs_b, metric: str, cfg) -> tuple[float, float, float, dict]:
    """Macro (a - b) over subsets with a bootstrap CI that resamples gold DOCUMENTS (questions about
    one contract succeed or fail together); also the per-subset mean difference."""
    b = {r["qid"]: r[metric] for r in recs_b}
    by_doc: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in recs_a:
        by_doc[r["subset"]][r["gold_docs"][0]].append(r[metric] - b[r["qid"]])
    diffs = {s: [np.array(v) for v in docs.values()] for s, docs in by_doc.items()}
    ev = cfg["eval"]
    mean, lo, hi = paired_cluster_bootstrap_macro_ci(diffs, ev["bootstrap_resamples"], ev["bootstrap_seed"])
    return mean, lo, hi, {s: float(np.concatenate(v).mean()) for s, v in diffs.items()}


def add_document_metrics(recs: list[dict], doc_list: int) -> None:
    """Add document ranking metrics to each run record: the pipeline's ranked documents (diag
    "docs"), else the documents of its hits in rank order (flat chunk retrievers)."""
    for r in recs:
        ranked = r.get("diag", {}).get("docs") or [h["doc_id"] for h in r["hits"]]
        r.update(document_ranking_metrics(ranked, set(r["gold_docs"]), [1, doc_list]))

"""Run any Retriever over a benchmark split and score it with one evaluator.

Writes results/runs/<method>_<split>_<subset>.jsonl (one line per query: hits at max k,
metrics at every k, latency) plus a run header line with the config and git hash.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from trr.config import git_hash
from trr.data.load import Query
from trr.eval.metrics import query_metrics
from trr.retrievers.base import Retriever


def run_subset(retriever: Retriever, queries: list[Query], subset: str, ks: list[int],
               cfg: dict, split: str, pool: str | None = None) -> list[dict]:
    """Queries of `subset` searched in `pool` (default: the subset's own corpus)."""
    kmax = max(ks)
    pool = pool or subset
    if hasattr(retriever, "prepare_queries"):
        retriever.prepare_queries([q.text for q in queries])
    records = []
    for q in queries:
        if getattr(retriever, "needs_gold", False):
            retriever.set_gold(q.gold_docs)
        t0 = time.perf_counter()
        hits = retriever.retrieve(q.text, kmax, pool)
        latency_ms = (time.perf_counter() - t0) * 1000
        records.append({
            "qid": q.qid, "subset": subset, "gold_docs": sorted(q.gold_docs),
            "latency_ms": latency_ms, **query_metrics(hits, q.gold, ks),
            **({"diag": retriever.last_diag} if hasattr(retriever, "last_diag") else {}),
            "hits": [asdict(h) for h in hits],
        })
    runs = Path(cfg["paths"]["runs"])
    runs.mkdir(parents=True, exist_ok=True)
    with open(runs / f"{retriever.name}_{split}_{subset}.jsonl", "w") as f:
        header = {"_header": True, "method": retriever.name, "split": split, "subset": subset, "pool": pool,
                  "git": git_hash(), "config": cfg}
        f.write(json.dumps(header) + "\n")
        for r in records:
            f.write(json.dumps(r) + "\n")
    return records


def aggregate(records: list[dict], method: str, ks: list[int]) -> pd.DataFrame:
    """Mean of every metric per subset and k, plus an 'ALL' row (macro mean over subsets)."""
    df = pd.DataFrame([{k: v for k, v in r.items() if k not in ("hits", "diag")} for r in records])
    rows = []
    for subset, g in df.groupby("subset", sort=False):
        for k in ks:
            rows.append({"method": method, "subset": subset, "k": k, "queries": len(g),
                         "drm": g[f"drm@{k}"].mean(), "doc_recall": g[f"doc_recall@{k}"].mean(),
                         "char_p": g[f"char_p@{k}"].mean(), "char_r": g[f"char_r@{k}"].mean(),
                         "chars": g[f"chars@{k}"].mean(), "ndcg": g[f"ndcg@{k}"].mean(),
                         "lat_p50_ms": g["latency_ms"].median(),
                         "lat_p95_ms": g["latency_ms"].quantile(0.95)})
    out = pd.DataFrame(rows)
    macro = out.groupby("k", as_index=False).mean(numeric_only=True)
    macro.insert(0, "subset", "ALL")
    macro.insert(0, "method", method)
    macro["queries"] = out.groupby("k")["queries"].sum().values
    return pd.concat([out, macro], ignore_index=True)

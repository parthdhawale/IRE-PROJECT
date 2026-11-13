"""Build the CLERC document pool and its queries for E11 (run on Kaggle: ~13 GB of downloads).

    python scripts/build_clerc_pool.py --download-dir /tmp/clerc     # -> data/external/clerc/pool_<N>/

Steps (logic in trr/data/clerc.py, unit-tested):
 1. download the training queries, the passage->case map and the full-case collection (resumable)
 2. read every training query (its 1 positive + 20 negative passage ids; passage texts dropped)
 3. map those passages to cases; walk the queries in a seeded random order, adding each query's
    gold case and negative cases, until the pool holds clerc.pool_docs cases
 4. stream the 1.84M-case collection once and keep the pool's full texts
 5. remove each query's own source opinion if it is in the pool (verbatim-copy check)
 6. split the queries into dev / test by gold case
Writes docs.parquet (case_id, text), queries.parquet (qid, text, gold_case, n_neg_cases, order,
side) and pool.meta.json (counts at every step, config, git hash).
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

import bm25s
import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import git_hash, load_config, set_seeds  # noqa: E402
from trr.data import clerc  # noqa: E402
from trr.routing.routers import tokenize_words  # noqa: E402


def fetch(cfg, name: str, download_dir: str) -> Path:
    print(f"downloading {name} ...", flush=True)
    return Path(hf_hub_download(cfg["clerc"]["hf_repo"], name, repo_type="dataset", cache_dir=download_dir))


def text_lines(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")


def remove_source_cases(cfg, docs: dict[int, str], used: list[dict]) -> tuple[dict, list, dict]:
    """Find each query's source opinion among its top full-query BM25 cases; remove it from the
    pool, or drop the query when that case is some query's gold case."""
    c, b = cfg["clerc"], cfg["bm25"]
    ids = list(docs)
    model = bm25s.BM25(k1=b["k1"], b=b["b"])
    model.index(tokenize_words([docs[i] for i in ids]), show_progress=False)
    golds = {q["gold"] for q in used}
    sources, dropped_queries = set(), set()
    top = min(c["source_check_top"], len(ids))
    for q, words in zip(used, tokenize_words([q["text"] for q in used])):
        if not words:
            continue
        hits, _ = model.retrieve([words], k=top, show_progress=False)
        for h in hits[0]:
            case = ids[int(h)]
            if case != q["gold"] and clerc.is_source(q["text"], docs[case], c["source_probe_words"],
                                                     c["source_probes"], c["source_min_probes"]):
                (dropped_queries.add(q["qid"]) if case in golds else sources.add(case))
    kept_docs = {i: t for i, t in docs.items() if i not in sources}
    kept = [q for q in used if q["qid"] not in dropped_queries]
    return kept_docs, kept, {"source_cases_removed": len(sources), "queries_dropped_source_is_gold": len(dropped_queries)}


def main() -> None:
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--download-dir", default=str(Path(cfg["paths"]["cache"]) / "clerc_download"),
                    help="where the ~13 GB of release files go (outside the Kaggle output folder)")
    args = ap.parse_args()
    set_seeds(cfg["seed"])
    c, meta, t0 = cfg["clerc"], {}, time.time()
    out = clerc.pool_dir(cfg)
    out.mkdir(parents=True, exist_ok=True)

    queries = [clerc.parse_query_line(line) for line in text_lines(fetch(cfg, c["queries_file"], args.download_dir))
               if line.strip()]
    meta["training_queries"] = len(queries)
    print(f"{len(queries)} training queries [{time.time() - t0:.0f}s]", flush=True)

    needed = {p for q in queries for p in q["pos"] + q["negs"]}
    pid2did = clerc.parse_pid2did(text_lines(fetch(cfg, c["pid2did_file"], args.download_dir)), needed)
    meta["passages_needed"], meta["passages_mapped"] = len(needed), len(pid2did)
    order = np.random.default_rng(cfg["seed"]).permutation(len(queries))
    pool, used = clerc.assemble_pool(queries, pid2did, order, c["pool_docs"])
    meta["queries_used"], meta["pool_cases_planned"] = len(used), len(pool)
    meta["neg_cases_per_query_mean"] = float(np.mean([len(q["neg_cases"]) for q in used]))
    print(f"pool: {len(pool)} cases from {len(used)} queries [{time.time() - t0:.0f}s]", flush=True)

    wanted, docs = set(pool), {}
    for line in text_lines(fetch(cfg, c["docs_file"], args.download_dir)):
        case, _, text = line.partition("\t")
        if case.isdigit() and int(case) in wanted:
            docs[int(case)] = text
    meta["pool_cases_found"] = len(docs)
    used = [q for q in used if q["gold"] in docs]
    meta["queries_with_gold_found"] = len(used)
    print(f"{len(docs)} case texts kept [{time.time() - t0:.0f}s]", flush=True)

    docs, used, meta["source_check"] = remove_source_cases(cfg, docs, used)
    side = clerc.split_by_gold([q["gold"] for q in used], c["dev_share"], cfg["seed"])
    ordered = [i for i in pool if i in docs]
    pd.DataFrame({"case_id": ordered, "text": [docs[i] for i in ordered]}).to_parquet(out / "docs.parquet")
    qdf = pd.DataFrame({"qid": [q["qid"] for q in used], "text": [q["text"] for q in used],
                        "gold_case": [q["gold"] for q in used],
                        "n_neg_cases": [sum(n in docs for n in q["neg_cases"]) for q in used],
                        "order": [q["order"] for q in used], "side": [side[q["gold"]] for q in used]})
    qdf.to_parquet(out / "queries.parquet")
    meta.update({"pool_cases": len(ordered), "queries": len(qdf), "dev_queries": int((qdf.side == "dev").sum()),
                 "test_queries": int((qdf.side == "test").sum()), "gold_cases": int(qdf.gold_case.nunique()),
                 "chars_mean": float(np.mean([len(docs[i]) for i in ordered])), "seconds": time.time() - t0,
                 "git": git_hash(), "config": c})
    (out / "pool.meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps({k: v for k, v in meta.items() if k != "config"}, indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()

"""CLERC (Hou et al., 2024): full US federal court cases with citation-retrieval queries.

Why CLERC for E11: its documents carry no class labels, so any grouping must be discovered (the
band clusters), and it is much larger than LegalBench-RAG, so pool size can be varied.

Release files used (Hugging Face jhu-clsp/CLERC; licence not stated -> private use only):
- teva_train_dir/train_data.jsonl.gz: one training query per line, {query_id, query,
  positive_passages, negative_passages}: 1 positive and 20 negative PASSAGES. Their "docid" fields
  are passage ids (350-word passages, ~2,200 characters), not case ids: verified on the files.
  The query is a ~300-word window of a citing opinion with one citation removed; the positive
  passage is the passage that citation points to.
- collection/mapping.pid2did.tsv: passage id -> case id.
- collection/collection.doc.tsv.gz: case id \\t full case text (one line per case, no line breaks).

Our pool skips passages: positive and negative passage ids are mapped to their cases; the gold
document is the positive passage's case, the negatives are the other cases (duplicates and the
gold case removed). Only CLERC's own documents enter the pool -- no random fill. Queries are taken
in a seeded random order until the pool holds the target number of cases, so a larger pool built
with the same seed contains the smaller one.

Gold is document-level: a query's gold is its whole gold case (GoldSpan over the full text), so
document metrics and DRM apply; character-level metrics do not and are not reported.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from trr.config import REPO_ROOT
from trr.data.heldout import cut
from trr.data.load import Document, GoldSpan, Query

SUBSET = "clerc"


def doc_key(case_id: int | str) -> str:
    return f"{SUBSET}/{case_id}"


def parse_query_line(line: str) -> dict:
    """One training line -> {qid, text, pos (passage id), negs (passage ids)}; passage texts dropped."""
    r = json.loads(line)
    return {"qid": str(r["query_id"]), "text": r["query"],
            "pos": [int(p["docid"]) for p in r["positive_passages"]],
            "negs": [int(p["docid"]) for p in r["negative_passages"]]}


def parse_pid2did(lines: Iterable[str], needed: set[int]) -> dict[int, int]:
    """passage id -> case id, kept only for the passages we need (the full map has 23.7M rows)."""
    out = {}
    for line in lines:
        pid, did = line.split("\t", 1)
        if int(pid) in needed:
            out[int(pid)] = int(did)
    return out


def assemble_pool(queries: list[dict], pid2did: dict[int, int], order: np.ndarray,
                  pool_docs: int) -> tuple[list[int], list[dict]]:
    """Walk the queries in `order`; each adds its gold case and its negative cases to the pool
    until it holds >= pool_docs cases. Returns (pool case ids in order of entry, used queries
    with "gold" and "neg_cases"). A query whose positive passages map to no case, or to several
    cases, is skipped (its gold would be undefined)."""
    pool, seen, used = [], set(), []
    for rank, i in enumerate(order):
        q = queries[i]
        gold = {pid2did[p] for p in q["pos"] if p in pid2did}
        if len(gold) != 1:
            continue
        gold_case = gold.pop()
        negs = list(dict.fromkeys(pid2did[p] for p in q["negs"] if p in pid2did and pid2did[p] != gold_case))
        for case in [gold_case] + negs:
            if case not in seen:
                seen.add(case)
                pool.append(case)
        used.append({**q, "gold": gold_case, "neg_cases": negs, "order": rank})
        if len(pool) >= pool_docs:
            break
    return pool, used


def probe_windows(text: str, words: int, n: int) -> list[str]:
    """n windows of `words` consecutive words, spread evenly over the text (start ... end)."""
    w = text.split()
    if len(w) <= words:
        return [" ".join(w)] if w else []
    starts = np.linspace(0, len(w) - words, n).round().astype(int)
    return [" ".join(w[s:s + words]) for s in dict.fromkeys(starts.tolist())]


def is_source(query_text: str, case_text: str, words: int, n: int, min_found: int) -> bool:
    """Does the case contain the query's text verbatim (>= min_found of n probe windows)? Then it
    is the opinion the query was cut from, which would match the query for a trivial reason."""
    flat = " ".join(case_text.split())
    return sum(p in flat for p in probe_windows(query_text, words, n)) >= min_found


def split_by_gold(gold_cases: list[int], dev_share: float, seed: int) -> dict[int, str]:
    """gold case -> "dev" / "test": a seeded random dev_share of the gold cases are dev, so all
    questions about one case fall on one side (as the LegalBench split, trr.eval.splits)."""
    cases = sorted(set(gold_cases))
    rng = np.random.default_rng(seed)
    dev = set(rng.choice(cases, size=round(dev_share * len(cases)), replace=False).tolist()) if cases else set()
    return {c: ("dev" if c in dev else "test") for c in cases}


def pool_dir(cfg: dict) -> Path:
    c = cfg["clerc"]
    return REPO_ROOT / c["root"] / f"pool_{c['pool_docs']}"


def load_clerc(cfg: dict) -> tuple[list[Document], list[Query], dict[str, str]]:
    """(documents, queries, qid -> "dev"/"test") of the built pool (scripts/build_clerc_pool.py)."""
    root = pool_dir(cfg)
    if not (root / "docs.parquet").exists():
        raise FileNotFoundError(f"{root}/docs.parquet missing: build it with scripts/build_clerc_pool.py")
    d = pd.read_parquet(root / "docs.parquet")
    q = pd.read_parquet(root / "queries.parquet")
    docs = [Document(doc_key(i), SUBSET, t) for i, t in zip(d.case_id, d.text)]
    length = {doc.doc_id: len(doc.text) for doc in docs}
    queries = [Query(qid, SUBSET, text, [GoldSpan(doc_key(g), 0, length[doc_key(g)])])
               for qid, text, g in zip(q.qid, q.text, q.gold_case)]
    return docs, queries, dict(zip(q.qid, q.side))


def heldout_dir(cfg: dict) -> Path:
    return pool_dir(cfg) / "heldout"


def load_clerc_heldout(cfg: dict, length: int, intact: bool = False
                       ) -> tuple[list[Document], list[Query], dict[str, str]]:
    """E13 (trr.data.heldout): (documents, queries of `length` words, qid -> side). Every queried
    case is indexed with its longest query span cut out (Document.cut), unless `intact` (the
    sanity control: the passage left in). Gold = the whole ORIGINAL case."""
    hq_path = heldout_dir(cfg) / "queries.parquet"
    if not hq_path.exists():
        raise FileNotFoundError(f"{hq_path} missing: build it with scripts/build_heldout_queries.py")
    hq = pd.read_parquet(hq_path)
    if f"end_{length}" not in hq.columns:
        raise ValueError(f"no queries of {length} words; built lengths: {cfg['clerc']['heldout']['lengths']}")
    longest = max(cfg["clerc"]["heldout"]["lengths"])
    d = pd.read_parquet(pool_dir(cfg) / "docs.parquet")
    spans = {} if intact else {int(c): (int(s), int(e)) for c, s, e in zip(hq.case_id, hq.start, hq[f"end_{longest}"])}
    docs = []
    for case_id, text in zip(d.case_id, d.text):
        span = spans.get(int(case_id))
        docs.append(Document(doc_key(case_id), SUBSET, cut(text, *span) if span else text, cut=span))
    original = dict(zip(d.case_id.astype(int), d.text))
    queries = [Query(qid, SUBSET, original[int(c)][int(s):int(e)], [GoldSpan(doc_key(c), 0, len(original[int(c)]))])
               for qid, c, s, e in zip(hq.qid, hq.case_id, hq.start, hq[f"end_{length}"])]
    return docs, queries, dict(zip(hq.qid, hq.side))

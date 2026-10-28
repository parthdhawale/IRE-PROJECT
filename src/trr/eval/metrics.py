"""Span-based retrieval metrics (plan Section 5.2).

Every method is scored on character spans in the original documents, so methods with
different chunkings are comparable. All functions take the ranked hit list and the query's
gold spans and look only at the top k hits.

- DRM@k: share of the top-k hits whose document is not a gold document. This is the failure
  our method targets: a passage from a look-alike contract instead of the right one.
- Doc-Recall@k: 1 if any top-k hit comes from a gold document, else 0.
- Char precision/recall@k: characters are counted per document; overlapping hits are merged
  first so a character retrieved twice counts once.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

import numpy as np

from trr.data.load import GoldSpan
from trr.retrievers.base import Hit

Interval = tuple[int, int]


def merge_intervals(intervals: Iterable[Interval]) -> list[Interval]:
    """Union of half-open intervals, returned sorted and non-overlapping."""
    merged: list[list[int]] = []
    for s, e in sorted(i for i in intervals if i[1] > i[0]):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def total_length(intervals: Sequence[Interval]) -> int:
    return sum(e - s for s, e in intervals)


def intersection_length(a: Sequence[Interval], b: Sequence[Interval]) -> int:
    """Overlap of two merged (sorted, disjoint) interval lists, by a two-pointer sweep."""
    i = j = total = 0
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        total += max(0, hi - lo)
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return total


def _by_doc(spans: Iterable[tuple[str, int, int]]) -> dict[str, list[Interval]]:
    out: dict[str, list[Interval]] = defaultdict(list)
    for doc_id, s, e in spans:
        out[doc_id].append((s, e))
    return {d: merge_intervals(iv) for d, iv in out.items()}


def drm_at_k(hits: Sequence[Hit], gold: Sequence[GoldSpan], k: int) -> float:
    """Share of the top-k hits from a non-gold document.

    The denominator is the number of hits actually returned (at most k), so a retriever that
    returns fewer hits is not rewarded for the missing ones. With no hits, DRM is 0.
    """
    top = hits[:k]
    if not top:
        return 0.0
    gold_docs = {g.doc_id for g in gold}
    return sum(h.doc_id not in gold_docs for h in top) / len(top)


def doc_recall_at_k(hits: Sequence[Hit], gold: Sequence[GoldSpan], k: int) -> float:
    gold_docs = {g.doc_id for g in gold}
    return float(any(h.doc_id in gold_docs for h in hits[:k]))


def char_precision_recall_at_k(hits: Sequence[Hit], gold: Sequence[GoldSpan],
                               k: int) -> tuple[float, float, int]:
    """(precision, recall, retrieved_chars) over the union of the top-k hit spans."""
    retrieved = _by_doc((h.doc_id, h.start, h.end) for h in hits[:k])
    relevant = _by_doc((g.doc_id, g.start, g.end) for g in gold)
    ret_chars = sum(total_length(iv) for iv in retrieved.values())
    gold_chars = sum(total_length(iv) for iv in relevant.values())
    overlap = sum(intersection_length(iv, relevant[d]) for d, iv in retrieved.items() if d in relevant)
    precision = overlap / ret_chars if ret_chars else 0.0
    recall = overlap / gold_chars if gold_chars else 0.0
    return precision, recall, ret_chars


def query_metrics(hits: Sequence[Hit], gold: Sequence[GoldSpan], ks: Sequence[int]) -> dict[str, float]:
    """All metrics at every k for one query, as a flat dict like {'drm@4': 0.75, ...}."""
    out: dict[str, float] = {}
    for k in ks:
        p, r, n = char_precision_recall_at_k(hits, gold, k)
        out[f"drm@{k}"] = drm_at_k(hits, gold, k)
        out[f"doc_recall@{k}"] = doc_recall_at_k(hits, gold, k)
        out[f"char_p@{k}"] = p
        out[f"char_r@{k}"] = r
        out[f"chars@{k}"] = n
    return out


def paired_bootstrap_ci(a: Sequence[float], b: Sequence[float], resamples: int = 1000,
                        seed: int = 0, alpha: float = 0.05) -> tuple[float, float, float]:
    """Mean of (a - b) over queries and its percentile bootstrap CI.

    Paired: the same resampled queries are used for both methods, so per-query difficulty
    cancels out. A gain is claimed only if the CI excludes 0.
    """
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    if d.size == 0:
        raise ValueError("no queries")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(resamples, d.size))
    means = d[idx].mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(d.mean()), float(lo), float(hi)

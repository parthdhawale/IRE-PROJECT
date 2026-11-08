"""Hand-checked toy cases for every metric (plan: 'Check this first')."""

from __future__ import annotations

import numpy as np
import pytest

from trr.data.load import GoldSpan
from trr.eval.metrics import (
    char_precision_recall_at_k,
    doc_recall_at_k,
    drm_at_k,
    intersection_length,
    merge_intervals,
    paired_bootstrap_ci,
    paired_cluster_bootstrap_macro_ci,
    query_metrics,
)
from trr.retrievers.base import Hit


def H(doc: str, s: int, e: int, score: float = 1.0) -> Hit:
    return Hit(doc, s, e, score)


def G(doc: str, s: int, e: int) -> GoldSpan:
    return GoldSpan(doc, s, e)


def test_merge_and_intersection() -> None:
    assert merge_intervals([(5, 10), (0, 3), (8, 12), (12, 14), (20, 20)]) == [(0, 3), (5, 14)]
    assert intersection_length([(0, 10), (20, 30)], [(5, 25)]) == 10
    assert intersection_length([(0, 5)], [(5, 10)]) == 0


def test_drm_counts_wrong_document_share() -> None:
    gold = [G("a", 0, 10)]
    hits = [H("a", 0, 5), H("b", 0, 5), H("a", 20, 30), H("c", 0, 5)]
    assert drm_at_k(hits, gold, 1) == 0.0
    assert drm_at_k(hits, gold, 2) == 0.5
    assert drm_at_k(hits, gold, 4) == 0.5
    # fewer hits than k: denominator is hits returned
    assert drm_at_k(hits[:2], gold, 8) == 0.5
    assert drm_at_k([], gold, 4) == 0.0


def test_drm_multiple_gold_documents() -> None:
    gold = [G("a", 0, 10), G("b", 50, 60)]
    hits = [H("b", 0, 5), H("a", 0, 5), H("c", 0, 5)]
    assert drm_at_k(hits, gold, 3) == pytest.approx(1 / 3)
    assert doc_recall_at_k(hits, gold, 1) == 1.0
    assert doc_recall_at_k([H("c", 0, 5)], gold, 1) == 0.0


def test_char_pr_overlapping_hits_count_once() -> None:
    gold = [G("a", 10, 20)]
    hits = [H("a", 0, 15), H("a", 5, 15)]  # union [0,15): 15 chars, overlap with gold 5
    p, r, n = char_precision_recall_at_k(hits, gold, 2)
    assert n == 15
    assert p == pytest.approx(5 / 15)
    assert r == pytest.approx(5 / 10)


def test_char_pr_multiple_gold_snippets_and_docs() -> None:
    gold = [G("a", 0, 10), G("a", 5, 20), G("b", 100, 110)]  # gold chars: a 20 + b 10 = 30
    hits = [H("a", 0, 20), H("b", 105, 115), H("c", 100, 110)]
    p, r, n = char_precision_recall_at_k(hits, gold, 3)
    assert n == 20 + 10 + 10
    assert p == pytest.approx(25 / 40)
    assert r == pytest.approx(25 / 30)
    # same offsets in a different document do not count
    p, r, _ = char_precision_recall_at_k([H("c", 0, 10)], [G("a", 0, 10)], 1)
    assert (p, r) == (0.0, 0.0)


def test_char_recall_rises_with_k() -> None:
    gold = [G("a", 0, 30)]
    hits = [H("a", 0, 10), H("a", 10, 20), H("a", 20, 30)]
    recalls = [char_precision_recall_at_k(hits, gold, k)[1] for k in (1, 2, 3)]
    assert recalls == pytest.approx([1 / 3, 2 / 3, 1.0])


def test_query_metrics_keys() -> None:
    m = query_metrics([H("a", 0, 10)], [G("a", 0, 10)], [1, 4])
    assert m["drm@1"] == 0.0 and m["char_p@4"] == 1.0 and m["char_r@1"] == 1.0 and m["chars@4"] == 10


def test_paired_bootstrap() -> None:
    a, b = [1.0] * 50, [0.0] * 50
    assert paired_bootstrap_ci(a, b) == (1.0, 1.0, 1.0)
    mean, lo, hi = paired_bootstrap_ci([1, 0] * 50, [0, 1] * 50, resamples=500, seed=0)
    assert mean == 0.0 and lo < 0 < hi
    assert paired_bootstrap_ci([1, 0, 1], [0, 0, 0], seed=0) == paired_bootstrap_ci([1, 0, 1], [0, 0, 0], seed=0)


def test_cluster_bootstrap_with_singletons_equals_query_bootstrap() -> None:
    a, b = [1, 0, 1, 1, 0, 0, 1], [0, 0, 1, 0, 1, 0, 0]
    d = [np.array([x - y], dtype=float) for x, y in zip(a, b)]
    assert paired_cluster_bootstrap_macro_ci({"s": d}, seed=3) == paired_bootstrap_ci(a, b, seed=3)


def test_cluster_bootstrap_macro_weighs_subsets_equally() -> None:
    # subset s1: 10 queries all -1; subset s2: 2 queries all 0 -> macro mean -0.5, not -10/12
    diffs = {"s1": [np.full(5, -1.0), np.full(5, -1.0)], "s2": [np.zeros(1), np.zeros(1)]}
    assert paired_cluster_bootstrap_macro_ci(diffs, resamples=200) == (-0.5, -0.5, -0.5)


def test_cluster_bootstrap_is_wider_when_errors_cluster() -> None:
    # same 20 differences, either as 20 independent queries or as 2 documents of 10
    vals = np.array([-1.0] * 10 + [0.0] * 10)
    _, lo_q, hi_q = paired_cluster_bootstrap_macro_ci({"s": [np.array([v]) for v in vals]}, seed=0)
    _, lo_d, hi_d = paired_cluster_bootstrap_macro_ci({"s": [vals[:10], vals[10:]]}, seed=0)
    assert hi_d - lo_d > hi_q - lo_q

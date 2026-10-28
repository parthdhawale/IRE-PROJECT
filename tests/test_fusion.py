from __future__ import annotations

import numpy as np
import pytest

from trr.retrievers.flat import rrf_fuse


def test_rrf_rewards_agreement() -> None:
    rows, scores = rrf_fuse([np.array([1, 2, 3]), np.array([3, 1, 4])], rrf_k=60)
    assert rows[0] == 1  # ranks 1 and 2
    assert scores[0] == pytest.approx(1 / 61 + 1 / 62)
    assert set(rows) == {1, 2, 3, 4}
    assert list(scores) == sorted(scores, reverse=True)


def test_rrf_ties_break_by_row() -> None:
    rows, _ = rrf_fuse([np.array([5]), np.array([2])], rrf_k=60)
    assert list(rows) == [2, 5]

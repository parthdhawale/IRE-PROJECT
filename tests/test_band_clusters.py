import numpy as np
import pytest

from trr.clustering.band_clusters import BandClusters, mid_band_vocab

MERGER = [["merger", "shares", "closing", "x1"], ["merger", "shares", "closing", "x2"],
          ["merger", "shares", "target", "x3"]]
PRIVACY = [["privacy", "data", "cookies", "y1"], ["privacy", "data", "cookies", "y2"],
           ["privacy", "data", "users", "y3"]]
DOCS = MERGER + PRIVACY   # band (min_df=2, <= 60% of 6 docs): merger shares closing privacy data cookies


def _fit(seed: int = 0, k: int = 2) -> BandClusters:
    return BandClusters(min_df=2, max_frac=0.6, k=k, n_init=5, max_iter=50, seed=seed).fit(DOCS)


def test_mid_band_floor_is_a_count_and_ceiling_a_share():
    tokens = [["a", "b"], ["a", "c"], ["a", "b", "d"]]           # df: a=3, b=2, c=1, d=1
    assert mid_band_vocab(tokens, min_df=2, max_frac=0.9) == ["b"]   # a is in 100% > 90%
    assert mid_band_vocab(tokens, min_df=2, max_frac=1.0) == ["a", "b"]
    assert mid_band_vocab(tokens, min_df=1, max_frac=0.5) == ["c", "d"]


def test_clusters_separate_the_two_kinds_for_any_seed():
    for seed in (0, 1, 2):
        c = _fit(seed)
        assert len(set(c.labels[:3])) == 1 and len(set(c.labels[3:])) == 1
        assert c.labels[0] != c.labels[3]
        assert np.allclose(np.linalg.norm(c.centroids, axis=1), 1.0)


def test_clusters_are_named_by_their_heaviest_words():
    c = _fit()
    merger_cluster = c.labels[0]
    assert set(c.names(2)[merger_cluster]) <= {"merger", "shares", "closing"}


def test_new_document_is_placed_and_added_without_refit():
    c = _fit()
    vocab, merger_cluster = list(c.vocab), c.labels[0]
    before = c.counts[merger_cluster]
    placed = c.add([["merger", "closing", "shares", "brand_new_word"]])
    assert placed[0] == merger_cluster
    assert c.counts[merger_cluster] == before + 1 and len(c.labels) == len(DOCS) + 1
    assert c.vocab == vocab                                   # frozen: nothing refit


def test_route_sends_a_query_to_its_kind_and_a_blank_query_everywhere():
    c = _fit()
    assert c.route(["privacy", "data"], b=1) == [int(c.labels[3])]
    assert c.route(["unrelated", "words"], b=1) == [0, 1]     # no mid-band word: flat search


def test_empty_mid_band_is_refused_with_a_clear_error():
    with pytest.raises(ValueError, match="empty mid band"):
        BandClusters(min_df=20, max_frac=0.5, k=2, n_init=1, max_iter=5, seed=0).fit(DOCS)


def test_k_never_exceeds_the_number_of_documents():
    assert _fit(k=50).n_clusters == len(DOCS)

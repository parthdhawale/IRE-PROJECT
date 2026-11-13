"""Embedding pipeline on a tiny pool, with a deterministic stand-in for the embedding model
(hashed bag-of-words vectors), so the maths is checked exactly and no model is downloaded."""

import hashlib

import numpy as np
import pytest

from trr.clustering.embed_clusters import EmbedClusters
from trr.data.load import Document
from trr.retrievers.chunk_store import ChunkStore
from trr.retrievers.embed_pipeline import POOL, EmbedIndex, EmbedPipelineRetriever
from trr.routing.routers import tokenize_words

DIM = 64
CFG = {"seed": 0, "chunking": {"method": "fixed", "chunk_chars": 60, "overlap": 10},
       "band_clusters": {"kmeans_n_init": 5, "kmeans_max_iter": 50}, "bm25": {"k1": 1.5, "b": 0.75}}
TOPICS = {"tax": "taxpayer deduction revenue income", "crime": "defendant sentence jury verdict",
          "patent": "patent claim infringement invention"}


def _vec(text: str) -> np.ndarray:
    v = np.zeros(DIM)
    for w in tokenize_words([text])[0]:
        v[int(hashlib.md5(w.encode()).hexdigest(), 16) % DIM] += 1
    return v / max(np.linalg.norm(v), 1e-12)


class FakeEmbedder:
    model_name = "fake"

    def encode_queries(self, texts):
        return np.stack([_vec(t) for t in texts]).astype(np.float32)


DOCS = [Document(f"clerc/{t}{j}", "clerc", f"The court weighed {w}. Party {t}{j} argued about {w} at length. "
                 f"Further {w} and {w} were discussed.") for t, w in TOPICS.items() for j in range(3)]


@pytest.fixture(scope="module")
def ix():
    store = ChunkStore(CFG)
    store.add(DOCS)
    store.merge(POOL, ["clerc"], embeddings=False)
    sc = store.subsets[POOL]
    sc.emb = np.stack([_vec(t) for t in sc.texts]).astype(np.float32)
    store._embedder = FakeEmbedder()
    return EmbedIndex(CFG, store, DOCS, k=3)


def _ret(ix, router="band", doc_score="maxp", b=1):
    return EmbedPipelineRetriever(ix.store, ix, router, b, doc_score)


def test_clusters_are_the_three_topics_and_the_query_is_routed_to_its_topic(ix):
    for t in TOPICS:
        assert len({ix.doc_cluster[f"clerc/{t}{j}"] for j in range(3)}) == 1
    assert len(set(ix.doc_cluster.values())) == 3
    assert _ret(ix).chosen_clusters(_vec("jury verdict for the defendant")) == [ix.doc_cluster["clerc/crime0"]]


def test_document_vectors_are_unit_means_of_their_chunks(ix):
    emb = ix.store.embeddings(POOL)
    for i, rows in enumerate(ix.rows):
        m = emb[rows].mean(axis=0)
        assert ix.doc_vecs[i] == pytest.approx(m / np.linalg.norm(m), abs=1e-6)


@pytest.mark.parametrize("how", ["mean", "maxp"])
def test_cluster_blocks_score_exactly_like_brute_force(ix, how):
    q, emb = _vec("patent claim infringement"), ix.store.embeddings(POOL)
    idx, scores = ix.doc_scores(q, [0, 1, 2], how)
    assert list(idx) == list(range(len(DOCS)))                     # corpus order
    ref = [ix.doc_vecs[i] @ q if how == "mean" else (emb[r] @ q).max() for i, r in enumerate(ix.rows)]
    assert scores == pytest.approx(ref, abs=1e-6)


def test_retrieve_returns_the_top_documents_chunks_and_ranks_documents(ix):
    ret = _ret(ix, b=1)
    hits = ret.retrieve("a patent claim and its infringement", k=5, pool=POOL)
    top = ret.last_diag["docs"][0]
    assert top.startswith("clerc/patent") and ret.last_diag["doc"] == top and len(ret.last_diag["docs"]) == 3
    assert hits and {h.doc_id for h in hits} == {top}
    assert [h.score for h in hits] == sorted([h.score for h in hits], reverse=True)


def test_router_none_searches_everything_and_oracle_the_gold_cluster(ix):
    none = _ret(ix, router="none")
    none.retrieve("taxpayer income", k=3, pool=POOL)
    assert none.last_diag["clusters"] == [0, 1, 2] and len(none.last_diag["docs"]) == 9   # all 9 cases ranked
    oracle = _ret(ix, router="oracle")
    oracle.set_gold({"clerc/tax1"})
    assert oracle.chosen_clusters(_vec("anything")) == [ix.doc_cluster["clerc/tax1"]]


def test_unknown_router_or_document_score_is_refused(ix):
    with pytest.raises(ValueError):
        EmbedPipelineRetriever(ix.store, ix, "magic", 1, "maxp")
    with pytest.raises(ValueError):
        EmbedPipelineRetriever(ix.store, ix, "band", 1, "sum")


def test_new_document_is_placed_without_reclustering():
    vecs = np.stack([_vec(w) for w in TOPICS.values() for _ in range(3)])
    c = EmbedClusters(k=3, n_init=3, max_iter=20, seed=0).fit(vecs)
    before = c.counts.copy()
    placed = c.add(_vec("jury verdict defendant")[None, :])[0]
    assert placed == c.labels[3] and c.counts[placed] == before[placed] + 1

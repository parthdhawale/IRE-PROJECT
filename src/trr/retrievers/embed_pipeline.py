"""Embedding pipeline (E12): embedding clusters -> embedding routing -> dense document -> dense passage.

The same three steps as the band pipeline (band_pipeline.py), with embeddings at every step:
1. Clusters: each document's vector is the normalised mean of its chunk vectors; spherical k-means
   groups them (trr.clustering.embed_clusters).
2. Route: the query's embedding goes to the B clusters with the closest centroids.
3. Document: the documents of those clusters are ranked by the query vector, either against the
   document vector ("mean") or by the best chunk of each document ("maxp", max-passage, as in the
   CLERC paper's ColBERT baseline). The top document is chosen.
4. Passage: the chosen document's chunks are ranked by cosine with the query.

Chunk vectors are stored grouped by cluster (one contiguous block per cluster, as in an
inverted-file index), so searching B clusters reads only their blocks: routing really cuts work.
Routers: "band" (the clusters), "none" (all clusters: flat dense doc-first, the ablation) and
"oracle" (the gold document's cluster). No model is trained: the embedding model is fixed, so a
new document is embedded and placed (extendible).
"""

from __future__ import annotations

import numpy as np

from trr.clustering.band_clusters import _unit_rows
from trr.clustering.embed_clusters import EmbedClusters
from trr.data.load import Document
from trr.retrievers.base import Hit
from trr.retrievers.chunk_store import ChunkStore
from trr.retrievers.flat import _Base, _hits

POOL = "all"
DOC_SCORES = ("mean", "maxp")


class EmbedIndex:
    """Built once per pool and k: document vectors, clusters, chunk vectors grouped by cluster."""

    def __init__(self, cfg: dict, store: ChunkStore, docs: list[Document], k: int):
        bc = cfg["band_clusters"]   # k-means restarts / iterations shared with the band clusters
        self.cfg, self.store, self.docs, self.k = cfg, store, docs, k
        emb, sc = store.embeddings(POOL), store.subsets[POOL]
        self.rows = [sc.doc_rows[d.doc_id] for d in docs]
        self.doc_vecs = _unit_rows(np.stack([emb[r].mean(axis=0) for r in self.rows]))
        self.clusters = EmbedClusters(k, bc["kmeans_n_init"], bc["kmeans_max_iter"], cfg["seed"]).fit(self.doc_vecs)
        self.doc_cluster = {d.doc_id: int(c) for d, c in zip(docs, self.clusters.labels)}
        self.cluster_docs = {c: np.array([i for i, d in enumerate(docs) if self.doc_cluster[d.doc_id] == c], dtype=int)
                             for c in range(self.clusters.n_clusters)}
        # chunk vectors in cluster order: block c holds the chunks of cluster c's documents, document
        # by document; starts[c] are the offsets inside block c where each document's chunks begin
        self.blocks, self.starts = {}, {}
        for c, idx in self.cluster_docs.items():
            if len(idx):
                self.blocks[c] = emb[np.concatenate([self.rows[i] for i in idx])]
                self.starts[c] = np.cumsum([0] + [len(self.rows[i]) for i in idx[:-1]])

    def doc_scores(self, qvec: np.ndarray, clusters: list[int], how: str) -> tuple[np.ndarray, np.ndarray]:
        """(document indices in corpus order, their scores) over the documents of these clusters."""
        idx, scores = [], []
        for c in clusters:
            if c not in self.blocks:
                continue
            idx.append(self.cluster_docs[c])
            if how == "mean":
                scores.append(self.doc_vecs[self.cluster_docs[c]] @ qvec)
            else:                                       # maxp: each document's best chunk
                scores.append(np.maximum.reduceat(self.blocks[c] @ qvec, self.starts[c]))
        idx, scores = np.concatenate(idx), np.concatenate(scores)
        order = np.argsort(idx, kind="stable")          # corpus order, so ties keep the first document
        return idx[order], scores[order]


class EmbedPipelineRetriever(_Base):
    """route -> dense document -> dense passages of that document."""

    def __init__(self, store: ChunkStore, index: EmbedIndex, router: str, b: int, doc_score: str,
                 doc_list: int = 10):
        super().__init__(store)
        if router not in ("band", "none", "oracle"):
            raise ValueError(f"unknown router {router!r}")
        if doc_score not in DOC_SCORES:
            raise ValueError(f"unknown document score {doc_score!r}")
        self.ix, self.router, self.b, self.doc_score, self.doc_list = index, router, b, doc_score, doc_list
        beam = f"_b{b}" if router == "band" else ""
        self.name = f"emb_{router}_k{index.k}{beam}_{doc_score}"
        self.needs_gold = router == "oracle"
        self.last_diag: dict = {}

    def index(self, docs: list[Document]) -> None:  # the pool and the EmbedIndex are built outside
        pass

    def set_gold(self, gold_docs: set[str]) -> None:
        self._gold_clusters = sorted({self.ix.doc_cluster[d] for d in gold_docs})

    def chosen_clusters(self, qvec: np.ndarray) -> list[int]:
        if self.router == "none":
            return list(range(self.ix.clusters.n_clusters))
        if self.router == "oracle":
            return self._gold_clusters
        return self.ix.clusters.route(qvec, self.b)

    def rank_documents(self, qvec: np.ndarray, clusters: list[int], n: int) -> list[str]:
        idx, scores = self.ix.doc_scores(qvec, clusters, self.doc_score)
        best = idx[np.argsort(-scores, kind="stable")[:n]]
        return [self.ix.docs[i].doc_id for i in best]

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        q = self.qvec(query)
        clusters = self.chosen_clusters(q)
        ranked = self.rank_documents(q, clusters, self.doc_list)
        rows = self.store.subsets[POOL].doc_rows[ranked[0]]
        scores = self.store.embeddings(POOL)[rows] @ q
        order = np.argsort(-scores, kind="stable")[:k]
        self.last_diag = {"clusters": clusters, "doc": ranked[0], "docs": ranked}
        return _hits(self.store, POOL, rows[order], scores[order])

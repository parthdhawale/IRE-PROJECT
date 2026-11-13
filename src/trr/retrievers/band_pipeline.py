"""Band pipeline (E11): band clusters -> band routing -> rare-in-cluster document -> passage.

IR idea: two document-frequency bands with two jobs.
- The MID band says what kind of document it is: it builds the clusters (trr.clustering) and
  routes the query to the top-B of them.
- The RARE band says which document it is: query words found in fewer than `rare_below`
  documents of the searched clusters -- party names, products, amounts. "Confidential" is in every
  NDA, so it cannot pick an NDA; a name in one NDA can. Rarity is counted INSIDE the searched
  clusters: a word common among merger agreements can still single out one NDA.
The document is chosen by BM25 over the query's rare words, with idf from the searched clusters
only (a collection-local index, as in group_first.py); a query without any rare word falls back to
full-query BM25. The passages are then ranked inside that one document. With passage="bm25" the
whole pipeline is lexical: no embedding model is needed to index, add a document or answer.

Routers: "band" (the clusters), "none" (every cluster: flat rare-band doc-first, the ablation
without clustering) and "oracle" (the gold document's cluster: the upper bound of routing).
Every query searches ONE mixed pool of all documents, so a wrong cluster can really be chosen.
"""

from __future__ import annotations

from collections import Counter

import bm25s
import numpy as np

from trr.clustering.band_clusters import BandClusters
from trr.data.load import Document
from trr.retrievers.base import Hit
from trr.retrievers.chunk_store import ChunkStore
from trr.retrievers.flat import _hits
from trr.routing.routers import tokenize_words

POOL = "all"


def unique(words: list[str]) -> list[str]:
    """Query words without repeats, in order of first appearance."""
    return list(dict.fromkeys(words))


class BandIndex:
    """Built once per pool and clustering setting: document tokens, clusters, local indexes."""

    def __init__(self, cfg: dict, docs: list[Document], min_df: int, max_frac: float, k: int,
                 doc_tokens: list[list[str]] | None = None):
        bc = cfg["band_clusters"]
        self.cfg, self.docs = cfg, docs
        self.min_df, self.max_frac, self.k = min_df, max_frac, k
        self.doc_tokens = doc_tokens if doc_tokens is not None else tokenize_words([d.text for d in docs])
        self.clusters = BandClusters(min_df, max_frac, k, bc["kmeans_n_init"], bc["kmeans_max_iter"],
                                     cfg["seed"]).fit(self.doc_tokens)
        self.doc_cluster = {d.doc_id: int(c) for d, c in zip(docs, self.clusters.labels)}
        self.cluster_docs = {c: [i for i, d in enumerate(docs) if self.doc_cluster[d.doc_id] == c]
                             for c in range(self.clusters.n_clusters)}
        self._local: dict[tuple[int, ...], tuple[bm25s.BM25, np.ndarray, Counter]] = {}

    def local(self, clusters: list[int]) -> tuple[bm25s.BM25, np.ndarray, Counter]:
        """(BM25 over the documents of these clusters, their document indices, their document
        frequencies), built once per cluster set. Both idf and rarity come from these documents."""
        key = tuple(sorted(clusters))
        if key not in self._local:
            idx = np.array(sorted(i for c in key for i in self.cluster_docs[c]))
            b = self.cfg["bm25"]
            model = bm25s.BM25(k1=b["k1"], b=b["b"])
            model.index([self.doc_tokens[i] for i in idx], show_progress=False)
            df = Counter(w for i in idx for w in set(self.doc_tokens[i]))
            self._local[key] = (model, idx, df)
        return self._local[key]


class BandPipelineRetriever:
    """route -> rare-in-cluster document -> passages of that document."""

    def __init__(self, store: ChunkStore, index: BandIndex, router: str, b: int, rare_below: int,
                 passage: str = "bm25"):
        if router not in ("band", "none", "oracle"):
            raise ValueError(f"unknown router {router!r}")
        if passage != "bm25":
            raise NotImplementedError("dense passages need chunk embeddings (Kaggle); not built yet")
        self.store, self.ix, self.router, self.b = store, index, router, b
        self.rare_below, self.passage = rare_below, passage
        beam = f"_b{b}" if router == "band" else ""
        self.name = (f"band_{router}_df{index.min_df}_mx{round(index.max_frac * 100)}_k{index.k}{beam}"
                     f"_r{rare_below}_{passage}")
        self.needs_gold = router == "oracle"
        self.last_diag: dict = {}

    def index(self, docs: list[Document]) -> None:  # the pool and the BandIndex are built outside
        pass

    def set_gold(self, gold_docs: set[str]) -> None:
        self._gold_clusters = sorted({self.ix.doc_cluster[d] for d in gold_docs})

    def chosen_clusters(self, words: list[str]) -> list[int]:
        if self.router == "none":
            return list(range(self.ix.clusters.n_clusters))
        if self.router == "oracle":
            return self._gold_clusters
        return self.ix.clusters.route(words, self.b)

    def choose_document(self, words: list[str], clusters: list[int]) -> tuple[str, list[str]]:
        """(doc_id, words used): BM25 over the query's rare-in-cluster words, else all its words."""
        model, idx, df = self.ix.local(clusters)
        rare = [w for w in unique(words) if 0 < df[w] < self.rare_below]
        used = rare or unique(words)
        scores = np.asarray(model.get_scores(used))
        return self.ix.docs[idx[int(np.argmax(scores))]].doc_id, rare

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        words = tokenize_words([query])[0]
        clusters = self.chosen_clusters(words)
        doc_id, rare = self.choose_document(words, clusters)
        rows = self.store.subsets[POOL].doc_rows[doc_id]
        scores = self.store.bm25_scores(POOL, query)[rows]   # chunk BM25, idf over the whole pool
        order = np.argsort(-scores, kind="stable")[:k]
        self.last_diag = {"clusters": clusters, "doc": doc_id, "n_rare": len(rare), "fallback": not rare}
        return _hits(self.store, POOL, rows[order], scores[order])

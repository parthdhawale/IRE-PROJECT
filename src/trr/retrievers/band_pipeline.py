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

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer

from trr.clustering.band_clusters import BandClusters, _identity
from trr.data.load import Document
from trr.retrievers.base import Hit
from trr.retrievers.chunk_store import ChunkStore
from trr.retrievers.flat import _hits
from trr.routing.routers import tokenize_words

POOL = "all"


def unique(words: list[str]) -> list[str]:
    """Query words without repeats, in order of first appearance."""
    return list(dict.fromkeys(words))


def count_terms(doc_tokens: list[list[str]]) -> tuple[CountVectorizer, sparse.csr_matrix]:
    """(vectorizer, documents x words count matrix). Independent of the clustering, so one count
    serves every BandIndex of a pool (the dev grid builds dozens)."""
    counter = CountVectorizer(analyzer=_identity, lowercase=False)
    return counter, counter.fit_transform(doc_tokens)


class BandIndex:
    """Built once per pool and clustering setting: document tokens, clusters, and one
    document-term count matrix from which BM25 is computed for ANY set of clusters.

    Collection-local BM25 (as in group_first.py) needs idf, document counts and average length
    from the searched clusters only. Instead of building a separate BM25 index per cluster set
    (fine for 714 contracts, hours for 10k court cases), the statistics are read from the count
    matrix restricted to the clusters' documents. Same formula as bm25s (Lucene variant):
        idf(w) = ln(1 + (N - df + 0.5) / (df + 0.5))
        score(d) = sum over query words of idf(w) * tf / (tf + k1 * (1 - b + b * len(d) / avg_len))
    with N, df and avg_len counted inside the searched clusters. Cost per query grows with the
    postings of the query words, not with the size of the clusters.
    """

    def __init__(self, cfg: dict, docs: list[Document], min_df: int, max_frac: float, k: int,
                 doc_tokens: list[list[str]] | None = None,
                 counts: tuple[CountVectorizer, sparse.csr_matrix] | None = None):
        bc = cfg["band_clusters"]
        self.cfg, self.docs = cfg, docs
        self.min_df, self.max_frac, self.k = min_df, max_frac, k
        self.doc_tokens = doc_tokens if doc_tokens is not None else tokenize_words([d.text for d in docs])
        self.clusters = BandClusters(min_df, max_frac, k, bc["kmeans_n_init"], bc["kmeans_max_iter"],
                                     cfg["seed"]).fit(self.doc_tokens)
        self.doc_cluster = {d.doc_id: int(c) for d, c in zip(docs, self.clusters.labels)}
        self.cluster_docs = {c: [i for i, d in enumerate(docs) if self.doc_cluster[d.doc_id] == c]
                             for c in range(self.clusters.n_clusters)}
        counter, counts = counts if counts is not None else count_terms(self.doc_tokens)
        self.counter = counter                                   # turns a new document into its count row
        self.word_id = counter.vocabulary_
        self.tf = counts.tocsc()                                 # column w = postings of word w
        self.doc_len = np.asarray(counts.sum(axis=1)).ravel().astype(float)
        self._local: dict[tuple[int, ...], np.ndarray] = {}

    def local(self, clusters: list[int]) -> np.ndarray:
        """Boolean mask over documents: those in these clusters (cached per cluster set)."""
        key = tuple(sorted(clusters))
        if key not in self._local:
            mask = np.zeros(len(self.docs), dtype=bool)
            mask[[i for c in key for i in self.cluster_docs[c]]] = True
            self._local[key] = mask
        return self._local[key]

    def postings(self, word: str, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(documents containing word, its count in each), inside the mask only."""
        w = self.word_id.get(word)
        if w is None:
            return np.empty(0, dtype=int), np.empty(0)
        lo, hi = self.tf.indptr[w], self.tf.indptr[w + 1]
        rows, tf = self.tf.indices[lo:hi], self.tf.data[lo:hi]
        keep = mask[rows]
        return rows[keep], tf[keep].astype(float)

    def doc_freq(self, word: str, mask: np.ndarray) -> int:
        return len(self.postings(word, mask)[0])

    def bm25(self, words: list[str], mask: np.ndarray) -> np.ndarray:
        """BM25 of every document for these query words, statistics from the masked documents
        only (0 outside the mask). A repeated word counts each time, as in bm25s."""
        b = self.cfg["bm25"]
        n, avg_len = int(mask.sum()), float(self.doc_len[mask].mean())
        scores = np.zeros(len(self.docs))
        for word in words:
            rows, tf = self.postings(word, mask)
            if len(rows):
                idf = np.log(1 + (n - len(rows) + 0.5) / (len(rows) + 0.5))
                norm = b["k1"] * (1 - b["b"] + b["b"] * self.doc_len[rows] / avg_len)
                scores[rows] += idf * tf / (tf + norm)
        return scores


class BandPipelineRetriever:
    """route -> rare-in-cluster document -> passages of that document."""

    def __init__(self, store: ChunkStore, index: BandIndex, router: str, b: int, rare_below: int,
                 passage: str = "bm25", doc_list: int = 10):
        if router not in ("band", "none", "oracle"):
            raise ValueError(f"unknown router {router!r}")
        if passage != "bm25":
            raise NotImplementedError("dense passages need chunk embeddings (Kaggle); not built yet")
        self.store, self.ix, self.router, self.b = store, index, router, b
        self.rare_below, self.passage = rare_below, passage
        self.doc_list = doc_list        # documents ranked per query (document-level metrics, e.g. @10)
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

    def rank_documents(self, words: list[str], clusters: list[int], n: int) -> tuple[list[str], list[str]]:
        """(top-n doc_ids best first, rare words used): BM25 over the query's rare-in-cluster words,
        else over all its words. Ties keep corpus order; a query with no usable word scores 0
        everywhere, so it gets the first documents (the tie rule)."""
        mask = self.ix.local(clusters)
        rare = [w for w in unique(words) if 0 < self.ix.doc_freq(w, mask) < self.rare_below]
        scores = self.ix.bm25(rare or unique(words), mask)
        cand = np.flatnonzero(mask)
        best = cand[np.argsort(-scores[cand], kind="stable")[:n]]
        return [self.ix.docs[i].doc_id for i in best], rare

    def choose_document(self, words: list[str], clusters: list[int]) -> tuple[str, list[str]]:
        """(doc_id, rare words used): the top document of rank_documents."""
        ranked, rare = self.rank_documents(words, clusters, 1)
        return ranked[0], rare

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        words = tokenize_words([query])[0]
        clusters = self.chosen_clusters(words)
        ranked, rare = self.rank_documents(words, clusters, self.doc_list)
        doc_id = ranked[0]
        rows = self.store.subsets[POOL].doc_rows[doc_id]
        scores = self.store.bm25_scores_in_rows(POOL, query, rows)   # chunk BM25, idf over the whole pool
        order = np.argsort(-scores, kind="stable")[:k]
        self.last_diag = {"clusters": clusters, "doc": doc_id, "docs": ranked, "n_rare": len(rare),
                          "fallback": not rare}
        return _hits(self.store, POOL, rows[order], scores[order])

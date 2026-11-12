"""Flat chunk baselines over a shared ChunkStore: BM25, dense, hybrid (RRF), oracle, doc-first.

Each class follows the Retriever protocol in base.py and returns Hits in original offsets.
Query vectors are cached per query text so one batch encode serves dense, hybrid and oracle.
"""

from __future__ import annotations

import bm25s
import numpy as np

from trr.data.load import Document
from trr.retrievers.base import Hit
from trr.retrievers.chunk_store import ChunkStore, tokenize
from trr.retrievers.query_split import split_query


def _hits(store: ChunkStore, subset: str, rows, scores) -> list[Hit]:
    sc = store.subsets[subset]
    return [Hit(sc.doc_ids[r], int(sc.starts[r]), int(sc.ends[r]), float(s))
            for r, s in zip(rows, scores) if r >= 0]


class _Base:
    name = "base"
    store_kind = "chunk"   # "chunk" = 500-char chunks, "leaf" = section-tree leaves

    def __init__(self, store: ChunkStore):
        self.store = store
        self._qvecs: dict[str, np.ndarray] = {}

    def index(self, docs: list[Document]) -> None:
        self.store.add(docs)

    def prepare_queries(self, queries: list[str]) -> None:
        """Batch-encode query texts once (dense methods only)."""
        todo = [q for q in dict.fromkeys(queries) if q not in self._qvecs]
        if todo:
            for q, v in zip(todo, self.store.embedder.encode_queries(todo)):
                self._qvecs[q] = v

    def qvec(self, query: str) -> np.ndarray:
        if query not in self._qvecs:
            self.prepare_queries([query])
        return self._qvecs[query]


class BM25Retriever(_Base):
    """Flat BM25 over all chunks of the pool (probabilistic relevance, tf saturation via k1,
    length normalisation via b)."""
    name = "bm25"

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        rows, scores = self.store.bm25_search(pool, query, k)
        return _hits(self.store, pool, rows, scores)


class DenseRetriever(_Base):
    """Standard chunk RAG: bi-encoder cosine top-k over all chunks of the pool."""
    name = "dense"

    def index(self, docs: list[Document]) -> None:
        super().index(docs)
        self.store.embeddings(docs[0].subset)

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        rows, scores = self.store.dense_search(pool, self.qvec(query), k)
        return _hits(self.store, pool, rows, scores)


def rrf_fuse(rankings: list[np.ndarray], rrf_k: int) -> tuple[np.ndarray, np.ndarray]:
    """Reciprocal Rank Fusion: score(d) = sum over rankings of 1 / (rrf_k + rank).

    Uses ranks only, so BM25 scores and cosines need no calibration to be combined.
    """
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, row in enumerate(ranking, start=1):
            fused[int(row)] = fused.get(int(row), 0.0) + 1.0 / (rrf_k + rank)
    items = sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))
    return np.array([r for r, _ in items]), np.array([s for _, s in items])


class HybridRetriever(DenseRetriever):
    """RRF of BM25 and dense, each taken to `depth` candidates."""
    name = "hybrid"

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        h = self.store.cfg["hybrid"]
        lex, _ = self.store.bm25_search(pool, query, h["depth"])
        den, _ = self.store.dense_search(pool, self.qvec(query), h["depth"])
        rows, scores = rrf_fuse([lex, den], h["rrf_k"])
        return _hits(self.store, pool, rows[:k], scores[:k])


class OracleRetriever(DenseRetriever):
    """Dense chunk search restricted to the gold document(s).

    DRM is 0 by construction; its char P/R is the upper bound that perfect document selection
    would give a dense chunk ranker. The harness calls set_gold() before every query.
    """
    name = "oracle"
    needs_gold = True

    def set_gold(self, gold_docs: set[str]) -> None:
        self._gold = gold_docs

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        rows, scores = self.store.dense_search_in_docs(pool, self.qvec(query), self._gold, k)
        return _hits(self.store, pool, rows, scores)


class DocFirstRetriever(DenseRetriever):
    """Naive two-stage pipeline: BM25 over whole documents -> top-1 document -> dense chunk
    search inside it. The baseline our family -> document -> chunk method must beat."""
    name = "docfirst"

    def index(self, docs: list[Document]) -> None:
        super().index(docs)
        if not hasattr(self, "_doc_bm25"):
            self._doc_bm25: dict[str, tuple[bm25s.BM25, list[str]]] = {}
        subset = docs[0].subset
        if subset not in self._doc_bm25:
            b = self.store.cfg["bm25"]
            model = bm25s.BM25(k1=b["k1"], b=b["b"])
            model.index(tokenize([d.text for d in docs]), show_progress=False)
            self._doc_bm25[subset] = (model, [d.doc_id for d in docs])

    def doc_query(self, query: str) -> str:
        """Text used to pick the document (stage 1): the full query."""
        return query

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        model, ids = self._doc_bm25[pool]
        top, _ = model.retrieve(tokenize([self.doc_query(query)]), k=1, show_progress=False)
        rows, scores = self.store.dense_search_in_docs(pool, self.qvec(query), {ids[top[0][0]]}, k)
        return _hits(self.store, pool, rows, scores)


class DocFirstHeaderRetriever(DocFirstRetriever):
    """Doc-first with query segmentation: only the header ("Consider the NDA between X and Y")
    picks the document, so generic question words cannot outvote the party names. Stage 2 is
    unchanged (dense search with the full query inside the chosen document)."""
    name = "docfirst_hdr"

    def doc_query(self, query: str) -> str:
        return split_query(query)[0]


class LeafBM25Retriever(BM25Retriever):
    """Section-tree baseline: flat BM25 over section leaves instead of 500-char chunks."""
    name = "leaf_bm25"
    store_kind = "leaf"


class LeafDenseRetriever(DenseRetriever):
    """Section-tree baseline: flat dense search over section leaves."""
    name = "leaf_dense"
    store_kind = "leaf"


class LeafHybridRetriever(HybridRetriever):
    """Section-tree baseline: RRF of BM25 and dense over section leaves."""
    name = "leaf_hybrid"
    store_kind = "leaf"


BASELINES = {c.name: c for c in
             [BM25Retriever, DenseRetriever, HybridRetriever, OracleRetriever, DocFirstRetriever,
              DocFirstHeaderRetriever, LeafBM25Retriever, LeafDenseRetriever, LeafHybridRetriever]}

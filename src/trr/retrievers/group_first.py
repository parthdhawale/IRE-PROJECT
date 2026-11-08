"""Group-first retrieval: route the query to its top-B document groups, then search only there.

Look-alike documents of another kind are one cause of DRM (a merger agreement answering an NDA
question). So before any chunk is scored, a router (src/trr/routing/routers.py) ranks the
document groups -- the 3 non-CUAD collections plus the CUAD contract types -- and the inner
search (BM25, dense, hybrid or doc-first) only sees chunks of documents in the top-B groups.
Doc-first inners ending in "_hdr" pick the document with the query header only.

Everything runs on ONE mixed pool of all 714 documents, so a wrong group really can be chosen.
router="none" searches every group: that is the flat mixed-pool baseline through the same code.
router="oracle" uses the gold document's group: the upper bound of perfect routing.

The routers are fit on all documents of the pool and never on queries: like any index, they
are built from the collection; adding a document means adding it to its group's statistics.
"""

from __future__ import annotations

from pathlib import Path

import bm25s
import numpy as np

from trr.data.load import Document
from trr.retrievers.base import Hit
from trr.retrievers.chunk_store import ChunkStore, tokenize
from trr.retrievers.flat import DenseRetriever, _hits, rrf_fuse
from trr.retrievers.query_split import split_query
from trr.routing.evaluate import FUSED, ROUTER_INPUT, make_router
from trr.routing.evaluate import rrf_fuse as rrf_fuse_scores
from trr.routing.groups import assign_groups
from trr.routing.prep import cached_embeddings, doc_full_vectors
from trr.routing.routers import tokenize_words

POOL = "all"


class GroupRouter:
    """Shared, built once: document groups, fitted routers, row index per group, doc-level BM25."""

    def __init__(self, cfg: dict, store: ChunkStore, docs: list[Document], level: str = "fine"):
        """level="fine": 28 groups (3 collections + CUAD contract types); "coarse": the 4 collections."""
        rc = cfg["routing"]
        self.cfg, self.store, self.docs, self.level = cfg, store, docs, level
        self.doc_group = (assign_groups(docs, rc["min_group_docs"]) if level == "fine"
                          else {d.doc_id: d.subset for d in docs})
        self.groups = sorted(set(self.doc_group.values()))
        sc = store.subsets[POOL]
        self.group_rows = {g: np.concatenate([sc.doc_rows[d.doc_id] for d in docs
                                              if self.doc_group[d.doc_id] == g and d.doc_id in sc.doc_rows])
                           for g in self.groups}
        self.group_docs = {g: [i for i, d in enumerate(docs) if self.doc_group[d.doc_id] == g]
                           for g in self.groups}
        labels = [self.doc_group[d.doc_id] for d in docs]
        emb = store.embedder
        key = {"model": emb.model_name, "chars": rc["excerpt_chars"], "n": len(docs)}  # = routing cache key
        doc_vecs = cached_embeddings("docs", [d.text[:rc["excerpt_chars"]] for d in docs], emb.encode, key,
                                     Path(cfg["paths"]["cache"]))
        self.doc_tokens = tokenize_words([d.text for d in docs])  # same preprocessing as BM25
        inputs = {"vec": doc_vecs, "vec_full": doc_full_vectors(cfg, docs), "tok": self.doc_tokens}
        self.routers = {name: make_router(name, rc, cfg["seed"]).fit(inputs[kind], labels)
                        for name, kind in ROUTER_INPUT.items()}
        self._local: dict[tuple[str, ...], tuple[bm25s.BM25, np.ndarray]] = {}
        b = cfg["bm25"]
        self.doc_bm25 = bm25s.BM25(k1=b["k1"], b=b["b"])
        self.doc_bm25.index(tokenize([d.text for d in docs]), show_progress=False)

    def local_doc_index(self, groups: list[str]) -> tuple[bm25s.BM25, np.ndarray]:
        """Whole-document BM25 built over the searched groups only (cached per group set).

        Its idf comes from those groups, not the whole pool: a party name that is rare among
        licence agreements stays rare, even if long merger agreements elsewhere use it often.
        """
        key = tuple(sorted(groups))
        if key not in self._local:
            idx = np.array(sorted(i for g in key for i in self.group_docs[g]))
            b = self.cfg["bm25"]
            model = bm25s.BM25(k1=b["k1"], b=b["b"])
            model.index([self.doc_tokens[i] for i in idx], show_progress=False)
            self._local[key] = (model, idx)
        return self._local[key]

    def _scores(self, name: str, query: str, qvec: np.ndarray) -> tuple[np.ndarray, list[str]]:
        r = self.routers[name]
        s = r.scores(tokenize_words([query])) if ROUTER_INPUT[name] == "tok" else r.scores(qvec[None, :])
        return s[0], list(r.groups)

    def rank_groups(self, name: str, query: str, qvec: np.ndarray) -> list[str]:
        """Groups best first, according to router `name` ("fused" = RRF of centroid and nb_band)."""
        if name == "fused":
            mats = []
            for part in FUSED:
                s, order = self._scores(part, query, qvec)
                mats.append(s[[order.index(g) for g in self.groups]][None, :])  # same column order
            fused = rrf_fuse_scores(mats, self.cfg["routing"]["fuse_rrf_k"])[0]
            return [self.groups[i] for i in np.argsort(-fused, kind="stable")]
        s, order = self._scores(name, query, qvec)
        return [order[i] for i in np.argsort(-s, kind="stable")]


class GroupFirstRetriever(DenseRetriever):
    """Route to the top-`beam_b` groups, then run the `inner` search restricted to them."""

    def __init__(self, store: ChunkStore, router: GroupRouter, router_name: str, beam_b: int, inner: str):
        super().__init__(store)
        self.gr, self.router_name, self.beam_b, self.inner = router, router_name, beam_b, inner
        prefix = "gf" if router.level == "fine" else "gfc"
        self.name = f"mixed_{inner}" if router_name == "none" else f"{prefix}_{router_name}_b{beam_b}_{inner}"
        self.needs_gold = router_name == "oracle"
        self.last_diag: dict = {}

    def index(self, docs: list[Document]) -> None:  # the pool is built once, outside, by the script
        pass

    def set_gold(self, gold_docs: set[str]) -> None:
        self._gold_groups = sorted({self.gr.doc_group[d] for d in gold_docs})

    def chosen_groups(self, query: str) -> list[str]:
        if self.router_name == "none":
            return list(self.gr.groups)
        if self.router_name == "oracle":
            return self._gold_groups
        return self.gr.rank_groups(self.router_name, query, self.qvec(query))[:self.beam_b]

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        groups = self.chosen_groups(query)
        self.last_diag = {"groups": groups}
        rows = np.concatenate([self.gr.group_rows[g] for g in groups])
        qv = self.qvec(query)
        emb = self.store.embeddings(POOL)
        if self.inner == "dense":
            top, scores = _top(emb[rows] @ qv, rows, k)
        elif self.inner == "bm25":
            top, scores = _top(self.store.bm25_scores(POOL, query)[rows], rows, k)
        elif self.inner == "hybrid":
            h = self.store.cfg["hybrid"]
            lex, _ = _top(self.store.bm25_scores(POOL, query)[rows], rows, h["depth"])
            den, _ = _top(emb[rows] @ qv, rows, h["depth"])
            top, scores = rrf_fuse([lex, den], h["rrf_k"])
            top, scores = top[:k], scores[:k]
        elif self.inner.removesuffix("_hdr") in ("docfirst", "docfirst_local"):
            # docfirst: pool-wide doc BM25 restricted to the groups; _local: an index of the groups alone
            # _hdr: only the query header picks the document (query segmentation, query_split.py)
            words = _words(split_query(query)[0] if self.inner.endswith("_hdr") else query)
            if self.inner.removesuffix("_hdr") == "docfirst":
                allowed = np.concatenate([self.gr.group_docs[g] for g in groups])
                doc_scores = np.asarray(self.gr.doc_bm25.get_scores(words))[allowed]
            else:
                model, allowed = self.gr.local_doc_index(groups)
                doc_scores = np.asarray(model.get_scores(words))
            best = self.gr.docs[allowed[int(np.argmax(doc_scores))]].doc_id
            top, scores = self.store.dense_search_in_docs(POOL, qv, {best}, k)
        elif self.inner == "docfirst_local_rrf":
            # rank the groups' documents twice -- by the header (which document) and by the full
            # query (which kind of document) -- and fuse the two rankings with RRF, as in hybrid
            model, allowed = self.gr.local_doc_index(groups)
            ranks = [np.argsort(-np.asarray(model.get_scores(_words(t))), kind="stable")
                     for t in (split_query(query)[0], query)]
            fused, _ = rrf_fuse(ranks, self.store.cfg["hybrid"]["rrf_k"])
            best = self.gr.docs[allowed[fused[0]]].doc_id
            top, scores = self.store.dense_search_in_docs(POOL, qv, {best}, k)
        else:
            raise ValueError(f"unknown inner search {self.inner!r}")
        return _hits(self.store, POOL, top, scores)


def _words(text: str) -> list[str]:
    """BM25 query words: lower-cased, English stopwords removed (as the indexes)."""
    return bm25s.tokenize([text], lower=True, stopwords="en", return_ids=False, show_progress=False)[0]


def _top(scores: np.ndarray, rows: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Best k of `scores` (aligned with `rows`), returned as pool row ids, best first."""
    order = np.argsort(-scores, kind="stable")[:k]
    return rows[order], scores[order]

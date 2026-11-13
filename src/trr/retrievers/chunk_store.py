"""Shared chunk store for the flat baselines.

BM25, dense, hybrid, oracle and doc-first all search the same 500-char chunks, so the chunks,
the BM25 index and the chunk embeddings are built once per subset here and shared.
Embeddings are cached to data/cache/ keyed by (model, chunking config, subset).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import bm25s
import faiss
import numpy as np
from scipy import sparse

from trr.chunking.recursive import split_recursive
from trr.config import config_hash
from trr.data.load import Document


@dataclass
class SubsetChunks:
    doc_ids: list[str]                # one entry per chunk
    starts: np.ndarray
    ends: np.ndarray
    texts: list[str]
    doc_rows: dict[str, np.ndarray]   # doc_id -> chunk row indices
    bm25: bm25s.BM25 | None = None
    emb: np.ndarray | None = None     # (n_chunks, dim) float32, L2-normalised
    faiss_index: faiss.Index | None = None
    embed_texts: list[str] | None = None  # text given to the encoder, if not `texts` (e.g. breadcrumb + leaf)
    bm25_by_row: sparse.csr_matrix | None = None  # BM25 term scores, one row per chunk (bm25_scores_in_rows)


def tokenize(texts: list[str]):
    return bm25s.tokenize(texts, lower=True, stopwords="en", show_progress=False)


class Embedder:
    """sentence-transformers wrapper: normalised float32 vectors, float16 on disk."""

    def __init__(self, cfg: dict, model_name: str | None = None):
        import torch
        from sentence_transformers import SentenceTransformer

        e = cfg["embedding"]
        self.model_name = model_name or e["dev_model"]
        self.batch_size = e["batch_size"]
        self.query_prefix = e["query_prefix"]
        device = e["device"]
        if device == "auto":
            device = ("mps" if torch.backends.mps.is_available()
                      else "cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(self.model_name, device=device)

    def encode(self, texts: list[str], show_progress: bool = False) -> np.ndarray:
        v = self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                              convert_to_numpy=True, show_progress_bar=show_progress)
        return v.astype(np.float32)

    def encode_queries(self, queries: list[str]) -> np.ndarray:
        return self.encode([self.query_prefix + q for q in queries])


@dataclass
class ChunkStore:
    cfg: dict
    subsets: dict[str, SubsetChunks] = field(default_factory=dict)
    docs: dict[str, dict[str, Document]] = field(default_factory=dict)
    _embedder: Embedder | None = None

    def add(self, docs: list[Document]) -> None:
        """Chunk the documents of one subset (idempotent per subset)."""
        subset = docs[0].subset
        if subset in self.subsets:
            return
        size = self.cfg["chunking"]["chunk_chars"]
        doc_ids, starts, ends, texts = [], [], [], []
        for d in docs:
            for s, e in split_recursive(d.text, size):
                doc_ids.append(d.doc_id)
                starts.append(s)
                ends.append(e)
                texts.append(d.text[s:e])
        rows: dict[str, list[int]] = {}
        for i, d in enumerate(doc_ids):
            rows.setdefault(d, []).append(i)
        self.subsets[subset] = SubsetChunks(
            doc_ids, np.array(starts), np.array(ends), texts,
            {d: np.array(r) for d, r in rows.items()})
        self.docs[subset] = {d.doc_id: d for d in docs}

    def merge(self, name: str, parts: list[str], embeddings: bool = True) -> None:
        """One pool `name` made of already-added subsets (e.g. all 714 documents together).

        Rows are concatenated and embeddings reused from each part's cache, so the mixed pool
        holds exactly the same chunks and vectors as the per-subset pools. embeddings=False builds
        a lexical-only pool (BM25 works, dense search does not): for fully lexical methods, which
        must not trigger embedding every chunk.
        """
        if name in self.subsets:
            return
        scs = [self.subsets[p] for p in parts]
        offset, rows = 0, {}
        for sc in scs:
            rows.update({d: r + offset for d, r in sc.doc_rows.items()})
            offset += len(sc.texts)
        if not embeddings:
            self.subsets[name] = SubsetChunks(
                [d for sc in scs for d in sc.doc_ids], np.concatenate([sc.starts for sc in scs]),
                np.concatenate([sc.ends for sc in scs]), [t for sc in scs for t in sc.texts], rows)
            self.docs[name] = {k: v for p in parts for k, v in self.docs[p].items()}
            return
        embs = [self.embeddings(p) for p in parts]
        merged = SubsetChunks(
            [d for sc in scs for d in sc.doc_ids], np.concatenate([sc.starts for sc in scs]),
            np.concatenate([sc.ends for sc in scs]), [t for sc in scs for t in sc.texts], rows,
            emb=np.concatenate(embs))
        merged.faiss_index = faiss.IndexFlatIP(merged.emb.shape[1])
        merged.faiss_index.add(merged.emb)
        self.subsets[name] = merged
        self.docs[name] = {k: v for p in parts for k, v in self.docs[p].items()}

    # ---- lexical ---------------------------------------------------------------------
    def bm25(self, subset: str) -> bm25s.BM25:
        sc = self.subsets[subset]
        if sc.bm25 is None:
            b = self.cfg["bm25"]
            sc.bm25 = bm25s.BM25(k1=b["k1"], b=b["b"])
            sc.bm25.index(tokenize(sc.texts), show_progress=False)
        return sc.bm25

    def bm25_scores(self, subset: str, query: str) -> np.ndarray:
        """BM25 score of every chunk of the pool for one query (0 where no term matches)."""
        words = bm25s.tokenize([query], lower=True, stopwords="en", return_ids=False,
                               show_progress=False)[0]
        return np.asarray(self.bm25(subset).get_scores(words))

    def bm25_scores_in_rows(self, subset: str, query: str, rows: np.ndarray) -> np.ndarray:
        """BM25 scores of the given chunk rows only: the same numbers as bm25_scores(...)[rows].

        bm25s precomputes each (word, chunk) BM25 term score at index time, stored word by word.
        Turned once into one row per chunk, a document's chunks can be scored from their own rows:
        the work grows with the document, not with the pool (a query word like "agreement" has
        postings in most of the pool's chunks, but only in this document's rows here).
        """
        model, sc = self.bm25(subset), self.subsets[subset]
        if sc.bm25_by_row is None:
            s = model.scores
            sc.bm25_by_row = sparse.csc_matrix((s["data"], s["indices"], s["indptr"]),
                                               shape=(s["num_docs"], len(s["indptr"]) - 1)).tocsr()
        words = bm25s.tokenize([query], lower=True, stopwords="en", return_ids=False, show_progress=False)[0]
        ids = model.get_tokens_ids(words)            # repeated query words count twice, as in get_scores
        scores = np.zeros(len(rows), dtype=np.float64)
        if ids:
            scores += np.asarray(sc.bm25_by_row[rows][:, ids].sum(axis=1)).ravel()
            if model.nonoccurrence_array is not None:  # BM25 variants that score absent words (not ours)
                scores += model.nonoccurrence_array[ids].sum()
        return scores

    def bm25_search(self, subset: str, query: str, depth: int) -> tuple[np.ndarray, np.ndarray]:
        """(row indices, scores) of the top `depth` chunks by BM25."""
        model = self.bm25(subset)
        n = len(self.subsets[subset].texts)
        rows, scores = model.retrieve(tokenize([query]), k=min(depth, n), show_progress=False)
        return rows[0], scores[0]

    # ---- dense -----------------------------------------------------------------------
    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = Embedder(self.cfg)
        return self._embedder

    def _emb_cache_path(self, subset: str) -> Path:
        key = config_hash({"model": self.embedder.model_name, "chunking": self.cfg["chunking"],
                           "n": len(self.subsets[subset].texts)})
        name = self.embedder.model_name.split("/")[-1]
        return Path(self.cfg["paths"]["cache"]) / f"chunk_emb_{subset}_{name}_{key}.npy"

    def embeddings(self, subset: str) -> np.ndarray:
        sc = self.subsets[subset]
        if sc.emb is None:
            path = self._emb_cache_path(subset)
            if path.exists():
                sc.emb = np.load(path).astype(np.float32)
            else:
                print(f"embedding {len(sc.texts)} units of {subset} ...", flush=True)
                sc.emb = self.embedder.encode(sc.embed_texts or sc.texts, show_progress=True)
                path.parent.mkdir(parents=True, exist_ok=True)
                np.save(path, sc.emb.astype(np.float16))
                sc.emb = sc.emb.astype(np.float16).astype(np.float32)  # same values as a reload
            sc.faiss_index = faiss.IndexFlatIP(sc.emb.shape[1])
            sc.faiss_index.add(sc.emb)
        return sc.emb

    def dense_search(self, subset: str, qvec: np.ndarray, depth: int) -> tuple[np.ndarray, np.ndarray]:
        """(row indices, cosine scores) of the top `depth` chunks; qvec is one normalised vector."""
        self.embeddings(subset)
        index = self.subsets[subset].faiss_index
        scores, rows = index.search(qvec.reshape(1, -1), min(depth, index.ntotal))
        return rows[0], scores[0]

    def dense_search_in_docs(self, subset: str, qvec: np.ndarray, doc_ids: set[str],
                             depth: int) -> tuple[np.ndarray, np.ndarray]:
        """Exact cosine search restricted to the chunks of the given documents."""
        emb = self.embeddings(subset)
        sc = self.subsets[subset]
        rows = np.concatenate([sc.doc_rows[d] for d in doc_ids if d in sc.doc_rows])
        scores = emb[rows] @ qvec
        order = np.argsort(-scores, kind="stable")[:depth]
        return rows[order], scores[order]

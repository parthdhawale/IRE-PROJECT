from __future__ import annotations

from types import SimpleNamespace

import faiss
import numpy as np

from trr.config import load_config
from trr.data.load import Document
from trr.retrievers.chunk_store import ChunkStore
from trr.retrievers.group_first import POOL, GroupFirstRetriever, _top

TEXT = {"a.txt": "return or destroy all information", "b.txt": "return the information on request",
        "c.txt": "merger consideration paid in cash", "d.txt": "closing conditions of the merger"}
GROUP = {"a.txt": "nda", "b.txt": "nda", "c.txt": "maud", "d.txt": "maud"}


def _setup(order: list[str]):
    """Pool of 4 one-chunk documents in 2 groups, hand-made unit vectors, a stub router."""
    cfg = load_config()
    store = ChunkStore(cfg)
    docs = [Document(d, POOL, t) for d, t in TEXT.items()]
    store.add(docs)
    sc = store.subsets[POOL]
    sc.emb = np.eye(4, dtype=np.float32)  # chunk i points along axis i
    sc.faiss_index = faiss.IndexFlatIP(4)
    sc.faiss_index.add(sc.emb)
    rows = {g: np.array([i for i, d in enumerate(sc.doc_ids) if GROUP[d] == g]) for g in ("nda", "maud")}
    router = SimpleNamespace(groups=["maud", "nda"], doc_group=GROUP, group_rows=rows, level="fine",
                             rank_groups=lambda name, q, v: order)
    return store, router


def _retriever(store, router, name, b, inner, qvec):
    r = GroupFirstRetriever(store, router, name, b, inner)
    r._qvecs["q"] = np.asarray(qvec, dtype=np.float32)
    return r


def test_top_returns_pool_rows_best_first() -> None:
    rows, scores = _top(np.array([0.1, 0.9, 0.5]), np.array([10, 11, 12]), 2)
    assert rows.tolist() == [11, 12] and scores.tolist() == [0.9, 0.5]


def test_beam_restricts_hits_to_chosen_groups() -> None:
    store, router = _setup(order=["nda", "maud"])
    # the query vector prefers a maud chunk, but the router sends it to nda only
    r = _retriever(store, router, "centroid", 1, "dense", [0.2, 0.1, 0.9, 0.0])
    hits = r.retrieve("q", 4, POOL)
    assert {GROUP[h.doc_id] for h in hits} == {"nda"} and hits[0].doc_id == "a.txt"
    assert r.last_diag["groups"] == ["nda"]


def test_no_routing_equals_flat_dense() -> None:
    store, router = _setup(order=["nda", "maud"])
    q = [0.2, 0.1, 0.9, 0.0]
    r = _retriever(store, router, "none", 1, "dense", q)
    hits = r.retrieve("q", 4, POOL)
    rows, _ = store.dense_search(POOL, np.asarray(q, dtype=np.float32), 4)
    assert [h.doc_id for h in hits] == [store.subsets[POOL].doc_ids[i] for i in rows]


def test_oracle_uses_gold_group() -> None:
    store, router = _setup(order=["nda", "maud"])
    r = _retriever(store, router, "oracle", 1, "dense", [0.9, 0.0, 0.0, 0.0])
    r.set_gold({"d.txt"})
    assert {GROUP[h.doc_id] for h in r.retrieve("q", 4, POOL)} == {"maud"}


def test_local_index_uses_only_the_searched_groups() -> None:
    from trr.retrievers.group_first import GroupRouter
    gr = object.__new__(GroupRouter)  # only the pieces local_doc_index needs
    gr.cfg = load_config()
    gr.group_docs = {"nda": [0, 1], "maud": [2, 3]}
    gr.doc_tokens = [["acme", "nda"], ["beta", "nda"], ["acme", "merger"], ["acme", "cash"]]
    gr._local = {}
    model, idx = gr.local_doc_index(["nda"])
    assert idx.tolist() == [0, 1] and len(model.get_scores(["acme"])) == 2
    # "acme" is in 3 of 4 pool documents but 1 of 2 nda documents: idf is computed per group set
    assert np.argmax(model.get_scores(["acme"])) == 0
    assert gr.local_doc_index(["maud", "nda"])[1].tolist() == [0, 1, 2, 3]

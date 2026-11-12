from __future__ import annotations

import pandas as pd

from trr.config import load_config
from trr.data.load import Document
from trr.retrievers.leaf_store import LeafStore

DOC_A = "1. Term. Three years.\n2. Return. Recipient shall return or destroy all information.\n"
DOC_B = "1. Law. New York law governs.\n2. Notices. Notices go to the address above.\n"


def _sections() -> pd.DataFrame:
    rows = []
    for doc_id, text in [("t/a.txt", DOC_A), ("t/b.txt", DOC_B)]:
        cut = text.index("2.")
        rows += [
            {"doc_id": doc_id, "subset": "t", "start": 0, "end": cut, "is_leaf": True, "breadcrumb": "1."},
            {"doc_id": doc_id, "subset": "t", "start": cut, "end": len(text), "is_leaf": True, "breadcrumb": "2."},
            {"doc_id": doc_id, "subset": "t", "start": 0, "end": len(text), "is_leaf": False, "breadcrumb": ""},
        ]
    return pd.DataFrame(rows)


def _store() -> tuple[LeafStore, list[Document]]:
    docs = [Document("t/a.txt", "t", DOC_A), Document("t/b.txt", "t", DOC_B)]
    store = LeafStore(load_config(), sections=_sections())
    store.add(docs)
    return store, docs


def test_leaves_keep_original_offsets() -> None:
    store, docs = _store()
    sc = store.subsets["t"]
    text = {d.doc_id: d.text for d in docs}
    assert len(sc.texts) == 4  # internal node dropped, 2 leaves per document
    for d, s, e, t in zip(sc.doc_ids, sc.starts, sc.ends, sc.texts):
        assert text[d][s:e] == t


def test_breadcrumb_is_for_embedding_only() -> None:
    store, _ = _store()
    sc = store.subsets["t"]
    assert all(et.endswith(t) and et != t for et, t in zip(sc.embed_texts, sc.texts))
    assert not any(t.startswith("1.\n") for t in sc.texts)


def test_bm25_hit_points_at_the_right_leaf() -> None:
    store, _ = _store()
    rows, _ = store.bm25_search("t", "return or destroy information", 1)
    sc = store.subsets["t"]
    r = rows[0]
    assert sc.doc_ids[r] == "t/a.txt" and DOC_A[sc.starts[r]:sc.ends[r]].startswith("2. Return")

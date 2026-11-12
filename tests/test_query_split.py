from __future__ import annotations

import numpy as np

from trr.config import load_config
from trr.data.load import Document
from trr.retrievers.chunk_store import ChunkStore
from trr.retrievers.flat import DocFirstHeaderRetriever, DocFirstRetriever
from trr.retrievers.query_split import split_query

QUERY = ("Consider the Non-Disclosure Agreement between Acme and Beta; may the receiving party "
         "share confidential information with employees?")
TEXT = {"acme.txt": "Agreement between Acme and Beta. The receiving party shall return confidential "
                    "information on request.",
        "zeta.txt": "Agreement between Zeta and Omega. The receiving party shall return confidential "
                    "information; the receiving party may share confidential information with employees "
                    "and advisers who need to know the confidential information."}


def test_split_query_header_and_question() -> None:
    header, question = split_query(QUERY)
    assert header == "Consider the Non-Disclosure Agreement between Acme and Beta"
    assert question.startswith("may the receiving party")


def test_split_query_without_semicolon_keeps_the_whole_text() -> None:
    assert split_query("governing law clause") == ("governing law clause", "governing law clause")


def _picked(cls) -> str:
    """Document chosen by a doc-first retriever on a 2-document pool (one chunk each)."""
    store = ChunkStore(load_config())
    docs = [Document(d, "nli", t) for d, t in TEXT.items()]
    store.add(docs)
    store.subsets["nli"].emb = np.eye(2, dtype=np.float32)
    r = cls(store)
    r.index(docs)
    r._qvecs[QUERY] = np.array([1.0, 0.0], dtype=np.float32)
    return r.retrieve(QUERY, 1, "nli")[0].doc_id


def test_header_picks_the_named_document_when_question_words_point_elsewhere() -> None:
    # the question words (share, employees, confidential ...) match the Zeta NDA better,
    # but only Acme carries the names in the header
    assert _picked(DocFirstRetriever) == "zeta.txt"
    assert _picked(DocFirstHeaderRetriever) == "acme.txt"


def test_group_first_local_header_inner_uses_the_header() -> None:
    from trr.retrievers.group_first import POOL, GroupFirstRetriever, GroupRouter
    from trr.routing.routers import tokenize_words
    cfg = load_config()
    store = ChunkStore(cfg)
    docs = [Document(d, POOL, t) for d, t in TEXT.items()]
    store.add(docs)
    store.subsets[POOL].emb = np.eye(2, dtype=np.float32)
    gr = object.__new__(GroupRouter)  # only the pieces the doc-first inner needs
    gr.cfg, gr.docs, gr.level, gr._local = cfg, docs, "coarse", {}
    gr.groups, gr.doc_group = ["nli"], {d.doc_id: "nli" for d in docs}
    gr.group_docs, gr.group_rows = {"nli": [0, 1]}, {"nli": np.array([0, 1])}
    gr.doc_tokens = tokenize_words([d.text for d in docs])
    picked = {}
    for inner in ("docfirst_local", "docfirst_local_hdr"):
        r = GroupFirstRetriever(store, gr, "none", 1, inner)
        r._qvecs[QUERY] = np.array([1.0, 0.0], dtype=np.float32)
        picked[inner] = r.retrieve(QUERY, 1, POOL)[0].doc_id
    assert picked == {"docfirst_local": "zeta.txt", "docfirst_local_hdr": "acme.txt"}

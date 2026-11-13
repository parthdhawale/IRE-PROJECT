import bm25s
import numpy as np
import pytest

from trr.data.load import Document
from trr.retrievers.band_pipeline import POOL, BandIndex, BandPipelineRetriever
from trr.retrievers.chunk_store import ChunkStore
from trr.routing.routers import tokenize_words

CFG = {"seed": 0, "chunking": {"chunk_chars": 80, "overlap": 0}, "bm25": {"k1": 1.5, "b": 0.75},
       "band_clusters": {"kmeans_n_init": 5, "kmeans_max_iter": 50}}

NDA = ("This Non-Disclosure Agreement protects confidential information. The recipient shall not disclose "
       "confidential information to employees without consent. {party} is the disclosing party. "
       "The recipient returns the information on request.")
MERGER = ("Agreement and Plan of Merger with Acme. Shares convert at the closing. The target board "
          "approves the merger. Acme pays the merger consideration at the closing. {n}")

# "Acme" is in one NDA but in every merger agreement: common in the pool, rare among NDAs.
DOCS = ([Document(f"contractnli/{p}.txt", "contractnli", NDA.format(party=p)) for p in ("Acme", "Bosch", "Cyber")]
        + [Document(f"maud/m{n}.txt", "maud", MERGER.format(n=f"Number {n}.")) for n in (1, 2, 3)])
QUERY = ("Consider the Non-Disclosure Agreement between Acme and Beta; may the recipient disclose "
         "confidential information to employees?")


@pytest.fixture(scope="module")
def setup():
    store = ChunkStore(CFG)
    for subset in ("contractnli", "maud"):
        store.add([d for d in DOCS if d.subset == subset])
    store.merge(POOL, ["contractnli", "maud"], embeddings=False)   # lexical pool, no embeddings
    return store, BandIndex(CFG, DOCS, min_df=2, max_frac=0.6, k=2)


def _ret(setup, router="band", rare_below=2):
    store, ix = setup
    return BandPipelineRetriever(store, ix, router, b=1, rare_below=rare_below)


def test_clusters_split_ndas_from_mergers(setup):
    ix = setup[1]
    nda, mer = {ix.doc_cluster[d.doc_id] for d in DOCS[:3]}, {ix.doc_cluster[d.doc_id] for d in DOCS[3:]}
    assert len(nda) == 1 and len(mer) == 1 and nda != mer


def test_rare_in_cluster_word_picks_the_document(setup):
    ret = _ret(setup)
    hits = ret.retrieve(QUERY, k=3, pool=POOL)
    assert ret.last_diag["doc"] == "contractnli/Acme.txt" and not ret.last_diag["fallback"]
    assert {h.doc_id for h in hits} == {"contractnli/Acme.txt"}


def test_rarity_is_counted_inside_the_searched_clusters(setup):
    words = tokenize_words([QUERY])[0]
    nda_cluster = setup[1].doc_cluster["contractnli/Acme.txt"]
    _, rare_in_ndas = _ret(setup).choose_document(words, [nda_cluster])
    _, rare_in_pool = _ret(setup, router="none").choose_document(words, [0, 1])
    assert rare_in_ndas == ["acme"]      # 1 of 3 NDAs
    assert rare_in_pool == []            # 4 of 6 documents pool-wide: not rare


def test_query_without_rare_words_falls_back_to_the_full_query(setup):
    ret = _ret(setup)
    ret.retrieve("may the recipient disclose confidential information to employees?", k=3, pool=POOL)
    assert ret.last_diag["fallback"] and ret.last_diag["doc"].startswith("contractnli/")


def test_hits_are_original_offsets_of_the_chosen_document(setup):
    store, _ = setup
    hits = _ret(setup).retrieve(QUERY, k=10, pool=POOL)
    text = {d.doc_id: d.text for d in DOCS}["contractnli/Acme.txt"]
    chunks = {(int(s), int(e)) for d, s, e in zip(store.subsets[POOL].doc_ids, store.subsets[POOL].starts,
                                                   store.subsets[POOL].ends) if d == "contractnli/Acme.txt"}
    assert hits and all((h.start, h.end) in chunks and 0 <= h.start < h.end <= len(text) for h in hits)
    assert len(hits) == len(chunks)      # k=10 > chunks of the document: every chunk, once


def test_local_bm25_equals_a_bm25s_index_of_the_same_documents(setup):
    ix = setup[1]
    words = ["acme", "merger", "confidential", "closing", "nobody"]
    for clusters in ([0], [1], [0, 1]):
        mask = ix.local(clusters)
        idx = np.flatnonzero(mask)
        ref = bm25s.BM25(k1=CFG["bm25"]["k1"], b=CFG["bm25"]["b"])
        ref.index([ix.doc_tokens[i] for i in idx], show_progress=False)
        assert ix.bm25(words, mask)[idx] == pytest.approx(np.asarray(ref.get_scores(words)), rel=1e-5)
        assert not ix.bm25(words, mask)[~mask].any()                  # 0 outside the clusters


def test_documents_are_ranked_and_the_top_one_is_the_choice(setup):
    ret = _ret(setup)
    ranked, rare = ret.rank_documents(tokenize_words([QUERY])[0], [setup[1].doc_cluster["contractnli/Acme.txt"]], 3)
    assert ranked[0] == "contractnli/Acme.txt" and len(ranked) == 3 and rare == ["acme"]
    ret.retrieve(QUERY, k=3, pool=POOL)
    assert ret.last_diag["docs"][0] == ret.last_diag["doc"]


def test_scoring_one_documents_rows_equals_scoring_the_pool(setup):
    store, _ = setup
    for doc in ("contractnli/Acme.txt", "maud/m2.txt"):
        rows = store.subsets[POOL].doc_rows[doc]
        for q in (QUERY, "merger closing closing shares", "zzz unknown words"):
            assert store.bm25_scores_in_rows(POOL, q, rows) == pytest.approx(store.bm25_scores(POOL, q)[rows],
                                                                             rel=1e-6, abs=1e-9)


def test_query_without_any_indexable_word_still_gets_an_answer(setup):
    ret = _ret(setup)
    hits = ret.retrieve("the of and", k=3, pool=POOL)    # stopwords only
    assert ret.last_diag["fallback"] and hits


def test_oracle_routes_to_the_gold_documents_cluster(setup):
    ret = _ret(setup, router="oracle")
    ret.set_gold({"maud/m2.txt"})
    assert ret.chosen_clusters([]) == [setup[1].doc_cluster["maud/m2.txt"]]


def test_unknown_router_and_dense_passages_are_refused(setup):
    store, ix = setup
    with pytest.raises(ValueError):
        BandPipelineRetriever(store, ix, "magic", b=1, rare_below=2)
    with pytest.raises(NotImplementedError):
        BandPipelineRetriever(store, ix, "band", b=1, rare_below=2, passage="dense")

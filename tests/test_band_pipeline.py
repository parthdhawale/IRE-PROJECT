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

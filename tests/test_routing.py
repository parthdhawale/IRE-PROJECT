"""Routing: discriminative vocabulary, leak-safe folds, both routers, gold-rank scoring."""

from __future__ import annotations

import numpy as np

from trr.data.load import Document
from trr.routing.evaluate import build_levels, rrf_fuse
from trr.routing.groups import assign_groups, leak_safe_folds, near_duplicate_components
from trr.routing.routers import (
    CentroidRouter,
    NBRouter,
    VocabLRRouter,
    all_words_selector,
    band_selector,
    band_vocab,
    discriminative_selector,
    discriminative_vocab,
    gold_rank,
)

UNIVERSAL = ["agreement", "party", "shall"]


def toy_tokens() -> tuple[list[list[str]], list[str]]:
    nda = [UNIVERSAL + ["confidential", "recipient", f"nda{i}"] for i in range(6)]
    merger = [UNIVERSAL + ["merger", "shareholders", f"mrg{i}"] for i in range(6)]
    return nda + merger, ["nda"] * 6 + ["merger"] * 6


def test_vocab_keeps_group_words_and_drops_universal_and_singletons() -> None:
    tokens, labels = toy_tokens()
    vocab = discriminative_vocab(tokens, labels, per_group=2, alpha=1.0)
    assert set(vocab) == {"confidential", "recipient", "merger", "shareholders"}


def test_band_vocab_drops_universal_and_rare_words() -> None:
    tokens, _ = toy_tokens()   # 12 docs: universal words df=12, group words df=6, id words df=1
    assert band_vocab(tokens, low=0.1, high=0.75) == ["confidential", "merger", "recipient", "shareholders"]
    assert "agreement" in band_vocab(tokens, low=0.1, high=1.0)   # high=1.0 keeps universal words
    assert "nda0" in band_vocab(tokens, low=0.0, high=0.75)       # low=0 keeps singletons


def test_both_vocab_routers_route_short_query() -> None:
    tokens, labels = toy_tokens()
    queries = [["confidential", "information"], ["merger", "consideration"]]
    for select in [discriminative_selector(5, 1.0), band_selector(0.1, 0.75)]:
        router = VocabLRRouter(select, c=1.0, max_iter=1000, seed=0).fit(tokens, labels)
        scores = router.scores(queries)
        assert [router.groups[i] for i in scores.argmax(axis=1)] == ["nda", "merger"]


def test_naive_bayes_files_unseen_document_by_word_distribution() -> None:
    tokens, labels = toy_tokens()
    # unseen documents: the group words repeat, a new id word is outside the vocabulary
    held_out = [UNIVERSAL + ["confidential", "confidential", "recipient", "nda99"],
                UNIVERSAL + ["merger", "shareholders", "shareholders", "mrg99"]]
    for select in [band_selector(0.1, 0.75), all_words_selector()]:
        router = NBRouter(select, alpha=1.0).fit(tokens, labels)
        scores = router.scores(held_out)
        assert [router.groups[i] for i in scores.argmax(axis=1)] == ["nda", "merger"]
    band = NBRouter(band_selector(0.1, 0.75), alpha=1.0).fit(tokens, labels)
    assert "agreement" not in band.vocab and "nda0" not in band.vocab


def test_rrf_fuse_combines_rankings_and_breaks_ties_by_first() -> None:
    a = np.array([[0.9, 0.5, 0.1]])   # ranks 1, 2, 3
    b = np.array([[-5.0, -1.0, -9.0]])  # ranks 2, 1, 3
    fused = rrf_fuse([a, b], k=60)      # groups 0 and 1 tie on rrf -> first ranker prefers 0
    assert list((-fused[0]).argsort()) == [0, 1, 2]
    c = np.array([[-9.0, -1.0, -5.0]])  # ranks 3, 1, 2: group 1 has the best sum
    assert (-rrf_fuse([a, c], k=60)[0]).argsort()[0] == 1


def test_levels_split_coarse_and_fine() -> None:
    subset = np.array(["cuad", "cuad", "maud"])
    group = np.array(["cuad/License", "cuad/Supply", "maud"])
    flat, coarse, fine = build_levels(subset, group, item_doc=np.array([0, 2]))
    assert list(coarse.item_gold) == ["cuad", "maud"] and list(flat.item_gold) == ["cuad/License", "maud"]
    assert list(fine.doc_labels) == ["cuad/License", "cuad/Supply", ""]   # fine trains on CUAD only
    assert list(fine.item_gold) == ["cuad/License", ""]                  # and scores CUAD items only


def test_centroid_router_and_gold_rank() -> None:
    vecs = np.array([[1, 0], [0.9, 0.1], [0, 1], [0.1, 0.9]], dtype=float)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    router = CentroidRouter().fit(vecs, ["a", "a", "b", "b"])
    q = np.array([[1.0, 0.0], [0.0, 1.0]])
    ranks = gold_rank(router.scores(q), router.groups, ["a", "a"])
    assert list(ranks) == [1, 2]
    assert gold_rank(router.scores(q), router.groups, ["unseen", "a"])[0] == 3  # unseen group = miss


def test_small_groups_merge_into_other() -> None:
    docs = [Document(f"cuad/X{i}-EX-1-LICENSE AGREEMENT.txt", "cuad", "") for i in range(5)]
    docs += [Document("cuad/Y-EX-1-SUPPLY AGREEMENT.txt", "cuad", ""), Document("nda/a.txt", "contractnli", "")]
    groups = assign_groups(docs, min_group_docs=5)
    assert groups["cuad/X0-EX-1-LICENSE AGREEMENT.txt"] == "cuad/License"
    assert groups["cuad/Y-EX-1-SUPPLY AGREEMENT.txt"] == "cuad/Other"
    assert groups["nda/a.txt"] == "contractnli/Other"


def test_folds_have_no_overlap_and_keep_near_duplicates_together() -> None:
    rng = np.random.default_rng(0)
    ids = [f"d{i}" for i in range(20)]
    sigs = rng.integers(0, 2**60, size=(20, 64), dtype=np.uint64)
    sigs[1] = sigs[0]          # d0 and d1 are copies
    sigs[3, :60] = sigs[2, :60]  # d2 and d3 near-identical (Jaccard ~0.94)
    comps = near_duplicate_components(ids, sigs, dup_tau=0.8)
    assert comps["d0"] == comps["d1"] and comps["d2"] == comps["d3"] and comps["d0"] != comps["d4"]
    groups = {d: "a" if i % 2 else "b" for i, d in enumerate(ids)}
    folds = leak_safe_folds(ids, groups, comps, n_folds=4, seed=0)
    assert set(folds) == set(ids)                       # every doc held out exactly once
    assert folds["d0"] == folds["d1"] and folds["d2"] == folds["d3"]
    for f in range(4):                                  # every group still trains in every fold
        assert {groups[d] for d in ids if folds[d] != f} == {"a", "b"}

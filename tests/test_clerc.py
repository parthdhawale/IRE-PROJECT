import json

import numpy as np
import pandas as pd
import pytest

from trr.data import clerc


def _line(qid, pos, negs):
    p = lambda i: {"docid": str(i), "title": "", "text": "passage"}  # noqa: E731
    return json.dumps({"query_id": qid, "query": f"query {qid}", "positive_passages": [p(pos)],
                       "negative_passages": [p(n) for n in negs]})


# passages 0-2 -> case 100, 3-4 -> case 200, 5 -> 300, 6 -> 400, 7 -> 500
PID2DID = {0: 100, 1: 100, 2: 100, 3: 200, 4: 200, 5: 300, 6: 400, 7: 500}


def test_passages_are_mapped_to_cases_without_duplicates_or_the_gold_case():
    q = clerc.parse_query_line(_line("q1", 0, [1, 3, 4, 5]))
    assert q == {"qid": "q1", "text": "query q1", "pos": [0], "negs": [1, 3, 4, 5]}
    pool, used = clerc.assemble_pool([q], PID2DID, np.array([0]), pool_docs=10)
    assert used[0]["gold"] == 100 and used[0]["neg_cases"] == [200, 300]   # passage 1 is the gold case
    assert pool == [100, 200, 300]


def test_pool_stops_at_the_target_and_follows_the_order():
    qs = [clerc.parse_query_line(_line(f"q{i}", pos, negs))
          for i, (pos, negs) in enumerate([(0, [3]), (5, [6]), (7, [0])])]
    pool, used = clerc.assemble_pool(qs, PID2DID, np.array([1, 2, 0]), pool_docs=3)
    assert [u["qid"] for u in used] == ["q1", "q2"] and pool == [300, 400, 500, 100]
    bigger, _ = clerc.assemble_pool(qs, PID2DID, np.array([1, 2, 0]), pool_docs=10)
    assert bigger[:len(pool)] == pool                                          # nested


def test_query_with_unmapped_positive_is_skipped():
    q = clerc.parse_query_line(_line("q", 99, [3]))
    assert clerc.assemble_pool([q], PID2DID, np.array([0]), 10) == ([], [])


def test_pid2did_keeps_only_needed_passages():
    assert clerc.parse_pid2did(["0\t100", "1\t100", "7\t500"], {0, 7}) == {0: 100, 7: 500}


def test_source_case_detection_needs_verbatim_windows():
    query = " ".join(f"w{i}" for i in range(60))
    source = "Opinion text. " + query.replace(" w30 ", "   w30\t") + " More text."   # spacing differs
    other = " ".join(f"w{i}" for i in range(0, 60, 2))
    assert clerc.is_source(query, source, words=12, n=3, min_found=2)
    assert not clerc.is_source(query, other, words=12, n=3, min_found=2)
    assert clerc.probe_windows("a b c", 12, 3) == ["a b c"]


def test_split_keeps_each_gold_case_on_one_side_and_is_seeded():
    side = clerc.split_by_gold([5, 1, 5, 2, 3, 4, 6, 7, 8, 9, 10], dev_share=0.2, seed=0)
    assert sum(v == "dev" for v in side.values()) == 2 and set(side) == set(range(1, 11))
    assert side == clerc.split_by_gold([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.2, 0)


def test_loader_builds_whole_document_gold(tmp_path, monkeypatch):
    root = tmp_path / "pool_2"
    root.mkdir()
    pd.DataFrame({"case_id": [100, 200], "text": ["first case text", "second"]}).to_parquet(root / "docs.parquet")
    pd.DataFrame({"qid": ["q1"], "text": ["query"], "gold_case": [200], "side": ["dev"]}).to_parquet(
        root / "queries.parquet")
    monkeypatch.setattr(clerc, "REPO_ROOT", tmp_path)
    docs, queries, side = clerc.load_clerc({"clerc": {"root": ".", "pool_docs": 2}})
    assert [d.doc_id for d in docs] == ["clerc/100", "clerc/200"] and side == {"q1": "dev"}
    g = queries[0].gold[0]
    assert (g.doc_id, g.start, g.end) == ("clerc/200", 0, len("second"))


def test_loader_says_how_to_build_a_missing_pool(tmp_path, monkeypatch):
    monkeypatch.setattr(clerc, "REPO_ROOT", tmp_path)
    with pytest.raises(FileNotFoundError, match="build_clerc_pool"):
        clerc.load_clerc({"clerc": {"root": ".", "pool_docs": 5}})

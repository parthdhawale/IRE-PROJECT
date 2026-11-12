import pytest

from trr.data.load import GoldSpan, Query
from trr.eval.splits import DEV, TEST, split_queries


def _q(qid: str, *docs: str) -> Query:
    return Query(qid=qid, subset="s", text="?", gold=[GoldSpan(d, 0, 1) for d in docs])


def test_queries_follow_their_gold_document():
    folds = {"a": 0, "b": 1, "c": 3}
    side = split_queries([_q("1", "a"), _q("2", "a"), _q("3", "b"), _q("4", "c")], folds, dev_folds=[0])
    assert side == {"1": DEV, "2": DEV, "3": TEST, "4": TEST}   # both questions on "a" stay together


def test_several_dev_folds_and_several_gold_spans_in_one_document():
    folds = {"a": 0, "b": 1, "c": 2}
    side = split_queries([_q("1", "a", "a"), _q("2", "b"), _q("3", "c")], folds, dev_folds=[0, 1])
    assert side == {"1": DEV, "2": DEV, "3": TEST}


def test_query_spanning_both_sides_is_refused():
    with pytest.raises(ValueError):
        split_queries([_q("1", "a", "b")], {"a": 0, "b": 1}, dev_folds=[0])

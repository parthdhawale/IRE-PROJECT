"""Loader, mini selection and span round-trip tests.

The real-data tests skip if data/raw is missing, so the toy tests still run on a fresh clone.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from trr.config import load_config
from trr.data.cuad_types import cuad_type, exhibit_title
from trr.data.load import SUBSETS, load_corpus, load_queries
from trr.data.sanity import check_subset

CFG = load_config()
RAW = Path(CFG["paths"]["raw"])
needs_data = pytest.mark.skipif(not (RAW / "benchmarks").is_dir(), reason="run `make data` first")


@pytest.fixture
def toy_raw(tmp_path: Path) -> Path:
    """A two-document toy dataset with CRLF line endings in one file."""
    (tmp_path / "corpus" / "toy").mkdir(parents=True)
    (tmp_path / "benchmarks").mkdir()
    (tmp_path / "corpus" / "toy" / "a.txt").write_bytes(b"Line one.\r\nThe term is 30 days.\r\n")
    (tmp_path / "corpus" / "toy" / "b.txt").write_text("Party B shall not disclose.", encoding="utf-8")
    tests = [
        # offsets are in universal-newline text: "Line one.\nThe term is 30 days.\n"
        {"query": "term?", "snippets": [{"file_path": "toy/a.txt", "span": [10, 30],
                                         "answer": "The term is 30 days."}]},
        {"query": "disclose?", "snippets": [
            {"file_path": "toy/b.txt", "span": [8, 17], "answer": "shall not"},
            {"file_path": "toy/a.txt", "span": [0, 9], "answer": "Line one."}]},
    ]
    (tmp_path / "benchmarks" / "toy.json").write_text(json.dumps({"tests": tests}))
    return tmp_path


def test_toy_round_trip_with_crlf(toy_raw: Path) -> None:
    docs = load_corpus(toy_raw, "toy")
    queries = load_queries(toy_raw, "toy", "full")
    assert [d.doc_id for d in docs] == ["toy/a.txt", "toy/b.txt"]
    assert "\r" not in docs[0].text
    stats = check_subset(docs, queries)
    assert stats["ok"] and stats["round_trip"] == 1.0
    assert stats["multi_doc_queries"] == 1
    assert queries[1].gold_docs == {"toy/a.txt", "toy/b.txt"}


def test_toy_detects_bad_span(toy_raw: Path) -> None:
    docs = load_corpus(toy_raw, "toy")
    bench = toy_raw / "benchmarks" / "toy.json"
    data = json.loads(bench.read_text())
    data["tests"][0]["snippets"][0]["span"] = [11, 31]  # shifted by one
    data["tests"][1]["snippets"][0]["span"] = [8, 999]  # out of bounds
    bench.write_text(json.dumps(data))
    stats = check_subset(docs, load_queries(toy_raw, "toy", "full"))
    assert not stats["ok"]
    assert stats["mismatch"] == 1 and stats["out_of_bounds"] == 1


def test_bad_split_name(toy_raw: Path) -> None:
    with pytest.raises(ValueError):
        load_queries(toy_raw, "toy", "small")


def test_cuad_type_parsing() -> None:
    assert cuad_type("cuad/X_20140520_10-Q_EX-10.27_8605784_EX-10.27_Affiliate Agreement.txt") == "Affiliate"
    assert cuad_type("cuad/KIROMICBIOPHARMA,INC_04_08_2020-EX-10.28-JOINT VENTURE AGREEMENT.txt") == "Joint Venture"
    # company name contains "SERVICE" but the exhibit title decides
    assert cuad_type("cuad/MANAKOASERVICESCORP_11_21_2007-EX-7.5-STRATEGIC ALLIANCE AGREEMENT.txt") == "Strategic Alliance"
    assert exhibit_title("cuad/A-EX-10.(D)-PROMOTION AGREEMENT.txt") == "PROMOTION AGREEMENT"
    assert cuad_type("cuad/Foo-EX-1.1-WIDGET AGREEMENT.txt") == "Other"


@needs_data
@pytest.mark.parametrize("subset", SUBSETS)
def test_real_spans_round_trip(subset: str) -> None:
    docs = load_corpus(RAW, subset)
    stats = check_subset(docs, load_queries(RAW, subset, "full"))
    assert stats["ok"], stats
    assert stats["round_trip"] == 1.0


@needs_data
@pytest.mark.parametrize("subset", SUBSETS)
def test_real_mini_selection(subset: str) -> None:
    n = CFG["data"]["mini_per_subset"]
    full = load_queries(RAW, subset, "full", n)
    mini = load_queries(RAW, subset, "mini", n)
    assert len(mini) == min(n, len(full))
    assert len({q.qid for q in mini}) == len(mini)
    assert {q.qid for q in mini} <= {q.qid for q in full}
    # deterministic across calls
    assert [q.qid for q in mini] == [q.qid for q in load_queries(RAW, subset, "mini", n)]

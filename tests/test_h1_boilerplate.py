"""H1 boilerplate analysis: near-duplicate detection, boilerplate share, go/no-go."""

from __future__ import annotations

import pandas as pd

from trr.analysis.h1_boilerplate import (
    boilerplate_share,
    go_no_go,
    leaf_frame,
    near_duplicate_edges,
    top_shared_leaves,
)
from trr.sketch.minhash import minhash_of, shingles, signature_bytes

NUM_PERM, SEED = 32, 0
SHARED_CLAUSE = "The Receiving Party shall keep all Confidential Information strictly secret forever and always"
UNIQUE_A = "Bosch Automotive agrees to a term of exactly ninety days for this specific pilot program"
UNIQUE_B = "Beta Industries shall deliver widgets to the loading dock every second Tuesday of the month"


def _sig(text: str) -> bytes:
    sh = shingles(text, size=5, short_size=3, short_words=40)
    return signature_bytes(minhash_of(sh, NUM_PERM, SEED))


def _row(doc_id: str, subset: str, section_id: str, text: str, start: int) -> dict:
    return {"doc_id": doc_id, "subset": subset, "section_id": section_id, "is_leaf": True,
            "start": start, "end": start + len(text), "minhash": _sig(text)}


def toy_sections() -> pd.DataFrame:
    rows = [
        _row("nda/a.txt", "contractnli", "nda/a.txt#0", SHARED_CLAUSE, 0),
        _row("nda/a.txt", "contractnli", "nda/a.txt#1", UNIQUE_A, 100),
        _row("nda/b.txt", "contractnli", "nda/b.txt#0", SHARED_CLAUSE, 0),
        _row("nda/c.txt", "contractnli", "nda/c.txt#0", UNIQUE_B, 0),
    ]
    return pd.DataFrame(rows)


def test_near_duplicate_edges_cross_document_only() -> None:
    leaves = leaf_frame(toy_sections(), "contractnli")
    edges = near_duplicate_edges(leaves, tau=0.5, num_perm=NUM_PERM, seed=SEED)
    pairs = {frozenset(e) for e in edges}
    assert frozenset({"nda/a.txt#0", "nda/b.txt#0"}) in pairs
    assert not any("nda/a.txt#1" in p or "nda/c.txt#0" in p for p in pairs)


def test_boilerplate_share() -> None:
    leaves = leaf_frame(toy_sections(), "contractnli")
    edges = near_duplicate_edges(leaves, tau=0.5, num_perm=NUM_PERM, seed=SEED)
    share = boilerplate_share(leaves, edges).set_index("doc_id")
    assert share.loc["nda/a.txt", "share"] == len(SHARED_CLAUSE) / (len(SHARED_CLAUSE) + len(UNIQUE_A))
    assert share.loc["nda/b.txt", "share"] == 1.0
    assert share.loc["nda/c.txt", "share"] == 0.0


def test_top_shared_leaves() -> None:
    leaves = leaf_frame(toy_sections(), "contractnli")
    edges = near_duplicate_edges(leaves, tau=0.5, num_perm=NUM_PERM, seed=SEED)
    top = top_shared_leaves(leaves, edges, n=10)
    assert set(top["section_id"]) == {"nda/a.txt#0", "nda/b.txt#0"}
    assert (top["doc_count"] == 2).all()


def test_cuad_groups_by_type_not_whole_subset() -> None:
    rows = [
        _row("cuad/LICENSEA_EX-1-LICENSE AGREEMENT.txt", "cuad", "cuad/A#0", SHARED_CLAUSE, 0),
        _row("cuad/LICENSEB_EX-1-LICENSE AGREEMENT.txt", "cuad", "cuad/B#0", SHARED_CLAUSE, 0),
        _row("cuad/SUPPLYC_EX-1-SUPPLY AGREEMENT.txt", "cuad", "cuad/C#0", SHARED_CLAUSE, 0),
    ]
    sections = pd.DataFrame(rows)
    leaves = leaf_frame(sections, "cuad")
    assert set(leaves["group"]) == {"License", "Supply"}
    edges = near_duplicate_edges(leaves, tau=0.5, num_perm=NUM_PERM, seed=SEED)
    pairs = {frozenset(e) for e in edges}
    assert frozenset({"cuad/A#0", "cuad/B#0"}) in pairs
    assert not any("cuad/C#0" in p for p in pairs)  # different type -> never compared


def test_go_no_go() -> None:
    shares = pd.DataFrame([
        {"subset": "contractnli", "tau": 0.5, "share": 0.1},
        {"subset": "contractnli", "tau": 0.5, "share": 0.5},
        {"subset": "contractnli", "tau": 0.5, "share": 0.9},
        {"subset": "cuad", "tau": 0.5, "share": 0.0},
        {"subset": "cuad", "tau": 0.5, "share": 0.1},
        {"subset": "maud", "tau": 0.5, "share": 0.3},
        {"subset": "maud", "tau": 0.5, "share": 0.4},
    ])
    go, medians = go_no_go(shares, go_tau=0.5, go_median_share=0.25)
    assert go  # contractnli median 0.5 >= 0.25, maud median 0.35 >= 0.25
    assert medians["contractnli"] == 0.5


def test_go_no_go_false_when_contractnli_low() -> None:
    shares = pd.DataFrame([
        {"subset": "contractnli", "tau": 0.5, "share": 0.1},
        {"subset": "maud", "tau": 0.5, "share": 0.9},
    ])
    go, _ = go_no_go(shares, go_tau=0.5, go_median_share=0.25)
    assert not go

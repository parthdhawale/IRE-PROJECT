from __future__ import annotations

from trr.segment.sections import detect_headings, iter_nodes, leaves, segment
from trr.sketch.minhash import jaccard_estimate, minhash_of, shingles, signature_bytes

CONTRACT = """MUTUAL NON-DISCLOSURE AGREEMENT
This agreement is made between Alpha Corp and Beta Inc for the purpose of evaluating a deal.
1. Definitions. "Confidential Information" means all non-public information disclosed by a party.
(a) It includes technical data, trade secrets and know-how disclosed in any form whatsoever.
(b) It excludes information that is or becomes publicly available through no fault of the recipient.
2. Term. This Agreement shall remain in force for three (3) years from the Effective Date unless ended.
3. Governing Law. This Agreement is governed by the laws of the State of New York, without conflicts.
"""


def test_detects_heading_kinds() -> None:
    kinds = [k for _, k, _ in detect_headings(CONTRACT)]
    assert kinds == ["caps", "num1", "paren_alpha", "paren_alpha", "num1", "num1"]


def test_tree_nesting_and_offsets() -> None:
    root, fallback = segment(CONTRACT, max_leaf_chars=1500, min_leaf_chars=10)
    assert not fallback
    nodes = [n for n, _ in iter_nodes(root)]
    sec1 = next(n for n in nodes if n.heading.startswith("1. Definitions"))
    assert [c.kind for c in sec1.children] == ["intro", "paren_alpha", "paren_alpha"]
    assert CONTRACT[sec1.start:].startswith("1. Definitions")
    assert CONTRACT[sec1.end:].startswith("2. Term")
    # each child lies inside its parent
    for n in nodes:
        for c in n.children:
            assert n.start <= c.start < c.end <= n.end


def test_leaves_partition_text() -> None:
    root, _ = segment(CONTRACT, max_leaf_chars=120, min_leaf_chars=30)
    lv = sorted(leaves(root), key=lambda n: n.start)
    assert all(a.end <= b.start for a, b in zip(lv, lv[1:]))
    assert all(n.end - n.start <= 120 for n in lv)
    covered = "".join(CONTRACT[n.start:n.end] for n in lv)
    assert covered.split() == CONTRACT.split()


def test_inline_headings_after_spaces() -> None:
    text = "AGREEMENT AND PLAN OF MERGER   ARTICLE 1 DEFINITIONS   Section 1.1 Definitions. Words mean things here.   Section 1.2 Other. More words follow here."
    kinds = [k for _, k, _ in detect_headings(text)]
    assert kinds[-3:] == ["article", "sec2", "sec2"]


def test_fallback_without_headings() -> None:
    text = "We collect data about you. " * 200
    root, fallback = segment(text, max_leaf_chars=500, min_leaf_chars=50)
    assert fallback and all(n.end - n.start <= 500 for n in leaves(root))


def test_minhash_estimates_jaccard() -> None:
    a = "the receiving party shall hold the information in strict confidence and not disclose it " * 3
    b = a.replace("strict", "reasonable")
    sa, sb = (shingles(t, 5, 3, 40) for t in (a, b))
    true_j = len(sa & sb) / len(sa | sb)
    est = jaccard_estimate(signature_bytes(minhash_of(sa, 128, 0)), signature_bytes(minhash_of(sb, 128, 0)))
    assert abs(est - true_j) < 0.15
    assert jaccard_estimate(signature_bytes(minhash_of(sa, 128, 0)), signature_bytes(minhash_of(sa, 128, 0))) == 1.0

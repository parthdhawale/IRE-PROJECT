"""Span sanity checks: every gold span must round-trip to its recorded answer (plan Section 5.1).

This is the single most important check in the project -- a metric bug caused by an off-by-one
span would silently corrupt every number downstream, so it is checked once here before any
retriever ever runs.
"""

from __future__ import annotations

from trr.data.load import Document, Query


def check_subset(docs: list[Document], queries: list[Query]) -> dict:
    doc_text = {d.doc_id: d.text for d in docs}
    total = mismatch = out_of_bounds = multi_doc = 0
    for q in queries:
        if len(q.gold_docs) > 1:
            multi_doc += 1
        for g in q.gold:
            total += 1
            text = doc_text.get(g.doc_id)
            if text is None or g.start < 0 or g.start >= g.end or g.end > len(text):
                out_of_bounds += 1
                continue
            if g.answer is not None and text[g.start:g.end] != g.answer:
                mismatch += 1
    round_trip = (total - mismatch - out_of_bounds) / total if total else 1.0
    return {
        "ok": mismatch == 0 and out_of_bounds == 0,
        "round_trip": round_trip,
        "mismatch": mismatch,
        "out_of_bounds": out_of_bounds,
        "multi_doc_queries": multi_doc,
        "snippets": total,
    }

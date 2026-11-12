"""Dev / test split of the benchmark queries, drawn over gold DOCUMENTS.

IR idea: a setting chosen on the same queries it is reported on looks better than it is -- the
selection ("winner's curse") bias we measured in the band sweep (E9). So the queries are split once:
dev queries choose the settings (number of clusters k, clusters searched B, band edges), test
queries are scored once with the chosen setting.

The split follows the queries' gold documents, never the queries themselves: all questions about
one contract fall on the same side, so a setting cannot be tuned on one question about a contract
and then scored on another question about the same contract. The document folds are the
leak-safe routing folds (stratified by group, near-duplicate contracts kept in one fold), so a dev
contract is also never the twin of a test contract.
"""

from __future__ import annotations

from trr.data.load import Query

DEV, TEST = "dev", "test"


def split_queries(queries: list[Query], doc_fold: dict[str, int], dev_folds: list[int]) -> dict[str, str]:
    """qid -> "dev" or "test": a query is dev when its gold document lies in one of dev_folds.

    A query whose gold documents fall on both sides would tie the two sets together, so it is
    refused (ValueError) rather than silently assigned; LegalBench-RAG has none (one gold
    document per query).
    """
    dev = set(dev_folds)
    side = {}
    for q in queries:
        sides = {DEV if doc_fold[d] in dev else TEST for d in q.gold_docs}
        if len(sides) != 1:
            raise ValueError(f"query {q.qid} has gold documents on both sides of the split")
        side[q.qid] = sides.pop()
    return side

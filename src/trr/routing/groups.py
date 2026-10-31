"""Document groups for routing, and leak-safe document folds.

IR idea: a router is only trustworthy on documents it has never seen, because new documents
must be addable without retraining. So evaluation folds are drawn over DOCUMENTS (never
queries), stratified by group so every group keeps training documents, and near-duplicate
documents (e.g. the same CUAD exhibit filed twice) are forced into the same fold -- otherwise a
training copy would quietly stand in for its held-out twin.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from trr.analysis.h1_boilerplate import UnionFind
from trr.data.cuad_types import cuad_type
from trr.data.load import Document


def assign_groups(docs: list[Document], min_group_docs: int) -> dict[str, str]:
    """doc_id -> group: "cuad/<contract type>" for CUAD, the subset name otherwise.

    Groups smaller than min_group_docs are merged into "<subset>/Other": a group with one or
    two documents cannot be both learned and tested.
    """
    raw = {d.doc_id: f"cuad/{cuad_type(d.doc_id)}" if d.subset == "cuad" else d.subset for d in docs}
    sizes = Counter(raw.values())
    subset = {d.doc_id: d.subset for d in docs}
    return {doc: g if sizes[g] >= min_group_docs else f"{subset[doc]}/Other" for doc, g in raw.items()}


def near_duplicate_components(doc_ids: list[str], sigs: np.ndarray, dup_tau: float) -> dict[str, int]:
    """doc_id -> component id, joining documents whose MinHash Jaccard estimate >= dup_tau.

    sigs is (n_docs, num_perm); the share of equal slots between two rows estimates Jaccard.
    """
    jac = (sigs[:, None, :] == sigs[None, :, :]).mean(axis=2)
    uf = UnionFind(doc_ids)
    for i, j in zip(*np.nonzero(np.triu(jac >= dup_tau, k=1))):
        uf.union(doc_ids[i], doc_ids[j])
    roots = {r: n for n, r in enumerate(sorted({uf.find(d) for d in doc_ids}))}
    return {d: roots[uf.find(d)] for d in doc_ids}


def leak_safe_folds(doc_ids: list[str], groups: dict[str, str], components: dict[str, int],
                    n_folds: int, seed: int) -> dict[str, int]:
    """doc_id -> fold, stratified by group, with each near-duplicate component kept whole."""
    labels = [groups[d] for d in doc_ids]
    comps = [components[d] for d in doc_ids]
    splitter = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    fold = {}
    for f, (_, test) in enumerate(splitter.split(np.zeros(len(doc_ids)), labels, comps)):
        for i in test:
            fold[doc_ids[i]] = f
    return fold

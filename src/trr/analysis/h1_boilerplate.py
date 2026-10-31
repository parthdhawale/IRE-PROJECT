"""H1: is there enough cross-document boilerplate to build families/templates on? (plan Phase 1).

IR idea: MinHash LSH turns "does this leaf have a near-duplicate in another document" from an
all-pairs text comparison into a hash-bucket lookup (Section sketch/minhash.py). A document's
boilerplate share is the fraction of its characters sitting in leaves with at least one such
near-duplicate -- the central evidence for whether family/template/residual retrieval has
anything to work with. CUAD is additionally restricted to same-contract-type pairs, since two
different contract types sharing a clause is not the kind of template overlap the method needs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from trr.data.cuad_types import cuad_type
from trr.sketch.minhash import build_lsh, from_bytes, jaccard_estimate


class UnionFind:
    """Tiny union-find so "how many documents share this leaf" counts whole clusters, not just
    direct LSH hits (duplicate clauses across many documents don't all pairwise collide)."""

    def __init__(self, items: list[str]):
        self.parent = {x: x for x in items}

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def leaf_frame(sections: pd.DataFrame, subset: str) -> pd.DataFrame:
    """Leaves of one subset, with a `group` column: CUAD type for cuad, else the whole subset.

    Near-duplicates are only sought within a group, so a shared clause counts as boilerplate
    only when it recurs within the same contract type (CUAD) or the same subset (others).
    """
    leaves = sections[(sections.subset == subset) & sections.is_leaf].reset_index(drop=True).copy()
    leaves["group"] = leaves["doc_id"].map(cuad_type) if subset == "cuad" else subset
    leaves["length"] = leaves["end"] - leaves["start"]
    return leaves


def near_duplicate_edges(leaves: pd.DataFrame, tau: float, num_perm: int, seed: int
                         ) -> list[tuple[str, str]]:
    """Cross-document (section_id, section_id) pairs with Jaccard >= tau, within each group.

    LSH gives candidates per group; each candidate is re-checked with the exact signature
    Jaccard since LSH banding can return false positives near the threshold.
    """
    edges: list[tuple[str, str]] = []
    for _, g in leaves.groupby("group"):
        if len(g) < 2:
            continue
        ids = g["section_id"].to_numpy()
        docs = g["doc_id"].to_numpy()
        sigs = g["minhash"].to_numpy()
        pos = {sid: i for i, sid in enumerate(ids)}
        lsh = build_lsh(list(ids), list(sigs), tau, num_perm, seed)
        for i, sid in enumerate(ids):
            query_mh = from_bytes(sigs[i], num_perm, seed)
            for cand_id in lsh.query(query_mh):
                j = pos[cand_id]
                if j <= i or docs[j] == docs[i]:
                    continue  # skip self, already-seen pairs, and same-document matches
                if jaccard_estimate(sigs[i], sigs[j]) >= tau:
                    edges.append((sid, cand_id))
    return edges


def boilerplate_share(leaves: pd.DataFrame, edges: list[tuple[str, str]]) -> pd.DataFrame:
    """Per document: share of leaf characters that have >=1 cross-document near-duplicate."""
    dup_ids = {sid for pair in edges for sid in pair}
    leaves = leaves.assign(has_dup=leaves["section_id"].isin(dup_ids))
    by_doc = leaves.groupby("doc_id").apply(
        lambda g: pd.Series({"boilerplate_chars": g.loc[g.has_dup, "length"].sum(),
                             "total_chars": g["length"].sum()}),
        include_groups=False,
    ).reset_index()
    by_doc["share"] = by_doc["boilerplate_chars"] / by_doc["total_chars"]
    return by_doc


def top_shared_leaves(leaves: pd.DataFrame, edges: list[tuple[str, str]], n: int = 10) -> pd.DataFrame:
    """The n leaves whose near-duplicate cluster spans the most distinct documents."""
    if not edges:
        return pd.DataFrame(columns=["section_id", "doc_id", "doc_count"])
    uf = UnionFind(leaves["section_id"].tolist())
    for a, b in edges:
        uf.union(a, b)
    doc_of = dict(zip(leaves["section_id"], leaves["doc_id"]))
    cluster_docs: dict[str, set[str]] = {}
    for sid, doc_id in doc_of.items():
        cluster_docs.setdefault(uf.find(sid), set()).add(doc_id)
    leaves = leaves.assign(doc_count=leaves["section_id"].map(lambda s: len(cluster_docs[uf.find(s)])))
    top = leaves[leaves["doc_count"] > 1].sort_values("doc_count", ascending=False)
    return top.head(n)[["section_id", "doc_id", "doc_count"]]


def run_h1(sections: pd.DataFrame, subsets: list[str], taus: list[float], num_perm: int, seed: int
          ) -> tuple[pd.DataFrame, dict[tuple[str, float], list[tuple[str, str]]]]:
    """All (subset, tau, doc_id, share) rows, plus the edges found at each (subset, tau)."""
    rows, edges_by = [], {}
    for subset in subsets:
        leaves = leaf_frame(sections, subset)
        for tau in taus:
            edges = near_duplicate_edges(leaves, tau, num_perm, seed)
            edges_by[(subset, tau)] = edges
            share = boilerplate_share(leaves, edges)
            share["subset"], share["tau"] = subset, tau
            rows.append(share)
    return pd.concat(rows, ignore_index=True), edges_by


def go_no_go(shares: pd.DataFrame, go_tau: float, go_median_share: float) -> tuple[bool, pd.Series]:
    """GO if median share at go_tau is >= go_median_share on ContractNLI AND on CUAD or MAUD."""
    medians = shares[shares.tau == go_tau].groupby("subset")["share"].median()
    go = medians.get("contractnli", 0) >= go_median_share and (
        medians.get("cuad", 0) >= go_median_share or medians.get("maud", 0) >= go_median_share)
    return bool(go), medians

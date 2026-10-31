"""Cross-fold evaluation of routers at one level of the group hierarchy.

A level labels documents (flat: all 28 groups; coarse: the subset; fine: the CUAD contract type)
and says which documents train it and which items -- queries or held-out documents -- are
scored at it. In every fold the routers are fit on that level's training documents outside the
fold and score only the items whose gold document lies inside the fold, so nothing about a
held-out document reaches its own score.

The fused router combines centroid and nb_band by reciprocal rank fusion (the same rule as the
hybrid baseline): each group scores sum_r 1 / (k + rank_r); ties go to the centroid's order.
Rank fusion needs no calibration between a cosine and a Naive Bayes log-posterior.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from trr.routing.prep import unit_bootstrap_ci
from trr.routing.routers import (
    CentroidRouter,
    NBRouter,
    VocabLRRouter,
    all_words_selector,
    band_selector,
    discriminative_selector,
    gold_rank,
)

ROUTER_INPUT = {"centroid": "vec", "vocab_lr": "tok", "band_lr": "tok", "nb_band": "tok", "nb_all": "tok"}
FUSED = ("centroid", "nb_band")


@dataclass
class Level:
    name: str
    doc_labels: np.ndarray  # label per document; "" = document not used at this level
    item_gold: np.ndarray   # gold label per item; "" = item not scored at this level


def build_levels(doc_subset: np.ndarray, doc_group: np.ndarray, item_doc: np.ndarray) -> list[Level]:
    """flat (all groups), coarse (subset), fine (CUAD contract types, CUAD documents/items only).

    item_doc is the index of each item's gold document.
    """
    fine = np.where(doc_subset == "cuad", doc_group, "")
    return [Level("flat", doc_group, doc_group[item_doc]),
            Level("coarse", doc_subset, doc_subset[item_doc]),
            Level("fine", fine, fine[item_doc])]


def make_router(name: str, rc: dict, seed: int):
    band = band_selector(rc["band_low"], rc["band_high"])
    if name == "centroid":
        return CentroidRouter()
    if name == "vocab_lr":
        return VocabLRRouter(discriminative_selector(rc["vocab_per_group"], rc["vocab_alpha"]),
                             rc["lr_c"], rc["lr_max_iter"], seed)
    if name == "band_lr":
        return VocabLRRouter(band, rc["lr_c"], rc["lr_max_iter"], seed)
    if name == "nb_band":
        return NBRouter(band, rc["nb_alpha"])
    if name == "nb_all":
        return NBRouter(all_words_selector(), rc["nb_alpha"])
    raise ValueError(f"unknown router {name!r}")


def rrf_fuse(score_mats: list[np.ndarray], k: int) -> np.ndarray:
    """Fused (n_items, n_groups) scores: higher = better, ties broken by the first matrix."""
    ranks = [(-s).argsort(axis=1, kind="stable").argsort(axis=1) + 1 for s in score_mats]
    rrf = sum(1.0 / (k + r) for r in ranks)
    order = np.lexsort((ranks[0], -rrf), axis=-1)       # primary: rrf desc; then first ranker
    return -order.argsort(axis=1).astype(float)          # position 0 -> score 0 (the best)


def level_ranks(level: Level, names: list[str], cfg: dict, d_fold: np.ndarray, doc_vecs: np.ndarray,
                doc_tokens: list[list[str]], item_fold: np.ndarray, item_vecs: np.ndarray,
                item_tokens: list[list[str]]) -> tuple[dict, dict]:
    """Per router: 1-based rank of each item's gold group (0 = not scored) and the top-1 group."""
    rc = cfg["routing"]
    all_names = names + (["fused"] if all(n in names for n in FUSED) else [])
    ranks = {n: np.zeros(len(item_fold), dtype=int) for n in all_names}
    top1 = {n: np.full(len(item_fold), "", dtype=object) for n in all_names}
    for f in range(rc["n_folds"]):
        tr = np.flatnonzero((d_fold != f) & (level.doc_labels != ""))
        te = np.flatnonzero((item_fold == f) & (level.item_gold != ""))
        if len(te) == 0:
            continue
        labels, gold = list(level.doc_labels[tr]), list(level.item_gold[te])
        scores, groups = {}, {}
        for name in names:
            vec = ROUTER_INPUT[name] == "vec"
            router = make_router(name, rc, cfg["seed"]).fit(
                doc_vecs[tr] if vec else [doc_tokens[i] for i in tr], labels)
            scores[name] = router.scores(item_vecs[te] if vec else [item_tokens[i] for i in te])
            groups[name] = router.groups
        if "fused" in all_names:
            assert groups["centroid"] == groups["nb_band"]
            scores["fused"], groups["fused"] = rrf_fuse([scores[n] for n in FUSED], rc["fuse_rrf_k"]), groups["centroid"]
        for name, s in scores.items():
            ranks[name][te] = gold_rank(s, groups[name], gold)
            top1[name][te] = [groups[name][j] for j in s.argmax(axis=1)]
    return ranks, top1


def gate_report(table, gates: dict) -> tuple[list[str], dict[str, bool]]:
    """One GO/NO-GO line per gated level, judged on the best router's ALL row."""
    lines, decisions = [], {}
    for level, g in gates.items():
        rows = table[(table.level == level) & (table.subset == "ALL")].set_index("router")
        col = f"acc@{g['b']}"
        best = rows[col].astype(float).idxmax()
        acc = float(rows.loc[best, col])
        decisions[level] = acc >= g["accuracy"]
        lines.append(f"- **{level}: {'GO' if decisions[level] else 'NO-GO'}** -- best router `{best}`, "
                     f"{col} = {acc:.3f} (gate >= {g['accuracy']})")
    return lines, decisions


def end_to_end(results: dict, item_subset: np.ndarray, fine_b: int) -> dict[str, float]:
    """CUAD items only: coarse level top-1 correct AND gold contract type within the fine top-b."""
    cuad = item_subset == "cuad"
    coarse, fine = results["coarse"][0], results["fine"][0]
    return {n: round(float(((coarse[n] == 1) & (fine[n] >= 1) & (fine[n] <= fine_b))[cuad].mean()), 3)
            for n in coarse}


def summarise(level: str, ranks: dict, scored: np.ndarray, subset: np.ndarray, unit: np.ndarray,
              bs: list[int], ci_b: int, cfg: dict) -> list[dict]:
    """Accuracy@b per router, per subset and ALL, with a document-bootstrap CI at ci_b on ALL."""
    ev, rows = cfg["eval"], []
    for name, r in ranks.items():
        groups = [(s, scored & (subset == s)) for s in dict.fromkeys(subset[scored])] + [("ALL", scored)]
        for sub, m in groups:
            row = {"level": level, "router": name, "subset": sub, "items": int(m.sum()),
                   **{f"acc@{b}": round(float((r[m] <= b).mean()), 3) for b in bs}}
            if sub == "ALL":
                lo, hi = unit_bootstrap_ci((r[m] <= ci_b).astype(float), unit[m],
                                           ev["bootstrap_resamples"], ev["bootstrap_seed"])
                row[f"ci95@{ci_b}"] = f"[{lo:.3f}, {hi:.3f}]"
            rows.append(row)
    return rows

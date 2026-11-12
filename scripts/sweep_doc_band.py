"""How does document placement change with the frequency band? Sensitivity only, never used to pick.

The band (words whose document frequency lies in band_low..band_high of the training documents)
was fixed before any result was seen. This script re-runs band_lr and nb_band on held-out
documents for every (low, high) pair in band_sweep_low x band_sweep_high (low < high), at the
coarse and fine levels, with the same folds and levels as the main grouping runs. The band is
recomputed per fold and per level from that level's training documents only.

    python scripts/sweep_doc_band.py                 # LegalBench-RAG  -> results/tables/doc_band_sweep.md
    python scripts/sweep_doc_band.py --dataset wos   # Web of Science  -> results/tables/wos_band_sweep.md
    python scripts/sweep_doc_band.py --dataset wos --bands 0.01-0.5 0.002-0.75 --folds 1 2 3 4
        # confirmation of bands picked on fold 0, scored on folds the pick never saw -> *_confirm.md

Metrics per cell: acc@1/2/3 (gold group in the top-b), MRR (mean 1/rank of the gold group),
macro@1 (top-1 accuracy averaged over groups, so small groups count as much as large ones),
vocab (mean band size) and the document-frequency range it means on the first fold (df_min..df_max
training documents; at the fine level, of the largest fine sub-pool).
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config, set_seeds  # noqa: E402
from trr.routing.prep import grouping_levels  # noqa: E402
from trr.routing.routers import NBRouter, VocabLRRouter, band_selector, gold_rank  # noqa: E402

ROUTERS = ("band_lr", "nb_band")


def make(name: str, low: float, high: float, rc: dict, seed: int):
    band = band_selector(low, high)
    if name == "band_lr":
        return VocabLRRouter(band, rc["lr_c"], rc["lr_max_iter"], seed)
    return NBRouter(band, rc["nb_alpha"])


def sweep(name: str, subs: list, S, cfg: dict, folds: list[int], bands: list[tuple[float, float]]) -> list[dict]:
    rc, rows = cfg["routing"], []
    n = len(S.docs)
    scored = np.zeros(n, dtype=bool)
    for lv in subs:
        scored |= lv.item_gold != ""
    scored &= np.isin(S.d_fold, folds)
    gold = np.full(n, "", dtype=object)
    for lv in subs:
        gold[lv.item_gold != ""] = lv.item_gold[lv.item_gold != ""]
    big = max(subs, key=lambda lv: (lv.doc_labels != "").sum())
    n_train0 = int(((S.d_fold != folds[0]) & (big.doc_labels != "")).sum())
    for router in ROUTERS:
        for low, high in bands:
            t0, ranks, vocab = time.time(), np.zeros(n, dtype=int), []
            for f in folds:
                for lv in subs:
                    tr = np.flatnonzero((S.d_fold != f) & (lv.doc_labels != ""))
                    te = np.flatnonzero((S.d_fold == f) & (lv.item_gold != ""))
                    m = make(router, low, high, rc, cfg["seed"]).fit([S.doc_tokens[i] for i in tr],
                                                                     list(lv.doc_labels[tr]))
                    ranks[te] = gold_rank(m.scores([S.doc_tokens[i] for i in te]), m.groups, list(lv.item_gold[te]))
                    if lv is big:
                        vocab.append(len(m.vocab))
            r, g = ranks[scored], gold[scored]
            per_group = pd.Series(r == 1).groupby(g).mean()
            rows.append({"level": name, "router": router, "low": low, "high": high,
                         "df_min": max(1, math.ceil(low * n_train0)), "df_max": int(high * n_train0),
                         "vocab": int(np.mean(vocab)),
                         **{f"acc@{b}": round(float((r <= b).mean()), 3) for b in rc["top_b"]},
                         "mrr": round(float((1.0 / r).mean()), 3), "macro@1": round(float(per_group.mean()), 3),
                         "fixed": "<- band used" if (low, high) == (rc["band_low"], rc["band_high"]) else ""})
            print(f"{name} {router} low={low} high={high} acc@1={rows[-1]['acc@1']} ({time.time() - t0:.0f}s)",
                  flush=True)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["legalbench", "wos"], default="legalbench")
    ap.add_argument("--bands", nargs="+", help="confirmation run: only these bands, as LOW-HIGH (e.g. 0.01-0.5)")
    ap.add_argument("--folds", nargs="+", type=int, help="folds to score (default: the first sweep_folds)")
    args = ap.parse_args()
    cfg = load_config()
    set_seeds(cfg["seed"])
    rc = cfg["routing"]
    n_sweep = cfg["wos"]["sweep_folds"] if args.dataset == "wos" else rc["n_folds"]
    folds = args.folds or list(range(n_sweep))
    bands = ([tuple(float(v) for v in b.split("-")) for b in args.bands] if args.bands else
             [(lo, hi) for lo in rc["band_sweep_low"] for hi in rc["band_sweep_high"] if lo < hi])
    S, levels = grouping_levels(args.dataset, cfg)
    table = pd.DataFrame([row for name, subs in levels.items() for row in sweep(name, subs, S, cfg, folds, bands)])
    title = "Web of Science (WOS-46985)" if args.dataset == "wos" else "LegalBench-RAG"
    out = [f"# Band-edge sensitivity of document placement: {title} (held-out documents)\n",
           "Sensitivity only: the band used everywhere else (1%-50%) was fixed before any result was seen and "
           "is NOT changed by this table. `df_min..df_max` = the document-frequency range the band means on "
           "fold 0 (training documents); `vocab` = mean band size; `macro@1` = top-1 accuracy averaged over "
           f"groups; `mrr` = mean reciprocal rank of the gold group. Scored folds: {folds} of "
           f"0-{rc['n_folds'] - 1}.\n"]
    for name in levels:
        for router in ROUTERS:
            part = table[(table.level == name) & (table.router == router)].drop(columns=["level", "router"])
            out += [f"## {name} level, {router}\n", part.to_markdown(index=False), ""]
    stem = ("wos_band_sweep" if args.dataset == "wos" else "doc_band_sweep") + ("_confirm" if args.bands else "")
    path = Path(cfg["paths"]["tables"]) / f"{stem}.md"
    path.write_text("\n".join(out) + "\n")
    table.to_csv(path.with_suffix(".csv"), index=False)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()

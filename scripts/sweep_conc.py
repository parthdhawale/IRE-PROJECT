"""conc_lr: does requiring words to be concentrated in one group help place unseen documents?

conc_lr = logistic regression on sublinear tf-idf (as band_lr) over routers.concentrated_vocab:
band words that (2) appear in >= m training documents of their best group and (3) have balanced
purity >= p. This script sweeps m x p x band floor at the coarse and fine levels on held-out
documents -- a sensitivity table; the defaults (conc_min_in, conc_purity, conc_band_low) were fixed
in configs/default.yaml before any result was seen and are marked in the table.

    python scripts/sweep_conc.py --dataset wos          # -> results/tables/wos_conc_sweep.md
    python scripts/sweep_conc.py --dataset legalbench   # -> results/tables/doc_conc_sweep.md

Per cell: acc@1/2/3, MRR, macro@1, vocab (mean size), words_per_doc (mean vocabulary words in a
held-out document) and empty (share of held-out documents with no vocabulary word at all -- such a
document can only be placed by the bias terms). The cell m=1, p=0, low=band_low is band_lr itself.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config, set_seeds  # noqa: E402
from trr.routing.prep import grouping_levels  # noqa: E402
from trr.routing.routers import VocabLRRouter, concentrated_vocab, gold_rank, group_doc_freq  # noqa: E402


def sweep(name: str, subs: list, S, cfg: dict, folds: int) -> list[dict]:
    rc, n, rows = cfg["routing"], len(S.docs), []
    gold = np.full(n, "", dtype=object)
    for lv in subs:
        gold[lv.item_gold != ""] = lv.item_gold[lv.item_gold != ""]
    scored = (gold != "") & (S.d_fold < folds)
    t0 = time.time()
    parts = []   # (train idx, test idx, labels, group df stats) per fold and sub-level, computed once
    for f in range(folds):
        for lv in subs:
            tr = np.flatnonzero((S.d_fold != f) & (lv.doc_labels != ""))
            te = np.flatnonzero((S.d_fold == f) & (lv.item_gold != ""))
            labels = list(lv.doc_labels[tr])
            parts.append((tr, te, labels, group_doc_freq([S.doc_tokens[i] for i in tr], labels)))
    test_sets = {i: set(S.doc_tokens[i]) for i in np.flatnonzero(scored)}
    print(f"{name}: group statistics for {len(parts)} fits ({time.time() - t0:.0f}s)", flush=True)
    defaults = (rc["conc_band_low"], rc["conc_min_in"], rc["conc_purity"])
    for low in rc["conc_sweep_band_low"]:
        for m in rc["conc_sweep_min_in"]:
            for p in rc["conc_sweep_purity"]:
                t0, ranks, vocab, per_doc = time.time(), np.zeros(n, dtype=int), [], np.zeros(n)
                for tr, te, labels, stats in parts:
                    words = concentrated_vocab(stats, low, rc["conc_band_high"], m, p)
                    vocab.append(len(words))
                    if not words:
                        ranks[te] = len(set(labels)) + 1
                        continue
                    router = VocabLRRouter(lambda *_: words, rc["lr_c"], rc["lr_max_iter"], cfg["seed"]).fit(
                        [S.doc_tokens[i] for i in tr], labels)
                    ranks[te] = gold_rank(router.scores([S.doc_tokens[i] for i in te]), router.groups, list(gold[te]))
                    ws = set(words)
                    per_doc[te] = [len(test_sets[i] & ws) for i in te]
                r, g, wpd = ranks[scored], gold[scored], per_doc[scored]
                tag = ("<- default" if (low, m, p) == defaults else
                       "= band_lr" if (low, m, p) == (rc["band_low"], 1, 0.0) and rc["conc_band_high"] == rc["band_high"]
                       else "")
                rows.append({"level": name, "band_low": low, "m": m, "p": p, "vocab": int(np.mean(vocab)),
                             "words_per_doc": round(float(wpd.mean()), 1), "empty": round(float((wpd == 0).mean()), 3),
                             **{f"acc@{b}": round(float((r <= b).mean()), 3) for b in rc["top_b"]},
                             "mrr": round(float((1.0 / r).mean()), 3),
                             "macro@1": round(float(pd.Series(r == 1).groupby(g).mean().mean()), 3), "note": tag})
                print(f"{name} low={low} m={m} p={p} vocab={rows[-1]['vocab']} acc@1={rows[-1]['acc@1']} "
                      f"acc@3={rows[-1]['acc@3']} ({time.time() - t0:.0f}s)", flush=True)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["legalbench", "wos"], default="wos")
    ap.add_argument("--levels", nargs="+", default=["fine", "coarse"])
    args = ap.parse_args()
    cfg = load_config()
    set_seeds(cfg["seed"])
    rc = cfg["routing"]
    folds = cfg["wos"]["sweep_folds"] if args.dataset == "wos" else rc["n_folds"]
    S, levels = grouping_levels(args.dataset, cfg)
    title = "Web of Science (WOS-46985)" if args.dataset == "wos" else "LegalBench-RAG"
    stem = "wos_conc_sweep" if args.dataset == "wos" else "doc_conc_sweep"
    path = Path(cfg["paths"]["tables"]) / f"{stem}.md"
    rows = []
    for name in args.levels:
        rows += sweep(name, levels[name], S, cfg, folds)
        table = pd.DataFrame(rows)    # rewritten after every level, so a long run leaves partial results
        out = [f"# conc_lr sensitivity: {title} (held-out documents)\n",
               f"Band high edge {rc['conc_band_high']:.0%}; m = minimum training documents of the word's best group; "
               "p = minimum balanced purity (chance = 1 / number of groups). `words_per_doc` = mean vocabulary words "
               "in a held-out document, `empty` = share with none. Sensitivity only; defaults fixed beforehand "
               f"(`<- default`). Scored folds: {folds} of {rc['n_folds']}.\n"]
        for lv in table.level.unique():
            out += [f"## {lv} level\n", table[table.level == lv].drop(columns=["level"]).to_markdown(index=False), ""]
        path.write_text("\n".join(out) + "\n")
        table.to_csv(path.with_suffix(".csv"), index=False)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()

"""Paired bootstrap confidence intervals for the key method comparisons.

    python scripts/paired_ci.py --split full [--metric drm@8]

Reads the per-query run files (results/runs/<method>_<split>_<subset>.jsonl) of two methods,
pairs them by query id, and reports the macro difference (a - b) with two 95% CIs: one that
resamples queries, and one that resamples gold documents (questions about one document tend to
fail together, so this one is the honest, wider interval). A gain is claimed only if the
document CI excludes 0. Writes results/tables/paired_ci_<split>.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config  # noqa: E402
from trr.eval.metrics import paired_cluster_bootstrap_macro_ci  # noqa: E402

# (method a, method b, what the comparison shows); negative DRM difference = a is better
COMPARISONS = [
    ("docfirst", "hybrid", "separate pools: doc-first vs best flat chunk method"),
    ("docfirst_hdr", "docfirst", "separate pools: header-only document choice"),
    ("leaf_hybrid", "hybrid", "separate pools: section leaves vs 500-char chunks"),
    ("mixed_docfirst", "mixed_hybrid", "mixed pool: doc-first vs flat hybrid"),
    ("gfc_centroid_full_b2_docfirst_local", "mixed_docfirst", "mixed pool: routing + local index"),
    ("gfc_centroid_full_b2_docfirst_local_rrf", "mixed_docfirst", "mixed pool: final method vs flat doc-first"),
    ("gfc_centroid_full_b2_docfirst_local_rrf", "gfc_centroid_full_b2_docfirst_local",
     "mixed pool: header+full RRF document choice"),
    ("gfc_centroid_full_b2_docfirst_local_hdr", "gfc_centroid_full_b2_docfirst_local",
     "mixed pool: header-only document choice"),
]


def load_run(runs: Path, method: str, split: str, subset: str, metric: str) -> dict[str, tuple[str, float]]:
    """qid -> (gold document, metric value) for one method on one subset."""
    out = {}
    with open(runs / f"{method}_{split}_{subset}.jsonl") as f:
        for line in f:
            r = json.loads(line)
            if not r.get("_header"):
                out[r["qid"]] = (sorted(r["gold_docs"])[0], r[metric])
    return out


def compare(runs: Path, a: str, b: str, split: str, subsets: list[str], metric: str,
            resamples: int, seed: int) -> dict:
    by_doc, by_query = {}, {}
    for s in subsets:
        ra, rb = load_run(runs, a, split, s, metric), load_run(runs, b, split, s, metric)
        if ra.keys() != rb.keys():  # e.g. a run file written before the loader's qid change
            raise ValueError(f"{a} and {b} have different query ids on {s}: re-run the older one")
        clusters = defaultdict(list)
        for qid, (doc, va) in ra.items():
            clusters[doc].append(va - rb[qid][1])
        by_doc[s] = [np.array(v) for v in clusters.values()]
        by_query[s] = [np.array([x]) for v in clusters.values() for x in v]
    mean, qlo, qhi = paired_cluster_bootstrap_macro_ci(by_query, resamples, seed)
    _, dlo, dhi = paired_cluster_bootstrap_macro_ci(by_doc, resamples, seed)
    per_subset = {s: float(np.concatenate(by_doc[s]).mean()) for s in subsets}
    return {"mean": mean, "q": (qlo, qhi), "d": (dlo, dhi), **per_subset}


def main() -> None:
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="full", choices=["mini", "full"])
    ap.add_argument("--metric", default="drm@8")
    args = ap.parse_args()
    runs, subsets, ev = Path(cfg["paths"]["runs"]), cfg["data"]["subsets"], cfg["eval"]

    md = [f"# Paired bootstrap CIs ({args.split}, {args.metric}, a - b; negative = a lower)", "",
          f"Macro mean over subsets; {ev['bootstrap_resamples']} resamples. CI(q) resamples queries; "
          "CI(doc) resamples gold documents (questions about one document move together). "
          "A difference counts only if CI(doc) excludes 0.", "",
          "| a | b | " + " | ".join(subsets) + " | macro | CI(q) | CI(doc) | real? | what |",
          "|---|---|" + "---|" * len(subsets) + "---|---|---|---|---|"]
    for a, b, what in COMPARISONS:
        try:
            r = compare(runs, a, b, args.split, subsets, args.metric, ev["bootstrap_resamples"], ev["bootstrap_seed"])
        except FileNotFoundError as e:
            print(f"skip {a} vs {b}: {e.filename} missing")
            continue
        except ValueError as e:
            print(f"skip: {e}")
            continue
        real = "yes" if r["d"][0] > 0 or r["d"][1] < 0 else "no"
        cells = " | ".join(f"{r[s]:+.3f}" for s in subsets)
        md.append(f"| {a} | {b} | {cells} | {r['mean']:+.3f} | [{r['q'][0]:+.3f}, {r['q'][1]:+.3f}] | "
                  f"[{r['d'][0]:+.3f}, {r['d'][1]:+.3f}] | {real} | {what} |")
        print(f"{a} vs {b}: {r['mean']:+.3f} doc-CI [{r['d'][0]:+.3f}, {r['d'][1]:+.3f}] {real}")
    out = Path(cfg["paths"]["tables"]) / f"paired_ci_{args.split}.md"
    out.write_text("\n".join(md) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()

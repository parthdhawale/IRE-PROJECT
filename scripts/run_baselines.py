"""Phase 1 Track B: run the flat baselines and write the baseline table.

    python scripts/run_baselines.py --split mini --methods bm25,dense,hybrid,oracle,docfirst

Outputs results/runs/*.jsonl, results/tables/baselines_<split>.{csv,md}.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config, set_seeds  # noqa: E402
from trr.data.load import load_subset  # noqa: E402
from trr.eval.run import aggregate, run_subset  # noqa: E402
from trr.retrievers.chunk_store import ChunkStore  # noqa: E402
from trr.retrievers.flat import BASELINES  # noqa: E402

TABLE_KS = [1, 4, 16, 64]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="mini", choices=["mini", "full"])
    ap.add_argument("--methods", default="bm25,dense,hybrid,oracle,docfirst")
    ap.add_argument("--subsets", default=None, help="comma list; default = all from config")
    args = ap.parse_args()

    cfg = load_config()
    set_seeds(cfg["seed"])
    ks = cfg["eval"]["ks"]
    subsets = args.subsets.split(",") if args.subsets else cfg["data"]["subsets"]
    store = ChunkStore(cfg)
    retrievers = [BASELINES[m](store) for m in args.methods.split(",")]

    tables = []
    for subset in subsets:
        docs, queries = load_subset(cfg["paths"]["raw"], subset, args.split, cfg["data"]["mini_per_subset"])
        for r in retrievers:
            r.index(docs)
            records = run_subset(r, queries, subset, ks, cfg, args.split)
            agg = aggregate(records, r.name, ks)
            tables.append(agg[agg.subset == subset])
            row = agg[(agg.subset == subset) & (agg.k == 8)].iloc[0]
            print(f"{subset:12s} {r.name:9s} DRM@8={row.drm:.3f} docR@8={row.doc_recall:.3f} "
                  f"charR@8={row.char_r:.3f} p50={row.lat_p50_ms:.1f}ms", flush=True)

    df = pd.concat(tables, ignore_index=True)
    macro = df.groupby(["method", "k"], as_index=False, sort=False).mean(numeric_only=True)
    macro.insert(1, "subset", "ALL")
    macro["queries"] = df.groupby(["method", "k"], sort=False)["queries"].sum().values
    df = pd.concat([df, macro], ignore_index=True)

    out = Path(cfg["paths"]["tables"])
    out.mkdir(parents=True, exist_ok=True)
    # merge with methods from earlier runs so re-running one method keeps the others
    csv = out / f"baselines_{args.split}.csv"
    if csv.exists():
        old = pd.read_csv(csv)
        old = old[~(old.method.isin(df.method.unique()) & old.subset.isin(df.subset.unique()))]
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(csv, index=False)

    t1 = df[df.k.isin(TABLE_KS)].copy()
    md = [f"# Baselines on LegalBench-RAG ({args.split})", "",
          "500-char recursive chunks, no overlap; pool = full subset corpus. "
          "DRM = share of top-k hits from a wrong document (lower is better). "
          "ALL = macro mean over subsets.", ""]
    for metric in ["drm", "doc_recall", "char_p", "char_r"]:
        pv = t1.pivot_table(index=["subset", "method"], columns="k", values=metric, sort=False)
        pv.columns = [f"{metric}@{k}" for k in pv.columns]
        md += [f"## {metric}", "", pv.round(3).to_markdown(), ""]
    (out / f"baselines_{args.split}.md").write_text("\n".join(md))
    print(f"wrote {csv} and baselines_{args.split}.md")


if __name__ == "__main__":
    main()

"""Task 2: group-first retrieval vs flat retrieval on one mixed pool of all 714 documents.

    python scripts/run_group_first.py --split mini [--routers centroid,fused --beams 1,3 --inners dense]

Every query of every subset searches the same mixed pool. Writes results/runs/*.jsonl and
results/tables/group_first_<split>.{csv,md} with DRM@k, Doc-Recall@k, char recall@k, and the
share of queries whose gold group was inside the searched groups ("in_beam").
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
from trr.retrievers.group_first import POOL, GroupFirstRetriever, GroupRouter  # noqa: E402


def main() -> None:
    cfg = load_config()
    g = cfg["group_first"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="mini", choices=["mini", "full"])
    ap.add_argument("--routers", default=",".join(g["routers"]))
    ap.add_argument("--beams", default=",".join(map(str, g["beams"])))
    ap.add_argument("--inners", default=",".join(g["inners"]))
    ap.add_argument("--level", default="fine", choices=["fine", "coarse"],
                    help="fine = 28 groups; coarse = the 4 collections (gfc_* methods)")
    args = ap.parse_args()
    set_seeds(cfg["seed"])
    ks, subsets = cfg["eval"]["ks"], cfg["data"]["subsets"]

    store, all_docs, queries = ChunkStore(cfg), [], {}
    for s in subsets:
        docs, queries[s] = load_subset(cfg["paths"]["raw"], s, args.split, cfg["data"]["mini_per_subset"])
        store.add(docs)
        all_docs += docs
    store.merge(POOL, subsets)
    print(f"mixed pool: {len(all_docs)} documents, {len(store.subsets[POOL].texts)} chunks", flush=True)
    router = GroupRouter(cfg, store, all_docs, args.level)
    print(f"{len(router.groups)} groups", flush=True)

    configs = []
    for r in args.routers.split(","):
        beams = [1] if r in ("none", "oracle") else [int(b) for b in args.beams.split(",")]
        configs += [(r, b, i) for b in beams for i in args.inners.split(",")]

    tables = []
    for r, b, inner in configs:
        ret = GroupFirstRetriever(store, router, r, b, inner)
        ret.prepare_queries([q.text for s in subsets for q in queries[s]])
        for s in subsets:
            recs = run_subset(ret, queries[s], s, ks, cfg, args.split, pool=POOL)
            agg = aggregate(recs, ret.name, ks)
            agg = agg[agg.subset == s].copy()
            gold_groups = [{router.doc_group[d] for d in rec["gold_docs"]} for rec in recs]
            agg["in_beam"] = sum(bool(gg & set(rec["diag"]["groups"])) for gg, rec in zip(gold_groups, recs)) / len(recs)
            agg["router"], agg["beam"], agg["inner"], agg["level"] = r, b, inner, args.level
            tables.append(agg)
            row = agg[agg.k == 8].iloc[0]
            print(f"{ret.name:26s} {s:12s} in_beam={row.in_beam:.3f} DRM@8={row.drm:.3f} "
                  f"charR@8={row.char_r:.3f}", flush=True)

    df = pd.concat(tables, ignore_index=True)
    macro = df.groupby(["method", "k"], as_index=False, sort=False).mean(numeric_only=True)
    macro.insert(1, "subset", "ALL")
    for c in ("router", "inner"):
        macro[c] = df.groupby(["method", "k"], sort=False)[c].first().values
    df = pd.concat([df, macro], ignore_index=True)
    out = Path(cfg["paths"]["tables"])
    csv = out / f"group_first_{args.split}.csv"
    if csv.exists():  # keep configurations from earlier runs
        old = pd.read_csv(csv)
        df = pd.concat([old[~old.method.isin(df.method.unique())], df], ignore_index=True)
    df.to_csv(csv, index=False)

    t = df[df.k.isin(g["table_ks"])]
    md = [f"# Group-first vs flat retrieval on one mixed pool of 714 documents ({args.split})", "",
          "mixed_* = flat search over the whole pool (no routing). gf_<router>_b<B>_<inner> = search only "
          "the top-B groups. gf_oracle = the gold document's group (perfect routing). in_beam = share of "
          "queries whose gold group was searched. DRM lower is better.", ""]
    for metric in ["drm", "char_r", "doc_recall"]:
        pv = t.pivot_table(index=["subset", "method"], columns="k", values=metric, sort=False)
        pv.columns = [f"{metric}@{k}" for k in pv.columns]
        md += [f"## {metric}", "", pv.round(3).to_markdown(), ""]
    beam = df[df.k == 8].pivot_table(index="method", columns="subset", values="in_beam", sort=False)
    md += ["## in_beam (gold group searched)", "", beam.round(3).to_markdown(), ""]
    (out / f"group_first_{args.split}.md").write_text("\n".join(md))
    print("wrote", csv)


if __name__ == "__main__":
    main()

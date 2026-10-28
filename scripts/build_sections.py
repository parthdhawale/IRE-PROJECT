"""Phase 1 Track A: segment every document and MinHash every leaf.

Writes data/cache/sections.parquet (columns in docs/artifacts.md) and
results/notes/segmentation_samples.md (3 printed trees per subset for manual checking).
Skips the build if the cached file exists for the same config (use --force to rebuild).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import config_hash, load_config  # noqa: E402
from trr.data.load import load_corpus  # noqa: E402
from trr.segment.sections import iter_nodes, segment  # noqa: E402
from trr.sketch.minhash import minhash_of, shingles, signature_bytes  # noqa: E402

SAMPLES_PER_SUBSET = 3


def doc_rows(doc, cfg) -> tuple[list[dict], str]:
    sg, mh, seed = cfg["segmentation"], cfg["minhash"], cfg["seed"]
    root, fallback = segment(doc.text, sg["max_leaf_chars"], sg["min_leaf_chars"], sg["min_headings"])
    ids = {}
    rows, tree_lines = [], []
    for n, (node, crumb) in enumerate(iter_nodes(root)):
        ids[id(node)] = f"{doc.doc_id}#{n}"
        is_leaf = not node.children
        sig = None
        if is_leaf:
            sh = shingles(doc.text[node.start:node.end], mh["shingle_words"],
                          mh["short_shingle_words"], mh["short_section_words"])
            sig = signature_bytes(minhash_of(sh, mh["num_perm"], seed))
        rows.append({
            "doc_id": doc.doc_id, "subset": doc.subset, "section_id": ids[id(node)],
            "parent_id": ids.get(id(node.parent)) if node.parent is not None else None,
            "start": node.start, "end": node.end, "level": node.level, "heading": node.heading,
            "kind": node.kind, "breadcrumb": crumb, "is_leaf": is_leaf,
            "used_fallback": fallback, "minhash": sig,
        })
        preview = doc.text[node.start:node.end][:70].replace("\n", " ").strip()
        tree_lines.append(f"{'  ' * node.level}- [{node.kind}] {node.start}-{node.end} "
                          f"({node.end - node.start}){' LEAF' if is_leaf else ''} | {preview}")
    return rows, "\n".join(tree_lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    cache = Path(cfg["paths"]["cache"])
    key = config_hash({"seg": cfg["segmentation"], "mh": cfg["minhash"], "seed": cfg["seed"]})
    out = cache / "sections.parquet"
    meta = cache / "sections.meta.json"
    if out.exists() and meta.exists() and json.loads(meta.read_text()).get("key") == key and not args.force:
        print(f"{out} is up to date (key {key})")
        return

    all_rows, samples = [], ["# Segmentation samples (3 documents per subset)", "",
                             "Format: [kind] start-end (chars) LEAF | first 70 chars. "
                             "Check that headings are found and leaves look like clauses.", ""]
    for subset in cfg["data"]["subsets"]:
        docs = load_corpus(cfg["paths"]["raw"], subset)
        sample_ids = {docs[i].doc_id for i in range(0, len(docs), max(1, len(docs) // SAMPLES_PER_SUBSET))[:SAMPLES_PER_SUBSET]}
        for doc in tqdm(docs, desc=subset):
            rows, tree = doc_rows(doc, cfg)
            all_rows.extend(rows)
            if doc.doc_id in sample_ids:
                lines = tree.split("\n")
                shown = "\n".join(lines[:120]) + (f"\n... ({len(lines) - 120} more nodes)" if len(lines) > 120 else "")
                samples += [f"## {doc.doc_id}", f"fallback={rows[0]['used_fallback']}, nodes={len(lines)}",
                            "", "```", shown, "```", ""]

    df = pd.DataFrame(all_rows)
    cache.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    meta.write_text(json.dumps({"key": key}))
    notes = Path(cfg["paths"]["notes"])
    notes.mkdir(parents=True, exist_ok=True)
    (notes / "segmentation_samples.md").write_text("\n".join(samples))

    leaves = df[df.is_leaf]
    summary = leaves.groupby("subset").agg(
        docs=("doc_id", "nunique"), leaves=("section_id", "size"),
        median_chars=("end", lambda e: int((e - leaves.loc[e.index, "start"]).median())))
    fb = df.groupby("subset").apply(lambda g: g.drop_duplicates("doc_id").used_fallback.mean(), include_groups=False)
    summary["fallback_docs"] = fb.round(3)
    print(summary.to_string())
    print(f"wrote {out} ({len(df)} nodes, {len(leaves)} leaves)")


if __name__ == "__main__":
    main()

"""Document grouping on Web of Science: is an UNSEEN abstract filed into the right domain / area?

The same test as scripts/run_doc_grouping.py on an external, non-legal hierarchy with hundreds
of training documents per fine class (see trr/data/wos.py). Same routers, routing parameters,
gates and fold rule; only the documents differ.

- coarse: the 7 domains, all documents, gated at top-1.
- fine: the areas, trained and scored WITHIN each domain (as CUAD types are within CUAD), gated at
  top-3 -- one classifier per domain, its scores pooled over all documents.
- end-to-end: coarse top-1 correct AND area within the fine top-3.

Folds: 5 document folds stratified by area. WOS has no duplicate abstracts and the all-pairs
MinHash duplicate check does not scale to 47k documents, so every document is its own component.

Writes results/runs/wos_grouping.jsonl, results/tables/wos_grouping.md, results/notes/wos_grouping.md.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import REPO_ROOT, git_hash, load_config, set_seeds  # noqa: E402
from trr.data.wos import load_wos  # noqa: E402
from trr.routing.evaluate import Level, gate_report, level_ranks, summarise  # noqa: E402
from trr.routing.groups import leak_safe_folds  # noqa: E402
from trr.routing.prep import cached_embeddings  # noqa: E402
from trr.routing.routers import tokenize_words  # noqa: E402

NAMES = ["centroid", "vocab_lr", "band_lr", "nb_band", "nb_all"]


def main() -> None:
    cfg = load_config()
    set_seeds(cfg["seed"])
    rc, w = cfg["routing"], cfg["wos"]
    cache = Path(cfg["paths"]["cache"])
    t0 = time.time()

    docs, domain, area = load_wos(REPO_ROOT / w["root"], w["version"], cache)
    ids = [d.doc_id for d in docs]
    folds = leak_safe_folds(ids, dict(zip(ids, area)), {d: i for i, d in enumerate(ids)}, rc["n_folds"], cfg["seed"])
    d_fold = np.array([folds[d] for d in ids])
    print(f"{len(docs)} docs, {len(set(domain))} domains, {len(set(area))} areas ({time.time() - t0:.0f}s)", flush=True)

    from trr.retrievers.chunk_store import Embedder
    emb = Embedder(cfg)
    key = {"model": emb.model_name, "chars": rc["excerpt_chars"], "n": len(docs), "set": w["version"]}
    vecs = cached_embeddings("wos", [d.text[:rc["excerpt_chars"]] for d in docs],
                             lambda t: emb.encode(t, show_progress=True), key, cache)
    tokens = tokenize_words([d.text for d in docs])
    print(f"embedded and tokenised ({time.time() - t0:.0f}s)", flush=True)

    results = {"coarse": level_ranks(Level("coarse", domain, domain), NAMES, cfg, d_fold, vecs, tokens,
                                     d_fold, vecs, tokens)}
    print(f"coarse done ({time.time() - t0:.0f}s)", flush=True)
    fine_ranks, fine_top1 = None, None
    for dom in sorted(set(domain)):
        lab = np.where(domain == dom, area, "")
        r, t = level_ranks(Level(f"fine:{dom}", lab, lab), NAMES, cfg, d_fold, vecs, tokens, d_fold, vecs, tokens)
        if fine_ranks is None:
            fine_ranks, fine_top1 = r, t
        else:
            for n in r:
                mine = domain == dom
                fine_ranks[n][mine], fine_top1[n][mine] = r[n][mine], t[n][mine]
        print(f"fine {dom} done ({time.time() - t0:.0f}s)", flush=True)
    results["fine"] = (fine_ranks, fine_top1)
    routers = list(fine_ranks)

    unit, everyone = np.arange(len(docs)), np.ones(len(docs), dtype=bool)
    rows = []
    for lv in ("coarse", "fine"):
        rows += summarise(lv, results[lv][0], everyone, domain, unit, rc["top_b"], rc["gates"][lv]["b"], cfg)
    table = pd.DataFrame(rows).fillna("")
    gate_lines, _ = gate_report(table, rc["gates"])
    fine_b = rc["gates"]["fine"]["b"]
    e2e = {n: round(float(((results["coarse"][0][n] == 1) & (fine_ranks[n] <= fine_b)).mean()), 3) for n in routers}

    per_area = (pd.DataFrame({"area": area, **{n: fine_ranks[n] for n in routers}})
                .groupby("area").agg(docs=("area", "size"),
                                     **{f"{n}@{fine_b}": (n, lambda r: round(float((r <= fine_b).mean()), 2))
                                        for n in routers}))
    best = table[(table.level == "fine") & (table.subset == "ALL")].set_index("router")[f"acc@{fine_b}"].astype(float).idxmax()
    worst = per_area.sort_values(f"{best}@{fine_b}").head(10)

    runs, tables, notes = (Path(cfg["paths"][k]) for k in ("runs", "tables", "notes"))
    runs.mkdir(parents=True, exist_ok=True)
    with open(runs / "wos_grouping.jsonl", "w") as fh:
        fh.write(json.dumps({"_header": True, "git": git_hash(), "config": cfg}) + "\n")
        for i, doc_id in enumerate(ids):
            fh.write(json.dumps({"doc_id": doc_id, "domain": str(domain[i]), "area": str(area[i]), "fold": int(d_fold[i]),
                                 **{f"{lv}_rank_{n}": int(results[lv][0][n][i]) for lv in results for n in routers},
                                 **{f"{lv}_top1_{n}": results[lv][1][n][i] for lv in results for n in routers}}) + "\n")

    md = table.to_markdown(index=False)
    (tables / "wos_grouping.md").write_text("# Web of Science: grouping of held-out abstracts, per level\n\n" + md + "\n")
    sizes = pd.Series(area).value_counts()
    note = [
        "# Document grouping on Web of Science (WOS-46985): are unseen abstracts filed correctly?\n",
        *gate_lines, "",
        f"End-to-end (coarse top-1 correct AND area in fine top-{fine_b}): "
        + ", ".join(f"`{n}` {v:.3f}" for n, v in e2e.items()) + "\n",
        "## Setup\n",
        f"- {len(docs)} abstracts, {len(set(domain))} domains, {len(set(area))} (domain, area) labels; "
        f"{sizes.min()}-{sizes.max()} abstracts per area (median {int(sizes.median())}), i.e. about "
        f"{int(sizes.median() * (rc['n_folds'] - 1) / rc['n_folds'])} training abstracts per area per fold "
        "(CUAD: 8-32 per type).",
        f"- {rc['n_folds']} document folds stratified by area; no duplicate abstracts, so no near-duplicate "
        "grouping (the all-pairs MinHash check does not scale to 47k documents).",
        "- Same routers, routing parameters and gates as LegalBench-RAG (configs/default.yaml `routing`). "
        f"Band = {rc['band_low']:.0%}-{rc['band_high']:.0%} of each level's training documents: with ~37k "
        "training abstracts at the coarse level the 1% floor is ~375 documents, far higher in absolute terms "
        "than on LegalBench-RAG.",
        "- fine: one classifier per domain, trained on that domain's training abstracts only, scored on its "
        "held-out abstracts (the gold domain is given, as CUAD is for the CUAD fine level).",
        f"- centroid embeds the first {rc['excerpt_chars']} characters, which covers almost every abstract.\n",
        "## Results\n", md, "",
        f"## Hardest areas ({best}, acc@{fine_b})\n", worst.to_markdown(), "",
        f"Run time {time.time() - t0:.0f}s.",
    ]
    (notes / "wos_grouping.md").write_text("\n".join(note) + "\n")
    print(md)
    print("\n".join(gate_lines))
    print("end-to-end:", e2e)


if __name__ == "__main__":
    main()

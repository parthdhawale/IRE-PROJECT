"""Build E13's held-out passage queries from the built CLERC pool (trr.data.heldout).

    python scripts/build_heldout_queries.py

Cases are visited in a seeded random order; each gets one span (a sentence start after the
opening, `max(lengths)` words, no leak into the rest of its case) until `n_queries` cases have
one. Cases where no position works within `tries` are skipped and counted. The split is by case
(clerc.dev_share, the same function as the pool's split). The pool itself is not changed: the
loader (trr.data.clerc.load_clerc_heldout) cuts the spans out when it builds the documents.

Writes data/external/clerc/pool_<n>/heldout/queries.parquet (qid, case_id, start, end_<len> per
length, side, attempts, leaks_rejected) and heldout.meta.json (counts, config, git hash).
Seconds to run, so it is simply rebuilt.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import git_hash, load_config, set_seeds  # noqa: E402
from trr.data.clerc import heldout_dir, pool_dir, split_by_gold  # noqa: E402
from trr.data.heldout import choose_span  # noqa: E402


def build(cfg: dict, docs: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    h = cfg["clerc"]["heldout"]
    lengths = sorted(h["lengths"])
    rng = np.random.default_rng(cfg["seed"])
    rows, skipped, leaks = [], 0, 0
    for i in rng.permutation(len(docs)):
        if len(rows) == h["n_queries"]:
            break
        case_id, text = int(docs.case_id.iloc[i]), docs.text.iloc[i]
        found = choose_span(text, rng, lengths, h["skip_frac"], h["leak_window"], h["tries"])
        if found is None:
            skipped += 1
            continue
        start, ends, attempts, rejected = found
        leaks += rejected
        rows.append({"qid": f"h{case_id}", "case_id": case_id, "start": start,
                     **{f"end_{n}": e for n, e in zip(lengths, ends)},
                     "attempts": attempts, "leaks_rejected": rejected})
    q = pd.DataFrame(rows)
    side = split_by_gold(q.case_id.tolist(), cfg["clerc"]["dev_share"], cfg["seed"])
    q["side"] = q.case_id.map(side)
    meta = {"queries": len(q), "dev": int((q.side == "dev").sum()), "test": int((q.side == "test").sum()),
            "cases_skipped": skipped, "leaky_positions_rejected": leaks,
            "queries_with_a_rejected_position": int((q.leaks_rejected > 0).sum()),
            "mean_attempts": float(q.attempts.mean()),
            "mean_start_share": float((q.start / docs.set_index("case_id").text.str.len().loc[q.case_id].values).mean()),
            "chars_per_length": {n: float((q[f"end_{n}"] - q.start).mean()) for n in lengths}}
    return q, meta


def main() -> None:
    cfg = load_config()
    set_seeds(cfg["seed"])
    t0 = time.time()
    docs = pd.read_parquet(pool_dir(cfg) / "docs.parquet")
    q, meta = build(cfg, docs)
    out = heldout_dir(cfg)
    out.mkdir(parents=True, exist_ok=True)
    q.to_parquet(out / "queries.parquet", index=False)
    meta.update({"pool_cases": len(docs), "seconds": time.time() - t0, "git": git_hash(),
                 "config": cfg["clerc"]["heldout"], "seed": cfg["seed"]})
    (out / "heldout.meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()

"""Failure analysis of doc-first's document selection (whole-document BM25 -> top-1).

For every mini query whose top-1 document is wrong, ask why:
- name_missing: an identifying word from the query's "Consider ...;" clause (a party or
  organisation name) never appears in the gold document's text, so no text-based ranker can
  use it;
- template_sibling: the wrongly picked document shares a lot of exact text with the gold one
  (document-level MinHash Jaccard well above the subset's background level);
- other: neither.
Also checks how many misses a filename match on the identifying words would fix.

Writes results/notes/failure_analysis_docfirst.md.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import bm25s
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from trr.config import load_config  # noqa: E402
from trr.data.load import load_subset  # noqa: E402
from trr.retrievers.chunk_store import tokenize  # noqa: E402
from trr.sketch.minhash import jaccard_estimate, minhash_of, shingles, signature_bytes  # noqa: E402

GENERIC = {"the", "a", "an", "and", "between", "of", "for", "to", "s", "consider", "agreement",
           "non", "disclosure", "nondisclosure", "mutual", "confidentiality", "confidential",
           "unilateral", "standard", "form", "nda", "privacy", "policy", "plan", "merger",
           "information", "terms", "service", "services", "inc", "llc", "ltd", "co", "corp"}
SIBLING_MARGIN = 0.10  # Jaccard this far above the subset's random-pair background = sibling


def identifiers(query: str) -> list[str]:
    """Distinctive words of the query's document description ('Consider ...;')."""
    m = re.match(r"Consider (.+?);", query)
    words = re.findall(r"[A-Za-z0-9]+", m.group(1)) if m else []
    return [w.lower() for w in words if w.lower() not in GENERIC and len(w) > 1]


def doc_sig(text: str, mh: dict, seed: int) -> bytes:
    sh = shingles(text, mh["shingle_words"], mh["short_shingle_words"], mh["short_section_words"])
    return signature_bytes(minhash_of(sh, mh["num_perm"], seed))


def analyse(subset: str, cfg: dict) -> tuple[dict, list[str]]:
    docs, queries = load_subset(cfg["paths"]["raw"], subset, "mini", cfg["data"]["mini_per_subset"])
    text = {d.doc_id: d.text for d in docs}
    ids = [d.doc_id for d in docs]
    b = cfg["bm25"]
    model = bm25s.BM25(k1=b["k1"], b=b["b"])
    model.index(tokenize([d.text for d in docs]), show_progress=False)

    mh, seed = cfg["minhash"], cfg["seed"]
    sigs: dict[str, bytes] = {}
    sig = lambda d: sigs.setdefault(d, doc_sig(text[d], mh, seed))  # noqa: E731
    rng = np.random.default_rng(seed)
    pairs = [rng.choice(len(ids), 2, replace=False) for _ in range(200)]
    background = float(np.mean([jaccard_estimate(sig(ids[i]), sig(ids[j])) for i, j in pairs]))

    counts, examples, n_miss, fname_fix = Counter(), [], 0, 0
    for q in queries:
        top, _ = model.retrieve(tokenize([q.text]), k=1, show_progress=False)
        picked, gold = ids[top[0][0]], sorted(q.gold_docs)[0]
        if picked == gold:
            continue
        n_miss += 1
        idw = identifiers(q.text)
        missing = [w for w in idw if w not in text[gold].lower()]
        jac = jaccard_estimate(sig(gold), sig(picked))
        if missing:
            cause = "name_missing"
        elif jac >= background + SIBLING_MARGIN:
            cause = "template_sibling"
        else:
            cause = "other"
        counts[cause] += 1
        hits = [d for d in ids if idw and all(w in d.lower() for w in idw)]
        fname_fix += hits == [gold]
        if len(examples) < 12:
            examples.append(f"- [{cause}] jac={jac:.2f} missing={missing} | {q.text[:110]}\n"
                            f"  gold: `{gold}` picked: `{picked}`")
    stats = {"subset": subset, "queries": len(queries), "misses": n_miss,
             "drm@1": round(n_miss / len(queries), 3), "background_jaccard": round(background, 3),
             **{k: counts.get(k, 0) for k in ("name_missing", "template_sibling", "other")},
             "fixed_by_filename_match": fname_fix}
    return stats, examples


def main() -> None:
    cfg = load_config()
    lines = ["# Failure analysis: doc-first document selection (mini)", "",
             "Doc-first = whole-document BM25 -> top-1 document. A miss is a query whose top-1 "
             "document is not the gold one (= DRM for doc-first). Causes, in priority order: "
             "name_missing (a distinctive word from the query's 'Consider ...;' clause is absent "
             "from the gold text), template_sibling (picked doc's MinHash Jaccard with the gold doc "
             f"is >= {SIBLING_MARGIN} above the subset's random-pair background), other. "
             "fixed_by_filename_match = misses where the distinctive words match exactly one file "
             "name, the gold one.", "", "| " + " | ".join(
                 ["subset", "queries", "misses", "drm@1", "background_jaccard", "name_missing",
                  "template_sibling", "other", "fixed_by_filename_match"]) + " |",
             "|" + "---|" * 9]
    all_examples = []
    for subset in cfg["data"]["subsets"]:
        stats, examples = analyse(subset, cfg)
        lines.append("| " + " | ".join(str(v) for v in stats.values()) + " |")
        all_examples += [f"### {subset}", *examples, ""]
        print(stats, flush=True)
    lines += ["", "## Example misses", "", *all_examples]
    out = Path(cfg["paths"]["notes"]) / "failure_analysis_docfirst.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

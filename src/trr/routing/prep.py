"""Shared inputs for the routing experiments: cached document signatures and embeddings, and a
bootstrap CI that resamples documents (the independent unit) rather than queries."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from trr.config import config_hash
from trr.data.load import load_corpus
from trr.routing.groups import assign_groups, leak_safe_folds, near_duplicate_components
from trr.sketch.minhash import minhash_of, shingles


def doc_signatures(docs, cfg: dict, cache: Path) -> np.ndarray:
    """(n_docs, num_perm) MinHash of each whole document, cached by config."""
    mh = cfg["minhash"]
    path = cache / f"doc_minhash_{config_hash({'mh': mh, 'seed': cfg['seed'], 'n': len(docs)})}.npy"
    if path.exists():
        return np.load(path)
    sigs = np.stack([minhash_of(shingles(d.text, mh["shingle_words"], mh["short_shingle_words"],
                                         mh["short_section_words"]), mh["num_perm"], cfg["seed"]).hashvalues
                     for d in docs]).astype(np.uint64)
    np.save(path, sigs)
    return sigs


def cached_embeddings(name: str, texts: list[str], encode, key: dict, cache: Path) -> np.ndarray:
    """encode(texts), stored as float16 per CLAUDE.md; returns the same values as a reload."""
    path = cache / f"routing_emb_{name}_{config_hash(key)}.npy"
    if path.exists():
        return np.load(path).astype(np.float32)
    vecs = encode(texts)
    np.save(path, vecs.astype(np.float16))
    return vecs.astype(np.float16).astype(np.float32)


def doc_full_vectors(cfg: dict, docs) -> np.ndarray:
    """(n_docs, dim) whole-document vectors: the normalised mean of each document's 500-char
    chunk embeddings (the same cached vectors the dense baseline uses), so a merger agreement is
    represented by all of its text rather than its cover page and table of contents."""
    from trr.retrievers.chunk_store import ChunkStore

    store = ChunkStore(cfg)
    by_subset: dict[str, list] = {}
    for d in docs:
        by_subset.setdefault(d.subset, []).append(d)
    vec = {}
    for subset, ds in by_subset.items():
        store.add(ds)
        emb, rows = store.embeddings(subset), store.subsets[subset].doc_rows
        for d in ds:
            m = emb[rows[d.doc_id]].mean(axis=0)
            vec[d.doc_id] = m / np.linalg.norm(m)
    return np.stack([vec[d.doc_id] for d in docs]).astype(np.float32)


def legalbench_doc_folds(cfg: dict, docs) -> tuple[dict[str, str], dict[str, int], dict[str, int]]:
    """(groups, near-duplicate components, leak-safe folds), each keyed by doc_id.

    The one place the LegalBench-RAG document folds are drawn: the routing experiments and the
    dev/test query split (trr.eval.splits) use the same folds, so they can never disagree."""
    rc, cache = cfg["routing"], Path(cfg["paths"]["cache"])
    cache.mkdir(parents=True, exist_ok=True)
    doc_ids = [d.doc_id for d in docs]
    groups = assign_groups(docs, rc["min_group_docs"])
    comps = near_duplicate_components(doc_ids, doc_signatures(docs, cfg, cache), rc["dup_tau"])
    return groups, comps, leak_safe_folds(doc_ids, groups, comps, rc["n_folds"], cfg["seed"])


def load_setup(cfg: dict, full_vectors: bool = False) -> SimpleNamespace:
    """Everything both routing experiments share: the mixed pool, its groups, leak-safe folds,
    document embeddings and tokens. Identical across scripts, so their numbers are comparable.

    full_vectors=True also builds the whole-document vectors (doc_full_vectors) for the
    centroid_full router. They need the chunk embeddings of all 714 documents (~207k chunks),
    which are expensive when not cached, so callers that do not use them leave it off
    (doc_vecs_full is then None)."""
    from trr.retrievers.chunk_store import Embedder
    from trr.routing.routers import tokenize_words

    rc, cache = cfg["routing"], Path(cfg["paths"]["cache"])
    docs = [d for s in cfg["data"]["subsets"] for d in load_corpus(cfg["paths"]["raw"], s)]
    doc_ids = [d.doc_id for d in docs]
    groups, comps, folds = legalbench_doc_folds(cfg, docs)
    emb = Embedder(cfg)
    key = {"model": emb.model_name, "chars": rc["excerpt_chars"], "n": len(docs)}
    doc_vecs = cached_embeddings("docs", [d.text[:rc["excerpt_chars"]] for d in docs], emb.encode, key, cache)
    return SimpleNamespace(
        docs=docs, doc_ids=doc_ids, emb=emb, cache=cache, doc_vecs=doc_vecs,
        doc_vecs_full=doc_full_vectors(cfg, docs) if full_vectors else None,
        doc_tokens=tokenize_words([d.text for d in docs]),
        doc_subset=np.array([d.subset for d in docs]), doc_group=np.array([groups[d] for d in doc_ids]),
        d_fold=np.array([folds[d] for d in doc_ids]),
        n_dup=sum(n > 1 for n in np.bincount(list(comps.values()))))


def load_wos_setup(cfg: dict, embed: bool = True) -> SimpleNamespace:
    """Web of Science counterpart of load_setup: documents, domain / area labels, 5 document folds
    stratified by area (no duplicate abstracts, so each document is its own fold component),
    tokens and -- if embed -- cached excerpt embeddings."""
    from trr.config import REPO_ROOT
    from trr.data.wos import load_wos
    from trr.routing.routers import tokenize_words

    rc, w, cache = cfg["routing"], cfg["wos"], Path(cfg["paths"]["cache"])
    docs, domain, area = load_wos(REPO_ROOT / w["root"], w["version"], cache)
    ids = [d.doc_id for d in docs]
    folds = leak_safe_folds(ids, dict(zip(ids, area)), {d: i for i, d in enumerate(ids)}, rc["n_folds"], cfg["seed"])
    vecs = None
    if embed:
        from trr.retrievers.chunk_store import Embedder
        emb = Embedder(cfg)
        key = {"model": emb.model_name, "chars": rc["excerpt_chars"], "n": len(docs), "set": w["version"]}
        vecs = cached_embeddings("wos", [d.text[:rc["excerpt_chars"]] for d in docs],
                                 lambda t: emb.encode(t, show_progress=True), key, cache)
    return SimpleNamespace(docs=docs, doc_ids=ids, domain=domain, area=area, doc_vecs=vecs,
                           d_fold=np.array([folds[d] for d in ids]),
                           doc_tokens=tokenize_words([d.text for d in docs]))


def grouping_levels(dataset: str, cfg: dict, embed: bool = False):
    """(setup, {"coarse": [Level], "fine": [Level, ...]}) for "legalbench" or "wos". A level may be
    several disjoint sub-levels whose scores are pooled (WOS fine = one classifier per domain)."""
    from trr.routing.evaluate import Level, build_levels

    if dataset == "wos":
        S = load_wos_setup(cfg, embed=embed)
        fine = [Level(f"fine:{d}", np.where(S.domain == d, S.area, ""), np.where(S.domain == d, S.area, ""))
                for d in sorted(set(S.domain))]
        return S, {"coarse": [Level("coarse", S.domain, S.domain)], "fine": fine}
    S = load_setup(cfg)
    lv = {x.name: x for x in build_levels(S.doc_subset, S.doc_group, np.arange(len(S.docs)))}
    return S, {"coarse": [lv["coarse"]], "fine": [lv["fine"]]}


def unit_bootstrap_ci(hit: np.ndarray, unit: np.ndarray, resamples: int, seed: int) -> tuple[float, float]:
    """95% CI of mean(hit), resampling units (documents): rows sharing a unit move together."""
    units, inv = np.unique(unit, return_inverse=True)
    hits, counts = np.bincount(inv, weights=hit), np.bincount(inv)
    idx = np.random.default_rng(seed).integers(0, len(units), size=(resamples, len(units)))
    acc = hits[idx].sum(axis=1) / counts[idx].sum(axis=1)
    lo, hi = np.quantile(acc, [0.025, 0.975])
    return float(lo), float(hi)

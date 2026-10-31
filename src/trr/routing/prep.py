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


def load_setup(cfg: dict) -> SimpleNamespace:
    """Everything both routing experiments share: the mixed pool, its groups, leak-safe folds,
    document embeddings and tokens. Identical across scripts, so their numbers are comparable."""
    from trr.retrievers.chunk_store import Embedder
    from trr.routing.routers import tokenize_words

    rc, cache = cfg["routing"], Path(cfg["paths"]["cache"])
    cache.mkdir(parents=True, exist_ok=True)
    docs = [d for s in cfg["data"]["subsets"] for d in load_corpus(cfg["paths"]["raw"], s)]
    doc_ids = [d.doc_id for d in docs]
    groups = assign_groups(docs, rc["min_group_docs"])
    comps = near_duplicate_components(doc_ids, doc_signatures(docs, cfg, cache), rc["dup_tau"])
    folds = leak_safe_folds(doc_ids, groups, comps, rc["n_folds"], cfg["seed"])
    emb = Embedder(cfg)
    key = {"model": emb.model_name, "chars": rc["excerpt_chars"], "n": len(docs)}
    doc_vecs = cached_embeddings("docs", [d.text[:rc["excerpt_chars"]] for d in docs], emb.encode, key, cache)
    return SimpleNamespace(
        docs=docs, doc_ids=doc_ids, emb=emb, cache=cache, doc_vecs=doc_vecs,
        doc_tokens=tokenize_words([d.text for d in docs]),
        doc_subset=np.array([d.subset for d in docs]), doc_group=np.array([groups[d] for d in doc_ids]),
        d_fold=np.array([folds[d] for d in doc_ids]),
        n_dup=sum(n > 1 for n in np.bincount(list(comps.values()))))


def unit_bootstrap_ci(hit: np.ndarray, unit: np.ndarray, resamples: int, seed: int) -> tuple[float, float]:
    """95% CI of mean(hit), resampling units (documents): rows sharing a unit move together."""
    units, inv = np.unique(unit, return_inverse=True)
    hits, counts = np.bincount(inv, weights=hit), np.bincount(inv)
    idx = np.random.default_rng(seed).integers(0, len(units), size=(resamples, len(units)))
    acc = hits[idx].sum(axis=1) / counts[idx].sum(axis=1)
    lo, hi = np.quantile(acc, [0.025, 0.975])
    return float(lo), float(hi)

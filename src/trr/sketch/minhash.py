"""MinHash signatures over word shingles (MMDS Ch. 3).

IR idea: the Jaccard similarity of two shingle sets equals the probability that their minimum
hash values agree under a random permutation, so the share of agreeing slots across
`num_perm` hash functions is an unbiased Jaccard estimate. Comparing 128 integers replaces
comparing whole shingle sets, and LSH banding over those integers finds near-duplicate
sections without all-pairs comparison.
"""

from __future__ import annotations

import re

import numpy as np
from datasketch import MinHash, MinHashLSH

_WORD = re.compile(r"\w+")


def normalize_words(text: str) -> list[str]:
    """Lower-case word tokens; punctuation and whitespace differences disappear."""
    return _WORD.findall(text.lower())


def shingles(text: str, size: int, short_size: int, short_words: int) -> set[bytes]:
    """Word n-gram shingles; sections shorter than `short_words` use `short_size`-grams."""
    words = normalize_words(text)
    n = short_size if len(words) < short_words else size
    if len(words) < n:
        return {" ".join(words).encode()} if words else set()
    return {" ".join(words[i:i + n]).encode() for i in range(len(words) - n + 1)}


def minhash_of(shingle_set: set[bytes], num_perm: int, seed: int) -> MinHash:
    m = MinHash(num_perm=num_perm, seed=seed)
    if shingle_set:
        m.update_batch(list(shingle_set))
    return m


def signature_bytes(m: MinHash) -> bytes:
    return m.hashvalues.astype(np.uint64).tobytes()


def from_bytes(b: bytes, num_perm: int, seed: int) -> MinHash:
    """Rebuild a MinHash from stored hash values (same num_perm and seed as when built)."""
    return MinHash(num_perm=num_perm, seed=seed, hashvalues=np.frombuffer(b, dtype=np.uint64))


def jaccard_estimate(a: bytes, b: bytes) -> float:
    """Share of agreeing hash slots = unbiased estimate of shingle-set Jaccard."""
    return float(np.mean(np.frombuffer(a, dtype=np.uint64) == np.frombuffer(b, dtype=np.uint64)))


def build_lsh(keys: list[str], sigs: list[bytes], threshold: float, num_perm: int, seed: int) -> MinHashLSH:
    """LSH index whose band/row split is chosen by datasketch to approximate `threshold`."""
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    with lsh.insertion_session() as session:
        for k, s in zip(keys, sigs):
            session.insert(k, from_bytes(s, num_perm, seed))
    return lsh

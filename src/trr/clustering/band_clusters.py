"""Band clusters: group documents by their mid-frequency words with spherical k-means.

IR idea (Luhn's "resolving power" of words): a word in only a handful of documents identifies a
document, a word in most documents says nothing, and the band in between says what KIND of
document it is. Each document becomes a sublinear tf-idf vector over that mid band, scaled to
length 1, and documents are grouped by cosine similarity with spherical k-means. This rests on the
cluster hypothesis: documents close in this space tend to be relevant to the same queries, so a
query can be sent to a few clusters instead of the whole collection.

Spherical k-means is k-means for unit vectors: a document joins the centroid with the highest
cosine, and a centroid is the mean of its documents rescaled to length 1. Each cluster is
"identified" by the heaviest words of its centroid (names()).

Extendible: the vocabulary and idf are frozen when the index is built. A new document is placed in
its nearest cluster (assign) and added to that cluster's running sum (add), which moves the
centroid. Nothing is re-clustered or retrained.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer


def _identity(tokens: list[str]) -> list[str]:
    return tokens


def mid_band_vocab(token_lists: list[list[str]], min_df: int, max_frac: float) -> list[str]:
    """Words in at least min_df documents (an absolute count) and at most max_frac of them.

    The floor is a count, not a share: a share grows with the collection and starts throwing away
    real topic words (results E6, E9); a count only drops words too rare to describe a kind.
    """
    n = len(token_lists)
    df = Counter(w for t in token_lists for w in set(t))
    return sorted(w for w, d in df.items() if min_df <= d <= max_frac * n)


def _kmeans_plus_plus(x: sparse.csr_matrix, k: int, rng: np.random.Generator) -> np.ndarray:
    """k starting centroids: the first at random, each next one drawn with probability proportional
    to its squared distance (1 - cosine) from the nearest centroid chosen so far (k-means++), so
    the starts are spread over the collection."""
    n = x.shape[0]
    centres = [x[rng.integers(n)].toarray()[0]]
    nearest = np.asarray(x @ centres[0]).ravel()          # best cosine to any chosen centre
    for _ in range(1, k):
        d2 = np.clip(1.0 - nearest, 0.0, None) ** 2
        p = d2 / d2.sum() if d2.sum() > 0 else np.full(n, 1.0 / n)
        c = x[rng.choice(n, p=p)].toarray()[0]
        centres.append(c)
        nearest = np.maximum(nearest, np.asarray(x @ c).ravel())
    return np.stack(centres)


def _unit_rows(m: np.ndarray) -> np.ndarray:
    return m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-12)


def cluster_sums(x: sparse.csr_matrix, labels: np.ndarray, k: int) -> np.ndarray:
    """(k, n_words) sum of the document vectors of each cluster."""
    member = sparse.csr_matrix((np.ones(len(labels)), (labels, np.arange(len(labels)))), shape=(k, x.shape[0]))
    return np.asarray((member @ x).todense())


def spherical_kmeans(x: sparse.csr_matrix, k: int, n_init: int, max_iter: int,
                     seed: int) -> tuple[np.ndarray, np.ndarray]:
    """(labels, unit centroids) of the best of n_init runs, best = highest total cosine of the
    documents to their own centroid. Rows of x must be unit length (or zero: a document with no
    mid-band word, which goes to cluster 0 and does not pull any centroid)."""
    rng = np.random.default_rng(seed)
    n, best = x.shape[0], None
    for _ in range(n_init):
        centroids, labels = _kmeans_plus_plus(x, k, rng), None
        for _ in range(max_iter):
            sims = np.asarray(x @ centroids.T)              # (n, k) cosines
            new = sims.argmax(axis=1)
            if labels is not None and np.array_equal(new, labels):
                break                                        # no document moved: converged
            labels = new
            sums = cluster_sums(x, labels, k)
            fit = sims[np.arange(n), labels]
            for c in np.flatnonzero(np.bincount(labels, minlength=k) == 0):
                worst = int(np.argmin(fit))                  # an empty cluster restarts at the
                sums[c], fit[worst] = x[worst].toarray()[0], np.inf   # worst-fitting document
            centroids = _unit_rows(sums)
        sims = np.asarray(x @ centroids.T)
        labels = sims.argmax(axis=1)
        score = float(sims[np.arange(n), labels].sum())
        if best is None or score > best[0]:
            best = (score, labels, centroids)
    return best[1], best[2]


class BandClusters:
    """Mid-band tf-idf vectors + spherical k-means; routes texts to clusters; takes new documents."""

    def __init__(self, min_df: int, max_frac: float, k: int, n_init: int, max_iter: int, seed: int):
        self.min_df, self.max_frac, self.k = min_df, max_frac, k
        self.n_init, self.max_iter, self.seed = n_init, max_iter, seed

    def fit(self, token_lists: list[list[str]]) -> "BandClusters":
        self.vocab = mid_band_vocab(token_lists, self.min_df, self.max_frac)
        self.vec = TfidfVectorizer(analyzer=_identity, vocabulary=self.vocab, sublinear_tf=True)  # L2 rows
        x = self.vec.fit_transform(token_lists)     # idf from these documents, then frozen
        k = min(self.k, x.shape[0])
        self.labels, _ = spherical_kmeans(x, k, self.n_init, self.max_iter, self.seed)
        self.sums = cluster_sums(x, self.labels, k)  # running sums: add() only adds to them
        self.counts = np.bincount(self.labels, minlength=k)
        return self

    @property
    def n_clusters(self) -> int:
        return len(self.counts)

    @property
    def centroids(self) -> np.ndarray:
        return _unit_rows(self.sums)

    def similarities(self, token_lists: list[list[str]]) -> np.ndarray:
        """(n_texts, n_clusters) cosine of each text's mid-band vector to each centroid."""
        return np.asarray(self.vec.transform(token_lists) @ self.centroids.T)

    def route(self, tokens: list[str], b: int) -> list[int]:
        """The b clusters with the highest cosine, best first. A text with no mid-band word has
        no evidence of its kind, so it is routed to every cluster (flat search)."""
        sims = self.similarities([tokens])[0]
        if not sims.any():
            return list(range(self.n_clusters))
        return [int(c) for c in np.argsort(-sims, kind="stable")[:b]]

    def assign(self, token_lists: list[list[str]]) -> np.ndarray:
        """Nearest cluster of each text (placement of a new document: no refit)."""
        return self.similarities(token_lists).argmax(axis=1)

    def add(self, token_lists: list[list[str]]) -> np.ndarray:
        """Place new documents and fold them into their clusters' centroids (O(1) per document)."""
        x = self.vec.transform(token_lists)
        labels = np.asarray(x @ self.centroids.T).argmax(axis=1)
        for row, c in enumerate(labels):
            self.sums[c] += x[row].toarray()[0]
            self.counts[c] += 1
        self.labels = np.concatenate([self.labels, labels])
        return labels

    def names(self, n: int) -> list[list[str]]:
        """The n heaviest centroid words of each cluster: a readable label for it."""
        words = np.array(self.vocab)
        return [list(words[np.argsort(-c, kind="stable")[:n]]) for c in self.centroids]

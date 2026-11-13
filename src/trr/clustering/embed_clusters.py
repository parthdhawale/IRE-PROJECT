"""Embedding clusters: group documents by their embedding vectors with spherical k-means.

IR idea: the cluster hypothesis again (documents close together tend to answer the same queries),
but "close" now means close in a sentence-embedding space instead of sharing mid-band words. A
document's vector is the normalised mean of its chunk vectors (whole-document "centroid_full",
which routed best in E10), so a long court case is represented by all of its text. The same
spherical k-means as the band clusters (trr.clustering.band_clusters) groups the vectors, so the
two pipelines differ only in the representation.

Extendible: the embedding model is fixed (never trained here). A new document is embedded, placed
in its nearest cluster and added to that cluster's running sum, which moves the centroid.
"""

from __future__ import annotations

import numpy as np

from trr.clustering.band_clusters import _unit_rows, cluster_sums, spherical_kmeans


class EmbedClusters:
    """Spherical k-means over unit document vectors; routes query vectors; takes new documents."""

    def __init__(self, k: int, n_init: int, max_iter: int, seed: int):
        self.k, self.n_init, self.max_iter, self.seed = k, n_init, max_iter, seed

    def fit(self, vecs: np.ndarray) -> "EmbedClusters":
        x = _unit_rows(np.asarray(vecs, dtype=float))
        k = min(self.k, len(x))
        self.labels, _ = spherical_kmeans(x, k, self.n_init, self.max_iter, self.seed)
        self.sums = cluster_sums(x, self.labels, k)
        self.counts = np.bincount(self.labels, minlength=k)
        return self

    @property
    def n_clusters(self) -> int:
        return len(self.counts)

    @property
    def centroids(self) -> np.ndarray:
        return _unit_rows(self.sums)

    def similarities(self, vecs: np.ndarray) -> np.ndarray:
        """(n_vectors, n_clusters) cosine of each (unit) vector to each centroid."""
        return np.asarray(vecs, dtype=float) @ self.centroids.T

    def route(self, qvec: np.ndarray, b: int) -> list[int]:
        """The b clusters whose centroids are closest to the query vector, best first."""
        sims = self.similarities(qvec[None, :])[0]
        return [int(c) for c in np.argsort(-sims, kind="stable")[:b]]

    def add(self, vecs: np.ndarray) -> np.ndarray:
        """Place new documents and fold them into their clusters' centroids (no re-clustering)."""
        x = _unit_rows(np.asarray(vecs, dtype=float))
        labels = (x @ self.centroids.T).argmax(axis=1)
        for row, c in zip(x, labels):
            self.sums[c] += row
            self.counts[c] += 1
        self.labels = np.concatenate([self.labels, labels])
        return labels

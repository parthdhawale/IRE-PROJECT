"""Routers: rank document groups for a query, fit on documents only.

All variants are extendible -- a new document is added by embedding/tokenising it and updating
its group, never by retraining on it:

- CentroidRouter (Rocchio / nearest centroid): a group is the mean of its training documents'
  L2-normalised embeddings; a query goes to the groups whose centroid has the highest cosine.
- NBRouter over band_vocab (nb_band): Luhn's "resolving power" band -- every word whose document
  frequency lies between a low and a high fraction of the training documents. Too-common words
  carry no topic, too-rare ones are document-specific; the middle band carries the topic.
  Label-free. Each group is then a Naive Bayes word distribution over the band.
- VocabLRRouter over band_vocab (band_lr): the same band, but texts become sublinear tf-idf
  vectors and a multinomial logistic regression maps them to groups.
"""

from __future__ import annotations

from collections import Counter
from typing import Callable

import bm25s
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB


def tokenize_words(texts: list[str]) -> list[list[str]]:
    """Lower-cased word tokens without English stopwords -- the same preprocessing BM25 uses."""
    return bm25s.tokenize(texts, lower=True, stopwords="en", return_ids=False, show_progress=False)


class CentroidRouter:
    def fit(self, doc_vecs: np.ndarray, labels: list[str]) -> "CentroidRouter":
        self.groups = sorted(set(labels))
        lab = np.array(labels)
        cent = np.stack([doc_vecs[lab == g].mean(axis=0) for g in self.groups])
        self.centroids = cent / np.linalg.norm(cent, axis=1, keepdims=True)
        return self

    def scores(self, query_vecs: np.ndarray) -> np.ndarray:
        """(n_queries, n_groups) cosine of each query to each group centroid."""
        return query_vecs @ self.centroids.T


def band_vocab(token_lists: list[list[str]], low: float, high: float) -> list[str]:
    """Words whose document frequency is between low and high (fractions of the documents)."""
    n = len(token_lists)
    df = Counter(w for t in token_lists for w in set(t))
    return sorted(w for w, d in df.items() if low * n <= d <= high * n)


def _identity(tokens: list[str]) -> list[str]:
    return tokens


VocabSelector = Callable[[list[list[str]], list[str]], list[str]]


def band_selector(low: float, high: float) -> VocabSelector:
    return lambda tokens, labels: band_vocab(tokens, low, high)  # label-free


def all_words_selector() -> VocabSelector:
    return lambda tokens, labels: sorted({w for t in tokens for w in t})


class NBRouter:
    """Multinomial Naive Bayes: each group is a word distribution P(w | group), estimated from
    the word counts of its training documents with additive (Laplace) smoothing alpha. A text
    is scored by log P(group) + sum_w count(w) * log P(w | group) -- "which group's word
    distribution best explains these words". Only words in the selected vocabulary count.
    Extendible: adding a document only adds its counts to its group's totals."""

    def __init__(self, select: VocabSelector, alpha: float):
        self.select, self.alpha = select, alpha

    def fit(self, token_lists: list[list[str]], labels: list[str]) -> "NBRouter":
        self.vocab = self.select(token_lists, labels)
        self.vec = CountVectorizer(analyzer=_identity, vocabulary=self.vocab)
        self.nb = MultinomialNB(alpha=self.alpha).fit(self.vec.transform(token_lists), labels)
        self.groups = list(self.nb.classes_)
        return self

    def scores(self, token_lists: list[list[str]]) -> np.ndarray:
        """(n_texts, n_groups) log posterior, columns in self.groups order."""
        return self.nb.predict_log_proba(self.vec.transform(token_lists))


class VocabLRRouter:
    """Same tf-idf + logistic regression for every variant; only `select` (the rule that picks
    the vocabulary from the training documents and their group labels) differs."""

    def __init__(self, select: VocabSelector, c: float, max_iter: int, seed: int):
        self.select, self.c, self.max_iter, self.seed = select, c, max_iter, seed

    def fit(self, token_lists: list[list[str]], labels: list[str]) -> "VocabLRRouter":
        self.vocab = self.select(token_lists, labels)
        self.vec = TfidfVectorizer(analyzer=_identity, vocabulary=self.vocab, sublinear_tf=True)
        x = self.vec.fit_transform(token_lists)  # idf from training documents only
        self.lr = LogisticRegression(C=self.c, max_iter=self.max_iter, class_weight="balanced",
                                     random_state=self.seed).fit(x, labels)
        self.groups = list(self.lr.classes_)
        return self

    def scores(self, token_lists: list[list[str]]) -> np.ndarray:
        """(n_queries, n_groups) class probabilities, columns in self.groups order."""
        return self.lr.predict_proba(self.vec.transform(token_lists))


def gold_rank(scores: np.ndarray, groups: list[str], gold: list[str]) -> np.ndarray:
    """1-based rank of each query's gold group (ties broken pessimistically)."""
    col = np.array([groups.index(g) if g in groups else -1 for g in gold])
    ranks = np.full(len(gold), len(groups) + 1)
    ok = col >= 0
    gold_score = scores[np.flatnonzero(ok), col[ok]]
    ranks[ok] = (scores[ok] >= gold_score[:, None]).sum(axis=1)
    return ranks

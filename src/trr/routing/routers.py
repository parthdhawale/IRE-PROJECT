"""Routers: rank document groups for a query, fit on documents only.

All variants are extendible -- a new document is added by embedding/tokenising it and updating
its group, never by retraining on it:

- CentroidRouter (Rocchio / nearest centroid): a group is the mean of its training documents'
  L2-normalised embeddings; a query goes to the groups whose centroid has the highest cosine.

Word-based routers pick a vocabulary from the training documents, by one of two rules:
  * band_vocab: Luhn's "resolving power" band -- every word whose document frequency lies
    between a low and a high fraction of the training documents. Too-common words carry no
    topic, too-rare ones are document-specific; the middle band carries the topic. Label-free.
  * discriminative_vocab: per group, the words with the highest p_in * log(p_in / p_out) on
    Laplace-smoothed document-frequency rates -- a supervised, information-gain style score.
  * concentrated_vocab: band words that also appear in several documents of one group and are
    concentrated in it (balanced purity) -- the band plus a group-specificity filter.
and then classify with one of two models:
- NBRouter (nb_band = band): each group is a Naive Bayes word distribution over the vocabulary.
  Fixes for its failure modes (results/notes/nb_band_failures.md): nb_band_bin (binary counts,
  alphabetic band) and cnb_band (Complement NB, alphabetic band).
- VocabLRRouter (band_lr = band, vocab_lr = discriminative, conc_lr = concentrated): sublinear
  tf-idf vectors and a multinomial logistic regression; variants differ only in the vocabulary rule.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Callable

import bm25s
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB, MultinomialNB


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


def discriminative_vocab(token_lists: list[list[str]], labels: list[str], per_group: int,
                         alpha: float) -> list[str]:
    """Union over groups of the per_group words with the highest p_in * log(p_in / p_out)."""
    n = len(token_lists)
    sets = [set(t) for t in token_lists]
    df_all = Counter(w for s in sets for w in s)
    vocab: set[str] = set()
    for g in set(labels):
        members = [s for s, lab in zip(sets, labels) if lab == g]
        n_in, n_out = len(members), n - len(members)
        df_in = Counter(w for s in members for w in s)
        scored = []
        for w, d_in in df_in.items():
            p_in = (d_in + alpha) / (n_in + 2 * alpha)
            p_out = (df_all[w] - d_in + alpha) / (n_out + 2 * alpha)
            if p_in > p_out:
                scored.append((p_in * math.log(p_in / p_out), w))
        vocab.update(w for _, w in sorted(scored, reverse=True)[:per_group])
    return sorted(vocab)


def band_vocab(token_lists: list[list[str]], low: float, high: float, alpha_only: bool = False) -> list[str]:
    """Words whose document frequency is between low and high (fractions of the documents).

    alpha_only drops tokens that are not purely alphabetic (numbers such as "01" or "1997",
    underscore runs from blank form fields), which pass the band but say nothing about the topic.
    """
    n = len(token_lists)
    df = Counter(w for t in token_lists for w in set(t))
    return sorted(w for w, d in df.items() if low * n <= d <= high * n and (not alpha_only or w.isalpha()))


def _identity(tokens: list[str]) -> list[str]:
    return tokens


def group_doc_freq(token_lists: list[list[str]], labels: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(words, counts, sizes): counts[g, j] = training documents of group g containing word j,
    sizes[g] = documents in group g. Groups in sorted order. Computed once, filtered many times."""
    groups = sorted(set(labels))
    vec = CountVectorizer(analyzer=_identity, binary=True)
    x = vec.fit_transform(token_lists)                                   # (docs, words) 0/1
    lab = np.array(labels)
    member = np.stack([lab == g for g in groups]).astype(np.float64)    # (groups, docs)
    counts = np.asarray((x.T @ member.T).T)                              # (groups, words)
    return vec.get_feature_names_out(), counts, member.sum(axis=1)


def concentrated_vocab(stats: tuple[np.ndarray, np.ndarray, np.ndarray], low: float, high: float,
                       min_in: int, purity: float) -> list[str]:
    """Band words that are also concentrated in one group. A word is kept if
      1. its document frequency is in [low, high] of all training documents (the band),
      2. it appears in >= min_in training documents of its best group (coverage: one-off
         names and typos seen in a single document are dropped), and
      3. its balanced purity >= purity, where balanced purity = the best group's share of the
         word's per-group document rates, rate_g = df_g / size_g. Rates rather than raw counts,
         so a large group does not look "pure" just by being large (chance level = 1 / groups).
    """
    words, counts, sizes = stats
    n, df = sizes.sum(), counts.sum(axis=0)
    rates = counts / sizes[:, None]
    pure = rates.max(axis=0) / rates.sum(axis=0)
    keep = (df >= low * n) & (df <= high * n) & (counts.max(axis=0) >= min_in) & (pure >= purity)
    return sorted(words[keep].tolist())


def concentrated_selector(low: float, high: float, min_in: int, purity: float) -> "VocabSelector":
    return lambda tokens, labels: concentrated_vocab(group_doc_freq(tokens, labels), low, high, min_in, purity)


VocabSelector = Callable[[list[list[str]], list[str]], list[str]]


def discriminative_selector(per_group: int, alpha: float) -> VocabSelector:
    return lambda tokens, labels: discriminative_vocab(tokens, labels, per_group, alpha)


def band_selector(low: float, high: float, alpha_only: bool = False) -> VocabSelector:
    return lambda tokens, labels: band_vocab(tokens, low, high, alpha_only)  # label-free


def all_words_selector() -> VocabSelector:
    return lambda tokens, labels: sorted({w for t in tokens for w in t})


class NBRouter:
    """Multinomial Naive Bayes: each group is a word distribution P(w | group), estimated from
    the word counts of its training documents with additive (Laplace) smoothing alpha. A text
    is scored by log P(group) + sum_w count(w) * log P(w | group) -- "which group's word
    distribution best explains these words". Only words in the selected vocabulary count.
    Extendible: adding a document only adds its counts to its group's totals.

    binary=True counts each word once per text (presence, not frequency), so one word repeated
    hundreds of times -- a party name like "bank" in an agency agreement -- cannot outvote the
    rest of the document. complement=True uses Complement Naive Bayes (Rennie et al. 2003):
    each group is scored against the word distribution of all OTHER groups, which is more
    stable when groups have very different sizes."""

    def __init__(self, select: VocabSelector, alpha: float, binary: bool = False, complement: bool = False):
        self.select, self.alpha, self.binary, self.complement = select, alpha, binary, complement

    def fit(self, token_lists: list[list[str]], labels: list[str]) -> "NBRouter":
        self.vocab = self.select(token_lists, labels)
        self.vec = CountVectorizer(analyzer=_identity, vocabulary=self.vocab, binary=self.binary)
        model = ComplementNB if self.complement else MultinomialNB
        self.nb = model(alpha=self.alpha).fit(self.vec.transform(token_lists), labels)
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

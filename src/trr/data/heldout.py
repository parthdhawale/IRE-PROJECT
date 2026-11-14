"""Held-out passage queries (E13): which case does this passage come from?

IR idea: known-item search with the item's own words removed. A passage of a case is the query
and that case is the one relevant document, but the passage is CUT OUT of the case before
indexing, so it cannot be found by matching its own text. The case must be recognised from what
the rest of it shares with the passage: party names, the judge, the facts, the statutes.

- One query per case, so a single index (every queried case missing its own passage) serves all
  queries, and no two queries are about the same case.
- The passage starts at a sentence start after the case's opening (`skip_frac`), which names the
  parties and the judge (the header shortcut seen on LegalBench, E10).
- Several query lengths share one start: the shorter queries are prefixes of the longest, and the
  longest span is the one cut, so one held-out index serves every length.
- Leak check: a court opinion can repeat its own sentences (a block quote restated later). A span
  with any `leak_window`-word sequence still present in the rest of its case is rejected and
  another position is tried.
- Offsets: the indexed text has the span removed; `to_original` maps offsets in it back to the
  original case text, so every hit is reported in original offsets.
"""

from __future__ import annotations

import re
from itertools import islice

import numpy as np

WORD = re.compile(r"\S+")
# end of a sentence: . ! or ? (optionally closing quotes / brackets), whitespace, then a capital or an opening mark
SENTENCE_END = re.compile(r"[.!?][\"')\]”’]*\s+(?=[A-Z\"(“])")
NORM_WORD = re.compile(r"\w+")


def sentence_start_after(text: str, pos: int) -> int:
    """Offset of the first sentence start at or after `pos`, or -1 if there is none."""
    m = SENTENCE_END.search(text, max(0, pos - 1))
    return m.end() if m else -1


def word_ends(text: str, start: int, n: int) -> list[int]:
    """End offsets of the first n whitespace-separated words from `start` (fewer if the text ends)."""
    return [m.end() for m in islice(WORD.finditer(text, start), n)]


def norm_words(text: str) -> list[str]:
    return NORM_WORD.findall(text.lower())


def leaked(span: str, rest: str, window: int) -> bool:
    """True if any `window`-word sequence of the span also occurs in the rest of the case."""
    s, r = norm_words(span), norm_words(rest)
    if len(s) < window:
        return " ".join(s) in " ".join(r)
    grams = {tuple(r[i:i + window]) for i in range(len(r) - window + 1)}
    return any(tuple(s[i:i + window]) in grams for i in range(len(s) - window + 1))


def cut(text: str, start: int, end: int) -> str:
    """The case text with [start, end) removed (what gets indexed)."""
    return text[:start] + text[end:]


def to_original(start: int, end: int, cut_span: tuple[int, int] | None) -> tuple[int, int]:
    """Map a [start, end) range of the held-out text back to the original text. A position at or
    after the cut point moves right by the cut's length (an end exactly at the cut point stays)."""
    if cut_span is None:
        return start, end
    a, b = cut_span
    return (start if start < a else start + (b - a)), (end if end <= a else end + (b - a))


def choose_span(text: str, rng: np.random.Generator, lengths: list[int], skip_frac: float,
                window: int, tries: int) -> tuple[int, list[int], int, int] | None:
    """(start, end offset per length, positions tried, leaks rejected), or None if no position works.

    A random position after the opening is moved to the next sentence start; the span is the
    longest length's words from there, and it must not leak (see `leaked`)."""
    lo, longest, leaks = int(skip_frac * len(text)), max(lengths), 0
    for attempt in range(1, tries + 1):
        start = sentence_start_after(text, int(rng.integers(lo, max(lo + 1, len(text)))))
        if start < 0:
            continue
        ends = word_ends(text, start, longest)
        if len(ends) < longest:
            continue
        span_end = ends[-1]
        if leaked(text[start:span_end], cut(text, start, span_end), window):
            leaks += 1
            continue
        return start, [ends[n - 1] for n in lengths], attempt, leaks
    return None

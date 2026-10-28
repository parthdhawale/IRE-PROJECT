from __future__ import annotations

import random

from trr.chunking.recursive import split_recursive


def _check(text: str, size: int) -> list[tuple[int, int]]:
    chunks = split_recursive(text, size)
    assert all(0 <= s < e <= len(text) and e - s <= size for s, e in chunks)
    assert all(a[1] <= b[0] for a, b in zip(chunks, chunks[1:]))  # sorted, non-overlapping
    # everything not covered is whitespace (only whitespace-only chunks are dropped)
    covered = set()
    for s, e in chunks:
        covered.update(range(s, e))
    assert all(text[i].isspace() for i in range(len(text)) if i not in covered)
    return chunks


def test_short_text_is_one_chunk() -> None:
    assert _check("hello world", 500) == [(0, 11)]


def test_prefers_paragraph_breaks() -> None:
    text = "a" * 300 + "\n\n" + "b" * 300
    assert _check(text, 500) == [(0, 302), (302, 602)]


def test_long_unbroken_text_falls_back_to_chars() -> None:
    chunks = _check("x" * 1200, 500)
    assert chunks == [(0, 500), (500, 1000), (1000, 1200)]


def test_random_texts_round_trip() -> None:
    rng = random.Random(0)
    words = ["term", "shall", "Party", "\n", "\n\n", "Section 4.2", "x" * 700]
    for _ in range(50):
        text = " ".join(rng.choice(words) for _ in range(rng.randint(1, 400)))
        _check(text, 500)

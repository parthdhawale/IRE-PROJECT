import random

import pytest

from trr.chunking.fixed import split_fixed


def _text(n_words: int, seed: int = 0) -> str:
    rng = random.Random(seed)
    return " ".join("".join(rng.choice("abcdefgh") for _ in range(rng.randint(1, 12))) for _ in range(n_words))


@pytest.mark.parametrize("size,overlap", [(50, 10), (500, 100), (80, 0)])
def test_windows_cover_the_text_overlap_and_never_cut_words(size, overlap):
    text = _text(2000)
    chunks = split_fixed(text, size, overlap)
    covered = set()
    for (s, e), (s2, _) in zip(chunks, chunks[1:] + [(len(text), None)]):
        assert 0 <= s < e <= len(text) and e - s <= size
        assert s == 0 or text[s - 1] == " "                    # starts at a word
        assert e == len(text) or text[e] == " "                 # ends before a space
        assert s2 <= e + 1 and e - s2 <= overlap                # no gap, overlap at most `overlap`
        covered.update(range(s, e))
    assert all(i in covered for i, c in enumerate(text) if c != " ")


def test_offsets_round_trip_and_short_text_is_one_chunk():
    text = "Plaintiff appeals. The court affirms."
    assert split_fixed(text, 500, 100) == [(0, len(text))]
    long = _text(300)
    assert all(long[s:e].strip() == long[s:e] for s, e in split_fixed(long, 60, 20))   # no edge spaces


def test_a_word_longer_than_the_window_is_cut_hard():
    text = "x" * 130
    assert split_fixed(text, 50, 10) == [(0, 50), (40, 90), (80, 130)]


def test_bad_overlap_is_refused():
    with pytest.raises(ValueError):
        split_fixed("abc", 10, 5)

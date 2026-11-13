"""Fixed-size chunks with overlap, with exact offsets (used for CLERC).

CLERC's case texts have no line breaks (one line per case), so splitting at paragraphs finds
nothing. A sliding window is the simplest unit that works for any text: windows of at most `size`
characters, each starting `overlap` characters before the previous one ended, so a sentence cut
at one window's edge is whole in the next. A window ends at the last space before its limit (when
one is in the second half of the window), so no word is cut and BM25 sees whole tokens. Chunks
are (start, end) ranges into the original text: nothing is copied or stripped.
"""

from __future__ import annotations


def split_fixed(text: str, size: int, overlap: int) -> list[tuple[int, int]]:
    """Overlapping windows over text; whitespace-only windows dropped."""
    if size <= 0 or not 0 <= overlap < size // 2:
        raise ValueError("need size > 0 and 0 <= overlap < size / 2")
    end, out, s = len(text), [], 0
    while s < end:
        e = min(s + size, end)
        if e < end:
            cut = text.rfind(" ", s + size // 2, e)     # end on a word boundary when one is near
            if cut != -1:
                e = cut
        if text[s:e].strip():
            out.append((s, e))
        if e >= end:
            break
        s_next = e - overlap                            # > s, because e - s >= size / 2 > overlap
        if text[s_next - 1] != " ":                     # mid-word: move on to the next word's start
            space = text.find(" ", s_next, e + 1)       # (e itself is a space unless the cut was hard)
            if space != -1:
                s_next = space + 1
        s = s_next
    return out

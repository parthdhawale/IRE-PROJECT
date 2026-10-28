"""Recursive character splitter with exact offsets (LegalBench-RAG baseline chunks).

Same idea as LangChain's RecursiveCharacterTextSplitter: split on the coarsest separator
(paragraph break, then line break, then space, then any character), greedily pack the pieces
into chunks of at most `size` characters, and recurse with the next separator only for pieces
that are still too long. Unlike LangChain we never copy or strip text: every chunk is a
(start, end) range into the original document, so hits map back exactly.
"""

from __future__ import annotations

SEPARATORS = ("\n\n", "\n", " ", "")


def _pieces(text: str, start: int, end: int, sep: str) -> list[tuple[int, int]]:
    """Split [start, end) after each occurrence of sep (the separator stays with the left piece)."""
    if sep == "":
        return [(i, i + 1) for i in range(start, end)]
    out, pos = [], start
    while pos < end:
        j = text.find(sep, pos, end)
        if j == -1:
            out.append((pos, end))
            break
        out.append((pos, j + len(sep)))
        pos = j + len(sep)
    return out


def _split(text: str, start: int, end: int, size: int, seps: tuple[str, ...]) -> list[tuple[int, int]]:
    if end - start <= size:
        return [(start, end)]
    sep, rest = seps[0], seps[1:]
    chunks: list[tuple[int, int]] = []
    cur_s = cur_e = None
    for s, e in _pieces(text, start, end, sep):
        if e - s > size:
            if cur_s is not None:
                chunks.append((cur_s, cur_e))
                cur_s = cur_e = None
            chunks.extend(_split(text, s, e, size, rest))
        elif cur_s is not None and e - cur_s <= size:
            cur_e = e
        else:
            if cur_s is not None:
                chunks.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    if cur_s is not None:
        chunks.append((cur_s, cur_e))
    return chunks


def split_recursive(text: str, size: int = 500, seps: tuple[str, ...] = SEPARATORS,
                    start: int = 0, end: int | None = None) -> list[tuple[int, int]]:
    """Contiguous, non-overlapping chunks of text[start:end]; whitespace-only chunks dropped."""
    end = len(text) if end is None else end
    return [(s, e) for s, e in _split(text, start, end, size, seps) if text[s:e].strip()]

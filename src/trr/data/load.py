"""LegalBench-RAG loader: corpus documents, benchmark queries, mini/full selection.

Expected layout under `raw`: `corpus/<subset>/*.txt` and `benchmarks/<subset>.json` (plan
Section 5.1). Every document is read in universal-newline mode so character offsets match
what the benchmark JSON's [start, end] spans assume (CRLF files would otherwise shift every
span after the first line break). File names are NFC-normalised so a path built from the
corpus listing always matches the same path referenced by a benchmark snippet.
"""

from __future__ import annotations

import json
import random
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SUBSETS = ("contractnli", "cuad", "maud", "privacy_qa")


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _canon(s: str) -> str:
    """Alphanumeric-only, lower-case key. Some LegalBench-RAG file names on disk have unsafe
    characters (%, :, |, ...) collapsed to '_' while the benchmark JSON keeps the original
    character; stripping all non-alphanumerics on both sides makes the two agree regardless of
    which characters got sanitised away."""
    return re.sub(r"[^a-z0-9]+", "", s.lower())


@dataclass(frozen=True)
class Document:
    doc_id: str   # path relative to corpus/, e.g. "cuad/LIMEENERGYCO_...txt"
    subset: str
    text: str     # universal-newline text


@dataclass(frozen=True)
class GoldSpan:
    doc_id: str
    start: int   # char offset in the original document text
    end: int     # exclusive
    answer: str | None = None   # the benchmark's recorded answer text, when given


@dataclass(frozen=True)
class Query:
    qid: str
    subset: str
    text: str
    gold: list[GoldSpan]

    @property
    def gold_docs(self) -> set[str]:
        return {g.doc_id for g in self.gold}


def read_document(path: Path) -> str:
    """Universal-newline read: \\r\\n -> \\n, matching the offsets used by the benchmark JSON."""
    return path.read_text(encoding="utf-8")


def _corpus_doc_ids(raw: str | Path, subset: str) -> list[str]:
    root = Path(raw) / "corpus" / subset
    return [_nfc(path.relative_to(root.parent).as_posix()) for path in sorted(root.rglob("*.txt"))]


def load_corpus(raw: str | Path, subset: str) -> list[Document]:
    root = Path(raw) / "corpus" / subset
    docs = []
    for path in sorted(root.rglob("*.txt")):
        doc_id = _nfc(path.relative_to(root.parent).as_posix())
        docs.append(Document(doc_id=doc_id, subset=subset, text=read_document(path)))
    return docs


def load_queries(raw: str | Path, subset: str, split: str, n_mini: int | None = None) -> list[Query]:
    """split='full' returns every test case; split='mini' returns the LegalBench-RAG-mini subset.

    Mini selection matches legalbenchrag/benchmark.py: each test gets a random key seeded on
    its first gold snippet's file_path, tests are sorted by that key, and the first `n_mini`
    are kept. This is deterministic (same seed every call) but independent of JSON order.
    """
    if split not in ("full", "mini"):
        raise ValueError(f"unknown split {split!r}, expected 'full' or 'mini'")
    bench = Path(raw) / "benchmarks" / f"{subset}.json"
    data = json.loads(bench.read_text(encoding="utf-8"))
    disk_ids = _corpus_doc_ids(raw, subset)
    disk_set = set(disk_ids)
    canon_to_disk = {_canon(d): d for d in disk_ids}

    def resolve(file_path: str) -> str:
        doc_id = _nfc(file_path)
        if doc_id in disk_set:
            return doc_id
        return canon_to_disk.get(_canon(doc_id), doc_id)

    queries, seeds = [], []
    for i, t in enumerate(data["tests"]):
        gold = [GoldSpan(doc_id=resolve(s["file_path"]), start=s["span"][0], end=s["span"][1],
                         answer=s.get("answer"))
                for s in t["snippets"]]
        queries.append(Query(qid=f"{subset}_{i}", subset=subset, text=t["query"], gold=gold))
        seeds.append(t["snippets"][0]["file_path"])  # raw JSON path, as benchmark.py seeds on
    if split == "full":
        return queries
    keyed = [(random.Random(s).random(), q) for s, q in zip(seeds, queries)]
    keyed.sort(key=lambda kv: kv[0])
    n = len(queries) if n_mini is None else n_mini
    return [q for _, q in keyed[:n]]


def load_subset(raw: str | Path, subset: str, split: str, n_mini: int | None = None
                ) -> tuple[list[Document], list[Query]]:
    """Convenience: the (docs, queries) pair a retriever needs for one subset."""
    return load_corpus(raw, subset), load_queries(raw, subset, split, n_mini)

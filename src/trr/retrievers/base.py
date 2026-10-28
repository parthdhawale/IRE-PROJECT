"""The one interface every retriever follows (plan Section 4.2).

A retriever returns character spans in the ORIGINAL documents, so a single evaluator can
score lexical, dense, hybrid and our template-residual method on equal terms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from trr.data.load import Document


@dataclass(frozen=True)
class Hit:
    doc_id: str      # path relative to corpus/, e.g. "cuad/LIMEENERGYCO_...txt"
    start: int       # char offset in the ORIGINAL document text
    end: int         # exclusive
    score: float


class Retriever(Protocol):
    name: str

    def index(self, docs: list[Document]) -> None: ...

    def retrieve(self, query: str, k: int, pool: str) -> list[Hit]:
        """pool = subset name; retrieval runs over that subset's documents only."""
        ...

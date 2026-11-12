"""Section-tree leaves as retrieval units (the section-tree baseline, plan Phase 2 Track B).

Same store as the 500-char chunk baselines, but the units are the leaves of the section tree
(data/cache/sections.parquet): a clause or sub-clause up to 1,500 chars, cut on headings instead
of at a fixed length. Comparing flat search over leaves with flat search over chunks isolates
the effect of the unit itself, so any later gain cannot be put down to chunking alone.

Leaves keep their original (start, end) offsets, so hits are scored exactly like chunk hits.
For embedding only, the leaf's breadcrumb (its parent headings) is prepended, so a sub-clause
such as "(b) ..." carries the context of the section it sits in; BM25 sees the leaf text alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from trr.config import config_hash
from trr.data.load import Document
from trr.retrievers.chunk_store import ChunkStore, SubsetChunks


@dataclass
class LeafStore(ChunkStore):
    sections: pd.DataFrame | None = field(default=None, repr=False)  # injectable for tests

    def _leaves(self, subset: str) -> pd.DataFrame:
        if self.sections is None:
            self.sections = pd.read_parquet(Path(self.cfg["paths"]["cache"]) / "sections.parquet")
        s = self.sections
        return s[s.is_leaf & (s.subset == subset)].sort_values(["doc_id", "start"])

    def add(self, docs: list[Document]) -> None:
        """Load the leaves of one subset (idempotent per subset)."""
        subset = docs[0].subset
        if subset in self.subsets:
            return
        by_id = {d.doc_id: d for d in docs}
        leaves = self._leaves(subset)
        leaves = leaves[leaves.doc_id.isin(by_id)]
        crumb_chars = self.cfg["leaf_store"]["breadcrumb_chars"]
        doc_ids, starts, ends, texts, embed_texts = [], [], [], [], []
        for r in leaves.itertuples():
            text = by_id[r.doc_id].text[r.start:r.end]
            if not text.strip():
                continue
            doc_ids.append(r.doc_id)
            starts.append(r.start)
            ends.append(r.end)
            texts.append(text)
            crumb = (r.breadcrumb or "")[:crumb_chars]
            embed_texts.append(f"{crumb}\n{text}" if crumb else text)
        rows: dict[str, list[int]] = {}
        for i, d in enumerate(doc_ids):
            rows.setdefault(d, []).append(i)
        self.subsets[subset] = SubsetChunks(
            doc_ids, np.array(starts), np.array(ends), texts,
            {d: np.array(r) for d, r in rows.items()}, embed_texts=embed_texts)
        self.docs[subset] = by_id

    def _emb_cache_path(self, subset: str) -> Path:
        key = config_hash({"model": self.embedder.model_name, "unit": "leaf",
                           "segmentation": self.cfg["segmentation"], "leaf_store": self.cfg["leaf_store"],
                           "n": len(self.subsets[subset].texts)})
        name = self.embedder.model_name.split("/")[-1]
        return Path(self.cfg["paths"]["cache"]) / f"leaf_emb_{subset}_{name}_{key}.npy"

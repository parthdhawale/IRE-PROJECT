"""Web of Science dataset (WOS-46985; Kowsari et al., HDLTex, ICMLA 2017).

46,985 paper abstracts, each labelled with a domain (7, e.g. Medical) and an area inside it (134,
e.g. Alzheimer's Disease). It is an external, non-legal two-level hierarchy -- the same shape as
our coarse (subset) / fine (CUAD contract type) levels, but with hundreds of documents per fine
class instead of a handful -- so it tests whether the routers can place unseen documents when
training data is not the bottleneck.

Files (from the Mendeley release, unzipped under `root`):
  <version>/X.txt    one abstract per line
  <version>/YL1.txt  domain id per line
  <version>/Y.txt    global area id per line (the standard fine label, 134 classes)
  Meta-data/Data.xlsx  the same rows with readable Domain / area names (used for names only)

A few area ids carry more than one area name in Data.xlsx (e.g. id 76 = "Anxiety" in Psychology
and "Bamboo as a Building Material" in Civil). The fine label is therefore the (domain, area id)
pair, named by its most frequent area name -- label noise we report, not repair.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from trr.data.load import Document


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _names(root: Path, cache: Path) -> dict:
    """{"domain": {id: name}, "area": {"<domain id>/<area id>": name}}, cached as JSON (the xlsx is slow)."""
    path = cache / "wos_names.json"
    if path.exists():
        return json.loads(path.read_text())
    meta = pd.read_excel(root / "Meta-data" / "Data.xlsx", usecols=["Y1", "Y", "Domain", "area"])
    meta["Domain"], meta["area"] = meta.Domain.astype(str).str.strip(), meta.area.astype(str).str.strip()
    names = {
        "domain": {str(k): v for k, v in meta.groupby("Y1").Domain.agg(lambda s: s.mode()[0]).items()},
        "area": {f"{a}/{b}": v for (a, b), v in meta.groupby(["Y1", "Y"]).area.agg(lambda s: s.mode()[0]).items()},
        "y1": meta.Y1.tolist(), "y": meta.Y.tolist(),
    }
    cache.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(names))
    return names


def load_wos(root: str | Path, version: str, cache: str | Path) -> tuple[list[Document], np.ndarray, np.ndarray]:
    """Documents (subset = domain name), and per document its domain and fine-area label."""
    root, cache = Path(root), Path(cache)
    texts = _read_lines(root / version / "X.txt")
    y1 = [int(v) for v in _read_lines(root / version / "YL1.txt")]
    y = [int(v) for v in _read_lines(root / version / "Y.txt")]
    if not len(texts) == len(y1) == len(y):
        raise ValueError(f"WOS files disagree in length: X={len(texts)} YL1={len(y1)} Y={len(y)}")
    names = _names(root, cache)
    if names["y1"][:len(y1)] != y1 or names["y"][:len(y)] != y:
        raise ValueError("Data.xlsx rows are not aligned with YL1.txt / Y.txt")
    domain = np.array([names["domain"][str(a)] for a in y1])
    area = np.array([f"{names['domain'][str(a)]}/{names['area'][f'{a}/{b}']}" for a, b in zip(y1, y)])
    docs = [Document(f"wos/{i:05d}", str(d), t.strip()) for i, (d, t) in enumerate(zip(domain, texts))]
    return docs, domain, area

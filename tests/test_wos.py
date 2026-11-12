"""Web of Science loader: line-aligned files, readable labels, (domain, area) fine label."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from trr.data.wos import load_wos


def write_wos(root: Path, y1: list[int], y: list[int], areas: list[str], domains: list[str]) -> None:
    (root / "V").mkdir(parents=True)
    (root / "Meta-data").mkdir()
    (root / "V" / "X.txt").write_text("\n".join(f"abstract {i} text" for i in range(len(y))))
    (root / "V" / "YL1.txt").write_text("\n".join(map(str, y1)))
    (root / "V" / "Y.txt").write_text("\n".join(map(str, y)))
    pd.DataFrame({"Y1": y1, "Y2": 0, "Y": y, "Domain": domains, "area": areas,
                  "keywords": "", "Abstract": ""}).to_excel(root / "Meta-data" / "Data.xlsx", index=False)


def test_load_wos_labels_and_shared_area_ids(tmp_path: Path) -> None:
    # area id 5 is used in two domains (as WOS id 76 is): it becomes two fine labels
    write_wos(tmp_path, y1=[0, 0, 1, 1], y=[3, 5, 5, 5],
              areas=["Vision", "Anxiety", "Bamboo ", "Bamboo"], domains=["CS ", "CS", "Civil", "Civil"])
    docs, domain, area = load_wos(tmp_path, "V", tmp_path / "cache")
    assert [d.doc_id for d in docs] == ["wos/00000", "wos/00001", "wos/00002", "wos/00003"]
    assert docs[2].text == "abstract 2 text" and docs[2].subset == "Civil"
    assert list(domain) == ["CS", "CS", "Civil", "Civil"]
    assert list(area) == ["CS/Vision", "CS/Anxiety", "Civil/Bamboo", "Civil/Bamboo"]
    assert (tmp_path / "cache" / "wos_names.json").exists()   # second load skips the xlsx


def test_load_wos_rejects_misaligned_files(tmp_path: Path) -> None:
    write_wos(tmp_path, y1=[0, 1], y=[3, 4], areas=["a", "b"], domains=["CS", "Civil"])
    (tmp_path / "V" / "Y.txt").write_text("3")
    with pytest.raises(ValueError):
        load_wos(tmp_path, "V", tmp_path / "cache")

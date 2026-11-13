"""End-to-end check of scripts/run_embed_pipeline.py on a tiny synthetic CLERC-style pool, with a
deterministic stand-in for the embedding model (hashed bag-of-words vectors)."""

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from trr.config import load_config
from trr.data import clerc
from trr.retrievers import chunk_store
from trr.routing.routers import tokenize_words

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_embed_pipeline.py"
TOPICS = {"tax": "taxpayer deduction revenue income assessment", "crime": "defendant sentence jury indictment verdict",
          "patent": "patent claim infringement invention prior"}


def _vec(text: str) -> np.ndarray:
    v = np.zeros(64)
    for w in tokenize_words([text])[0]:
        v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1
    return v / max(np.linalg.norm(v), 1e-12)


class FakeEmbedder:
    model_name = "fake/model"

    def __init__(self, cfg, model_name=None):
        pass

    def encode(self, texts, show_progress=False):
        return np.stack([_vec(t) for t in texts]).astype(np.float32)

    encode_queries = encode


def _pool(root: Path) -> None:
    cases, texts, queries = [], [], []
    for t, words in enumerate(TOPICS.values()):
        for j in range(4):
            case, name = 100 * (t + 1) + j, f"party{t}{j}"
            cases.append(case)
            texts.append(" ".join([f"The court considered {words}.", f"Plaintiff {name} appeals."] * 6))
            queries.append({"qid": f"q{case}", "text": f"{words} raised by {name}", "gold_case": case})
    side = clerc.split_by_gold([q["gold_case"] for q in queries], 0.25, 0)
    root.mkdir(parents=True)
    pd.DataFrame({"case_id": cases, "text": texts}).to_parquet(root / "docs.parquet")
    q = pd.DataFrame(queries)
    q["side"] = [side[g] for g in q.gold_case]
    q.to_parquet(root / "queries.parquet")


@pytest.fixture()
def script(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("run_embed_pipeline", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(clerc, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(chunk_store, "Embedder", FakeEmbedder)
    return mod


def test_clerc_dev_then_test_with_document_metrics(script, tmp_path):
    cfg = load_config()
    cfg["paths"].update(tables=str(tmp_path / "tables"), runs=str(tmp_path / "runs"), cache=str(tmp_path / "cache"))
    (tmp_path / "tables").mkdir()
    cfg["clerc"].update(root="pool", pool_docs=12, doc_list=10,
                        chunking={"method": "fixed", "chunk_chars": 120, "overlap": 20})
    cfg["embed_clusters"].update(sweep_k=[3], sweep_b=[1, 2], k=3, b=1, add_doc_trials=2)
    cfg["band_clusters"].update(kmeans_n_init=2)
    cfg["eval"]["bootstrap_resamples"] = 50
    _pool(tmp_path / "pool" / "pool_12")
    script.use_dataset(cfg, "clerc")
    docs, queries = script.load_data(cfg, None)

    script.stage_dev(cfg, docs, queries, "_clerc")
    sel = json.loads((tmp_path / "tables" / "embed_selected_clerc.json").read_text())
    assert sel["selected"]["k"] == 3 and sel["selected"]["doc_score"] in ("mean", "maxp")
    assert any((tmp_path / "cache").glob("chunk_emb_clerc_model_*.npy"))      # chunks embedded once, cached

    script.stage_test(cfg, docs, queries, "_clerc")
    df = pd.read_csv(tmp_path / "tables" / "embed_test_clerc.csv")
    assert {"emb_none_k3_" + sel["selected"]["doc_score"], "mixed_dense"} <= set(df.method)
    assert {"rdoc_recall@1", "rdoc_mrr", "rdoc_ndcg@10"} <= set(df.columns)
    md = (tmp_path / "tables" / "embed_test_clerc.md").read_text()
    assert "embed_doc_ms" in md and "cohesion" in md
    ci = pd.read_csv(tmp_path / "tables" / "embed_test_ci_clerc.csv")
    assert set(ci.metric) == set(cfg["band_clusters"]["ci_metrics"])

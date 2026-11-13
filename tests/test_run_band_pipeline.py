"""End-to-end check of scripts/run_band_pipeline.py on a tiny synthetic CLERC-style pool:
dev search -> selection file -> test run -> tables, with document-level metrics."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from trr.config import load_config
from trr.data import clerc

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_band_pipeline.py"
TOPICS = {"tax": "taxpayer deduction revenue income assessment", "crime": "defendant sentence jury indictment verdict",
          "patent": "patent claim infringement invention prior"}


def _pool(root: Path) -> None:
    cases, texts, queries = [], [], []
    for t, (topic, words) in enumerate(TOPICS.items()):
        for j in range(4):
            case, name = 100 * (t + 1) + j, f"party{t}{j}"
            cases.append(case)
            texts.append(" ".join([f"The court considered {words}." , f"Plaintiff {name} appeals.",
                                   f"{words} {words} discussed at length."] * 8))
            queries.append({"qid": f"q{case}", "text": f"{words} raised by {name} on appeal", "gold_case": case})
    side = clerc.split_by_gold([q["gold_case"] for q in queries], 0.25, 0)
    root.mkdir(parents=True)
    pd.DataFrame({"case_id": cases, "text": texts}).to_parquet(root / "docs.parquet")
    q = pd.DataFrame(queries)
    q["side"] = [side[g] for g in q.gold_case]
    q.to_parquet(root / "queries.parquet")


@pytest.fixture()
def script(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("run_band_pipeline", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(clerc, "REPO_ROOT", tmp_path)
    return mod


def test_clerc_dev_then_test_writes_tables_with_document_metrics(script, tmp_path):
    cfg = load_config()
    cfg["paths"].update(tables=str(tmp_path / "tables"), runs=str(tmp_path / "runs"))
    (tmp_path / "tables").mkdir()
    cfg["clerc"].update(root="pool", pool_docs=12, sweep_k=[3], doc_list=10,
                        chunking={"method": "fixed", "chunk_chars": 120, "overlap": 20})
    cfg["band_clusters"].update(sweep_min_df=[2], sweep_max_frac=[0.5], sweep_rare_below=[2], sweep_b=[1, 2],
                                k=3, b=1, min_df=2, max_frac=0.5, rare_below=2, kmeans_n_init=2, add_doc_trials=2)
    cfg["eval"]["bootstrap_resamples"] = 50
    _pool(tmp_path / "pool" / "pool_12")
    script.use_dataset(cfg, "clerc")
    docs, queries = script.load_data(cfg, None)
    assert len(docs) == 12 and len(queries["dev"]) + len(queries["test"]) == 12

    script.stage_dev(cfg, docs, queries, "_clerc")
    sel = json.loads((tmp_path / "tables" / "band_selected_clerc.json").read_text())
    assert sel["selected"]["k"] == 3 and sel["dataset"] == "clerc"

    script.stage_test(cfg, docs, queries, "_clerc", dense=False)
    df = pd.read_csv(tmp_path / "tables" / "band_test_clerc.csv")
    main = df[(df.method == df.method.iloc[0]) & (df.subset == "ALL") & (df.k == 1)].iloc[0]
    assert {"rdoc_recall@1", "rdoc_recall@10", "rdoc_mrr", "rdoc_ndcg@10"} <= set(df.columns)
    assert main["rdoc_recall@1"] == pytest.approx(main["doc_recall"])   # the top case = the hits' case
    assert not any("qonly" in m for m in df.method.unique())                   # no header on CLERC
    md = (tmp_path / "tables" / "band_test_clerc.md").read_text()
    assert "cohesion" in md and "NMI" not in md and "char_r" not in md
    ci = pd.read_csv(tmp_path / "tables" / "band_test_ci_clerc.csv")
    assert set(ci.metric) == set(cfg["clerc"]["ci_metrics"])

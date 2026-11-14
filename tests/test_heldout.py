"""E13 held-out passage queries: span choice, leak check, the cut and its offset map (original
offsets round-trip through the chunk store), the loader, and an end-to-end run of the band
pipeline script with the intact sanity control."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from trr.config import load_config
from trr.data import clerc
from trr.data.heldout import choose_span, cut, leaked, sentence_start_after, to_original, word_ends
from trr.data.load import Document
from trr.retrievers.chunk_store import ChunkStore

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
TOPICS = {"tax": "taxpayer deduction revenue income", "crime": "defendant sentence jury verdict",
          "patent": "patent claim infringement invention"}
LENGTHS, WINDOW = [5, 10, 20], 10


def _case(c: int, words: str, n: int = 40) -> str:
    """Sentences with two unique words each (so any 10-word window is unique within the case) and
    the party name repeated, which is what identifies the case once a passage is cut out."""
    return " ".join(f"Witness w{c}x{i} for party{c} said {words} near place p{c}x{i}." for i in range(n))


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sentence_starts_and_word_ends():
    text = "First one here. Second one follows! third is lower. Fourth."
    assert text[sentence_start_after(text, 3):].startswith("Second")
    assert text[sentence_start_after(text, 20):].startswith("Fourth")       # "third" is not a start
    assert sentence_start_after(text, 55) == -1
    s = sentence_start_after(text, 0)
    assert [text[s:e].split()[-1] for e in word_ends(text, s, 3)] == ["Second", "one", "follows!"]


def test_leak_check_finds_a_repeated_window_only():
    rest = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    assert leaked("x " + " ".join(rest.split()[:10]) + " y", rest, 10)
    assert not leaked("alpha beta gamma delta epsilon zeta eta theta iota QQ", rest, 10)
    assert leaked("Alpha, BETA gamma", rest, 10)            # shorter than the window: whole span, normalised


def test_span_is_a_sentence_start_after_the_opening_and_shorter_queries_are_prefixes():
    text = _case(7, TOPICS["tax"])
    rng = np.random.default_rng(0)
    for _ in range(20):
        start, ends, attempts, leaks = choose_span(text, rng, LENGTHS, 0.1, WINDOW, 5)
        assert start >= 0.1 * len(text) and text[start] == "W" and text[start - 2] == "."
        assert [len(text[start:e].split()) for e in ends] == LENGTHS
        assert ends == sorted(ends) and leaks == 0
    assert choose_span("Too short. Really.", rng, LENGTHS, 0.1, WINDOW, 3) is None


def test_a_span_that_repeats_in_its_case_is_rejected():
    text = " ".join(["The same sentence is repeated here in this case again and again."] * 30)
    assert choose_span(text, np.random.default_rng(0), LENGTHS, 0.1, WINDOW, 5) is None


@pytest.mark.parametrize("a,b", [(0, 5), (40, 90), (250, 400)])
def test_offset_map_round_trips_every_chunk_that_does_not_straddle_the_cut(a, b):
    text = _case(3, TOPICS["crime"], 12)
    held = cut(text, a, b)
    store = ChunkStore({"chunking": {"method": "fixed", "chunk_chars": 60, "overlap": 10}})
    store.add([Document("clerc/3", "clerc", held, cut=(a, b))])
    sc = store.subsets["clerc"]
    straddles = 0
    for s, e, t in zip(sc.starts, sc.ends, sc.texts):
        assert not (a <= s < b) and not (a < e <= b)     # no chunk starts or ends inside the removed span
        if s < a and e > b:      # a chunk joining text from both sides of the cut covers the hole
            straddles += 1
        else:
            assert text[s:e] == t                    # ORIGINAL offsets, same characters
    assert straddles <= 1
    assert to_original(10, 20, None) == (10, 20) and to_original(a, a, (a, b)) == (b, a)


def _heldout_pool(root: Path) -> None:
    cases, texts = [], []
    for t, words in enumerate(TOPICS.values()):
        for j in range(4):
            c = 100 * (t + 1) + j
            cases.append(c)
            texts.append(_case(c, words))
    root.mkdir(parents=True)
    pd.DataFrame({"case_id": cases, "text": texts}).to_parquet(root / "docs.parquet")


def _cfg(tmp_path):
    cfg = load_config()
    cfg["paths"].update(tables=str(tmp_path / "tables"), runs=str(tmp_path / "runs"))
    (tmp_path / "tables").mkdir()
    cfg["clerc"].update(root="pool", pool_docs=12, sweep_k=[3], doc_list=10, dev_share=0.25,
                        chunking={"method": "fixed", "chunk_chars": 120, "overlap": 20})
    cfg["clerc"]["heldout"].update(n_queries=12, lengths=LENGTHS, main_length=10, skip_frac=0.1,
                                   leak_window=WINDOW, tries=5)
    cfg["band_clusters"].update(sweep_min_df=[2], sweep_max_frac=[0.5], sweep_rare_below=[2], sweep_b=[1, 2],
                                k=3, b=1, min_df=2, max_frac=0.5, rare_below=2, kmeans_n_init=2, add_doc_trials=2)
    cfg["eval"]["bootstrap_resamples"] = 50
    return cfg


@pytest.fixture()
def built(tmp_path, monkeypatch):
    monkeypatch.setattr(clerc, "REPO_ROOT", tmp_path)
    cfg = _cfg(tmp_path)
    _heldout_pool(tmp_path / "pool" / "pool_12")
    builder = _load(SCRIPTS / "build_heldout_queries.py")
    q, meta = builder.build(cfg, pd.read_parquet(tmp_path / "pool" / "pool_12" / "docs.parquet"))
    clerc.heldout_dir(cfg).mkdir(parents=True)
    q.to_parquet(clerc.heldout_dir(cfg) / "queries.parquet", index=False)
    return cfg, q, meta


def test_builder_is_deterministic_and_splits_by_case(built, tmp_path):
    cfg, q, meta = built
    q2, _ = _load(SCRIPTS / "build_heldout_queries.py").build(
        cfg, pd.read_parquet(tmp_path / "pool" / "pool_12" / "docs.parquet"))
    pd.testing.assert_frame_equal(q, q2)
    assert meta["queries"] == 12 and q.case_id.is_unique and meta["dev"] == 3 and meta["cases_skipped"] == 0
    assert {f"end_{n}" for n in LENGTHS} <= set(q.columns)


def test_loader_cuts_the_longest_span_and_keeps_original_gold(built):
    cfg, q, _ = built
    original = dict(zip(*[pd.read_parquet(clerc.pool_dir(cfg) / "docs.parquet")[c] for c in ("case_id", "text")]))
    for length in LENGTHS:
        docs, queries, side = clerc.load_clerc_heldout(cfg, length)
        by_id = {d.doc_id: d for d in docs}
        for query in queries:
            case = int(query.gold[0].doc_id.split("/")[1])
            doc = by_id[query.gold[0].doc_id]
            assert query.text in original[case] and query.text not in doc.text      # held out
            assert len(query.text.split()) == length and query.gold[0].end == len(original[case])
            s, e = doc.cut
            assert doc.text == original[case][:s] + original[case][e:]
        assert set(side.values()) == {"dev", "test"}
    docs, queries, _ = clerc.load_clerc_heldout(cfg, 10, intact=True)
    assert all(d.cut is None for d in docs) and all(q.text in {d.doc_id: d for d in docs}[q.gold[0].doc_id].text
                                                     for q in queries)
    with pytest.raises(ValueError):
        clerc.load_clerc_heldout(cfg, 7)


def test_run_tags_select_once_and_label_each_length():
    from trr.eval.experiment import run_tags, use_dataset
    cfg = load_config()
    use_dataset(cfg, "clerc_heldout")
    assert run_tags(cfg, None) == (f"_clerc_heldout_q{cfg['clerc']['heldout']['main_length']}", "_clerc_heldout")
    use_dataset(cfg, "clerc_heldout", 25, intact=True)
    assert run_tags(cfg, 50) == ("_clerc_heldout_q25_intact_smoke50", "_clerc_heldout_smoke50")
    assert cfg["cache_variant"] == "intact"
    use_dataset(cfg, "clerc")
    assert run_tags(cfg, None) == ("_clerc", "_clerc")


def test_band_script_end_to_end_held_out_and_intact(built, tmp_path):
    cfg, _, _ = built
    script = _load(SCRIPTS / "run_band_pipeline.py")
    script.use_dataset(cfg, "clerc_heldout")
    docs, queries = script.load_data(cfg, None)
    script.stage_dev(cfg, docs, queries, "_clerc_heldout_q10", "_clerc_heldout")
    assert (tmp_path / "tables" / "band_selected_clerc_heldout.json").exists()
    for length, intact in [(10, False), (5, False), (10, True)]:
        script.use_dataset(cfg, "clerc_heldout", length, intact)
        tag, sel_tag = script.run_tags(cfg, None)
        docs, queries = script.load_data(cfg, None)
        script.stage_test(cfg, docs, queries, tag, sel_tag, dense=False)
        df = pd.read_csv(tmp_path / "tables" / f"band_test{tag}.csv")
        first = df[(df.method == "mixed_docfirst_bm25") & (df.subset == "ALL") & (df.k == 1)].iloc[0]
        if intact:     # sanity control: the passage is in the index, so full-query BM25 finds its case
            assert first["rdoc_recall@1"] == 1.0
        else:          # held out: the party name repeated elsewhere in the case still identifies it
            assert first["rdoc_recall@1"] >= 0.5
    runs = list((tmp_path / "runs").glob("*_test_clerc_heldout_q10_intact_clerc.jsonl"))
    assert runs and json.loads(runs[0].read_text().splitlines()[0])["_header"]

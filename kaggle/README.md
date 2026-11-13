# Running E11 on Kaggle

Heavy runs go to Kaggle; the local machine only builds the upload files and reads the results back.

## 1. Build the upload files (local, seconds)

Commit first: the code bundle is made from the last commit, so every result names the exact code.

    kaggle/make_bundle.sh

This writes:

- `dist/kaggle/trr_code.zip`: the committed code plus a `GIT_HASH` file. Re-upload it after every code change.
- `dist/kaggle/trr_data.zip`: the LegalBench-RAG corpus and benchmarks (~90 MB), the document MinHash
  signatures (they fix the folds, and so the dev/test split) and the routing document embeddings. Upload it once.

## 2. Upload (on kaggle.com)

1. **Datasets -> New Dataset**: upload `trr_data.zip`, name it `trr-data`, keep it **private**.
2. **Datasets -> New Dataset**: upload `trr_code.zip`, name it `trr-code`, **private**. For later code changes,
   use **New Version** on this dataset instead of a new one.
3. **Code -> New Notebook -> File -> Import Notebook**: `kaggle/e11_band_pipeline.ipynb`.
4. In the notebook's right panel:
   - **Add Input**: add both datasets.
   - **Accelerator**: GPU T4 x1. This is only needed for the dense baselines; without it the lexical part still runs.
   - **Internet**: on. It is needed for `pip install` and the embedding model.
5. **Save Version -> Save & Run All (Commit)**. The run continues with the browser closed.

## 3. What the notebook does

| step | what | expected time |
|---|---|---|
| checks | `pip install`, 89 unit tests, confirms the dev/test split is identical to `results/tables/query_split.csv` | ~3 min |
| smoke | the whole pipeline on 12 documents per subset | ~1 min |
| dev | the full grid on 1,403 dev queries: 24 clusterings x (9 band + 3 oracle) settings, plus 4 no-cluster settings | ~10-30 min |
| test | the selected and default settings and all baselines, scored once on 5,486 test queries; with GPU, also Parth's final method and dense doc-first (embeds ~207k chunks first) | ~30-90 min |
| package | zips the tables, per-query run files, logs and chunk embeddings | ~1 min |

Any failing step stops the notebook, and its log stays in `results/logs/`.

## 4. Bring the results back

Download `e11_outputs.zip` from the notebook's **Output** tab and unzip it in the repository root:

    unzip e11_outputs.zip -d .

It holds:

- `results/tables/band_dev.md`, `band_selected.json`, `band_test.md`, `band_test_ci.csv` and the smoke versions
- `results/runs/*_test_*.jsonl`: one line per query, with config and git hash. These are not committed.
- `results/logs/e11_*.log`
- `data/cache/chunk_emb_*.npy` (GPU run only): reused by the dense pipelines. Check them against a local re-embed
  of ~50 chunks (cosine >= 0.999) before relying on them.

# Running E11 (CLERC) on Kaggle

Heavy runs go to Kaggle; the local machine only builds the upload files and reads the results back.

## 1. Build the upload files (local, seconds)

Commit first: the code bundle is made from the last commit, so every result names the exact code.

    kaggle/make_bundle.sh

This writes `dist/kaggle/trr_code.zip`: the committed code plus a `GIT_HASH` file. Re-upload it after every
code change. No data is uploaded: the notebook downloads CLERC from Hugging Face (`jhu-clsp/CLERC`) itself.
LegalBench is not involved; its real-data unit tests skip themselves when its files are absent.

## 2. Upload

**With the Kaggle CLI** (token in `~/.kaggle/kaggle.json`; `pip install kaggle` in the venv):

    kaggle/push.sh datasets    # private dataset trr-code (a new version each time)
    kaggle/push.sh kernel      # pushes the notebook; Kaggle runs it (Save & Run All)
    .venv/bin/kaggle kernels status <user>/trr-e11-clerc
    .venv/bin/kaggle kernels output <user>/trr-e11-clerc -p dist/kaggle/output

**Or by hand (on kaggle.com):**

1. **Datasets -> New Dataset**: upload `trr_code.zip`, name it `trr-code`, keep it **private**. For later code
   changes, use **New Version** on this dataset.
2. **Code -> New Notebook -> File -> Import Notebook**: `kaggle/e11_clerc.ipynb`.
3. In the notebook's right panel:
   - **Add Input**: add the `trr-code` dataset.
   - **Accelerator**: None. The pipeline is lexical and runs on CPU.
   - **Internet**: on.
4. **Save Version -> Save & Run All (Commit)**. The run continues with the browser closed.

## 3. What the notebook does

| step | what | rough time |
|---|---|---|
| checks | `pip install`, the unit tests, > 20 GB free under `/tmp` | ~3 min |
| pool | downloads ~13 GB (training queries 4.1 GB, passage->case map 0.4 GB, case collection 8.2 GB), builds the 10k-case pool, the source-opinion check, and the dev / test split | ~30-60 min |
| smoke | the pipeline on 50 cases | ~2 min |
| dev | grid on the dev queries: 30 clusterings x (9 band + 3 oracle) settings, plus 4 without clusters | ~1-3 h |
| test | selected and default settings, the no-cluster and oracle ablations, flat BM25 and doc-first, scored once | ~30-60 min |
| package | tables, per-query runs, logs and the pool | ~2 min |

The times are estimates. Any failing step stops the notebook, and its log stays in `results/logs/`.

## 4. Bring the results back

Download `e11_clerc_outputs.zip` from the notebook's **Output** tab and unzip it in the repository root:

    unzip e11_clerc_outputs.zip -d .

It holds:

- `results/tables/band_dev_clerc.md`, `band_selected_clerc.json`, `band_test_clerc.md`, `band_test_ci_clerc.csv` and the smoke versions
- `results/runs/*_test_clerc_clerc.jsonl`: one line per query, with config and git hash. These are not committed.
- `results/logs/e11_clerc_*.log`
- `data/external/clerc/pool_10000/`: `docs.parquet`, `queries.parquet` and `pool.meta.json`. The pool is not
  committed and not redistributed, because the CLERC licence is unstated. Later runs can reuse it instead of
  downloading again.

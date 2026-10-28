# Handoff: H1 boilerplate analysis (for 30 Oct)

You own this piece end to end, including explaining it in the viva.

## Setup (once, on WSL2 Ubuntu)
```
git clone <repo> && cd ire-project
make setup          # venv + dependencies
make data           # downloads LegalBench-RAG, checks spans, writes corpus_stats.md
make test           # should pass
.venv/bin/python scripts/build_sections.py   # ~30 s, writes data/cache/sections.parquet
```

## What already exists
- `data/cache/sections.parquet`: one row per section-tree node; columns in `docs/artifacts.md`.
  Use rows with `is_leaf == True`. Each leaf has `start`, `end` (original char offsets) and a
  128-value MinHash signature in `minhash` (bytes of `np.uint64`).
- `src/trr/sketch/minhash.py`: `from_bytes`, `jaccard_estimate`, `build_lsh(keys, sigs, threshold, ...)`.
- `src/trr/segment/sections.py`: the parser. Samples in `results/notes/segmentation_samples.md`.
- Config: `h1.taus = [0.3, 0.5, 0.7, 0.9]`, `h1.go_tau = 0.5`, `h1.go_median_share = 0.25`.

## The task (plan page 6, Track A)
Write `src/trr/analysis/h1_boilerplate.py` + `scripts/run_h1.py`:
1. For each subset and each τ, build an LSH over all leaves of that subset
   (`build_lsh(section_ids, sigs, τ, num_perm=128, seed=0)`).
2. For each leaf, query the LSH; keep candidates from **other documents** whose
   `jaccard_estimate` ≥ τ (LSH candidates can be false positives). For CUAD also do it
   **within the same contract type** (`results/tables/cuad_types.csv`).
3. Boilerplate share of a document = chars in leaves with ≥ 1 near-duplicate / total leaf chars.
4. Outputs: box plot per subset × τ (`results/figures/F1_boilerplate_share.{png,pdf}`), table of
   medians (`results/tables/h1_boilerplate.md`), and the 10 most-shared leaves per subset with
   how many documents each appears in.
5. SHOULD: document-level Jaccard for 200 random same-subset pairs vs cross-subset pairs (histogram).
6. **Go/no-go:** GO if median share at τ = 0.5 ≥ 25 % on ContractNLI **and** on at least one of
   CUAD (within type) or MAUD. Write the decision + numbers in `results/notes/phase1.md`.

## Things to know
- MAUD has ~74k leaves and very long documents; LSH queries are fast, but avoid all-pairs loops.
- About 12% of MAUD leaves are tiny (table of contents, definitions). They hardly affect the
  char-weighted share, but mention it.
- PrivacyQA has only 7 documents and 4 of them use the paragraph fallback; treat its numbers
  as indicative only.

## Viva questions to be ready for
- Why does the share of agreeing MinHash slots estimate Jaccard without bias?
- How do LSH bands × rows set the similarity threshold (the S-curve)?
- Why 5-word shingles (3 for sections under 40 words)?

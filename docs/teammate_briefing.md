# TRR project: catch-up briefing (as of Wed 28 Oct 2026)

This is everything done so far, so you can pick up on 30 Oct without asking.
Mid-project report is due **Sat 31 Oct**. Your piece for 30 Oct is the **H1 boilerplate
analysis + go/no-go** (details in [`results/notes/handoff_h1.md`](../results/notes/handoff_h1.md)).

---

## 1. TL;DR

- Phase 0 (setup, data, sanity checks) and Phase 1 Track B (metrics, baselines, figures) are **done**.
- Track A has a head start: the **section tree parser** and **MinHash signatures** are built, so
  H1 only needs the LSH analysis on top.
- Baselines confirm the problem: on ContractNLI, flat retrieval picks a chunk from the **wrong
  NDA 62–73% of the time at top-1**.
- Surprise finding: a simple **doc-first** baseline (pick the document with BM25, then search
  inside it) nearly solves CUAD and MAUD. **ContractNLI is where TRR has to win.**
- 32 tests pass. Two commits so far (`b082ccf`, `5ce2295`). Not yet pushed to GitHub.

---

## 2. Who does what

| Track | Owner | Scope |
|---|---|---|
| **A: indexing** | you (mostly) | section tree, MinHash/LSH, H1, template families, slots, residual spans |
| **B: retrieval + eval** | Parth | metrics, chunker, baselines, harness, embeddings, figures |

- Track A writes files into `data/cache/`, Track B reads them. The column contract is in
  [`docs/artifacts.md`](artifacts.md). **Change a column only after we both agree**, and update that
  file in the same commit.
- Vivas are individual, so each of us must be able to explain our own code. Keep it simple.

---

## 3. Setup on your laptop (WSL2 Ubuntu)

```bash
git clone <repo-url> && cd ire-project
make setup      # creates .venv (Python 3.13) and installs everything
make data       # downloads LegalBench-RAG (~80M chars), checks every gold span, writes corpus_stats.md
make test       # 32 tests, should all pass
make sections   # ~30 s, writes data/cache/sections.parquet
```

- `data/` and `.venv/` are git-ignored, so you must run `make data` yourself.
- On your machine set `embedding.device: cpu` in `configs/default.yaml` (the Mac uses `mps`). You
  should not need embeddings for H1 at all.
- `make baselines` (embeds 207k chunks) took ~15 min on the M4 GPU; on CPU it will be much
  slower. You do **not** need to rerun it; the results are committed in `results/`.

---

## 4. Repo map

```
configs/default.yaml        every parameter (seed, k values, chunk size, BM25, RRF, segmentation, MinHash, H1)
src/trr/
  config.py                 load_config(), config_hash(), set_seeds(), git_hash()
  data/load.py              Document / GoldSpan / Query, load_corpus, load_queries (mini|full)
  data/sanity.py            checks every gold span maps back to the document text
  data/cuad_types.py        CUAD contract type from file name (25 types)
  chunking/recursive.py     500-char recursive splitter with exact offsets
  retrievers/base.py        Hit(doc_id, start, end, score) + Retriever protocol
  retrievers/chunk_store.py chunks, BM25 index, embeddings cache, FAISS
  retrievers/flat.py        bm25, dense, hybrid, oracle, docfirst
  eval/metrics.py           DRM@k, Doc-Recall@k, char P/R@k, bootstrap CI
  eval/run.py               runs a retriever on a subset, writes per-query JSONL
  segment/sections.py       section tree parser            <- Track A
  sketch/minhash.py         MinHash + LSH helpers           <- Track A
scripts/                    download_data, build_corpus_stats, run_baselines, plot_baselines, build_sections
tests/                      test_data, test_metrics, test_chunking, test_fusion, test_sections
results/tables, figures, notes   all outputs that go into the report
docs/                       plan.pdf, course_README.md, artifacts.md, this file
```

Rules we follow (also in `CLAUDE.md`): one config file, seed 0 everywhere, every output records
its config hash and git hash, offsets are always into the original document text.

---

## 5. Phase 0: data (done)

**Benchmark: LegalBench-RAG**, 4 subsets, 714 documents, 79.7M characters.

- Full set: 6,889 queries (the plan said 6,858; the real number is 6,889).
- **Mini set: 776 queries (194 per subset)**, selected exactly as the official
  `legalbenchrag/benchmark.py` does, so our numbers are comparable with the paper.
- The retrieval pool is always the **whole subset corpus**, not just the mini documents.
- Every gold span round-trips: `doc.text[start:end] == answer` for 100% of snippets.

Two bugs worth knowing (you may be asked "how did you verify the data?"):

1. **Newlines.** Files must be opened with Python's default universal newlines. With
   `newline=''`, 2,801 of 2,839 MAUD spans break because the offsets assume `\r\n` → `\n`.
2. **Unicode file names.** macOS returns file names in NFD (`LECLANCHÉ` decomposed), the JSON
   uses NFC, so 8 CUAD snippets looked like "missing document". Fixed by NFC-normalising
   `doc_id` on both sides (`normalize_doc_id`).

CUAD type labels: from the exhibit title in the file name, 25 regex categories. Only 1 document
ends up as "Other". Output: `results/tables/cuad_types.csv` (you need this for H1 within-type).

Outputs: `results/tables/corpus_stats.md`, `results/tables/cuad_types.csv`, `results/notes/phase0.md`.

---

## 6. Phase 1 Track B: metrics and baselines (done)

### Metrics (`eval/metrics.py`)
- **DRM@k** (our main metric): share of the top-k hits that come from a document that is *not*
  a gold document. 0 is perfect.
- **Doc-Recall@k**: did any top-k hit land in a gold document?
- **Char precision / recall@k**: character overlap between merged retrieved spans and gold spans
  (same as LegalBench-RAG).
- **Retrieved chars@k**, and a **paired bootstrap CI** (1000 resamples, seed 0) for comparing methods.

### Baselines (`retrievers/flat.py`), all on 500-char chunks
| name | what it does |
|---|---|
| bm25 | bm25s, k1 = 1.5, b = 0.75, English stopwords |
| dense | bge-small-en-v1.5, FAISS inner product, bge query prefix |
| hybrid | Reciprocal Rank Fusion of bm25 + dense (k = 60, depth 200) |
| oracle | dense search **only inside the gold document(s)**, upper bound for doc selection |
| docfirst | BM25 over whole documents, take top-1, then dense inside it |

### Results (mini, pool = full subset)

| DRM@8 | BM25 | dense | hybrid | doc-first | oracle |
|---|---|---|---|---|---|
| ContractNLI | .838 | .854 | .813 | .320 | 0 |
| CUAD | .300 | .265 | .262 | .005 | 0 |
| MAUD | .292 | .611 | .368 | .057 | 0 |
| PrivacyQA | .522 | .233 | .229 | .284 | 0 |

| char recall@64 | dense | hybrid | doc-first | oracle |
|---|---|---|---|---|
| ContractNLI | .366 | .431 | .680 | 1.000 |
| CUAD | .302 | .296 | .822 | .827 |
| MAUD | .072 | .064 | .363 | .392 |
| PrivacyQA | .631 | .603 | .682 | .962 |

Sanity checks passed: oracle DRM = 0 everywhere, oracle recall rises with k, and dense DRM@64 on
ContractNLI is 0.95, matching the SAC paper (>95% on NDAs).

### What it means
1. **DRM is real.** On ContractNLI, 62–73% of top-1 hits and 93–95% of top-64 are from the wrong NDA.
2. **Doc-first is a strong baseline where queries name the parties.** CUAD/MAUD queries spell out
   the agreement and both parties, so whole-document BM25 finds the right contract (99.5% on CUAD).
3. **ContractNLI is the hard case.** Doc-first still picks the wrong NDA 32% of the time, because
   NDAs share templates. **TRR must beat doc-first, not just hybrid**, and the main evidence will
   come from ContractNLI (plus MAUD, where absolute recall is still low).
4. Dense is much worse than BM25 on MAUD (DRM@8 .61 vs .29): merger agreements look the same to
   an embedding model; exact wording tells them apart. That supports the template-residual idea.

Outputs: `results/tables/baselines_mini.{csv,md}`, `results/figures/F2_drm_at_k_mini.*`,
`results/figures/F3_char_recall_oracle_mini.*`, per-query runs in `results/runs/` (git-ignored),
notes in `results/notes/phase1_trackB.md`.

---

## 7. Phase 1 Track A: what's already built for you

### Section tree (`segment/sections.py`)
- Detects headings with regexes: `ARTICLE`, `Section 1.2`, `1.`, `1.1.1`, `(a)`, `(iv)`, `(1)`,
  `IV.`, ALL-CAPS lines. Also catches headings that appear mid-line after 3+ spaces (MAUD has
  flattened text).
- Builds a tree with a stack: a heading of the same kind closes back to its sibling; ranked kinds
  (article > section > subsection) pop the stack; others nest as children.
- Leaves are the retrieval units: **max 1500 chars** (longer ones split on paragraph/sentence),
  leaves **under 100 chars merged** into a neighbour, and documents with **fewer than 3 headings fall
  back to paragraph splitting**.
- Leaves cover 100% of the non-whitespace text, with exact original offsets.

| | fallback rate |
|---|---|
| ContractNLI | 6.3% |
| CUAD | 6.5% |
| MAUD | 0.7% |
| PrivacyQA | 57% (4 of 7 docs) |

117,767 leaves in total; build takes ~27 s. ~12.5% of MAUD leaves are under 100 chars (table of
contents, short definitions). Samples you can eyeball: `results/notes/segmentation_samples.md`.

### MinHash (`sketch/minhash.py`)
- 128 permutations, seed 0, **5-word shingles** (3-word for sections under 40 words), via `datasketch`.
- Each leaf's signature is stored in `sections.parquet` column `minhash` (128 × uint64 as bytes).
- Helpers: `from_bytes`, `jaccard_estimate`, `build_lsh(keys, sigs, threshold, num_perm, seed)`.

---

## 8. Your task for 30 Oct: H1 + go/no-go

Full spec in [`results/notes/handoff_h1.md`](../results/notes/handoff_h1.md). Short version:

1. Write `src/trr/analysis/h1_boilerplate.py` and `scripts/run_h1.py`.
2. For each subset and τ ∈ {0.3, 0.5, 0.7, 0.9}: LSH over all leaves; a leaf is "boilerplate" if
   it has a near-duplicate (estimated Jaccard ≥ τ) in **another document**. For CUAD also do it
   **within the same contract type**.
3. Boilerplate share per document = boilerplate leaf chars / total leaf chars.
4. Outputs: F1 box plot (`results/figures/F1_boilerplate_share.*`), median table
   (`results/tables/h1_boilerplate.md`), top-10 most-shared leaves per subset.
5. **Decision rule:** GO if median share at τ = 0.5 is **≥ 25%** on ContractNLI **and** on at least
   one of CUAD (within type) or MAUD. Write it up in `results/notes/phase1.md`.

If it's NO-GO we need to talk the same day; the method story in the report depends on it.

---

## 9. Mid report (due 31 Oct)

Outline is on page 7 of `docs/plan.pdf`. Status:

| part | status | who |
|---|---|---|
| Problem + DRM definition | not started | Parth |
| Data + sanity checks | material ready (§5) | Parth |
| Baselines + F2/F3/T1 | material ready (§6) | Parth |
| H1 + F1 + go/no-go | your task, 30 Oct | you |
| Plan for Phases 2–4 | not started | both, 30–31 Oct |

---

## 10. Viva prep (things we should both be able to answer)

- Why does DRM matter more than recall alone here? (Wrong-document hits look relevant but are legally wrong.)
- Why is the oracle a useful upper bound, and why must DRM be 0 for it?
- Why does doc-first do so well on CUAD and so badly on ContractNLI?
- Why can't we open files with `newline=''`? Why NFC normalisation?
- Why does the share of agreeing MinHash slots estimate Jaccard without bias?
- How do LSH bands × rows set the threshold (S-curve)?
- Why 5-word shingles, and 3-word for short sections?

---

## 11. Open items

- [ ] GitHub repo: Parth is creating it; you'll get the URL to clone.
- [ ] H1 + go/no-go (you, 30 Oct).
- [ ] Mid report draft (both, 30–31 Oct).
- [ ] Later (Phase 2): SAC baseline, document-level Jaccard histogram (SHOULD in H1).

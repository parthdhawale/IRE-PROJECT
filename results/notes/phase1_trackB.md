# Phase 1, Track B: harness and baselines (Wed 28 Oct)

The H1 analysis and the go/no-go decision go in `phase1.md` (teammate, 30 Oct).

## What was built
- `eval/metrics.py`: DRM@k, Doc-Recall@k, char P/R@k, retrieved chars, paired bootstrap CI.
  Tested on toy cases (overlapping hits, several gold snippets, several gold documents).
- `chunking/recursive.py`: 500-char recursive splitter, no overlap, exact original offsets.
  The corpus gives 207k chunks (mean 385 chars).
- `retrievers/flat.py`: bm25 (bm25s, k1 = 1.5, b = 0.75, English stopwords), dense (bge-small,
  MPS, FAISS IndexFlatIP, bge query instruction), hybrid (RRF k = 60, depth 200), oracle (dense
  inside the gold document), docfirst (BM25 over whole documents → top-1 → dense inside it).
- `eval/run.py` + `scripts/run_baselines.py`: per-query JSONL in results/runs/, table
  `results/tables/baselines_mini.{csv,md}`. `scripts/plot_baselines.py`: F2, F3.
- Track A start: `segment/sections.py`, `sketch/minhash.py`, `scripts/build_sections.py` →
  `data/cache/sections.parquet` (117,767 leaves; 27 s). Samples in segmentation_samples.md.
- Cost: embedding all chunks with bge-small on the M4 took ~13 min (MAUD ~8 min).
  Query latency p50 is 0.1–3 ms for every method (single thread, warm).

## Numbers (mini, 194 queries per subset, pool = full subset)

| DRM@k | k | BM25 | dense | hybrid | doc-first | oracle |
|---|---|---|---|---|---|---|
| ContractNLI | 1 | .732 | .624 | .675 | .320 | 0 |
| ContractNLI | 8 | .838 | .854 | .813 | .320 | 0 |
| ContractNLI | 64 | .932 | .950 | .934 | .320 | 0 |
| CUAD | 8 | .300 | .265 | .262 | .005 | 0 |
| MAUD | 8 | .292 | .611 | .368 | .057 | 0 |
| PrivacyQA | 8 | .522 | .233 | .229 | .284 | 0 |

| char recall@64 | dense | hybrid | doc-first | oracle |
|---|---|---|---|---|
| ContractNLI | .366 | .431 | .680 | 1.000 |
| CUAD | .302 | .296 | .822 | .827 |
| MAUD | .072 | .064 | .363 | .392 |
| PrivacyQA | .631 | .603 | .682 | .962 |

## Exit check
- Metric tests pass (32 tests in total).
- Oracle DRM = 0 on every subset and k; oracle recall rises with k. ✔
- Dense DRM@64 on ContractNLI = 0.95, in line with the SAC paper (>95% on NDAs). ✔
- F2, F3, T1 exist. H1 and the go/no-go are still to do (30 Oct).

## Observations (for the mid report)
1. **DRM is real for flat retrieval.** On ContractNLI 62–73% of top-1 hits come from the
   wrong NDA, and 93–95% of top-64. The oracle gap in F3 shows what this costs: dense
   reaches 0.37 char recall@64 where the right document alone would give 1.0.
2. **Naming the document fixes most of it where queries name the parties.** Doc-first (whole-
   document BM25 → top-1) gets the right CUAD contract for 99.5% of queries and MAUD for
   94%, and its char recall is close to the oracle (CUAD .822 vs .827). CUAD/MAUD queries
   spell out the agreement and both parties, so lexical document matching wins.
3. **ContractNLI is the hard case.** Doc-first still picks the wrong NDA for 32% of queries,
   and recall@64 stays at .68 vs 1.0. NDAs share templates and the queries name the parties
   less distinctively. This is where template-residual retrieval has to show a gain.
4. Consequence for the method: TRR must beat **doc-first**, not only hybrid, and the main
   evidence will come from ContractNLI (plus MAUD, where doc-first leaves a 6% DRM gap and
   absolute recall is low because the documents are huge).
5. BM25's top-1 chunk on CUAD is in the right document but almost never the right passage
   (char recall@1 = 0.000). It matches the party names in the title block. This supports
   the plan's "identity card" (title + parties) idea for document selection, kept separate
   from chunk scoring.
6. Dense is clearly worse than BM25 on MAUD (DRM@8 .61 vs .29). Merger agreements are
   semantically near-identical, so embeddings cannot tell them apart; exact tokens can.

# Phase 2, Track B: section-tree baseline and group-first retrieval (Tue 3 Nov)

Branch `trackB-retrieval`. Mini benchmark (194 queries per subset). Tables:
`results/tables/baselines_mini.md` (section-tree rows) and `results/tables/group_first_mini.md`.

## What was built
- `retrievers/leaf_store.py`: section-tree leaves (data/cache/sections.parquet, 117,767 leaves,
  max 1,500 chars) as retrieval units, same store as the chunk baselines. Breadcrumb (parent
  headings, capped at 200 chars) prepended for embedding only. Methods `leaf_bm25`,
  `leaf_dense`, `leaf_hybrid`. Leaf embedding with bge-small on the M4 took about 25 min.
- `ChunkStore.merge`: one mixed pool of all 714 documents (206,869 chunks) reusing the cached
  per-subset embeddings. `ChunkStore.bm25_scores`: BM25 score of every chunk for one query.
- `retrievers/group_first.py`: `GroupRouter` (groups, routers from `trr.routing` fit on all
  documents, never on queries) + `GroupFirstRetriever`: top-B groups -> inner search only inside
  them. Inner: `dense`, `hybrid`, `docfirst` (pool-wide doc BM25 restricted to the groups),
  `docfirst_local` (doc BM25 built over the searched groups only). `router=none` = flat mixed
  pool baseline through the same code; `router=oracle` = gold group. `level=fine` (28 groups)
  or `coarse` (4 collections).
- `eval/run.py`: `pool` argument; per-query `diag` (chosen groups) in the run JSONL.
- Tests: `test_leaf_store.py` (offset round-trip, breadcrumb for embedding only, BM25 hit),
  `test_group_first.py` (beam restriction, no-routing = flat dense, oracle, local idf). 55 pass.

## Task 1: section-tree baseline (per-subset pools)

| DRM@8 | ContractNLI | CUAD | MAUD | PrivacyQA | mean |
|---|---|---|---|---|---|
| bm25 / leaf_bm25 | .838 / .816 | .300 / .298 | .292 / .254 | .522 / .470 | .488 / .459 |
| dense / leaf_dense | .854 / .840 | .265 / .290 | .608 / .656 | .233 / .258 | .490 / .511 |
| hybrid / leaf_hybrid | .813 / .806 | .262 / .264 | .368 / .396 | .229 / .284 | .418 / .438 |

| char recall@64 (chars retrieved) | chunks | leaves |
|---|---|---|
| bm25 | .256 (25.7k) | .435 (54.3k) |
| dense | .343 (25.8k) | .479 (64.1k) |
| hybrid | .349 (25.7k) | .493 (60.0k) |

- Changing the unit barely moves DRM (within about ±0.05, no consistent direction). Document
  confusion is not caused by fixed-length chunking.
- Leaves give much higher char recall, but they return 2-2.5x more text at the same k, so this is
  not a fair win. Compare at a matched character budget before claiming anything (plan H5).

## Task 2: group-first on one mixed pool of 714 documents

Every query searches all 714 documents, so a wrong collection can now be picked.

| DRM@8 | ContractNLI | CUAD | MAUD | PrivacyQA | mean |
|---|---|---|---|---|---|
| mixed_hybrid (flat) | .851 | .272 | .377 | .251 | .438 |
| mixed_docfirst (flat) | .325 | .052 | .052 | .294 | .181 |
| fine oracle + docfirst | .289 | .052 | .052 | .258 | .163 |
| fine nb_all B=3 + docfirst | .299 | .062 | .155 | .278 | .199 |
| coarse oracle + docfirst_local | .320 | .005 | .057 | .284 | .167 |
| **coarse centroid B=2 + docfirst_local** | **.294** | .041 | .062 | **.268** | **.166** |
| coarse nb_all B=2 + docfirst_local | .294 | .015 | .088 | .289 | .172 |
| separate pools, docfirst (Phase 1) | .320 | .005 | .057 | .284 | .167 |

Findings:
1. **Even perfect routing gains little.** Fine oracle routing improves doc-first by 0.018
   (mean DRM@8). The remaining errors are inside one group: one NDA confused with another NDA.
   Grouping cannot fix that, as expected after H1.
2. **Learned fine routing costs more than it gains on MAUD.** Merger questions are hard to route
   (centroid puts the gold group first for only 11% of MAUD queries; nb_all 76%), so MAUD
   DRM@8 rises from .052 to .155 even at B=3.
3. **Index statistics depend on what is indexed.** Doc-first on CUAD picks the right contract
   99.5% of the time with a CUAD-only index, 94.8% with the 714-document index, and 94.8% with a
   per-contract-type index. Mixed collections pollute idf; tiny groups make it noisy;
   collection level is best.
4. **Coarse routing with collection-local indexes recovers separate-pool quality inside a mixed
   pool** (mean .166 vs .167 for separate pools and .181 for flat doc-first). This is the
   honest positive result: routing lets one mixed collection behave like separately indexed
   collections. It does not reduce within-collection DRM.

## Open points for the report / next steps
- All settings were compared on mini (the test queries); freeze one configuration before the
  full run, and say so.
- Within-collection confusion (ContractNLI .29-.32) is the remaining problem; routing alone does
  not address it.
- Matched-budget comparison for leaves vs chunks (char recall at equal retrieved chars).

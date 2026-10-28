# Phase 0: setup, data, statistics (Wed 28 Oct)

## What was built
- Repo skeleton as in plan Section 4, `CLAUDE.md`, `configs/default.yaml`, `Makefile`,
  `docs/artifacts.md` (the Track A → Track B parquet contract).
- `make data`: downloads LegalBench-RAG from the Dropbox link in the official repo (skips if
  present), then runs the span sanity checks and writes `results/tables/corpus_stats.md`.
- `trr.data.load`: `Document`, `GoldSpan`, `Query`, `load_corpus`, `load_queries(split=mini|full)`.
  Mini selection is copied from `legalbenchrag/benchmark.py` (sort by a random key seeded on the
  first snippet's file path, keep 194). The retrieval pool is always the full subset corpus.
- `trr.retrievers.base`: the `Hit` / `Retriever` interface.
- `trr.data.cuad_types`: CUAD type from the exhibit title in the file name (evaluation only).
- 12 tests: toy round-trip with CRLF, bad-span detection, CUAD parsing, real-data round-trip
  and mini determinism for all four subsets.

## Numbers
- 714 documents, 79.7M characters, ~160k 500-char chunks.
- 6,889 queries full (the plan said 6,858; the files we downloaded have 6,889), 776 mini.
- 10,928 gold snippets; span round-trip 100% on every subset.
- Mini queries touch only 72 documents (CN 18, CUAD 29, MAUD 18, PQA 7), but the pool is the
  full subset, so DRM is measured against all look-alikes.
- CUAD: 25 types parsed; 1 file has no title in its name (`MSCIINC_02_28_2008-EX-10.10-.txt`) → Other.

## Surprises (worth a line in the mid report)
1. **Newlines matter.** Offsets assume universal-newline reading (`\r\n` → `\n`). Reading raw
   bytes breaks 2,801 of 2,839 MAUD spans. `read_document()` documents this.
2. **Unicode file names.** macOS returns NFD (`LECLANCHÉ` decomposed); the JSON is NFC. Without
   normalising ids, 8 CUAD snippets point at a "missing" document. All ids are NFC now.
3. **No query has more than one gold document.** So DRM@k = share of top-k hits outside the single
   gold document, and Doc-Recall@k is a hit/miss on one document.
4. **MAUD dominates size:** 66% of characters and 105k of 160k chunks, with documents up to
   1M characters. Dense embedding time is mostly MAUD.
5. Queries name the contract first ("Consider the Marketing Affiliate Agreement between Birch
   First Global Investments Inc. and Mount Knowledge Holdings Inc.; ..."). That supports the
   document "identity card" idea in plan Section 7.

## Next (Phase 1, Thu 29 Oct)
Track B first: `eval/metrics.py` + toy tests, 500-char chunker, BM25 / dense / hybrid / oracle
on mini, F2 + F3. Then Track A: `segment/sections.py`, `sketch/minhash.py` →
`data/cache/sections.parquet` so the H1 analysis can be handed off on 30 Oct.

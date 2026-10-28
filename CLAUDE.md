# Template–Residual Retrieval (TRR) — working rules
Goal: cut Document-Level Retrieval Mismatch (DRM) on LegalBench-RAG with a training-free
family -> document -> chunk retriever. Plan: docs/plan.pdf. Work one phase at a time.

Rules
- Every retriever returns Hit(doc_id, start, end, score) in ORIGINAL char offsets.
  Never evaluate on transformed text. Section/leaf objects always carry (start, end).
- All parameters live in configs/default.yaml. No magic numbers in code.
- Expensive steps cache to data/cache/ (parquet/npy/jsonl) keyed by a config hash;
  re-running a script must be fast if inputs are unchanged.
- Fixed seeds (numpy, random, torch). Log config + git hash with every run in results/runs/.
- Develop on the mini benchmark; run full only when a phase's exit check passes.
- Embeddings: sentence-transformers on device "mps", normalised, float16 on disk.
- Write a unit test for every metric and for span offset round-trips before using them.
- Keep modules small and readable: we must explain every line in a viva.
  Prefer clear numpy over clever tricks. Docstrings state the IR idea being used.
- After each phase: write results/notes/phaseN.md (what was built, numbers, surprises).
- Do not add training, fine-tuning, or per-document LLM calls to our method.
  (SAC is a baseline and is the only place an LLM is used.)

Project notes
- Environment: `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"` (Python >= 3.11).
  On Windows use WSL2 so `make` works.
- Data contract between Track A and Track B: docs/artifacts.md.
- Track A = indexing (segmentation, MinHash, families, slots, residuals, diff index).
  Track B = retrieval + evaluation (loader, metrics, baselines, codes, query path).

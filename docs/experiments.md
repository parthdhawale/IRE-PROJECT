# Experiments

Every experiment so far: the question it asked, how it was run, what it found and what we concluded.
Newest last. Design choices are explained in `docs/design_decisions.md` (D-numbers). The full
running record, with all files and side notes, stays in `results/notes/experiment_log.md`.

Numbers are on held-out documents unless stated. DRM = share of returned passages from a wrong
document (lower is better). "Real" = the document-level bootstrap CI excludes 0 (D17).

| # | experiment | verdict |
|---|---|---|
| E0 | Baselines and failure analysis on LegalBench-RAG | DRM is large for flat retrieval; doc-first is the bar |
| E1 | H1: is there reusable boilerplate? | NO-GO |
| E2 | Routing queries to groups | Works, but leans on the query header; parked |
| E3 | Placing new documents into groups | Coarse GO, fine NO-GO |
| E4 | Why Naive Bayes misses | Bursty repeated words |
| E5 | Why vocab_lr is noisy on small groups | One-off names and typos fill its vocabulary |
| E6 | Band-edge sweep on LegalBench | The band is not the bottleneck |
| E7 | Web of Science: data-limited or method-limited? | Data-limited: with enough data, word routers win |
| E8 | conc_lr (band + concentration filter) | Designed; main sweep not run |
| E9 | Band-edge sweep on Web of Science, confirmed on unseen folds | Floor of ~0.1% is better by 4-5 points (coarse) |
| E10 | Track B: group-first retrieval, header-only document choice | DRM@8 .161 -> .108, real but small |
| E11 | Band pipeline (our method) | Pre-registered, built, not yet run |

---

## E0. Baselines and failure analysis (Phase 0-1)

- **Question:** how big is DRM for standard retrieval, and what is the method up against?
- **Setup:** 714 documents, 6,889 queries (one gold document each); 500-character chunks; BM25, dense
  (bge-small), hybrid (RRF), oracle (dense inside the gold document) and doc-first (BM25 over whole
  documents -> top-1 -> dense inside it). Separate pool per collection.
- **Results (full benchmark, DRM@8 macro):** hybrid .437, doc-first .154, doc-first with the header only
  .070, oracle 0. On mini, ContractNLI DRM@64 for dense is .95 (matching the SAC paper's >95% on NDAs),
  and dense reaches .37 character recall@64 where the right document alone would give 1.0.
- **Failure analysis of doc-first (mini):** ContractNLI misses 62 of 194 queries, PrivacyQA 55. For 45 of
  the 62 NDA misses, a distinctive word from the query's "Consider ..." clause is absent from the gold
  document's text. None are explained by template siblings.
- **Conclusion:** DRM is real; picking the document first removes most of it; the method has to beat
  doc-first, not hybrid. ContractNLI is the hard case. Some NDA misses cannot be fixed lexically.
- **Files:** `results/notes/phase0.md`, `phase1_trackB.md`, `failure_analysis_docfirst.md`,
  `results/tables/baselines_full.md`, `corpus_stats.md`.

## E1. H1: is there reusable boilerplate?

- **Question:** do contracts share enough exact template text to separate the template from the
  document-specific part?
- **Setup:** MinHash (128 permutations, 5-word shingles) over clauses; GO if the median boilerplate share
  is >= 0.25 at Jaccard 0.5.
- **Result:** NO-GO. Only MAUD reuses template text. Shorter shingles looked better, but a spot check
  showed false matches on generic legal vocabulary.
- **Conclusion:** exact-text matching is too brittle. Course correction: group documents by word
  frequencies and retrieve within the group (D1, D24).
- **Files:** `results/notes/phase1.md`, `results/tables/h1_boilerplate.md`.

## E2. Routing queries to groups

- **Question:** can a query be sent to the right group?
- **Result (coarse top-1):** Naive Bayes on all words .880, Naive Bayes on the band .831 (ContractNLI
  .377), embedding centroid .789 (MAUD .152), band_lr .621, vocab_lr .530. Fine top-3: centroid .906.
- **Conclusion:** works, but queries are short and template-like ("Consider <document>; ..."). Without
  the header, fine top-3 falls to ~.15-.19 (E10). Parked in favour of placing documents.
- **Files:** `results/tables/routing.md`, `routing_qonly.md`, `results/notes/routing_gate.md`.

## E3. Placing new documents into groups

- **Question:** is an unseen document filed into the right group?
- **Setup:** 5 leak-safe document folds (D15); routers fit on training documents only. Coarse = 4
  collections (gate top-1 >= .95); fine = 25 CUAD types (gate top-3 >= .95).

| router | coarse top-1 | fine top-1 | fine top-3 |
|---|---|---|---|
| centroid | .992 | **.801** | **.929** |
| fused | .993 | .742 | .903 |
| vocab_lr | .986 | .671 | .861 |
| band_lr | **.994** | .630 | .838 |
| nb_band | .952 | .615 | .803 |
| nb_all | .948 | .535 | .740 |

- **Conclusion:** coarse solved (GO). Fine misses the gate (NO-GO); the embedding centroid is best and
  the word routers lag. End-to-end CUAD (coarse right and type in top-3): .920.
- **Files:** `results/tables/doc_grouping.md`, `results/notes/doc_grouping.md`.

## E4. Why Naive Bayes misses

- **Finding:** misses are driven by bursty words repeated hundreds of times in one document ("bank"
  x282, "google" x251, "iso" x362), by labels that do not match the content, and by junk tokens. 112 of
  178 fine misses are not shared with the centroid, so the two routers err differently.
- **Consequence:** sublinear term frequency in later designs (D35).
- **Files:** `results/notes/nb_band_failures.md`.

## E5. Why vocab_lr is noisy on small groups

- **Finding:** vocab_lr keeps the top 200 words per group with no minimum document count. For most CUAD
  types (8-32 training documents per fold) the bottom of the list is words seen in one document:
  company names, typos, ids. The fine level has ~117k weights for 369 training documents per fold.
- **Conclusion:** "only in this group" is not enough; a word also needs to recur. Led to conc_lr (E8).

## E6. Band-edge sweep on LegalBench (sensitivity only)

- **Question:** how much do results change with the frequency range of words the routers use?
- **Setup:** band_lr and nb_band, coarse and fine, 5 folds; 39 bands (floor 0-10%, ceiling 10-100%).
  The band in use (1%-50%) was fixed beforehand.
- **Results:** fine band_lr top-3 ranges .714-.840; ours .838. Capping the ceiling at 10% is worst
  everywhere; the floor barely matters for logistic regression (27k or 8k words give the same .838);
  Naive Bayes is more sensitive at both ends.
- **Conclusion:** our band is on the plateau; the band is not what holds back the fine level.
- **Files:** `results/tables/doc_band_sweep.md`.

## E7. Web of Science: data-limited or method-limited?

- **Question:** do the routers work when each class has hundreds of training documents (CUAD has 8-32)?
- **Setup:** 46,985 abstracts, 7 domains -> 134 areas; same routers, parameters and gates; 5 folds.

| router | coarse top-1 | fine top-1 | fine top-3 | end-to-end |
|---|---|---|---|---|
| vocab_lr | **.834** | **.819** | **.955** | **.803** |
| band_lr | .799 | .802 | .945 | .762 |
| nb_all | .752 | .687 | .872 | .663 |
| centroid | .698 | .679 | .880 | .616 |

- **Conclusion:** the ranking flips: with enough data the discriminative word routers beat embeddings.
  Supports "CUAD fine is data-starved". Caveat: domain and document length also changed; a clean test
  would subsample Web of Science to CUAD-like sizes (open item).
- **Files:** `results/notes/wos_grouping.md`, `results/tables/wos_grouping.md`.

## E8. conc_lr: band + concentration filter

- **Idea:** keep a word only if it is in the band, appears in at least m training documents of its best
  group, and is concentrated in that group (balanced purity >= p). Defaults m = 2, p = 1/3 fixed first.
- **Only result (LegalBench fine, 4-cell smoke test):** p = 1/3 shrinks the vocabulary 8,154 -> 2,567
  words and fine top-3 .838 -> .775. With few documents per type, the filter removed more useful shared
  words than noise.
- **Pending:** the Web of Science sweep.
- **Files:** `results/notes/conc_lr.md`, `scripts/sweep_conc.py`.

## E9. Band-edge sweep on Web of Science, confirmed on unseen folds

- **Question:** which frequency range is best on Web of Science, and is the gain real?
- **Method:** search all 39 bands on fold 0; confirm only the winner and 1%-50% on folds 1-4 (~37,600
  abstracts never used to pick).
- **Results (folds 1-4, top-1):** coarse band_lr .843 vs .800 (+4.3), coarse nb_band +5.0, fine band_lr
  +0.6, fine nb_band +2.2. Gains shrank by at most 0.6 points from search to confirmation.
- **Conclusion:** here the floor decides (a 1% floor = 375 abstracts leaves only ~1,900 words). A floor
  of ~0.1% wins. The confirmation shows the level of the plateau is real, not that one band is the
  unique optimum (the top 6-8 bands are within noise). Across both datasets: the floor should be a small
  absolute number of documents (D28, D34).
- **Files:** `results/tables/wos_band_sweep.md`, `wos_band_sweep_confirm.md`.

## E10. Track B (Parth): group-first retrieval, header-only document choice

- **Question:** does routing to a group and searching only there reduce DRM on one mixed pool?
- **Setup:** one mixed pool of 714 documents; route to the top-B groups; local document index;
  header-only document choice; document-level bootstrap. Full benchmark.
- **Results (DRM@8 macro):**

| comparison | difference | real? |
|---|---|---|
| doc-first vs hybrid (separate pools) | -.283 | yes |
| section leaves vs chunks | +.027 | yes (leaves worse) |
| header-only vs full-query doc-first | -.085 | yes (ContractNLI alone -.054, yes) |
| routing + local index vs flat doc-first (mixed pool) | -.017 | yes |
| final method vs flat doc-first (mixed pool): .161 -> .108 | -.053 | yes, CI [-.122, -.004] |
| final method vs routing alone | -.036 | no |

- **Findings:** even perfect routing barely helps (.181 -> .163): wrong-document errors happen inside a
  group, between look-alikes. Query routing depends on the header.
- **Caveats:** settings were chosen on mini, which is part of full; most of the macro gain is PrivacyQA
  (7 documents); the header is a property of the benchmark's question template.
- **Files:** `results/notes/phase2_trackB.md`, `phase3_full_run.md`, `results/tables/paired_ci_full.md`,
  `group_first_full.md`.

## E11. Band pipeline: band clusters -> band routing -> rare-in-cluster document (pre-registered)

- **Question:** can a purely word-frequency pipeline group documents, route a query to its group and
  pick the exact document, extendibly, and how does it compare with Track B's method?
- **Method:** mid band (words in >= 5 documents and <= 50%) -> sublinear tf-idf -> spherical k-means
  (k = 8) -> route the query to the top B = 2 clusters -> BM25 over the query's words that are rare
  (< 5 documents) inside those clusters picks one document -> BM25 ranks its passages. Details: D34-D47.
- **Data / split:** one mixed pool of 714 documents; dev 1,403 queries / 143 documents, test 5,486 / 571,
  split by gold document.
- **Dev search:** min_df {2, 5, 20} x max_frac {25%, 50%} x rare_below {2, 5, 10} x k {4, 8, 16, 32} x
  B {1, 2, 3}; selection = document recall@1 over dev queries.
- **Metrics:** document recall@1, DRM@1/8, nDCG@10, character recall, how often the right cluster is
  searched, fallback rate, latency, queries/s, cluster quality (NMI / ARI), time to add one document vs
  re-clustering; document-level CIs.
- **Expectation (written before running):** clusters cut the searched pool a lot and DRM only a little;
  the rare band is where DRM can fall, and it should hold without the header; some NDA misses are
  unfixable lexically; k-means clusters will be uneven.
- **Status:** built and unit-tested (89 tests pass); run script `scripts/run_band_pipeline.py`; passage
  scoring restricted to the chosen document (D47); Kaggle notebook and bundle ready (`kaggle/`). Not run.

---

## Planned
- Embedding-cluster pipeline; fused pipeline (confidence-weighted RRF per stage); comparison study
  against a trained bi-encoder and cross-encoder; hierarchical chunking.
- Bigger pools: LegalBench + EDGAR distractors, then CLERC 10k / 30k / 100k.
- conc_lr sweep on Web of Science; learning curve (subsample training documents per class).

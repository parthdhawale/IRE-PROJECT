# Experiment log -- what we ran and what we found

Running record for the final compiled report. One entry per experiment: question, setup, result,
conclusion, files. Newest entries at the bottom. Numbers are on held-out documents unless stated.

Project motto (since the H1 NO-GO): a scalable retriever that first groups like documents together
and then retrieves within the group. Only hard constraint: extendible -- a new document is placed
without retraining.

---

## E1. H1 boilerplate go/no-go (LegalBench-RAG)

- **Question:** do contracts share enough exact template text (boilerplate) to separate template from
  document-specific content?
- **Setup:** MinHash (128 perms, 5-word shingles) over clauses; gate = median boilerplate share >= 0.25
  at Jaccard 0.5 on ContractNLI and CUAD/MAUD.
- **Result:** NO-GO. Only MAUD reuses template text; shorter shingles looked better but a spot check
  showed false positives (shared generic legal vocabulary, not shared templates).
- **Conclusion:** exact-text matching is too brittle; moved to word-frequency based grouping.
- **Files:** `results/notes/phase1.md`, `results/tables/h1_boilerplate.md`.

## E2. Query routing (LegalBench-RAG, queries -> group)

- **Question:** can a query be sent to the right group?
- **Result (coarse top-1, 4 subsets):** nb_all 0.880, nb_band 0.831 (ContractNLI 0.377), centroid 0.789
  (MAUD 0.152), band_lr 0.621, vocab_lr 0.530 (MAUD 0). Fine top-3: centroid 0.906.
- **Conclusion:** queries are short and template-like ("Consider <doc>; ..."); parked -- current focus is
  placing documents, not queries.
- **Files:** `results/tables/routing.md`, `results/notes/routing_gate.md`.

## E3. Document placement (LegalBench-RAG, 714 documents)

- **Question:** is an unseen document filed into the right group?
- **Setup:** 5 document folds (StratifiedGroupKFold), near-duplicates (MinHash Jaccard >= 0.8) kept in
  one fold; everything fit on training documents only. Levels: coarse = 4 subsets (gate top-1 >= 0.95),
  fine = 25 CUAD contract types from file names (gate top-3 >= 0.95; gates set post hoc).
  Routers: centroid (bge-small, first 2,000 chars), nb_band / nb_all (Naive Bayes), band_lr (LR on band
  1%-50%), vocab_lr (LR on top-200 words per group by p_in*log(p_in/p_out)), fused (RRF centroid+nb_band).

| router | coarse top-1 | fine top-1 | fine top-3 |
|---|---|---|---|
| centroid | 0.992 | **0.801** | **0.929** |
| fused | 0.993 | 0.742 | 0.903 |
| vocab_lr | 0.986 | 0.671 | 0.861 |
| band_lr | **0.994** | 0.630 | 0.838 |
| nb_band | 0.952 | 0.615 | 0.803 |
| nb_all | 0.948 | 0.535 | 0.740 |

- **Conclusion:** coarse solved (GO). Fine NO-GO; the embedding centroid is best; word routers lag.
  End-to-end CUAD (coarse right AND type in top-3): 0.920.
- **Files:** `results/tables/doc_grouping.md`, `results/notes/doc_grouping.md`.

## E4. nb_band failure analysis (LegalBench-RAG)

- **Finding:** misses driven by bursty repeated words (`bank` x282, `google` x251, `iso` x362), label vs
  content mismatch, junk tokens; 112 of 178 fine misses not shared with the centroid.
- **Files:** `results/notes/nb_band_failures.md`.

## E5. Why vocab_lr is noisy on small groups (2026-11-12)

- **Question:** what is the effective cut-off for a word to enter vocab_lr's vocabulary?
- **Finding:** there is no fixed threshold -- it is "top 200 per group", so the cut-off score differs per
  group, and vocab_lr has no minimum document frequency. For most fine types (8-32 training documents
  per fold) the bottom of the 200 is words seen in ONE document of the group: company names
  (`linksynergy`, `purinix`), typos (`incluidng`), IDs (`87105110`), underscore junk. Same for small
  coarse groups (PrivacyQA, 6 training docs).
- **Conclusion:** "only in this group" is not enough; a word also needs coverage (several documents of
  the group). Led to conc_lr (E8). Fine level has 369 CUAD training docs per fold (462 x 4/5) and the
  LR has ~117k weights (25 x 4,691) -- heavily data-limited.

## E6. Band-edge sweep (LegalBench-RAG, sensitivity only)

- **Question:** how much do accuracy and other metrics change with the frequency range of the band?
- **Setup:** band_lr and nb_band, coarse and fine, all 5 folds. First 16 bands (low {0.5,1,2,5}% x high
  {25,50,75,100}%), then widened to 39 bands (low {0, 0.1, 0.2, 0.5, 1, 2, 5, 10}% x high
  {10, 25, 50, 75, 100}%, low < high). Metrics: acc@1/2/3, MRR, macro@1, vocab size, df range.
  The band used everywhere (1%-50%) was fixed beforehand and not changed.

| level / router | top-1 range | top-3 range | our band (top-1 / top-3) |
|---|---|---|---|
| fine / band_lr | 0.502 - 0.632 | 0.714 - 0.840 | 0.630 / 0.838 |
| fine / nb_band | 0.416 - 0.628 | 0.576 - 0.816 | 0.615 / 0.803 |
| coarse / band_lr | 0.957 - 0.996 | 1.000 | 0.994 / 1.000 |
| coarse / nb_band | 0.853 - 0.965 | 0.987 - 1.000 | 0.952 / 1.000 |

- **Findings:**
  1. The upper edge matters: capping at 10% is worst everywhere (fine band_lr top-3 0.71-0.76).
     Sweet spot ~25-75%; 100% (keeping "agreement", "shall") costs a little.
  2. The lower edge barely matters for LR: 27k words (all, singletons included) and 8k words (1% floor)
     both give 0.838 -- L2 regularisation makes rare words harmless.
  3. NB is more sensitive at both ends (0%-100%: 0.740 vs 1%-75%: 0.816).
  4. Our fixed band is on the plateau (best cell +0.002 for LR = 1 document; +0.013 for NB, within noise).
- **Conclusion:** the band is not the bottleneck of the fine level.
- **Files:** `results/tables/doc_band_sweep.md` (+ `.csv`), `scripts/sweep_doc_band.py`.

## E7. External dataset: Web of Science (WOS-46985)

- **Question:** do the routers work when each fine class has hundreds of training documents (CUAD has
  8-32)? I.e. is CUAD's fine level data-limited or method-limited?
- **Data:** 46,985 paper abstracts (~200 words), 7 domains -> 134 areas (137 domain/area labels; a few
  area ids carry two names -- label noise kept). ~365 abstracts per area (~290 training per fold).
  Source: Mendeley release of HDLTex (Kowsari et al. 2017), `data/external/wos/`.
- **Setup:** identical routers, parameters and gates; 5 folds stratified by area (no duplicate abstracts,
  so no near-duplicate grouping). coarse = 7 domains; fine = one classifier per domain over its areas
  (gold domain given, like CUAD); end-to-end = coarse top-1 right AND area in fine top-3.

| router | coarse top-1 | coarse top-2 / top-3 | fine top-1 | fine top-3 | end-to-end |
|---|---|---|---|---|---|
| **vocab_lr** | **0.834** | 0.961 / 0.985 | **0.819** | **0.955** | **0.803** |
| band_lr | 0.799 | 0.947 / 0.980 | 0.802 | 0.945 | 0.762 |
| nb_all | 0.752 | 0.929 / 0.969 | 0.687 | 0.872 | 0.663 |
| nb_band | 0.702 | 0.905 / 0.955 | 0.678 | 0.868 | 0.618 |
| fused | 0.701 | 0.915 / 0.965 | 0.685 | 0.889 | 0.627 |
| centroid | 0.698 | 0.912 / 0.967 | 0.679 | 0.880 | 0.616 |

(95% CIs about +-0.003.)

- **Findings:**
  1. The ranking flips vs CUAD: with enough data per class the discriminative word models win
     (vocab_lr fine top-3 0.955 vs centroid 0.880; on CUAD centroid 0.929 vs vocab_lr 0.861).
     Supports "CUAD fine is data-starved for LR". Caveat: domain and document length also changed --
     a clean test subsamples WOS to CUAD-like sizes (~10 per area).
  2. Group-specific vocabulary (vocab_lr) beats the label-free band (band_lr) by 1-2 points at both levels.
  3. Coarse is harder than on LegalBench (domains overlap: Medical/Psychology/Biochemistry, CS/ECE);
     Medical top-1 0.786 but top-2 0.969 -> routing to the top-2 domains is nearly lossless.
  4. NB is 13-14 points behind LR at the fine level (burstiness again); fusion does not help here.
  5. Hardest areas are Medical, mostly mental-health topics: Schizophrenia (38 docs) 0.45, Depression
     0.62, Rheumatoid Arthritis 0.81 (vocab_lr top-3). Easiest domain: Civil (0.995).
- **Files:** `results/notes/wos_grouping.md`, `results/tables/wos_grouping.md`,
  `results/runs/wos_grouping.jsonl`, `scripts/run_wos_grouping.py`, `src/trr/data/wos.py`.

## E8. conc_lr: band + group-concentration filter (designed; WOS sweep NOT yet run)

- **Idea (from the discussion of E5):** keep a word only if (1) its df is in the band, (2) it appears in
  >= m training documents of its best group (coverage), (3) its balanced purity >= p
  (purity = best group's share of the per-group document rates df_g/size_g; chance = 1/K).
- **Pre-registered defaults:** m = 2 (smallest evidence of recurrence; drops one-off names/typos),
  p = 1/3 ("in at most ~3 groups", matches the top-3 gate), band low = 0 (a 1% floor of a large pool
  drops words frequent inside one small group), high = 50%. Reasoning: `results/notes/conc_lr.md`.
  Sweep grid: m {1,2,3,5,10} x p {0, 0.2, 0.33, 0.5, 0.7, 0.9} x low {0, 1%}.
- **Only result so far (LegalBench fine, 4-cell smoke test, after defaults were fixed):**
  m=1/p=0 reproduces band_lr exactly (0.630 / 0.838); p = 0.33 cuts vocabulary 8,154 -> 2,567 words,
  words per held-out document 655 -> 44, and top-3 0.838 -> 0.775 (m=2: 0.779). With few documents per
  type, purity filtering removed more useful shared words than noise.
- **Pending:** the WOS conc_lr sweep (`python scripts/sweep_conc.py --dataset wos`) and the WOS band
  sweep (`python scripts/sweep_doc_band.py --dataset wos`); both score fold 0 only (~9,400 held-out
  abstracts, SE ~0.005) -- `wos.sweep_folds` in the config.
- **Files:** `src/trr/routing/routers.py` (`group_doc_freq`, `concentrated_vocab`), `scripts/sweep_conc.py`.

## E9. Band-edge sweep on Web of Science, with an unbiased confirmation (2026-11-12)

- **Question:** which frequency range is best on WOS, and how much does it really gain over 1%-50%?
- **Method (validation / test split, to avoid the winner's curse):**
  1. *Search* -- all 39 bands x band_lr, nb_band x coarse, fine, scored on fold 0 only (~9,400 held-out
     abstracts). Winner per router and level = highest MRR.
  2. *Confirm* -- only the winners and 1%-50%, scored on folds 1-4 (~37,600 abstracts never used to pick).
- **Search finding:** opposite of LegalBench -- the LOWER edge decides, the upper barely matters.
  coarse band_lr top-1 by floor: 0 -> 0.843, 0.1% -> 0.846, 0.5% -> 0.835, 1% -> 0.796, 2% -> 0.759,
  5% -> 0.634, 10% -> 0.523. The 1% floor = 375 training abstracts, leaving only ~1,900 words; the upper
  edge changes the vocabulary by ~100 words (short abstracts, stopwords already removed).
- **Confirmation (folds 1-4):**

| level / router | best band (picked on fold 0) | top-1 / top-3 / MRR (folds 1-4) | 1%-50% (folds 1-4) | gain top-1 (fold 0 -> folds 1-4) |
|---|---|---|---|---|
| coarse / band_lr | 0.1%-25% | 0.843 / 0.987 / 0.914 | 0.800 / 0.979 / 0.889 | +4.9 -> **+4.3** |
| coarse / nb_band | 0%-10% | 0.752 / 0.969 / 0.861 | 0.702 / 0.954 / 0.829 | +5.3 -> **+5.0** |
| fine / band_lr | 0.1%-25% | 0.808 / 0.951 / 0.882 | 0.802 / 0.945 / 0.877 | +0.7 -> **+0.6** |
| fine / nb_band | 0.1%-25% | 0.700 / 0.886 / 0.802 | 0.678 / 0.868 / 0.784 | +2.2 -> **+2.2** |

- **Conclusion:** the gains hold on unseen folds (shrinking by at most 0.6 points), so they are real, not
  luck. Best WOS range: a floor of ~0.1% (12-38 training documents) with any upper edge >= 25%;
  0.1%-25% is best or tied-best in 3 of 4 cases. Biggest effect at the coarse level (+4-5 points).
  No significance test was run on the differences (per-document results of the sweep are not stored);
  +4-5 points on 37,600 paired abstracts is far outside noise, +0.6 (fine band_lr) is small.
- **What the confirmation does NOT show:** that 0.1%-25% is the optimal band. Only the winner and
  1%-50% were scored on folds 1-4. On fold 0 the top 6-8 bands differ by 0.001-0.004 MRR (SE ~0.005):
  a plateau (floor 0-0.2%, any upper edge; for coarse nb_band the 0%-floor bands), with the winner only
  nominally on top. The confirmed claim is the *level* of that plateau versus the 1% floor, not a
  unique optimum. Checking the curve's shape on unseen data would need the floors re-scored on folds 1-4
  (not run).
- **Across both datasets:** a floor should be a small absolute number of documents, not a fixed share.
  LegalBench: lower edge irrelevant between 0 and 2%, best upper 25-75%. WOS: floor ~0.1%, upper edge
  irrelevant. A single band of **0.1%-50%** is within noise of the best on both (LegalBench fine band_lr
  top-3 0.838 = fixed, coarse 0.990 vs 0.994; WOS fold 0 coarse 0.845, fine 0.811) -- a recommendation
  read off the tables, not separately confirmed on LegalBench.
- **Files:** `results/tables/wos_band_sweep.md` (+ `.csv`), `results/tables/wos_band_sweep_confirm.md`
  (+ `.csv`), `scripts/sweep_doc_band.py` (`--bands`, `--folds`).

---

## E10. Track B (Parth, merged 2026-11-12): group-first retrieval, header-only document choice

Summary of the merged branch `trackB-header-docsel` (merge commit `b7df2ad`); details in his notes.

- **Built:** section-leaf retrieval units (`leaf_store.py`); one mixed pool of all 714 documents;
  group-first retriever (route to top-B groups, search only there; `none` = flat, `oracle` = gold group);
  collection-local document BM25 indexes; header-only document choice (`query_split.py`, split at the first
  ";") and RRF of header-only and full-query document rankings; document-level paired bootstrap
  (`paired_cluster_bootstrap_macro_ci`).
- **Results (full benchmark, DRM@8 macro, document-level CIs):** doc-first vs hybrid -0.283 (real);
  leaves vs chunks +0.027 (leaves slightly worse, real); routing + local index vs flat doc-first on the
  mixed pool -0.017 (real, small); header-only vs doc-first -0.085 (real; ContractNLI alone -0.054, real);
  final method (centroid_full coarse B=2 + local index + header/full RRF) vs flat doc-first .161 -> .108
  (CI [-.122, -.004], real); final vs routing alone -0.036 (not real).
- **Findings:** even oracle fine routing barely helps (.181 -> .163): wrong-document errors are inside a
  group. Fine query routing depends on the benchmark header (question only: top-3 .906 -> ~.15-.19).
  Whole-document centroid routes MAUD queries far better (.152 -> .748) but places new documents worse.
- **Caveats:** settings chosen on mini, which is part of full (PrivacyQA mini = full), so full is not an
  independent confirmation; most macro gain is PrivacyQA (7 documents); the header is a property of the
  benchmark's query template.
- **Files:** `results/notes/phase2_trackB.md`, `phase2_task3_routing.md`, `phase2_task4_header_docsel.md`,
  `phase3_full_run.md`; `results/tables/paired_ci_full.md`, `group_first_full.md`, `baselines_full.md`.

## E11. Band pipeline: band clusters -> band routing -> rare-in-cluster document (PRE-REGISTERED)

Written 2026-11-12 before any result. Defaults in `configs/default.yaml` (`band_clusters`), not changed
by the dev search.

- **Question:** can a purely word-frequency pipeline group documents, route a query to its group and pick
  the exact document, extendibly (no retraining for new documents) -- and how does it compare with the
  embedding pipeline and a fused one (later entries)?
- **Idea:** two bands of document frequency with two jobs. The **mid band** (df >= 5 documents and
  <= 50% of documents) says *what kind* of document: it builds the clusters and routes the query. The
  **rare band** (query words in < 5 documents *of the chosen cluster*) says *which* document: party names,
  products, amounts. "Confidential" is in every NDA, so it cannot pick an NDA; a name in one NDA can.
  The floor is an absolute count because a share grows with the pool and drops topic words (E6, E9).
- **Method:**
  1. Index: sublinear tf-idf over the mid band, L2-normalised; spherical k-means (k = 8 default,
     10 restarts); each cluster named by its top centroid words. A new document joins its nearest
     centroid and updates the mean (O(1), no re-clustering).
  2. Route: query mid-band vector, cosine to the centroids, top B = 2 clusters.
  3. Document: BM25 over the query's rare-in-cluster words, idf inside the searched clusters (Parth's
     local index); fallback to full-query BM25 when the query has no rare word.
  4. Passage: BM25 inside the chosen document (fully lexical, no embedding model); dense passages later
     (needs chunk embeddings, Kaggle). Stage 4 is the same for all compared pipelines.
- **Data / split:** LegalBench-RAG, one mixed pool of 714 documents, all 6,889 queries. Dev / test split
  by gold document = leak-safe routing fold 0 (`eval.dev_folds`, `trr/eval/splits.py`): dev 1,403 queries
  / 143 documents, test 5,486 / 571 (PrivacyQA has 1 dev document). Clusters are built from all documents
  (an index, never queries).
- **Dev search:** min_df {2, 5, 20} x max_frac {25%, 50%} x rare_below {2, 5, 10} x k {4, 8, 16, 32} x
  B {1, 2, 3}; selection = document recall@1 over all dev queries (query-weighted, because of PrivacyQA's
  single dev document); ties -> smaller k, then smaller B. Test scored once with the selected setting and
  with the defaults.
- **Metrics:** cluster NMI / ARI vs subsets and vs CUAD types; routing (gold document in the top-B
  clusters); document recall@1, DRM@1/8, char precision / recall@k; latency per query, index build time,
  time to add one document. Full queries and question-only (header removed). Document-level bootstrap.
- **Baselines:** flat BM25, flat doc-first, Parth's final method, oracle routing (gold document's cluster).
- **Expectation:** clusters cut the searched pool a lot and DRM only a little (errors are inside a topic,
  E10); the rare band is where DRM can fall, and it should hold without the header where the header trick
  cannot. Some NDA misses are unfixable lexically (party name absent from the document text). k-means will
  be lopsided (462 CUAD vs 7 PrivacyQA documents).
- **Implementation details fixed while building (before any result):** rarity and idf are counted over
  the union of the B searched clusters; a query with no mid-band word is routed to every cluster (no
  evidence of its kind -> flat search); passage BM25 uses chunk idf over the whole pool; document ties
  go to the first document in corpus order. Routers: `band`, `none` (all clusters = rare-band doc-first
  without clustering, the ablation) and `oracle` (gold document's cluster).
- **Added before any result (2026-11-13), reporting only, not used for selection:** span-level nDCG@10
  (a hit gains 1 when it reaches a gold snippet not reached before; `eval.ks` now includes 10); a lexical
  flat doc-first baseline (`mixed_docfirst_bm25` = router none with no rare band, BM25 passages) so
  every lexical method shares the passage step; question-only runs of the selected setting and of
  doc-first; throughput (queries/s); time to place one new document and rebuild its cluster's local
  BM25, versus re-clustering from scratch. Cluster-local indexes are built before timing, so latency is
  query-time work only (their build time is reported separately). Parth's final method and dense
  doc-first run only with `--dense-baselines` (chunk embeddings, Kaggle GPU).
- **Status:** pre-registered; split drawn (`results/tables/query_split.md`, `.csv`); pipeline built and
  unit-tested (`src/trr/clustering/band_clusters.py`, `src/trr/retrievers/band_pipeline.py`); run script
  `scripts/run_band_pipeline.py` (`--stage dev`, then `--stage test`); not run.
- **Before running (2026-11-13):** passage BM25 now reads only the chosen document's rows of the
  precomputed term-score matrix (`ChunkStore.bm25_scores_in_rows`), with scores identical to full-pool
  scoring (unit test), so latency reflects the method. A query with no indexable word falls back to
  the first document (tie rule) instead of crashing. Kaggle run prepared: `kaggle/README.md`,
  `kaggle/e11_band_pipeline.ipynb` (checks the dev/test split is identical to the local one, smoke run,
  dev, test, packaged outputs), `kaggle/make_bundle.sh`.
- **AMENDED 2026-11-13, before any result: E11 runs on CLERC, not LegalBench** (the LegalBench run is
  skipped; its notebook is removed). Reason: the point of E11 is a collection WITHOUT predefined classes,
  where the band clusters are the only grouping; LegalBench's groups are known.
  - *Data:* CLERC (jhu-clsp/CLERC; licence unstated -> private use, never redistributed). Training queries
    (`teva_train_dir/train_data.jsonl.gz`: query + 1 positive + 20 negative passages). Verified on the files
    that these "docid"s are PASSAGE ids (~2,200-character passages, consecutive ids from one case), not cases.
    Passages are only an id bridge: positive and negatives mapped to cases (`mapping.pid2did.tsv`), duplicates
    and the gold case removed; the pipeline works on full case texts (`collection.doc.tsv.gz`).
  - *Pool:* queries in a seeded random order, each adding its gold case and CLERC's negative cases, until
    10,000 cases; no random fill (only CLERC's own documents); larger pools continue the same order (nested).
    A query's own source opinion would match it verbatim: a pool case holding >= 2 of 3 twelve-word windows
    of the query, among its top-5 BM25 cases, is removed (or the query dropped if that case is a gold case).
  - *Split:* 20% of gold cases (seeded) -> dev queries, rest -> test.
  - *Chunks:* fixed 500-character windows, 100 overlap, ending at word boundaries (CLERC texts have no line
    breaks). LegalBench keeps the recursive splitter.
  - *Grid:* as pre-registered except k {8, 16, 32, 64, 128} (scaled to 10k cases); defaults unchanged.
  - *Metrics:* document-level gold only. Document recall@1 / @10, MRR, nDCG@10 over the ranked cases (the
    pipeline ranks 10 cases per query), DRM@k, gold cluster searched, fallback rate, latency, queries/s,
    add-one-document time. No character metrics (no span gold), no NMI/ARI (no labels): cluster sizes,
    cohesion (mean cosine to own centroid) and names instead. CIs resample gold cases.
  - *Baselines:* flat BM25 over chunks, full-query doc-first, the no-cluster and oracle-routing ablations.
    Parth's final method needs labelled groups and the question-only run needs LegalBench's header: both
    not applicable.
  - *Expectation (CLERC):* the citation is removed from the query, so the gold case's name is not in it; the
    rare band must work from rare facts and terms and will be weaker than on LegalBench. CLERC's negatives
    are hard (topically close), so most sit in the gold case's cluster: routing will rarely exclude the gold
    case and will remove few of the confusers; gains, if any, come from the rare band inside the cluster.
  - *Implementation (before running):* cluster-local BM25 is computed from one shared count matrix (same
    formula as bm25s Lucene, unit-tested equal to a bm25s index of the same cases) instead of one index per
    cluster set, which would take hours on 10k cases. Files: `src/trr/data/clerc.py`,
    `scripts/build_clerc_pool.py`, `src/trr/chunking/fixed.py`, `kaggle/e11_clerc.ipynb`.
- **RESULT (2026-11-13, Kaggle CPU, git e1945fb, 3.3 h).** Pool: 9,777 cases (10,007 planned, 230 source
  opinions removed, no query dropped), 807 queries (dev 160 / test 647), mean case 43,763 characters,
  1,074,740 chunks. Tables: `results/tables/band_dev_clerc.md`, `band_test_clerc.md`, `band_test_ci_clerc.csv`.
  - *Dev selection:* min_df 5, max_frac 25%, k 16, rare_below 10, B 3 (dev recall@1 0.106 = 17 / 160; 2
    settings tied; 13 more at 0.094). The dev grid is flat: one query = 0.006, so the selection is mostly noise.
  - *Test (647 queries; doc recall@1 / @10, MRR, nDCG@10, gold cluster searched, p50 latency):*

    | method | r@1 | r@10 | MRR | nDCG@10 | gold searched | p50 ms |
    |---|---|---|---|---|---|---|
    | band, selected (k16 B3 r10) | 0.077 | 0.291 | 0.145 | 0.180 | 0.896 | 17.6 |
    | band, default (k8 B2 r5) | 0.087 | 0.263 | 0.139 | 0.168 | 0.920 | 14.6 |
    | rare band, no clusters | 0.087 | 0.308 | 0.151 | 0.189 | 1 | 6.8 |
    | rare band, oracle cluster | 0.155 | 0.447 | 0.242 | 0.291 | 1 | 7.0 |
    | full-query doc-first BM25 | **0.116** | **0.501** | 0.212 | **0.279** | 1 | 20.5 |
    | flat BM25 over chunks | 0.111 | 0.488 | **0.223** | 0.272 | - | 40.7 |

  - *CIs (resampling gold cases):* selected vs doc-first BM25: recall@1 -0.039 [-0.064, -0.014], MRR -0.068,
    nDCG@10 -0.100, all real. Selected vs no clusters: no difference on any metric. Selected vs oracle:
    -0.077 [-0.101, -0.054] recall@1.
  - *Clusters:* discovered without labels and readable as areas of federal law (k 16: immigration,
    bankruptcy, ERISA, habeas, Social Security disability, tax, sentencing, patents, admiralty, labour
    arbitration, employment discrimination, ...). Sizes 123-1,678, cohesion 0.29.
  - *Timing:* band index 121 s; adding one case = place 9 ms + count row 1.2 ms, vs re-clustering 110 s.
  - *Verdict:* **the rare band fails on CLERC.** Full-query BM25 picks the case better than BM25 over
    rare-in-cluster words, with clusters or without (dev: rare_below 0 / 2 / 5 / 10 without clusters =
    0.075 / 0.062 / 0.056 / 0.056). As expected before the run, the query does not name the cited case,
    so its rare words are not that case's identifying facts; what does identify it is the shared legal
    argument, which lives in the common words. Routing itself is fine (gold cluster searched 90% at B 3
    of 16, a quarter of the pool searched), and it costs nothing against no clusters. The oracle shows the
    real ceiling: even searching only the gold case's cluster, recall@1 is 0.155. The hard step on CLERC
    is choosing among topically close cases, not finding the topic.

## E12. Embedding pipeline on CLERC: embedding clusters -> routing -> dense document (PRE-REGISTERED)

Written 2026-11-13 before any result. Defaults in `configs/default.yaml` (`embed_clusters`).

- **Question:** the same three steps as E11 with embeddings instead of word frequencies -- how well do
  embedding clusters route, and how well does a dense document choice pick the exact case? Run on the
  same pool, split and test queries as E11, so the two compare query by query (and can be fused later).
- **Method:** every 500-character chunk embedded with bge-small (fixed model, GPU); a case's vector =
  normalised mean of its chunk vectors; spherical k-means (same code and restarts as E11) -> query embedding
  routed to the top-B centroids -> the searched cases ranked by `mean` (query . case vector) or `maxp` (the
  case's best chunk, as the CLERC paper's MaxP) -> top case; its chunks ranked by cosine. Chunk vectors are
  stored grouped by cluster (an inverted-file layout), so routing cuts the work.
- **Data / split:** the E11 pool (10,000 cases), rebuilt in the E12 session by the same deterministic
  builder (same code, seed and files); the two pools are compared after both runs. Same dev / test split.
- **Dev search:** k {8, 16, 32, 64, 128} x B {1, 2, 3} x document score {mean, maxp}; selection as E11 (most
  correct dev queries at document recall@1; ties -> smaller k, then smaller B, then grid order). Defaults
  k = 8, B = 2, maxp. Test scored once with the selected setting and the defaults.
- **Metrics:** as E11 (document recall@1 / @10, MRR, nDCG@10, DRM@1/8, gold cluster searched, latency,
  queries/s, cohesion and sizes), plus query-encoding time per query and the time to add one case (embed
  its chunks + place it) vs re-clustering. Document-level CIs.
- **Baselines:** flat dense retrieval over all chunks (standard chunk RAG), the no-cluster ablation (flat
  dense document choice) and oracle routing. Comparison with E11 from the per-query run files afterwards.
- **Expectation:** embeddings capture topic well, so routing (gold case's cluster searched) should be at
  least as good as E11's; picking the exact case among topically close negatives is harder for embeddings
  than for rare words, so `maxp` should beat `mean`, and E11 and E12 should fail on different queries
  (the case for fusion).
- **Status:** built and unit-tested (`src/trr/clustering/embed_clusters.py`,
  `src/trr/retrievers/embed_pipeline.py`, `scripts/run_embed_pipeline.py`, end-to-end test on a synthetic
  pool); Kaggle notebook `kaggle/e12_clerc.ipynb` (GPU). Not run.
- **RESULT (2026-11-13, Kaggle T4 GPU, git 2ea23f0).** Pool rebuilt in the E12 session: same metadata as
  E11 (9,777 cases, 230 removed, 807 queries, 160 / 647 split, same 1,074,740 chunks). Tables:
  `results/tables/embed_dev_clerc.md`, `embed_test_clerc.md`, `embed_test_ci_clerc.csv`.
  - *Dev selection:* k 32, B 3, mean (dev recall@1 0.094; 4 settings tied).
  - *Test (647 queries; latency excludes query encoding, 11 ms per query on the GPU, the same for all):*

    | method | r@1 | r@10 | MRR | nDCG@10 | gold searched | pool searched | p50 ms |
    |---|---|---|---|---|---|---|---|
    | emb, selected (k32 B3 mean) | 0.096 | 0.369 | 0.172 | 0.218 | 0.760 | ~12% | 0.6 |
    | emb, default (k8 B2 maxp) | 0.073 | 0.363 | 0.148 | 0.198 | 0.805 | ~30% | 20.1 |
    | dense doc choice, no clusters (mean) | 0.096 | 0.399 | 0.179 | 0.231 | 1 | 100% | 3.0 |
    | dense, oracle cluster (k32 mean) | 0.161 | 0.550 | 0.275 | 0.341 | 1 | - | 0.3 |
    | flat dense over all chunks | 0.066 | 0.402 | 0.164 | 0.209 | - | 100% | 129 |

  - *CIs:* selected vs no clusters: recall@1 0.000 [-0.009, 0.008], MRR -0.007 (no), nDCG@10 -0.012
    [-0.022, -0.003] (real, small). Selected vs flat dense chunks: recall@1 +0.029 [0.005, 0.054], DRM@8
    -0.040 [-0.063, -0.020], both real. Selected vs oracle: -0.065 [-0.084, -0.047].
  - *Timing:* embedding all 1.07M chunks is cached from the dev stage; building the cluster index 7 s;
    adding one case = embed its chunks 122 ms + place 0.2 ms, vs re-clustering 6.7 s.
  - *Against the expectation:* (1) **mean beat maxp**, clearly (dev, no clusters: 0.088 vs 0.031). Likely
    reason: CLERC's negatives quote the same statutes and precedents, so a single near-identical passage
    is common in the wrong cases; the whole-case average is steadier. (2) Embedding clusters routed
    *worse* than band clusters at equal k (dev, gold cluster searched at k 16 B 3: 0.869 vs 0.944).
  - *Verdict:* routing with embedding clusters is a pure speed gain: searching 12% of the cases (5x faster
    than no clusters, 200x faster than flat dense chunks) loses nothing at recall@1 and a little at
    nDCG@10. Case-level dense choice (one vector per case) beats chunk-level dense retrieval at recall@1.
    But dense document choice (0.096) is still below full-query BM25 doc-first (0.116, E11 run).
- **E11 vs E12 query by query** (`scripts/compare_e11_e12.py` -> `results/tables/e11_e12_compare_clerc.md`).
  The two sessions' `queries.parquet` are byte-identical (sha256) and every run scored the same 647
  queries with the same gold cases.
  - *They fail on different queries (as expected).* Of the queries that BM25 doc-first or dense case
    choice gets right at recall@1, only 28 are shared: 47 only BM25, 34 only dense. Either one is right
    on 16.8% (vs 11.6% for the better alone); at recall@10, either one holds the gold case on 62.8% (vs
    50.1%). Band vs embedding pipelines: 13 shared, 37 / 49 alone.
  - *Exploratory, not pre-registered:* plain RRF (k 60) of BM25 doc-first and dense case lists (top 10
    each): recall@1 0.121 (+0.005 [-0.017, 0.026], not real), recall@10 0.530, MRR 0.220. A rank-only
    fusion captures almost none of the 16.8% ceiling at rank 1, though it lifts recall@10. The fused
    pipeline needs a signal that says *which* ranker to trust per query, not equal votes.

---

## Open items

- E11 and E12 done on CLERC (2026-11-13). Next: a fused pipeline with a per-query confidence signal.
- After E11 / E12: fused pipeline (stage-wise RRF, confidence-weighted); comparison
  study (bi-encoder, cross-encoder; time, throughput, accuracy, DRM); hierarchical chunking (tree descent).
- Datasets for scale: LegalBench + EDGAR Exhibit-10 distractors (deduped against the 714 documents with
  MinHash); CLERC subsampled pools (10k / 30k / 100k) if its licence and court metadata check out.
- Run the conc_lr sweep on WOS (E8).
- Learning curve: subsample WOS (and CUAD) training data per class to test data-size vs domain directly.
- Fix the routers.py module docstring: the LR routers need a refit to absorb new documents (placement
  needs none).

# Design decisions

Every key choice in the project, why we made it, and what evidence backs it. Grouped by area, in the
order the project needs them. Experiment numbers (E0-E11) refer to `docs/experiments.md`; parameter
values live in `configs/default.yaml`.

Status: **fixed** = in use; **tried, dropped** = tested and not adopted; **planned** = decided, not built.

---

## 1. Project-level rules

| # | decision | reason | status |
|---|---|---|---|
| D1 | **Training-free and extendible.** A new document is added without retraining any model. No fine-tuning, no per-document LLM calls (an LLM appears only in the SAC baseline). | The project motto since the H1 NO-GO (E1): a scalable retriever that first groups like documents and then retrieves within the group. Retraining for every new contract does not scale. | fixed |
| D2 | **Every retriever returns hits as (document, start, end, score) in original character offsets.** Never score on transformed text. | Methods with different units (chunks, section leaves, documents) stay comparable, and gold spans are checked exactly. | fixed |
| D3 | **All parameters in one config; caches keyed by a config hash; fixed seeds; every run logs config + git hash.** | Reproducibility, and every number in a table can be traced to the exact code and setting that made it. | fixed |
| D4 | **Heavy compute runs on Kaggle; locally only code, unit tests and tiny throttled smoke tests.** | Keeps the development machine usable. Embeddings, sweeps and full runs go to Kaggle; results come back as tables, run files and cache files. | fixed |
| D5 | **Pre-register before running.** Question, method, defaults, search grid, selection rule and expectation are written down before any result. Additions made later are dated and marked "before any result". | Choosing settings after seeing results inflates them. This keeps the reported numbers honest. | fixed (from E8 on) |
| D6 | **Unit test every metric and every offset round-trip before use.** | A wrong metric silently invalidates every table. | fixed |

## 2. Data

| # | decision | reason | status |
|---|---|---|---|
| D7 | **LegalBench-RAG is the main benchmark:** 714 contracts in 4 collections (ContractNLI 95 NDAs, CUAD 462 commercial contracts, MAUD 150 merger agreements, PrivacyQA 7 privacy policies), 6,889 queries with gold character spans. | It has real full documents, look-alike contracts and span-level gold, which is what DRM needs. Every query has exactly one gold document. | fixed |
| D8 | **Read text with universal newlines; normalise document ids to Unicode NFC.** | Raw bytes broke 2,801 of 2,839 MAUD spans; macOS file names (NFD) broke 8 CUAD snippets. With both fixes the span round-trip is 100% (E0). | fixed |
| D9 | **Develop on the mini benchmark (194 queries per subset), run full only when a phase passes its check.** | Fast iteration. Caveat: mini is part of full, so a setting picked on mini is not independently confirmed on full (seen in E10). E11 replaces this with a proper dev/test split (D16). | fixed, superseded for E11 |
| D10 | **Web of Science (47k abstracts, 7 domains, 134 areas) as a second dataset for grouping.** | Separates "the method is weak" from "CUAD has too few documents per type" (8-32 per fold). | fixed (E7, E9) |
| D11 | **Bigger legal pools:** CLERC (full federal court cases, no class labels) is E11's dataset, at 10k cases first, then 30k / 100k nested pools from the same seeded query order (D55). LegalBench + EDGAR distractors (deduplicated with MinHash) remain an option for span-level gold at scale. | CLERC has queries, document-level gold and its own negatives, and no labels, so clusters must be discovered. Its licence is not stated: private use only. Nested pools make pool size the only thing that changes. | fixed (10k), planned (30k / 100k) |

## 3. Evaluation

| # | decision | reason | status |
|---|---|---|---|
| D12 | **DRM@k = share of the top-k hits from a wrong document**, divided by the number of hits actually returned. | It is the failure the project targets (a passage from a look-alike contract). Dividing by the returned hits stops a method from looking good by returning fewer. | fixed |
| D13 | **Also: document recall@k, character precision/recall@k (overlapping hits merged, so a character counts once), and span-level nDCG@10** (a hit gains 1 when it reaches a gold snippet no earlier hit reached, discounted by log2(rank + 1)). | DRM alone does not say whether the right passage was found. nDCG@10 is the standard rank-aware metric and is needed for the comparison study. | fixed (nDCG added 2026-11-13) |
| D14 | **Doc-first is the baseline to beat, not hybrid.** | Picking the document first already cuts DRM@8 from .437 (hybrid) to .154 (E0). A new method has to improve on that. | fixed |
| D15 | **Leak-safe document folds:** 5 folds stratified by group; near-duplicate documents (MinHash Jaccard >= 0.8) kept in one fold. | A router scored on a near-copy of a training document looks better than it is. | fixed |
| D16 | **Dev / test split of the queries by gold document** (fold 0 = dev: 1,403 queries / 143 documents; test: 5,486 / 571). Settings are chosen on dev; test is scored once. | Avoids the winner's curse (E9) and stops a setting being tuned on one question about a contract and scored on another question about the same contract. | fixed (E11) |
| D17 | **Confidence intervals resample gold documents** (paired, stratified per subset, macro mean). A difference counts only if this CI excludes 0. | Questions about one contract succeed or fail together; resampling queries gives CIs 1.25-4.4x too narrow. | fixed |
| D18 | **Report macro means over the 4 subsets; select E11 settings by a query-weighted mean.** | Macro keeps CUAD from drowning the others in the tables. For selection, PrivacyQA has a single dev document, which a macro would weigh as a quarter of the decision. | fixed |
| D19 | **One mixed pool of all 714 documents** for every query (from E10 on). | With a separate pool per collection the right kind of document is given for free; in one pool a wrong group can really be chosen. | fixed |

## 4. Chunking and baseline retrievers

| # | decision | reason | status |
|---|---|---|---|
| D20 | **Chunks: recursive character splitter, at most 500 characters, no overlap** (split at blank lines, then line breaks, then spaces, then characters). ~207k chunks, mean ~385 characters. | It is the LegalBench-RAG paper's baseline, so our numbers are comparable to theirs and across all our tables. Offsets are kept exactly (D2). | fixed |
| D21 | **Section-tree leaves as an alternative unit** (headings detected, leaves of 100-1,500 characters, parent headings prepended for embedding only). | Tested whether structure-aware units help. Result: slightly worse than chunks (+.027 DRM@8, CI excludes 0; E10). | tried, dropped |
| D22 | **BM25 with k1 = 1.5, b = 0.75, lower-casing and English stopwords** (bm25s). | Standard settings; the same tokenizer is used everywhere words are counted (routers, bands, BM25), so every stage sees the same words. | fixed |
| D23 | **Dense: bge-small-en-v1.5, normalised vectors, float16 cache, the model's query instruction; hybrid = RRF (k = 60) of BM25 and dense, depth 200.** | A small, strong, open model that is cheap to re-run; RRF needs no score calibration. | fixed |

## 5. Grouping and routing

| # | decision | reason | status |
|---|---|---|---|
| D24 | **Drop exact-text template detection; group by word frequencies instead.** | H1 was NO-GO (E1): only MAUD reuses template text, and shorter shingles produced false matches on generic legal words. Word frequencies survive rewording. | fixed |
| D25 | **Two levels of groups:** coarse = the 4 collections; fine = 3 collections + 25 CUAD contract types read from file names (types under 5 documents merged into "Other"). | These are the only human labels available; they are used to evaluate grouping, never inside the method. | fixed |
| D26 | **Separate gates per level:** coarse top-1 >= 0.95 (a miss costs a whole collection); fine top-3 >= 0.95 (3 of 25 types is still a small search). | Set after the first results were seen, and stated as such. | fixed |
| D27 | **Routers compared:** embedding centroid (first 2,000 characters), Naive Bayes on all words and on a band, logistic regression on a band (band_lr), on top-200 group words (vocab_lr), and RRF of centroid + Naive Bayes (fused). conc_lr (band + concentration filter) designed. | Covers dense vs lexical and generative vs discriminative. Results: coarse solved by all good routers; fine best with the centroid on CUAD (data-starved), with vocab_lr / band_lr on Web of Science (E3, E7). | fixed (conc_lr sweep pending) |
| D28 | **The band (frequency range of words used) was fixed at 1%-50% before any sweep**, and sweeps were reported as sensitivity only. | Avoids picking the band on the test data. Lesson from E6/E9: the floor should be a small absolute number of documents, not a share. | fixed |
| D29 | **Winner's-curse protection for sweeps:** search on fold 0, confirm only the winner and the default on folds 1-4. | The gain of a picked setting shrinks on new data; the confirmation shows how much is real (E9: at most 0.6 points shrinkage). | fixed |

## 6. Group-first retrieval (Track B, Parth)

| # | decision | reason | status |
|---|---|---|---|
| D30 | **Route the query to the top-B groups and search only there; `none` (all groups) and `oracle` (gold group) as references.** | The group-first idea in its simplest form; the two references show the floor and the ceiling of routing. | fixed |
| D31 | **Local document index:** whole-document BM25 built over the searched groups only, so idf comes from those groups. | A name rare among NDAs stays rare even if long merger agreements use it. Routing + local index: -.017 DRM@8, real (E10). | fixed |
| D32 | **Header-only document choice:** the text before the first ";" ("Consider the NDA between X and Y") picks the document; RRF of header-only and full-query rankings in the final method. | Generic question words outvote the one or two party names. Header: -.085 DRM@8, real. Caveat: the header is a property of the benchmark's question template. | fixed (baseline) |
| D33 | **Final Track B method:** centroid on whole-document vectors, coarse level, B = 2, local index, header + full-query RRF; dense passages inside the chosen document. | Best measured method so far: DRM@8 .161 -> .108 vs flat doc-first on the mixed pool (CI just excludes 0). It is the bar E11 must clear. | fixed (baseline) |

## 7. E11 band pipeline (our method, pre-registered 2026-11-12)

Route with the mid band, pick the document with the rare band, rank passages inside it. Fully lexical.

| # | decision | reason | status |
|---|---|---|---|
| D34 | **Mid band ("what kind of document") = words in >= 5 documents and <= 50% of documents.** | The floor is an absolute count (D28); the ceiling drops words every contract has ("agreement", "shall"). | fixed, tuned on dev |
| D35 | **Document vector = sublinear tf-idf over the mid band, scaled to length 1.** | 1 + log(count) stops bursty words dominating (E4: "bank" x282); unit length makes a 3-page NDA and a 200-page merger agreement comparable, and cosine becomes a dot product. | fixed |
| D36 | **Clusters = spherical k-means (k-means++ starts, 10 restarts, best total cosine), k = 8 by default; each cluster named by its top centroid words.** | Needs no labels, so it works on any new collection; matches the cosine used for routing. k = 8 is a rough guess (4 collections + a few broad contract kinds); the dev search decides. | fixed, tuned on dev |
| D37 | **Clusters are built from documents only, never queries.** | It is an index of the collection; no query information can leak in. | fixed |
| D38 | **Extendible by construction:** vocabulary and idf frozen at build; a new document joins its nearest cluster and is added to that cluster's centre. | D1. The cost: idf drifts slowly as the collection grows, so an occasional full rebuild is optional. Time to add vs time to re-cluster is measured. | fixed |
| D39 | **Route to the top B = 2 clusters by default (dev grid B = 1, 2, 3); a query with no mid-band word searches every cluster.** | Top-1 misses the right group too often (CUAD types: .80 top-1 vs .93 top-3). But each extra cluster adds look-alike documents and makes fewer query words count as rare. B = 2 is the middle; dev decides. With no evidence of kind, a guess would be arbitrary. | fixed, tuned on dev |
| D40 | **Rare band ("which document") = query words in fewer than 5 documents of the searched clusters.** Same cut-off as the mid band's floor. | Party names, products and amounts identify a contract; "confidential" is in every NDA. Counting inside the clusters keeps a name rare among NDAs even if it is common among merger agreements. | fixed, tuned on dev |
| D41 | **Pick the top-1 document by BM25 over the rare words, idf from the searched clusters; fall back to the full query when there is no rare word; ties go to the first document in corpus order.** | DRM is the target: one right document gives DRM = 0. Cost: no hedge, a wrong document makes every passage wrong (top-2 documents is a follow-up). The fallback rate is reported, showing how often the rare band actually decides. | fixed |
| D42 | **Passages = BM25 with the full query over the chosen document's 500-character chunks; idf from the whole pool.** | Keeps the pipeline lexical (no model to index, add or answer) and identical to the lexical baselines, so differences come from the document choice. Dense passages are a later variant. | fixed |
| D43 | **Full query by default; a question-only run (header removed) is also reported.** | The header is a quirk of the benchmark template; real users do not write one. | fixed |
| D44 | **Selection = most correct dev queries at document recall@1; ties -> smaller k, then smaller B, then grid order. Test scored once with the selected setting and with the pre-registered default.** | Document choice decides DRM in a one-document pipeline. Smaller is cheaper and simpler when scores are equal. The default shows the method without tuning. | fixed |
| D45 | **Compared against:** flat BM25, flat lexical doc-first, the same pipeline without clusters, the same pipeline with oracle routing, and (GPU run) Parth's final method and dense doc-first. | No clusters shows what clustering adds; oracle shows the ceiling of routing; Parth's method is the current best. | fixed |
| D46 | **Latency measured on query work only:** cluster-local indexes are built before timing and their build time reported separately. | Index building and answering are different costs. | fixed |
| D47 | **Passage scoring restricted to the chosen document's chunks:** bm25s's precomputed term scores are turned once into one row per chunk, and only the document's rows are read. | Identical scores (unit-tested against full-pool scoring), but the work grows with the document instead of the pool. The old path walked the whole pool's postings of common query words ("agreement", "party") and threw most away, which inflated our latency. The gain depends on the query's words; it is measured, not assumed. Costs ~100 MB extra memory. | fixed |

## 7b. E11 on CLERC (amended 2026-11-13, before any result)

| # | decision | reason | status |
|---|---|---|---|
| D52 | **Run E11 on CLERC, not LegalBench.** | E11 tests clusters discovered without labels. LegalBench's groups are known; CLERC's 1.84M federal court cases carry no class labels. The LegalBench run is skipped. | fixed |
| D53 | **Training queries with CLERC's own negatives**, not our mined ones. | Fair and unmodified: the difficulty is CLERC's, not ours. Verified on the files: their ids are passage ids (~2,200-character passages, consecutive ids from one case). | fixed |
| D54 | **Skip passages: map positive and negative passages to their cases** (duplicates and the gold case removed) and use full case texts. | The method groups and picks whole documents; passages are only an id bridge. | fixed |
| D55 | **Pool = queries in a seeded order, each adding its gold and negative cases, until 10,000 cases; no random fill. Larger pools continue the same order.** | Only CLERC's documents enter. Nested pools make pool size the only change when we scale to 30k / 100k. | fixed |
| D56 | **Remove each query's own source opinion from the pool** (a case holding >= 2 of 3 twelve-word windows of the query, among its top-5 BM25 cases). | The query is cut from that opinion, so it would match verbatim and count as a wrong document for a trivial reason. | fixed |
| D57 | **Fixed 500-character windows with 100 overlap, ending at word boundaries** (LegalBench keeps the recursive splitter). | CLERC texts have no line breaks, so paragraph splitting finds nothing. Chunking is not the focus; a window is the simplest unit that works. Overlap keeps a sentence cut at one edge whole in the next. | fixed |
| D58 | **Document-level evaluation:** the pipeline ranks 10 cases per query. Metrics are recall@1 / @10, MRR, nDCG@10 over cases, and DRM; no character metrics. Cluster quality = sizes, cohesion, names (no labels for NMI / ARI). k grid scaled to {8 ... 128}. | CLERC's gold is a case, not a span. Passage-level gold can be added later. | fixed |
| D59 | **Cluster-local BM25 from one shared count matrix**, same formula as bm25s (Lucene), instead of one BM25 index per cluster set. | Identical scores (unit-tested), but no per-query index builds, which would take hours on 10k long cases. The counts are shared by every clustering of the dev grid. | fixed |

## 8. Later pipelines

| # | decision | reason | status |
|---|---|---|---|
| D48 | **Order of work: band pipeline (E11) -> embedding pipeline -> fused pipeline -> comparison study -> hierarchical chunking -> bigger datasets.** | Measure each signal alone first, so the gain of combining them can be attributed. | planned |
| D49 | **Fused pipeline = RRF at each stage, weighted by confidence** (e.g. a large score gap between the top two documents makes the rare-band ranking count more; no rare word makes the dense ranking lead). Weights chosen on dev. | Rare words catch names and amounts, embeddings catch paraphrases. Fusion is mainly expected to help at the document stage, where wrong-document errors happen. Training-free (D1). | planned |
| D50 | **Comparison study: our routers and pipelines vs a trained bi-encoder and cross-encoder,** on time, throughput, accuracy, DRM and nDCG@10. | The trained models are the standard alternative; the question is what they buy and at what cost (query-time cost, need for labelled data, re-embedding when the model changes). | planned |
| D51 | **Adaptive B** (add the 2nd / 3rd cluster only when its similarity is close to the top one). | Confident queries search narrowly, uncertain ones widely. Not in the E11 grid, so it is its own experiment. | idea |

## Known limitations we accept
- Some NDA questions name parties that never appear in the document text; no lexical method can fix
  those (E0 failure analysis: 45 of 62 ContractNLI doc-first misses on mini).
- k-means clusters will be uneven (462 CUAD documents vs 7 PrivacyQA).
- The rare band cannot match paraphrases; dense and fused pipelines address that later.

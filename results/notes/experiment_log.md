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

## Open items

- Run the conc_lr sweep on WOS (E8).
- Learning curve: subsample WOS (and CUAD) training data per class to test data-size vs domain directly.
- Larger legal training set if needed: SEC Exhibit-10 dump (Hugging Face), labelled by our own exhibit-title
  rule; dedupe against CUAD with MinHash. Stanford MCC rejected (only 8 coarse labels, no titles).
- Earlier recommendations still open: fix nb_band (binary counts / ComplementNB), whole-document
  centroid, label audit, within-group retrieval + DRM, scaling with distractors.
- Not committed yet: everything from E5 on (code, config, tables, notes).

# conc_lr: band words concentrated in one group -- choice of m and p

Written before any Web of Science conc_lr result was seen. The defaults below are in
configs/default.yaml (`routing.conc_*`) and are not changed by the sweep, which is a sensitivity
table only (scripts/sweep_conc.py).

## The rule

A word is in the conc_lr vocabulary if

1. its document frequency is in [low, high] of the training documents (the band),
2. it appears in at least **m** training documents of its best group (coverage), and
3. its **balanced purity** is at least **p**: with rate_g = df_g / size_g (the share of group g's
   documents containing the word), purity = max_g rate_g / sum_g rate_g. Rates rather than counts,
   so a group does not look pure just by being large. Chance level = 1 / (number of groups).

## m -- minimum documents in the word's best group

- m = 1 is no requirement: a company name, typo or ID number seen in a single training contract is
  "perfectly concentrated" (vocab_lr's cut-offs were full of these: `linksynergy`, `purinix`,
  `incluidng`, `87105110`).
- m = 2 is the smallest evidence that a word *recurs* across different documents of a group. It
  removes singletons, typically the largest part of a vocabulary, and almost never a useful word:
  a word in 1 of ~290 training abstracts of an area fires on roughly 0.3% of new abstracts.
- Larger m keeps only words a new document is likely to contain (about m / group size of them do).
  But m is absolute: m = 5 is 60% of a 8-document CUAD type and 2% of a 290-abstract WOS area, and
  an m above a group's size removes every word of that group.
- **Default m = 2**; sweep m in {1, 2, 3, 5, 10}.

## p -- minimum balanced purity

- Chance purity is 1 / K: WOS coarse 1/7 = 0.14; WOS fine 1/56 = 0.018 (Medical) to 1/9 = 0.11 (MAE);
  CUAD fine 1/25 = 0.04. The same p is therefore stricter at levels with more groups.
- p >= 1/k roughly means "the word belongs to at most k groups". **Default p = 1/3**: words shared
  by a small family of related groups (e.g. `amyloid` in Alzheimer's and Parkinson's) are kept --
  exactly the words that put the right group into the top 3, which is what the fine gate counts.
- High p (0.7-0.9) keeps only near-exclusive words: a much smaller vocabulary, fewer vocabulary
  words per held-out document (short abstracts may end up with almost none), and the loss of
  contrastive evidence -- a word common in 3 of 25 groups is still strong evidence against the other 22,
  and logistic regression already learns per-group weights for it.
- p = 0 switches the filter off (conc_lr with m = 1 and the band 1%-50% is band_lr).
- Sweep p in {0, 0.2, 0.33, 0.5, 0.7, 0.9}. An alternative scale-free form, p = lambda / K
  ("lambda times chance"), is not used.

## Band floor

The 1% floor is relative to the whole training pool. In a large pool it removes words that are
frequent inside one group but rare overall: WOS Medical has ~11,700 training abstracts per fold, so
the floor is ~117 documents, while one Medical area has ~210 -- an area word in 50 of them is dropped.
With m guarding against one-off words, **conc_lr uses low = 0** (high stays 50%); the sweep also
runs low = 1% to show the effect.

## Expectation stated beforehand

On LegalBench-RAG fine (a 4-cell smoke test run after the defaults were fixed), p = 0.33 cut the
vocabulary from 8,154 to 2,567 words and words per held-out document from 655 to 44, and lowered
top-3 from 0.838 to 0.775: with only 8-32 documents per type, purity filtering removed more useful
shared words than noise. WOS has ~20x more documents per group, so purity estimates are far less
noisy; if purity filtering helps anywhere, it should be there.

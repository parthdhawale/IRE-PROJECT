# Task 3: router fixes and the question-only test (Tue 3 Nov)

Follow-up of the handover (steps 1-2) and of `nb_band_failures.md`. New routers are added next
to the old ones; the old routers' numbers in `doc_grouping.md` and `routing.md` are reproduced
exactly (0 changed cells), so all rows stay comparable.

## What was built
- `routing/routers.py`: `band_vocab(..., alpha_only=True)` drops non-alphabetic tokens ("01",
  "1997", "___"); `NBRouter(binary=True)` counts each word once per text; `NBRouter(complement=True)`
  uses Complement Naive Bayes.
- New routers (`routing/evaluate.py`): `nb_band_bin` (binary counts + alphabetic band),
  `cnb_band` (Complement NB + alphabetic band), `centroid_full` (group centroid of whole-document
  vectors = normalised mean of each document's 500-char chunk embeddings, `prep.doc_full_vectors`).
- `scripts/run_routing.py --question-only`: routes on the question with the benchmark header
  ("Consider the NDA between X and Y;") removed. Writes `routing_qonly.md`, `routing_gate_qonly.md`.
- `retrievers/group_first.py` accepts the new router kinds. 3 new unit tests; 58 pass.

## Results (full query set, leak-safe document folds)

| router | held-out docs: coarse@1 | docs: fine@3 | queries: coarse@1 (ALL / NLI / MAUD / PQA) | queries: fine@3 |
|---|---|---|---|---|
| centroid (first 2,000 chars) | .992 | **.929** | .789 / .997 / .152 / .990 | **.906** |
| **centroid_full** (whole doc) | .938 | .812 | **.933** / .996 / .748 / 1.000 | .764 |
| nb_band | .952 | .803 | .831 / .377 / .820 / .665 | .754 |
| nb_band_bin | .961 | .677 | .635 / .201 / .271 / .041 | .616 |
| cnb_band | .826 | .833 | .801 / .055 / .918 / .093 | .829 |
| fused (centroid + nb_band) | .993 | .903 | .765 / .843 / .153 / .892 | .868 |

Question only (header removed), queries:

| router | coarse@1 (ALL / NLI / MAUD / PQA) | fine@3 |
|---|---|---|
| centroid | .694 / .983 / .000 / .799 | .146 |
| centroid_full | .801 / .924 / .237 / .954 | .167 |
| nb_all | .756 / .924 / .347 / .278 | .187 |

## Findings
1. **Whole-document centroid fixes MAUD query routing** (MAUD coarse@1 .152 -> .748; all queries
   .789 -> .933, the best query router at the coarse level). A short question resembles the body
   of a merger agreement, not its cover page and table of contents. It is worse at placing new
   *documents* into CUAD types (fine@3 .929 -> .812), so the two tasks prefer different document
   vectors. Coarse query gate (95% top-1) is still missed.
2. **The Naive Bayes fixes did not work.** Binary counts make everything worse (documents fine@3
   .803 -> .677): for long documents word frequency carries real signal, so removing it hurts more
   than the repeated-word errors it fixes. Complement NB helps documents (fine@3 .833) and MAUD
   queries (.918), but collapses on ContractNLI and PrivacyQA queries (.055, .093).
3. **Fine routing depends on the query header.** Without "Consider the <type> Agreement between
   ...;", fine routing falls from .906 to about .15-.21 top-3: the contract type is read from
   the header, not the question. Coarse routing survives for ContractNLI (NDA questions sound
   like NDAs) but not for MAUD. Report fine routing as header-dependent.
4. **End to end (group-first, coarse level, mini, DRM@8 mean):** centroid_full B=2 + collection-
   local doc-first = .164, vs .166 with the old centroid and .180 for flat doc-first. At B=1 it
   misroutes MAUD (in_beam .62 on mini), so B=2 is needed.

# Full benchmark run (Sun 8 Nov)

Branch `trackB-header-docsel`. All 6,889 queries; every pool is the full corpus. Tables:
`results/tables/baselines_full.md`, `group_first_full.md`, `paired_ci_full.md`.
Logs: `results/logs/full_*.log`. Both runs took under an hour on the M4 (embeddings cached).

## New: document-level paired bootstrap
`metrics.paired_cluster_bootstrap_macro_ci` + `scripts/paired_ci.py`. Resamples gold documents
(stratified per subset, macro mean), because questions about one document succeed or fail
together; a query-level bootstrap gives CIs that are too narrow. 3 new unit tests (65 pass).
A difference is called real only if the document CI excludes 0.

## DRM@8, full benchmark

Separate pool per collection:

| method | NLI | CUAD | MAUD | PQA | mean |
|---|---|---|---|---|---|
| hybrid | .863 | .203 | .451 | .229 | .437 |
| leaf_hybrid | .857 | .213 | .501 | .284 | .464 |
| docfirst | .302 | .022 | .008 | .284 | .154 |
| docfirst_hdr | **.248** | .023 | .007 | **.000** | **.070** |

One mixed pool of 714 documents:

| method | NLI | CUAD | MAUD | PQA | mean |
|---|---|---|---|---|---|
| mixed_hybrid | .904 | .211 | .462 | .251 | .457 |
| mixed_docfirst | .318 | .024 | .008 | .294 | .161 |
| gfc centroid_full B=2 docfirst_local | .286 | .024 | .008 | .258 | .144 |
| gfc centroid_full B=2 docfirst_local_hdr | .257 | .024 | .007 | .155 | .111 |
| **gfc centroid_full B=2 docfirst_local_rrf (final candidate)** | .261 | .023 | .007 | .139 | **.108** |
| gfc oracle docfirst_local_hdr (perfect routing) | .250 | .022 | .007 | .000 | .070 |

## Paired CIs (DRM@8 difference a - b, macro; CI resamples documents)

| a vs b | diff | doc CI | real? |
|---|---|---|---|
| docfirst vs hybrid | -.283 | [-.341, -.209] | yes |
| leaf_hybrid vs hybrid | +.027 | [+.016, +.041] | yes (leaves slightly worse) |
| docfirst_hdr vs docfirst | -.085 | [-.158, -.025] | yes |
| gfc docfirst_local vs mixed_docfirst | -.017 | [-.030, -.005] | yes |
| **final (rrf) vs mixed_docfirst** | **-.053** | **[-.122, -.004]** | **yes** |
| rrf vs gfc docfirst_local | -.036 | [-.095, +.006] | no (macro) |
| ContractNLI only: docfirst_hdr vs docfirst | -.054 | [-.089, -.024] | yes |
| ContractNLI only: rrf vs gfc docfirst_local | -.025 | [-.051, -.005] | yes |

## Findings
1. **Mini was pessimistic, not optimistic.** MAUD doc-first is .008 on full vs .057 on mini (the
   mini set happened to contain 11 questions on the one Bancorp agreement doc-first misses);
   the header gain on ContractNLI is larger on full (.302 -> .248) than on mini (.320 -> .289).
2. **The header helps NDAs for real**, not only PrivacyQA: ContractNLI -0.054 with a document
   CI excluding 0. PrivacyQA (7 documents) is where most of the macro gain comes from.
3. **Final method vs flat doc-first on one mixed pool: .161 -> .108 (-33%), CI excludes 0.**
   The step from routing alone (.144) to routing + header is real for NDAs but not significant
   in the macro, because the PrivacyQA part rests on 7 documents.
4. **Section leaves are slightly worse than chunks** on full (+.027, significant): Task 1's
   "no help" holds, now with a CI.
5. **Surprise to check:** for NDAs, the pool-wide document index restricted to the NDA group
   beats the NDA-only local index (oracle routing: .242 vs .302, doc CI [-.102, -.025]) -- the
   opposite of CUAD. Possibly length normalisation: the pool's average length is dominated by
   MAUD, which nearly switches off b for short NDAs. Not yet combined with the header.
6. ContractNLI is still the open problem (.26 at best); most remaining misses are queries whose
   party names are not in the document text.

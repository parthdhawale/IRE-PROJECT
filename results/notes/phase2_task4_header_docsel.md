# Task 4 (experiment): header-only document selection (Sun 8 Nov)

Branch `trackB-header-docsel` (off `trackB-retrieval`). Mini benchmark. Motivated by
`failure_analysis_docfirst.md`: many doc-first misses have the party name in the gold document,
but ~15 generic question words, shared by every NDA, outvote it.

## What was built
- `retrievers/query_split.py`: `split_query(text) -> (header, question)`, split at the first ";".
  Every one of the 6,889 queries has a header.
- `flat.py`: `DocFirstHeaderRetriever` (`docfirst_hdr`): stage 1 (whole-document BM25) scores
  only the header; stage 2 (dense inside the chosen document) is unchanged.
- `group_first.py`: inners `docfirst_hdr`, `docfirst_local_hdr` (same, inside the routed groups),
  and `docfirst_local_rrf`: RRF (k=60, as hybrid) of the header-only and full-query document
  rankings over the routed groups' local index.
- `tests/test_query_split.py`: 4 tests (split, fallback, header beats question words in flat and
  in group-first). 62 tests pass.

## Results (mini, DRM@8, lower is better)

Separate pool per collection:

| method | NLI | CUAD | MAUD | PQA | mean |
|---|---|---|---|---|---|
| docfirst | .320 | .005 | .057 | .284 | .167 |
| docfirst_hdr | **.289** | .005 | .057 | **.000** | **.088** |

One mixed pool of 714 documents:

| method | NLI | CUAD | MAUD | PQA | mean |
|---|---|---|---|---|---|
| mixed_docfirst (flat) | .325 | .052 | .052 | .294 | .181 |
| gfc centroid_full B=2 docfirst_local (previous best) | .294 | .052 | .052 | .258 | .164 |
| gfc centroid_full B=2 docfirst_local_hdr | .289 | .057 | .057 | .155 | .140 |
| **gfc centroid_full B=2 docfirst_local_rrf** | .289 | .052 | .057 | .139 | **.134** |
| gfc oracle docfirst_local_hdr (perfect routing) | .289 | .005 | .057 | .000 | .088 |

Paired bootstrap (DRM@8, 776 mini queries pooled, 1000 resamples):
- rrf vs previous best: -0.030, CI [-0.045, -0.014]; vs flat mixed doc-first: -0.046, CI [-0.063, -0.031].
- Without PrivacyQA: rrf vs previous best +0.000, CI [-0.005, +0.005] -- no gain.

## Findings
1. **Header-only selection never hurt with separate pools** (0 questions broken) and fixed all
   55 PrivacyQA misses and 6 of 62 ContractNLI misses. The remaining NDA misses are mostly the
   "name missing from the text" cases, which no text-only method can fix.
2. **In the mixed pool the header also matches other collections.** Words like "Non-Disclosure
   Agreement" or "privacy policy" score CUAD exhibits that mention them, so with B=2 some NDA and
   privacy questions pick a CUAD document. Fusing header and full-query rankings (RRF) recovers
   part of this: PrivacyQA .155 -> .139, CUAD back to .052.
3. **The gain is almost all PrivacyQA.** That subset has 7 documents and its mini set equals its
   full set (194 questions). Wordscapes (29 questions) does not contain its own app name, so its
   correct picks with the header come from "privacy policy" and length normalisation, not from
   identity evidence -- partly luck.
4. **Routing is now the bottleneck for PrivacyQA:** perfect routing + header gives .000, the
   centroid_full router with B=2 gives .139.

## Caveats
- Three variants were compared on mini; the choice must be confirmed on the full benchmark.
- Query-level bootstrap is optimistic: questions about one document fail together.

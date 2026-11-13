# E11 vs E12 on CLERC, query by query (647 test queries)

## Who gets the case right at recall@1

| a             | b            |   a r@1 |   b r@1 |   both |   only a |   only b |   either r@1 |
|:--------------|:-------------|--------:|--------:|-------:|---------:|---------:|-------------:|
| bm25_docfirst | emb_none     |   0.116 |   0.096 |     28 |       47 |       34 |        0.168 |
| bm25_docfirst | emb_selected |   0.116 |   0.096 |     28 |       47 |       34 |        0.168 |
| band_selected | emb_selected |   0.077 |   0.096 |     13 |       37 |       49 |        0.153 |
| bm25_docfirst | band_none    |   0.116 |   0.087 |     35 |       40 |       21 |        0.148 |
| bm25_docfirst | bm25_chunks  |   0.116 |   0.111 |     41 |       34 |       31 |        0.164 |
| emb_none      | dense_chunks |   0.096 |   0.066 |     17 |       45 |       26 |        0.136 |

## Exploratory: plain RRF (k=60) of two top-10 case lists (not pre-registered)

CI = paired bootstrap resampling gold cases, against full-query BM25 doc-first.

| fused                            |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   r@1 - bm25_docfirst |     lo |    hi | real   |
|:---------------------------------|----------------:|-----------------:|-----------:|----------------------:|-------:|------:|:-------|
| rrf(bm25_docfirst, emb_none)     |           0.121 |            0.530 |      0.220 |                 0.005 | -0.017 | 0.026 | no     |
| rrf(bm25_docfirst, emb_selected) |           0.114 |            0.513 |      0.215 |                -0.002 | -0.025 | 0.019 | no     |
| rrf(band_selected, emb_selected) |           0.102 |            0.433 |      0.189 |                -0.014 | -0.040 | 0.011 | no     |

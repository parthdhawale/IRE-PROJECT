# E13 error analysis: held-out passage queries on CLERC (1600 test queries per length)

Name = capitalised word in at most 5 of 9777 pool cases.

## Who gets the case right at recall@1

|   words | a             | b            |   a r@1 |   b r@1 |   both |   only a |   only b |   either r@1 |
|--------:|:--------------|:-------------|--------:|--------:|-------:|---------:|---------:|-------------:|
|      25 | bm25_docfirst | emb_none     |   0.454 |   0.331 |    458 |      269 |       72 |        0.499 |
|      25 | band_selected | emb_selected |   0.414 |   0.287 |    363 |      300 |       97 |        0.475 |
|      25 | bm25_docfirst | band_none    |   0.454 |   0.454 |    725 |        2 |        2 |        0.456 |
|      25 | bm25_docfirst | bm25_chunks  |   0.454 |   0.409 |    562 |      165 |       92 |        0.512 |
|      25 | emb_none      | dense_chunks |   0.331 |   0.331 |    530 |        0 |        0 |        0.331 |
|     100 | bm25_docfirst | emb_none     |   0.625 |   0.537 |    753 |      247 |      106 |        0.691 |
|     100 | band_selected | emb_selected |   0.579 |   0.506 |    658 |      268 |      152 |        0.674 |
|     100 | bm25_docfirst | band_none    |   0.625 |   0.605 |    959 |       41 |        9 |        0.631 |
|     100 | bm25_docfirst | bm25_chunks  |   0.625 |   0.545 |    782 |      218 |       90 |        0.681 |
|     100 | emb_none      | dense_chunks |   0.537 |   0.537 |    859 |        0 |        0 |        0.537 |
|     350 | bm25_docfirst | emb_none     |   0.700 |   0.657 |    875 |      245 |      177 |        0.811 |
|     350 | band_selected | emb_selected |   0.618 |   0.624 |    735 |      254 |      264 |        0.783 |
|     350 | bm25_docfirst | band_none    |   0.700 |   0.639 |    981 |      139 |       42 |        0.726 |
|     350 | bm25_docfirst | bm25_chunks  |   0.700 |   0.627 |    873 |      247 |      131 |        0.782 |
|     350 | emb_none      | dense_chunks |   0.657 |   0.657 |   1052 |        0 |        0 |        0.657 |

## When the rare band fires (no clusters; the query has a word found in exactly one case)

Otherwise it falls back to full-query BM25, so the two agree on the rest.

|   words |   band fired |   share |   rare band r@1 |   full-query BM25 r@1 |   full-query BM25 r@1, rest |
|--------:|-------------:|--------:|----------------:|----------------------:|----------------------------:|
|      25 |          123 |   0.077 |           0.821 |                 0.821 |                       0.424 |
|     100 |          308 |   0.193 |           0.701 |                 0.805 |                       0.582 |
|     350 |          658 |   0.411 |           0.629 |                 0.777 |                       0.646 |

## Recall@1 by the number of names the query shares with the rest of its case

|   words | names in query   |   queries |   bm25_docfirst r@1 |   band_selected r@1 |   emb_none r@1 |   emb_selected r@1 |
|--------:|:-----------------|----------:|--------------------:|--------------------:|---------------:|-------------------:|
|      25 | 0                |      1367 |               0.376 |               0.340 |          0.272 |              0.238 |
|      25 | 1-2              |       228 |               0.912 |               0.846 |          0.671 |              0.570 |
|      25 | 3+               |         5 |               1.000 |               1.000 |          1.000 |              1.000 |
|     100 | 0                |      1124 |               0.517 |               0.473 |          0.448 |              0.427 |
|     100 | 1-2              |       448 |               0.875 |               0.826 |          0.734 |              0.683 |
|     100 | 3+               |        28 |               0.964 |               0.857 |          0.929 |              0.857 |
|     350 | 0                |       775 |               0.574 |               0.446 |          0.564 |              0.552 |
|     350 | 1-2              |       663 |               0.786 |               0.751 |          0.716 |              0.668 |
|     350 | 3+               |       162 |               0.951 |               0.895 |          0.864 |              0.790 |

## What the wrong top case is (share of errors)

Near-duplicate = at least 0.5 of the smaller case's word 8-grams in the other; same dispute = at least 3 shared names. The name rule fires on 0.000 of 2000 random case pairs.

|   words | method        |   errors |   near-duplicate text |   same dispute |   different dispute |
|--------:|:--------------|---------:|----------------------:|---------------:|--------------------:|
|      25 | bm25_docfirst |      873 |                 0.014 |          0.030 |               0.956 |
|      25 | emb_none      |     1070 |                 0.007 |          0.019 |               0.974 |
|     100 | bm25_docfirst |      600 |                 0.022 |          0.055 |               0.923 |
|     100 | emb_none      |      741 |                 0.018 |          0.038 |               0.945 |
|     350 | bm25_docfirst |      480 |                 0.031 |          0.077 |               0.892 |
|     350 | emb_none      |      548 |                 0.024 |          0.055 |               0.922 |

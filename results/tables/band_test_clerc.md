# E11 test run on clerc: band pipeline vs baselines (647 test queries)

Selected on dev: `{'min_df': 5, 'max_frac': 0.25, 'k': 16, 'rare_below': 10, 'b': 3}`; pre-registered default: `{'min_df': 5, 'max_frac': 0.5, 'k': 8, 'rare_below': 5, 'b': 2}`. One mixed pool of 9777 documents. Macro over subsets. git e1945fb.

## Main metrics (macro over subsets; rdoc_* = the ranked list of documents)

| method                             |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   fallback |   lat_p50_ms |   lat_p95_ms |     qps |   drm@1 |   drm@8 |   drm@10 |
|:-----------------------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-----------:|-------------:|-------------:|--------:|--------:|--------:|---------:|
| band_band_df5_mx25_k16_b3_r10_bm25 |           0.077 |            0.291 |      0.145 |          0.18  |        0.896 |      0.151 |       17.61  |       29.99  |  35.961 |   0.923 |   0.923 |    0.923 |
| band_band_df5_mx50_k8_b2_r5_bm25   |           0.087 |            0.263 |      0.139 |          0.168 |        0.92  |      0.34  |       14.576 |       29.315 |  55.929 |   0.913 |   0.913 |    0.913 |
| band_none_df5_mx25_k16_r10_bm25    |           0.087 |            0.308 |      0.151 |          0.189 |        1     |      0.277 |        6.817 |       22.45  |  97.239 |   0.913 |   0.913 |    0.913 |
| band_oracle_df5_mx25_k16_r10_bm25  |           0.155 |            0.447 |      0.242 |          0.291 |        1     |      0.025 |        7.006 |        9.349 | 138.652 |   0.845 |   0.845 |    0.845 |
| mixed_docfirst_bm25                |           0.116 |            0.501 |      0.212 |          0.279 |        1     |      1     |       20.527 |       23.805 |  49.379 |   0.884 |   0.884 |    0.884 |
| mixed_bm25                         |           0.111 |            0.488 |      0.223 |          0.272 |      nan     |    nan     |       40.651 |       54.296 |  24.274 |   0.889 |   0.923 |    0.925 |

## Document recall@1 per subset

| method                             |   clerc |   ALL |
|:-----------------------------------|--------:|------:|
| band_band_df5_mx25_k16_b3_r10_bm25 |   0.077 | 0.077 |
| band_band_df5_mx50_k8_b2_r5_bm25   |   0.087 | 0.087 |
| band_none_df5_mx25_k16_r10_bm25    |   0.087 | 0.087 |
| band_oracle_df5_mx25_k16_r10_bm25  |   0.155 | 0.155 |
| mixed_docfirst_bm25                |   0.116 | 0.116 |
| mixed_bm25                         |   0.111 | 0.111 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                                  | b                                 | metric        |   clerc |   macro |     lo |     hi | real   |
|:-----------------------------------|:----------------------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| band_band_df5_mx25_k16_b3_r10_bm25 | band_band_df5_mx50_k8_b2_r5_bm25  | rdoc_recall@1 |  -0.009 |  -0.009 | -0.029 |  0.011 | no     |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_band_df5_mx50_k8_b2_r5_bm25  | rdoc_mrr      |   0.006 |   0.006 | -0.015 |  0.026 | no     |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_band_df5_mx50_k8_b2_r5_bm25  | rdoc_ndcg@10  |   0.012 |   0.012 | -0.011 |  0.035 | no     |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_band_df5_mx50_k8_b2_r5_bm25  | drm@8         |   0.009 |   0.009 | -0.011 |  0.029 | no     |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_none_df5_mx25_k16_r10_bm25   | rdoc_recall@1 |  -0.009 |  -0.009 | -0.028 |  0.009 | no     |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_none_df5_mx25_k16_r10_bm25   | rdoc_mrr      |  -0.007 |  -0.007 | -0.023 |  0.01  | no     |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_none_df5_mx25_k16_r10_bm25   | rdoc_ndcg@10  |  -0.009 |  -0.009 | -0.026 |  0.009 | no     |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_none_df5_mx25_k16_r10_bm25   | drm@8         |   0.009 |   0.009 | -0.009 |  0.028 | no     |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_oracle_df5_mx25_k16_r10_bm25 | rdoc_recall@1 |  -0.077 |  -0.077 | -0.101 | -0.054 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_oracle_df5_mx25_k16_r10_bm25 | rdoc_mrr      |  -0.097 |  -0.097 | -0.119 | -0.076 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_oracle_df5_mx25_k16_r10_bm25 | rdoc_ndcg@10  |  -0.111 |  -0.111 | -0.134 | -0.088 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | band_oracle_df5_mx25_k16_r10_bm25 | drm@8         |   0.077 |   0.077 |  0.054 |  0.101 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | mixed_docfirst_bm25               | rdoc_recall@1 |  -0.039 |  -0.039 | -0.064 | -0.014 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | mixed_docfirst_bm25               | rdoc_mrr      |  -0.068 |  -0.068 | -0.092 | -0.045 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | mixed_docfirst_bm25               | rdoc_ndcg@10  |  -0.1   |  -0.1   | -0.125 | -0.076 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | mixed_docfirst_bm25               | drm@8         |   0.039 |   0.039 |  0.014 |  0.064 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | mixed_bm25                        | rdoc_recall@1 |  -0.034 |  -0.034 | -0.062 | -0.006 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | mixed_bm25                        | rdoc_mrr      |  -0.079 |  -0.079 | -0.105 | -0.053 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | mixed_bm25                        | rdoc_ndcg@10  |  -0.092 |  -0.092 | -0.12  | -0.066 | yes    |
| band_band_df5_mx25_k16_b3_r10_bm25 | mixed_bm25                        | drm@8         |  -0     |  -0     | -0.019 |  0.018 | no     |

## Cluster quality and names

**selected**: vocab 56836, cohesion 0.286, sizes 123..1678

0. immunity officials police qualified prison
1. ij bia immigration alien asylum
2. regulation injunction secretary political school
3. patent infringement patents invention copyright
4. bankruptcy debtor bankr trustee creditor
5. discrimination employer vii discriminatory facie
6. vessel maritime negligence admiralty ship
7. arbitration bargaining union labor collective
8. erisa pension retirement plans fiduciary
9. habeas petitioner corpus writ 2254
10. disability alj claimant disabled dr
11. fees fraud award breach market
12. forfeiture seizure seized search liquor
13. tax taxpayer revenue commissioner income
14. search crime police offense indictment
15. sentencing guidelines offense 3553 guideline

**default**: vocab 57699, cohesion 0.318, sizes 220..2205

0. jury conviction criminal crime police
1. disability disabled impairment alj claimant
2. discrimination plaintiffs employment employees summary
3. tax commissioner company supra taxpayer
4. bankruptcy debtor bankr trustee creditor
5. sentencing sentence guidelines offense imprisonment
6. ij bia immigration asylum alien
7. plaintiffs damages contract fees agreement

## Timing (index and extendibility)

```
{
  "chunks": 1074740,
  "chunk_index_s": 132.83877882100023,
  "band_index_selected_s": 120.77916386499965,
  "band_index_default_s": 116.99214024100002,
  "warm_band_band_df5_mx25_k16_b3_r10_bm25_s": 4.5237817950001045,
  "warm_band_band_df5_mx50_k8_b2_r5_bm25_s": 2.3700475599998754,
  "warm_band_none_df5_mx25_k16_r10_bm25_s": 0.13799328399909427,
  "warm_band_oracle_df5_mx25_k16_r10_bm25_s": 0.14299997899979644,
  "warm_mixed_docfirst_bm25_s": 0.13481574300021748,
  "add_one_document": {
    "place_ms": 9.06489350109041,
    "count_row_ms": 1.1843545007650391,
    "recluster_s": 110.06415250200007,
    "kmeans_restarts": 10
  }
}
```

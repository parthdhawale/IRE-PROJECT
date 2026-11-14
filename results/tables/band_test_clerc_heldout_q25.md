# E11 test run on clerc_heldout: band pipeline vs baselines (1600 test queries)

Selected on dev: `{'min_df': 2, 'max_frac': 0.5, 'k': 8, 'rare_below': 2, 'b': 3}`; pre-registered default: `{'min_df': 5, 'max_frac': 0.5, 'k': 8, 'rare_below': 5, 'b': 2}`. One mixed pool of 9777 documents. Macro over subsets. git b92b70b.

## Main metrics (macro over subsets; rdoc_* = the ranked list of documents)

| method                           |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   fallback |   lat_p50_ms |   lat_p95_ms |     qps |   drm@1 |   drm@8 |   drm@10 |
|:---------------------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-----------:|-------------:|-------------:|--------:|--------:|--------:|---------:|
| band_band_df2_mx50_k8_b3_r2_bm25 |           0.414 |            0.586 |      0.465 |          0.494 |        0.888 |      0.902 |        6.483 |        7.705 | 142.533 |   0.586 |   0.586 |    0.586 |
| band_band_df5_mx50_k8_b2_r5_bm25 |           0.357 |            0.511 |      0.404 |          0.43  |        0.773 |      0.774 |        4.73  |        5.951 | 215.103 |   0.643 |   0.643 |    0.643 |
| band_none_df2_mx50_k8_r2_bm25    |           0.454 |            0.64  |      0.51  |          0.541 |        1     |      0.923 |        3.306 |        4.055 | 310.911 |   0.546 |   0.546 |    0.546 |
| band_oracle_df2_mx50_k8_r2_bm25  |           0.482 |            0.69  |      0.545 |          0.579 |        1     |      0.851 |        2.29  |        3.141 | 438.481 |   0.518 |   0.518 |    0.518 |
| mixed_docfirst_bm25              |           0.454 |            0.646 |      0.513 |          0.544 |        1     |      1     |        3.345 |        4.084 | 296.575 |   0.546 |   0.546 |    0.546 |
| mixed_bm25                       |           0.409 |            0.622 |      0.478 |          0.508 |      nan     |    nan     |        6.433 |        8.578 | 153.145 |   0.591 |   0.719 |    0.739 |

## Document recall@1 per subset

| method                           |   clerc |   ALL |
|:---------------------------------|--------:|------:|
| band_band_df2_mx50_k8_b3_r2_bm25 |   0.414 | 0.414 |
| band_band_df5_mx50_k8_b2_r5_bm25 |   0.357 | 0.357 |
| band_none_df2_mx50_k8_r2_bm25    |   0.454 | 0.454 |
| band_oracle_df2_mx50_k8_r2_bm25  |   0.482 | 0.482 |
| mixed_docfirst_bm25              |   0.454 | 0.454 |
| mixed_bm25                       |   0.409 | 0.409 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                                | b                                | metric        |   clerc |   macro |     lo |     hi | real   |
|:---------------------------------|:---------------------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_recall@1 |   0.058 |   0.058 |  0.044 |  0.072 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_mrr      |   0.061 |   0.061 |  0.048 |  0.075 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_ndcg@10  |   0.064 |   0.064 |  0.052 |  0.078 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | drm@8         |  -0.058 |  -0.058 | -0.072 | -0.044 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_recall@1 |  -0.04  |  -0.04  | -0.052 | -0.028 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_mrr      |  -0.045 |  -0.045 | -0.058 | -0.034 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_ndcg@10  |  -0.047 |  -0.047 | -0.06  | -0.036 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | drm@8         |   0.04  |   0.04  |  0.028 |  0.052 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_recall@1 |  -0.068 |  -0.068 | -0.083 | -0.052 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_mrr      |  -0.08  |  -0.08  | -0.093 | -0.065 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_ndcg@10  |  -0.085 |  -0.085 | -0.1   | -0.071 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | drm@8         |   0.068 |   0.068 |  0.052 |  0.083 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_recall@1 |  -0.04  |  -0.04  | -0.052 | -0.027 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_mrr      |  -0.047 |  -0.047 | -0.059 | -0.036 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_ndcg@10  |  -0.051 |  -0.051 | -0.063 | -0.039 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | drm@8         |   0.04  |   0.04  |  0.027 |  0.052 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_recall@1 |   0.006 |   0.006 | -0.016 |  0.029 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_mrr      |  -0.013 |  -0.013 | -0.032 |  0.006 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_ndcg@10  |  -0.014 |  -0.014 | -0.032 |  0.004 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | drm@8         |  -0.133 |  -0.133 | -0.152 | -0.114 | yes    |

## Cluster quality and names

**selected**: vocab 106096, cohesion 0.307, sizes 477..1985

0. plaintiffs constitutional amendment administrative board
1. plaintiffs damages contract fees litigation
2. patent infringement patents invention trademark
3. discrimination employer employment vii discriminatory
4. tax company commissioner taxpayer supra
5. jury conviction criminal crime police
6. sentencing sentence guidelines offense imprisonment
7. bankruptcy debtor bankr trustee debt

**default**: vocab 57441, cohesion 0.318, sizes 254..2290

0. discrimination employer employment vii employee
1. jury conviction criminal crime police
2. constitutional plaintiffs amendment public board
3. plaintiffs contract damages agreement patent
4. vessel negligence maritime accident liability
5. disability alj claimant dr medical
6. bankruptcy debtor bankr trustee debt
7. sentencing sentence guidelines offense imprisonment

## Timing (index and extendibility)

```
{
  "chunks": 1063964,
  "chunk_index_s": 82.4243259040004,
  "band_index_selected_s": 82.69552260899945,
  "band_index_default_s": 63.761224959000174,
  "warm_band_band_df2_mx50_k8_b3_r2_bm25_s": 4.969509286000175,
  "warm_band_band_df5_mx50_k8_b2_r5_bm25_s": 2.737493489999906,
  "warm_band_none_df2_mx50_k8_r2_bm25_s": 0.0722713630002545,
  "warm_band_oracle_df2_mx50_k8_r2_bm25_s": 0.07250796299922513,
  "warm_mixed_docfirst_bm25_s": 0.06833539400031441,
  "add_one_document": {
    "place_ms": 4.107144500267168,
    "count_row_ms": 0.7803049993526656,
    "recluster_s": 85.61044687300091,
    "kmeans_restarts": 10
  }
}
```

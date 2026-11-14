# E11 test run on clerc_heldout: band pipeline vs baselines (1600 test queries)

Selected on dev: `{'min_df': 2, 'max_frac': 0.5, 'k': 8, 'rare_below': 2, 'b': 3}`; pre-registered default: `{'min_df': 5, 'max_frac': 0.5, 'k': 8, 'rare_below': 5, 'b': 2}`. One mixed pool of 9777 documents. Macro over subsets. git b92b70b.

## Main metrics (macro over subsets; rdoc_* = the ranked list of documents)

| method                           |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   fallback |   lat_p50_ms |   lat_p95_ms |     qps |   drm@1 |   drm@8 |   drm@10 |
|:---------------------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-----------:|-------------:|-------------:|--------:|--------:|--------:|---------:|
| band_band_df2_mx50_k8_b3_r2_bm25 |           0.579 |            0.763 |      0.637 |          0.668 |        0.956 |      0.768 |       11.07  |       13.374 |  90.87  |   0.421 |   0.421 |    0.421 |
| band_band_df5_mx50_k8_b2_r5_bm25 |           0.513 |            0.664 |      0.564 |          0.588 |        0.892 |      0.49  |        6.56  |       11.148 | 136.136 |   0.487 |   0.487 |    0.487 |
| band_none_df2_mx50_k8_r2_bm25    |           0.605 |            0.8   |      0.668 |          0.699 |        1     |      0.808 |        6.987 |        8.656 | 158.693 |   0.395 |   0.395 |    0.395 |
| band_oracle_df2_mx50_k8_r2_bm25  |           0.604 |            0.782 |      0.663 |          0.691 |        1     |      0.649 |        5.075 |        7.538 | 207.641 |   0.396 |   0.396 |    0.396 |
| mixed_docfirst_bm25              |           0.625 |            0.842 |      0.696 |          0.731 |        1     |      1     |        7.254 |        8.689 | 138.031 |   0.375 |   0.375 |    0.375 |
| mixed_bm25                       |           0.545 |            0.799 |      0.631 |          0.667 |      nan     |    nan     |       11.721 |       15.588 |  84.126 |   0.455 |   0.555 |    0.576 |

## Document recall@1 per subset

| method                           |   clerc |   ALL |
|:---------------------------------|--------:|------:|
| band_band_df2_mx50_k8_b3_r2_bm25 |   0.579 | 0.579 |
| band_band_df5_mx50_k8_b2_r5_bm25 |   0.513 | 0.513 |
| band_none_df2_mx50_k8_r2_bm25    |   0.605 | 0.605 |
| band_oracle_df2_mx50_k8_r2_bm25  |   0.604 | 0.604 |
| mixed_docfirst_bm25              |   0.625 | 0.625 |
| mixed_bm25                       |   0.545 | 0.545 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                                | b                                | metric        |   clerc |   macro |     lo |     hi | real   |
|:---------------------------------|:---------------------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_recall@1 |   0.066 |   0.066 |  0.048 |  0.084 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_mrr      |   0.073 |   0.073 |  0.057 |  0.089 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_ndcg@10  |   0.079 |   0.079 |  0.063 |  0.096 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | drm@8         |  -0.066 |  -0.066 | -0.084 | -0.048 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_recall@1 |  -0.026 |  -0.026 | -0.038 | -0.015 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_mrr      |  -0.03  |  -0.03  | -0.041 | -0.019 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_ndcg@10  |  -0.032 |  -0.032 | -0.043 | -0.021 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | drm@8         |   0.026 |   0.026 |  0.015 |  0.038 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_recall@1 |  -0.026 |  -0.026 | -0.041 | -0.009 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_mrr      |  -0.025 |  -0.025 | -0.04  | -0.01  | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_ndcg@10  |  -0.024 |  -0.024 | -0.038 | -0.01  | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | drm@8         |   0.026 |   0.026 |  0.009 |  0.041 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_recall@1 |  -0.046 |  -0.046 | -0.059 | -0.034 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_mrr      |  -0.058 |  -0.058 | -0.07  | -0.047 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_ndcg@10  |  -0.063 |  -0.063 | -0.076 | -0.052 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | drm@8         |   0.046 |   0.046 |  0.034 |  0.059 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_recall@1 |   0.034 |   0.034 |  0.011 |  0.056 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_mrr      |   0.007 |   0.007 | -0.013 |  0.026 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_ndcg@10  |   0.001 |   0.001 | -0.019 |  0.019 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | drm@8         |  -0.133 |  -0.133 | -0.154 | -0.115 | yes    |

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
  "chunk_index_s": 84.64253180099968,
  "band_index_selected_s": 84.7460601720004,
  "band_index_default_s": 65.7112805100005,
  "warm_band_band_df2_mx50_k8_b3_r2_bm25_s": 4.863957086000482,
  "warm_band_band_df5_mx50_k8_b2_r5_bm25_s": 2.771545277999394,
  "warm_band_none_df2_mx50_k8_r2_bm25_s": 0.12312883799950214,
  "warm_band_oracle_df2_mx50_k8_r2_bm25_s": 0.12656855899967923,
  "warm_mixed_docfirst_bm25_s": 0.12385178800013819,
  "add_one_document": {
    "place_ms": 4.389619499761466,
    "count_row_ms": 0.7964200003698352,
    "recluster_s": 85.81007255500026,
    "kmeans_restarts": 10
  }
}
```

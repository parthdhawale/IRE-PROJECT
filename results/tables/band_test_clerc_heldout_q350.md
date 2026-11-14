# E11 test run on clerc_heldout: band pipeline vs baselines (1600 test queries)

Selected on dev: `{'min_df': 2, 'max_frac': 0.5, 'k': 8, 'rare_below': 2, 'b': 3}`; pre-registered default: `{'min_df': 5, 'max_frac': 0.5, 'k': 8, 'rare_below': 5, 'b': 2}`. One mixed pool of 9777 documents. Macro over subsets. git b92b70b.

## Main metrics (macro over subsets; rdoc_* = the ranked list of documents)

| method                           |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   fallback |   lat_p50_ms |   lat_p95_ms |     qps |   drm@1 |   drm@8 |   drm@10 |
|:---------------------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-----------:|-------------:|-------------:|--------:|--------:|--------:|---------:|
| band_band_df2_mx50_k8_b3_r2_bm25 |           0.618 |            0.751 |      0.665 |          0.686 |        0.978 |      0.517 |       20.081 |       27.259 |  52.963 |   0.382 |   0.382 |    0.382 |
| band_band_df5_mx50_k8_b2_r5_bm25 |           0.561 |            0.681 |      0.604 |          0.623 |        0.94  |      0.188 |       10.412 |       23.289 |  82.412 |   0.439 |   0.439 |    0.439 |
| band_none_df2_mx50_k8_r2_bm25    |           0.639 |            0.787 |      0.69  |          0.713 |        1     |      0.589 |       16.035 |       20.072 |  79.749 |   0.361 |   0.361 |    0.361 |
| band_oracle_df2_mx50_k8_r2_bm25  |           0.63  |            0.735 |      0.667 |          0.684 |        1     |      0.362 |        7.211 |       18.091 | 103.209 |   0.37  |   0.37  |    0.37  |
| mixed_docfirst_bm25              |           0.7   |            0.902 |      0.768 |          0.801 |        1     |      1     |       17.722 |       20.394 |  56.757 |   0.3   |   0.3   |    0.3   |
| mixed_bm25                       |           0.628 |            0.881 |      0.715 |          0.753 |      nan     |    nan     |       27.507 |       37.304 |  35.755 |   0.372 |   0.445 |    0.464 |

## Document recall@1 per subset

| method                           |   clerc |   ALL |
|:---------------------------------|--------:|------:|
| band_band_df2_mx50_k8_b3_r2_bm25 |   0.618 | 0.618 |
| band_band_df5_mx50_k8_b2_r5_bm25 |   0.561 | 0.561 |
| band_none_df2_mx50_k8_r2_bm25    |   0.639 | 0.639 |
| band_oracle_df2_mx50_k8_r2_bm25  |   0.63  | 0.63  |
| mixed_docfirst_bm25              |   0.7   | 0.7   |
| mixed_bm25                       |   0.628 | 0.628 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                                | b                                | metric        |   clerc |   macro |     lo |     hi | real   |
|:---------------------------------|:---------------------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_recall@1 |   0.058 |   0.058 |  0.034 |  0.08  | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_mrr      |   0.061 |   0.061 |  0.04  |  0.081 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_ndcg@10  |   0.063 |   0.063 |  0.043 |  0.083 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | drm@8         |  -0.058 |  -0.058 | -0.08  | -0.034 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_recall@1 |  -0.021 |  -0.021 | -0.036 | -0.008 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_mrr      |  -0.025 |  -0.025 | -0.039 | -0.011 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_ndcg@10  |  -0.028 |  -0.028 | -0.042 | -0.014 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | drm@8         |   0.021 |   0.021 |  0.008 |  0.036 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_recall@1 |  -0.012 |  -0.012 | -0.032 |  0.008 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_mrr      |  -0.002 |  -0.002 | -0.021 |  0.016 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_ndcg@10  |   0.002 |   0.002 | -0.016 |  0.021 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | drm@8         |   0.012 |   0.012 | -0.008 |  0.032 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_recall@1 |  -0.082 |  -0.082 | -0.099 | -0.064 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_mrr      |  -0.104 |  -0.104 | -0.119 | -0.088 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_ndcg@10  |  -0.115 |  -0.115 | -0.131 | -0.099 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | drm@8         |   0.082 |   0.082 |  0.064 |  0.099 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_recall@1 |  -0.009 |  -0.009 | -0.036 |  0.018 | no     |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_mrr      |  -0.051 |  -0.051 | -0.073 | -0.028 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_ndcg@10  |  -0.067 |  -0.067 | -0.088 | -0.046 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | drm@8         |  -0.063 |  -0.063 | -0.085 | -0.039 | yes    |

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
  "chunk_index_s": 81.9516109569995,
  "band_index_selected_s": 90.5352406080001,
  "band_index_default_s": 67.16047815899947,
  "warm_band_band_df2_mx50_k8_b3_r2_bm25_s": 5.998555943999236,
  "warm_band_band_df5_mx50_k8_b2_r5_bm25_s": 3.2298276030014677,
  "warm_band_none_df2_mx50_k8_r2_bm25_s": 0.3006409560002794,
  "warm_band_oracle_df2_mx50_k8_r2_bm25_s": 0.3049172049995832,
  "warm_mixed_docfirst_bm25_s": 0.29686702499930107,
  "add_one_document": {
    "place_ms": 4.48415400023805,
    "count_row_ms": 0.7391645003735903,
    "recluster_s": 85.72092010599954,
    "kmeans_restarts": 10
  }
}
```

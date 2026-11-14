# E11 test run on clerc_heldout: band pipeline vs baselines (1600 test queries)

Selected on dev: `{'min_df': 2, 'max_frac': 0.5, 'k': 8, 'rare_below': 2, 'b': 3}`; pre-registered default: `{'min_df': 5, 'max_frac': 0.5, 'k': 8, 'rare_below': 5, 'b': 2}`. One mixed pool of 9777 documents. Macro over subsets. git b92b70b.

## Main metrics (macro over subsets; rdoc_* = the ranked list of documents)

| method                           |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   fallback |   lat_p50_ms |   lat_p95_ms |     qps |   drm@1 |   drm@8 |   drm@10 |
|:---------------------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-----------:|-------------:|-------------:|--------:|--------:|--------:|---------:|
| band_band_df2_mx50_k8_b3_r2_bm25 |           0.948 |            0.958 |      0.953 |          0.954 |        0.959 |      0.726 |       11.068 |       13.454 |  91.175 |   0.052 |   0.052 |    0.052 |
| band_band_df5_mx50_k8_b2_r5_bm25 |           0.857 |            0.915 |      0.884 |          0.892 |        0.916 |      0.467 |        6.064 |       11.066 | 138.215 |   0.143 |   0.143 |    0.143 |
| band_none_df2_mx50_k8_r2_bm25    |           0.987 |            0.999 |      0.992 |          0.994 |        1     |      0.762 |        7.025 |        8.831 | 161.266 |   0.013 |   0.013 |    0.013 |
| band_oracle_df2_mx50_k8_r2_bm25  |           0.991 |            0.999 |      0.995 |          0.996 |        1     |      0.589 |        4.809 |        7.808 | 208.994 |   0.009 |   0.009 |    0.009 |
| mixed_docfirst_bm25              |           0.987 |            0.999 |      0.992 |          0.994 |        1     |      1     |        7.372 |        8.939 | 135.6   |   0.013 |   0.013 |    0.013 |
| mixed_bm25                       |           0.991 |            0.999 |      0.995 |          0.996 |      nan     |    nan     |       10.744 |       14.557 |  91.542 |   0.009 |   0.356 |    0.403 |

## Document recall@1 per subset

| method                           |   clerc |   ALL |
|:---------------------------------|--------:|------:|
| band_band_df2_mx50_k8_b3_r2_bm25 |   0.948 | 0.948 |
| band_band_df5_mx50_k8_b2_r5_bm25 |   0.857 | 0.857 |
| band_none_df2_mx50_k8_r2_bm25    |   0.987 | 0.987 |
| band_oracle_df2_mx50_k8_r2_bm25  |   0.991 | 0.991 |
| mixed_docfirst_bm25              |   0.987 | 0.987 |
| mixed_bm25                       |   0.991 | 0.991 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                                | b                                | metric        |   clerc |   macro |     lo |     hi | real   |
|:---------------------------------|:---------------------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_recall@1 |   0.091 |   0.091 |  0.076 |  0.106 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_mrr      |   0.069 |   0.069 |  0.057 |  0.082 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_ndcg@10  |   0.062 |   0.062 |  0.051 |  0.074 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | drm@8         |  -0.091 |  -0.091 | -0.106 | -0.076 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_recall@1 |  -0.039 |  -0.039 | -0.049 | -0.029 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_mrr      |  -0.04  |  -0.04  | -0.049 | -0.03  | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | rdoc_ndcg@10  |  -0.04  |  -0.04  | -0.049 | -0.03  | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_none_df2_mx50_k8_r2_bm25    | drm@8         |   0.039 |   0.039 |  0.029 |  0.049 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_recall@1 |  -0.044 |  -0.044 | -0.053 | -0.034 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_mrr      |  -0.042 |  -0.042 | -0.051 | -0.033 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | rdoc_ndcg@10  |  -0.042 |  -0.042 | -0.05  | -0.033 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | band_oracle_df2_mx50_k8_r2_bm25  | drm@8         |   0.044 |   0.044 |  0.034 |  0.053 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_recall@1 |  -0.039 |  -0.039 | -0.049 | -0.029 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_mrr      |  -0.04  |  -0.04  | -0.049 | -0.03  | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | rdoc_ndcg@10  |  -0.04  |  -0.04  | -0.049 | -0.03  | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_docfirst_bm25              | drm@8         |   0.039 |   0.039 |  0.029 |  0.049 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_recall@1 |  -0.044 |  -0.044 | -0.055 | -0.032 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_mrr      |  -0.043 |  -0.043 | -0.052 | -0.032 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | rdoc_ndcg@10  |  -0.042 |  -0.042 | -0.052 | -0.032 | yes    |
| band_band_df2_mx50_k8_b3_r2_bm25 | mixed_bm25                       | drm@8         |  -0.304 |  -0.304 | -0.321 | -0.286 | yes    |

## Cluster quality and names

**selected**: vocab 106597, cohesion 0.309, sizes 381..2207

0. discrimination employer employment employee vii
1. sentencing sentence guidelines offense imprisonment
2. constitutional plaintiffs amendment board congress
3. plaintiffs damages contract fees patent
4. tax commissioner taxpayer revenue company
5. ij alj disability bia claimant
6. bankruptcy debtor bankr trustee creditor
7. jury conviction criminal crime police

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
  "chunk_index_s": 80.67578863299968,
  "band_index_selected_s": 76.80095451299894,
  "band_index_default_s": 71.07992347599975,
  "warm_band_band_df2_mx50_k8_b3_r2_bm25_s": 5.079817199999525,
  "warm_band_band_df5_mx50_k8_b2_r5_bm25_s": 2.7558755120007845,
  "warm_band_none_df2_mx50_k8_r2_bm25_s": 0.12175414999910572,
  "warm_band_oracle_df2_mx50_k8_r2_bm25_s": 0.1288387889999285,
  "warm_mixed_docfirst_bm25_s": 0.12258239000038884,
  "add_one_document": {
    "place_ms": 4.424889501024154,
    "count_row_ms": 0.7927400001790375,
    "recluster_s": 79.12022081099894,
    "kmeans_restarts": 10
  }
}
```

# E11 test run on clerc: band pipeline vs baselines (5 test queries, SMOKE)

Selected on dev: `{'min_df': 5, 'max_frac': 0.25, 'k': 8, 'rare_below': 2, 'b': 1}`; pre-registered default: `{'min_df': 5, 'max_frac': 0.5, 'k': 8, 'rare_below': 5, 'b': 2}`. One mixed pool of 50 documents. Macro over subsets. git e1945fb.

## Main metrics (macro over subsets; rdoc_* = the ranked list of documents)

| method                           |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   fallback |   lat_p50_ms |   lat_p95_ms |     qps |   drm@1 |   drm@8 |   drm@10 |
|:---------------------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-----------:|-------------:|-------------:|--------:|--------:|--------:|---------:|
| band_band_df5_mx25_k8_b1_r2_bm25 |             0.4 |              0.6 |      0.5   |          0.526 |          0.6 |          0 |        3.487 |        5.882 | 256.519 |     0.6 |   0.6   |     0.6  |
| band_band_df5_mx50_k8_b2_r5_bm25 |             0.6 |              1   |      0.672 |          0.746 |          1   |          0 |        3.554 |        3.642 | 294.313 |     0.4 |   0.4   |     0.4  |
| band_none_df5_mx25_k8_r2_bm25    |             0.6 |              0.8 |      0.667 |          0.7   |          1   |          0 |        2.087 |        2.369 | 482.731 |     0.4 |   0.4   |     0.4  |
| band_oracle_df5_mx25_k8_r2_bm25  |             0.8 |              1   |      0.9   |          0.926 |          1   |          0 |        2.378 |        2.691 | 443.299 |     0.2 |   0.2   |     0.2  |
| mixed_docfirst_bm25              |             0.6 |              1   |      0.707 |          0.777 |          1   |          1 |        4.382 |        4.861 | 236.92  |     0.4 |   0.4   |     0.4  |
| mixed_bm25                       |             0.6 |              1   |      0.662 |          0.738 |        nan   |        nan |        1.647 |       15.493 | 198.451 |     0.4 |   0.525 |     0.58 |

## Document recall@1 per subset

| method                           |   clerc |   ALL |
|:---------------------------------|--------:|------:|
| band_band_df5_mx25_k8_b1_r2_bm25 |     0.4 |   0.4 |
| band_band_df5_mx50_k8_b2_r5_bm25 |     0.6 |   0.6 |
| band_none_df5_mx25_k8_r2_bm25    |     0.6 |   0.6 |
| band_oracle_df5_mx25_k8_r2_bm25  |     0.8 |   0.8 |
| mixed_docfirst_bm25              |     0.6 |   0.6 |
| mixed_bm25                       |     0.6 |   0.6 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                                | b                                | metric        |   clerc |   macro |     lo |     hi | real   |
|:---------------------------------|:---------------------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| band_band_df5_mx25_k8_b1_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_recall@1 |  -0.2   |  -0.2   | -0.6   |  0     | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_mrr      |  -0.172 |  -0.172 | -0.35  | -0.022 | yes    |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | rdoc_ndcg@10  |  -0.22  |  -0.22  | -0.38  | -0.06  | yes    |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_band_df5_mx50_k8_b2_r5_bm25 | drm@8         |   0.2   |   0.2   |  0     |  0.6   | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_none_df5_mx25_k8_r2_bm25    | rdoc_recall@1 |  -0.2   |  -0.2   | -0.6   |  0     | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_none_df5_mx25_k8_r2_bm25    | rdoc_mrr      |  -0.167 |  -0.167 | -0.367 |  0     | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_none_df5_mx25_k8_r2_bm25    | rdoc_ndcg@10  |  -0.174 |  -0.174 | -0.374 |  0     | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_none_df5_mx25_k8_r2_bm25    | drm@8         |   0.2   |   0.2   |  0     |  0.6   | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_oracle_df5_mx25_k8_r2_bm25  | rdoc_recall@1 |  -0.4   |  -0.4   | -0.8   |  0     | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_oracle_df5_mx25_k8_r2_bm25  | rdoc_mrr      |  -0.4   |  -0.4   | -0.8   |  0     | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_oracle_df5_mx25_k8_r2_bm25  | rdoc_ndcg@10  |  -0.4   |  -0.4   | -0.8   |  0     | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | band_oracle_df5_mx25_k8_r2_bm25  | drm@8         |   0.4   |   0.4   |  0     |  0.8   | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | mixed_docfirst_bm25              | rdoc_recall@1 |  -0.2   |  -0.2   | -0.6   |  0     | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | mixed_docfirst_bm25              | rdoc_mrr      |  -0.207 |  -0.207 | -0.373 | -0.04  | yes    |
| band_band_df5_mx25_k8_b1_r2_bm25 | mixed_docfirst_bm25              | rdoc_ndcg@10  |  -0.251 |  -0.251 | -0.429 | -0.074 | yes    |
| band_band_df5_mx25_k8_b1_r2_bm25 | mixed_docfirst_bm25              | drm@8         |   0.2   |   0.2   |  0     |  0.6   | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | mixed_bm25                       | rdoc_recall@1 |  -0.2   |  -0.2   | -0.6   |  0     | no     |
| band_band_df5_mx25_k8_b1_r2_bm25 | mixed_bm25                       | rdoc_mrr      |  -0.162 |  -0.162 | -0.34  | -0.022 | yes    |
| band_band_df5_mx25_k8_b1_r2_bm25 | mixed_bm25                       | rdoc_ndcg@10  |  -0.211 |  -0.211 | -0.363 | -0.06  | yes    |
| band_band_df5_mx25_k8_b1_r2_bm25 | mixed_bm25                       | drm@8         |   0.075 |   0.075 | -0.075 |  0.3   | no     |

## Cluster quality and names

**selected**: vocab 1886, cohesion 0.548, sizes 1..12

0. disclosure product ingredients names privileged
1. theatres conspiracy object overruled affiliated
2. interpleader fund claimants stakeholder pleader
3. error errors bond instructions assignment
4. board employment labor local discrimination
5. patent stores relevancy bowles examination
6. motor car patent field electric
7. bankruptcy debtor bankr loan contempt

**default**: vocab 2543, cohesion 0.598, sizes 1..16

0. interrogatories ingredients corporation production products
1. interrogatories interrogatory objections objection answers
2. interpleader claimants fund 1335 liability
3. interpleader conflicting fear stakeholder ins
4. petitioner wife bona together status
5. work union id congress amendment
6. qualified smith clause belief amendment
7. bankruptcy debtor bankr loan her

## Timing (index and extendibility)

```
{
  "chunks": 3498,
  "chunk_index_s": 0.3581873820000965,
  "band_index_selected_s": 0.1995478409999123,
  "band_index_default_s": 0.16536701399991216,
  "warm_band_band_df5_mx25_k8_b1_r2_bm25_s": 0.0061189060002107,
  "warm_band_band_df5_mx50_k8_b2_r5_bm25_s": 0.006560606999983065,
  "warm_band_none_df5_mx25_k8_r2_bm25_s": 0.0016541689999485243,
  "warm_band_oracle_df5_mx25_k8_r2_bm25_s": 0.0015811789999133907,
  "warm_mixed_docfirst_bm25_s": 0.0015332079999552661,
  "add_one_document": {
    "place_ms": 1.7450025000016467,
    "count_row_ms": 0.7931115001156286,
    "recluster_s": 0.15716663099988182,
    "kmeans_restarts": 10
  }
}
```

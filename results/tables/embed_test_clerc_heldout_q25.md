# E12 test run on clerc_heldout: embedding pipeline vs baselines (1600 test queries)

Selected on dev: `{'k': 8, 'b': 3, 'doc_score': 'maxp'}`; pre-registered default: `{'k': 8, 'b': 2, 'doc_score': 'maxp'}`. One mixed pool of 9777 documents. git b92b70b.

## Main metrics (rdoc_* = the ranked list of documents)

| method              |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   lat_p50_ms |   lat_p95_ms |    qps |   drm@1 |   drm@8 |
|:--------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-------------:|-------------:|-------:|--------:|--------:|
| emb_band_k8_b3_maxp |           0.288 |            0.438 |      0.332 |          0.357 |        0.805 |       33.535 |       41.686 | 30.903 |   0.712 |   0.712 |
| emb_band_k8_b2_maxp |           0.252 |            0.381 |      0.29  |          0.311 |        0.672 |       21.346 |       32.388 | 44.255 |   0.748 |   0.748 |
| emb_none_k8_maxp    |           0.331 |            0.499 |      0.38  |          0.408 |        1     |       69.705 |       74.419 | 14.138 |   0.669 |   0.669 |
| emb_oracle_k8_maxp  |           0.379 |            0.59  |      0.44  |          0.476 |        1     |       10.442 |       16.864 | 85.724 |   0.621 |   0.621 |
| mixed_dense         |           0.331 |            0.499 |      0.386 |          0.408 |      nan     |      135.552 |      142.173 |  7.316 |   0.669 |   0.787 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                   | b                   | metric        |   clerc |   macro |     lo |     hi | real   |
|:--------------------|:--------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | rdoc_recall@1 |   0.036 |   0.036 |  0.026 |  0.045 | yes    |
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | rdoc_mrr      |   0.042 |   0.042 |  0.033 |  0.052 | yes    |
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | rdoc_ndcg@10  |   0.046 |   0.046 |  0.036 |  0.056 | yes    |
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | drm@8         |  -0.036 |  -0.036 | -0.045 | -0.026 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | rdoc_recall@1 |  -0.044 |  -0.044 | -0.056 | -0.032 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | rdoc_mrr      |  -0.048 |  -0.048 | -0.06  | -0.036 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | rdoc_ndcg@10  |  -0.051 |  -0.051 | -0.063 | -0.039 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | drm@8         |   0.044 |   0.044 |  0.032 |  0.056 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | rdoc_recall@1 |  -0.092 |  -0.092 | -0.106 | -0.078 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | rdoc_mrr      |  -0.109 |  -0.109 | -0.122 | -0.096 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | rdoc_ndcg@10  |  -0.119 |  -0.119 | -0.133 | -0.105 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | drm@8         |   0.092 |   0.092 |  0.078 |  0.106 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | rdoc_recall@1 |  -0.044 |  -0.044 | -0.056 | -0.032 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | rdoc_mrr      |  -0.054 |  -0.054 | -0.066 | -0.043 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | rdoc_ndcg@10  |  -0.051 |  -0.051 | -0.063 | -0.039 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | drm@8         |  -0.075 |  -0.075 | -0.09  | -0.06  | yes    |

## Cluster quality

**selected**: largest 2325, smallest 409, cohesion 0.950

## Timing (index and extendibility)

```
{
  "chunks": 1063964,
  "embed_and_index_s": 16.190462726000078,
  "query_encode_ms_per_query": 1.4231241250001858,
  "embed_index_selected_s": 5.059428023999317,
  "add_one_document": {
    "embed_doc_ms": 111.0782374998962,
    "place_ms": 0.2239529999314982,
    "recluster_s": 4.956753889000538
  }
}
```

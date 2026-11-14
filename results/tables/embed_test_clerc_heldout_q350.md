# E12 test run on clerc_heldout: embedding pipeline vs baselines (1600 test queries)

Selected on dev: `{'k': 8, 'b': 3, 'doc_score': 'maxp'}`; pre-registered default: `{'k': 8, 'b': 2, 'doc_score': 'maxp'}`. One mixed pool of 9777 documents. git b92b70b.

## Main metrics (rdoc_* = the ranked list of documents)

| method              |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   lat_p50_ms |   lat_p95_ms |    qps |   drm@1 |   drm@8 |
|:--------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-------------:|-------------:|-------:|--------:|--------:|
| emb_band_k8_b3_maxp |           0.624 |            0.828 |      0.69  |          0.723 |        0.938 |       33.882 |       40.991 | 31.031 |   0.376 |   0.376 |
| emb_band_k8_b2_maxp |           0.589 |            0.775 |      0.649 |          0.679 |        0.874 |       21.118 |       31.907 | 45.496 |   0.411 |   0.411 |
| emb_none_k8_maxp    |           0.658 |            0.873 |      0.729 |          0.764 |        1     |       68.847 |       72.642 | 14.282 |   0.342 |   0.342 |
| emb_oracle_k8_maxp  |           0.704 |            0.911 |      0.772 |          0.805 |        1     |       10.531 |       17.021 | 85.133 |   0.296 |   0.296 |
| mixed_dense         |           0.658 |            0.873 |      0.733 |          0.764 |      nan     |      135.895 |      143.538 |  7.287 |   0.342 |   0.507 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                   | b                   | metric        |   clerc |   macro |     lo |     hi | real   |
|:--------------------|:--------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | rdoc_recall@1 |   0.036 |   0.036 |  0.024 |  0.046 | yes    |
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | rdoc_mrr      |   0.041 |   0.041 |  0.031 |  0.051 | yes    |
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | rdoc_ndcg@10  |   0.044 |   0.044 |  0.033 |  0.054 | yes    |
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | drm@8         |  -0.036 |  -0.036 | -0.046 | -0.024 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | rdoc_recall@1 |  -0.033 |  -0.033 | -0.043 | -0.024 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | rdoc_mrr      |  -0.038 |  -0.038 | -0.048 | -0.029 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | rdoc_ndcg@10  |  -0.04  |  -0.04  | -0.05  | -0.031 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | drm@8         |   0.033 |   0.033 |  0.024 |  0.043 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | rdoc_recall@1 |  -0.08  |  -0.08  | -0.094 | -0.067 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | rdoc_mrr      |  -0.082 |  -0.082 | -0.094 | -0.07  | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | rdoc_ndcg@10  |  -0.082 |  -0.082 | -0.094 | -0.071 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | drm@8         |   0.08  |   0.08  |  0.067 |  0.094 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | rdoc_recall@1 |  -0.033 |  -0.033 | -0.043 | -0.024 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | rdoc_mrr      |  -0.042 |  -0.042 | -0.053 | -0.033 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | rdoc_ndcg@10  |  -0.04  |  -0.04  | -0.05  | -0.031 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | drm@8         |  -0.132 |  -0.132 | -0.15  | -0.113 | yes    |

## Cluster quality

**selected**: largest 2325, smallest 409, cohesion 0.950

## Timing (index and extendibility)

```
{
  "chunks": 1063964,
  "embed_and_index_s": 16.361322769999788,
  "query_encode_ms_per_query": 10.65004072062493,
  "embed_index_selected_s": 4.900360859000102,
  "add_one_document": {
    "embed_doc_ms": 110.99869100007709,
    "place_ms": 0.23405699994327733,
    "recluster_s": 4.775831840000137
  }
}
```

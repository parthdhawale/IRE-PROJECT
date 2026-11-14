# E12 test run on clerc_heldout: embedding pipeline vs baselines (1600 test queries)

Selected on dev: `{'k': 8, 'b': 3, 'doc_score': 'maxp'}`; pre-registered default: `{'k': 8, 'b': 2, 'doc_score': 'maxp'}`. One mixed pool of 9777 documents. git b92b70b.

## Main metrics (rdoc_* = the ranked list of documents)

| method              |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   lat_p50_ms |   lat_p95_ms |    qps |   drm@1 |   drm@8 |
|:--------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-------------:|-------------:|-------:|--------:|--------:|
| emb_band_k8_b3_maxp |           0.506 |            0.715 |      0.573 |          0.607 |        0.916 |       33.769 |       41.533 | 30.627 |   0.494 |   0.494 |
| emb_band_k8_b2_maxp |           0.476 |            0.671 |      0.538 |          0.57  |        0.839 |       20.979 |       32.126 | 45.641 |   0.524 |   0.524 |
| emb_none_k8_maxp    |           0.537 |            0.764 |      0.609 |          0.646 |        1     |       69.078 |       72.683 | 14.244 |   0.463 |   0.463 |
| emb_oracle_k8_maxp  |           0.586 |            0.818 |      0.661 |          0.699 |        1     |       10.506 |       17.189 | 82.283 |   0.414 |   0.414 |
| mixed_dense         |           0.537 |            0.764 |      0.614 |          0.646 |      nan     |      135.642 |      142.882 |  7.326 |   0.463 |   0.616 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                   | b                   | metric        |   clerc |   macro |     lo |     hi | real   |
|:--------------------|:--------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | rdoc_recall@1 |   0.031 |   0.031 |  0.02  |  0.041 | yes    |
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | rdoc_mrr      |   0.035 |   0.035 |  0.024 |  0.045 | yes    |
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | rdoc_ndcg@10  |   0.037 |   0.037 |  0.027 |  0.047 | yes    |
| emb_band_k8_b3_maxp | emb_band_k8_b2_maxp | drm@8         |  -0.031 |  -0.031 | -0.041 | -0.02  | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | rdoc_recall@1 |  -0.031 |  -0.031 | -0.042 | -0.02  | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | rdoc_mrr      |  -0.036 |  -0.036 | -0.047 | -0.027 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | rdoc_ndcg@10  |  -0.039 |  -0.039 | -0.05  | -0.029 | yes    |
| emb_band_k8_b3_maxp | emb_none_k8_maxp    | drm@8         |   0.031 |   0.031 |  0.02  |  0.042 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | rdoc_recall@1 |  -0.079 |  -0.079 | -0.093 | -0.067 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | rdoc_mrr      |  -0.088 |  -0.088 | -0.1   | -0.076 | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | rdoc_ndcg@10  |  -0.091 |  -0.091 | -0.104 | -0.08  | yes    |
| emb_band_k8_b3_maxp | emb_oracle_k8_maxp  | drm@8         |   0.079 |   0.079 |  0.067 |  0.093 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | rdoc_recall@1 |  -0.031 |  -0.031 | -0.042 | -0.02  | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | rdoc_mrr      |  -0.042 |  -0.042 | -0.053 | -0.032 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | rdoc_ndcg@10  |  -0.039 |  -0.039 | -0.05  | -0.029 | yes    |
| emb_band_k8_b3_maxp | mixed_dense         | drm@8         |  -0.122 |  -0.122 | -0.139 | -0.104 | yes    |

## Cluster quality

**selected**: largest 2325, smallest 409, cohesion 0.950

## Timing (index and extendibility)

```
{
  "chunks": 1063964,
  "embed_and_index_s": 16.413114984000458,
  "query_encode_ms_per_query": 4.052352638125285,
  "embed_index_selected_s": 4.781421095999576,
  "add_one_document": {
    "embed_doc_ms": 111.22971199984022,
    "place_ms": 0.22142399984659278,
    "recluster_s": 4.780686801999764
  }
}
```

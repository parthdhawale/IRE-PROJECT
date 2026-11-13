# E12 test run on clerc: embedding pipeline vs baselines (5 test queries, SMOKE)

Selected on dev: `{'k': 8, 'b': 1, 'doc_score': 'mean'}`; pre-registered default: `{'k': 8, 'b': 2, 'doc_score': 'maxp'}`. One mixed pool of 50 documents. git 2ea23f0.

## Main metrics (rdoc_* = the ranked list of documents)

| method              |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   lat_p50_ms |   lat_p95_ms |      qps |   drm@1 |   drm@8 |
|:--------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-------------:|-------------:|---------:|--------:|--------:|
| emb_band_k8_b1_mean |             0.2 |              0.4 |      0.3   |          0.326 |          0.6 |        0.134 |        0.258 | 5597.26  |     0.8 |   0.8   |
| emb_band_k8_b2_maxp |             0.2 |              0.4 |      0.3   |          0.326 |          0.6 |        0.444 |        0.555 | 2287.47  |     0.8 |   0.8   |
| emb_none_k8_mean    |             0.2 |              0.4 |      0.3   |          0.326 |          1   |        0.213 |        0.25  | 4641.78  |     0.8 |   0.8   |
| emb_oracle_k8_mean  |             0.6 |              0.8 |      0.7   |          0.726 |          1   |        0.13  |        0.175 | 7282.15  |     0.4 |   0.4   |
| mixed_dense         |             0.4 |              0.6 |      0.518 |          0.526 |        nan   |        0.464 |        6.521 |  499.925 |     0.6 |   0.775 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                   | b                   | metric        |   clerc |   macro |     lo |    hi | real   |
|:--------------------|:--------------------|:--------------|--------:|--------:|-------:|------:|:-------|
| emb_band_k8_b1_mean | emb_band_k8_b2_maxp | rdoc_recall@1 |   0     |   0     |  0     | 0     | no     |
| emb_band_k8_b1_mean | emb_band_k8_b2_maxp | rdoc_mrr      |   0     |   0     |  0     | 0     | no     |
| emb_band_k8_b1_mean | emb_band_k8_b2_maxp | rdoc_ndcg@10  |   0     |   0     |  0     | 0     | no     |
| emb_band_k8_b1_mean | emb_band_k8_b2_maxp | drm@8         |   0     |   0     |  0     | 0     | no     |
| emb_band_k8_b1_mean | emb_none_k8_mean    | rdoc_recall@1 |   0     |   0     |  0     | 0     | no     |
| emb_band_k8_b1_mean | emb_none_k8_mean    | rdoc_mrr      |   0     |   0     |  0     | 0     | no     |
| emb_band_k8_b1_mean | emb_none_k8_mean    | rdoc_ndcg@10  |   0     |   0     |  0     | 0     | no     |
| emb_band_k8_b1_mean | emb_none_k8_mean    | drm@8         |   0     |   0     |  0     | 0     | no     |
| emb_band_k8_b1_mean | emb_oracle_k8_mean  | rdoc_recall@1 |  -0.4   |  -0.4   | -0.8   | 0     | no     |
| emb_band_k8_b1_mean | emb_oracle_k8_mean  | rdoc_mrr      |  -0.4   |  -0.4   | -0.8   | 0     | no     |
| emb_band_k8_b1_mean | emb_oracle_k8_mean  | rdoc_ndcg@10  |  -0.4   |  -0.4   | -0.8   | 0     | no     |
| emb_band_k8_b1_mean | emb_oracle_k8_mean  | drm@8         |   0.4   |   0.4   |  0     | 0.8   | no     |
| emb_band_k8_b1_mean | mixed_dense         | rdoc_recall@1 |  -0.2   |  -0.2   | -0.6   | 0     | no     |
| emb_band_k8_b1_mean | mixed_dense         | rdoc_mrr      |  -0.218 |  -0.218 | -0.618 | 0     | no     |
| emb_band_k8_b1_mean | mixed_dense         | rdoc_ndcg@10  |  -0.2   |  -0.2   | -0.6   | 0     | no     |
| emb_band_k8_b1_mean | mixed_dense         | drm@8         |   0.025 |   0.025 | -0.2   | 0.225 | no     |

## Cluster quality

**selected**: largest 14, smallest 1, cohesion 0.964

## Timing (index and extendibility)

```
{
  "chunks": 3498,
  "embed_and_index_s": 7.6240405459999465,
  "query_encode_ms_per_query": 60.54556720000619,
  "embed_index_selected_s": 0.02143753099994683,
  "add_one_document": {
    "embed_doc_ms": 124.84334150002496,
    "place_ms": 0.15398050004478137,
    "recluster_s": 0.021640801999978976
  }
}
```

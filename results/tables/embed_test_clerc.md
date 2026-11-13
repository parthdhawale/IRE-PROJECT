# E12 test run on clerc: embedding pipeline vs baselines (647 test queries)

Selected on dev: `{'k': 32, 'b': 3, 'doc_score': 'mean'}`; pre-registered default: `{'k': 8, 'b': 2, 'doc_score': 'maxp'}`. One mixed pool of 9777 documents. git 2ea23f0.

## Main metrics (rdoc_* = the ranked list of documents)

| method               |   rdoc_recall@1 |   rdoc_recall@10 |   rdoc_mrr |   rdoc_ndcg@10 |   in_cluster |   lat_p50_ms |   lat_p95_ms |      qps |   drm@1 |   drm@8 |
|:---------------------|----------------:|-----------------:|-----------:|---------------:|-------------:|-------------:|-------------:|---------:|--------:|--------:|
| emb_band_k32_b3_mean |           0.096 |            0.369 |      0.172 |          0.218 |        0.76  |        0.608 |        0.851 | 1629.86  |   0.904 |   0.904 |
| emb_band_k8_b2_maxp  |           0.073 |            0.363 |      0.148 |          0.198 |        0.805 |       20.114 |       29.043 |   48.778 |   0.927 |   0.927 |
| emb_none_k32_mean    |           0.096 |            0.399 |      0.179 |          0.231 |        1     |        3.045 |        3.389 |  325.065 |   0.904 |   0.904 |
| emb_oracle_k32_mean  |           0.161 |            0.55  |      0.275 |          0.341 |        1     |        0.262 |        0.4   | 3682.62  |   0.839 |   0.839 |
| mixed_dense          |           0.066 |            0.402 |      0.164 |          0.209 |      nan     |      129.014 |      134.671 |    7.703 |   0.934 |   0.944 |

## Paired bootstrap, resampling gold documents (a - b; DRM: negative = a better)

| a                    | b                   | metric        |   clerc |   macro |     lo |     hi | real   |
|:---------------------|:--------------------|:--------------|--------:|--------:|-------:|-------:|:-------|
| emb_band_k32_b3_mean | emb_band_k8_b2_maxp | rdoc_recall@1 |   0.023 |   0.023 | -0.002 |  0.05  | no     |
| emb_band_k32_b3_mean | emb_band_k8_b2_maxp | rdoc_mrr      |   0.024 |   0.024 | -0.001 |  0.049 | no     |
| emb_band_k32_b3_mean | emb_band_k8_b2_maxp | rdoc_ndcg@10  |   0.02  |   0.02  | -0.005 |  0.047 | no     |
| emb_band_k32_b3_mean | emb_band_k8_b2_maxp | drm@8         |  -0.023 |  -0.023 | -0.05  |  0.002 | no     |
| emb_band_k32_b3_mean | emb_none_k32_mean   | rdoc_recall@1 |   0     |   0     | -0.009 |  0.008 | no     |
| emb_band_k32_b3_mean | emb_none_k32_mean   | rdoc_mrr      |  -0.007 |  -0.007 | -0.016 |  0.001 | no     |
| emb_band_k32_b3_mean | emb_none_k32_mean   | rdoc_ndcg@10  |  -0.012 |  -0.012 | -0.022 | -0.003 | yes    |
| emb_band_k32_b3_mean | emb_none_k32_mean   | drm@8         |   0     |   0     | -0.008 |  0.009 | no     |
| emb_band_k32_b3_mean | emb_oracle_k32_mean | rdoc_recall@1 |  -0.065 |  -0.065 | -0.084 | -0.047 | yes    |
| emb_band_k32_b3_mean | emb_oracle_k32_mean | rdoc_mrr      |  -0.104 |  -0.104 | -0.123 | -0.086 | yes    |
| emb_band_k32_b3_mean | emb_oracle_k32_mean | rdoc_ndcg@10  |  -0.122 |  -0.122 | -0.143 | -0.103 | yes    |
| emb_band_k32_b3_mean | emb_oracle_k32_mean | drm@8         |   0.065 |   0.065 |  0.047 |  0.084 | yes    |
| emb_band_k32_b3_mean | mixed_dense         | rdoc_recall@1 |   0.029 |   0.029 |  0.005 |  0.054 | yes    |
| emb_band_k32_b3_mean | mixed_dense         | rdoc_mrr      |   0.007 |   0.007 | -0.016 |  0.034 | no     |
| emb_band_k32_b3_mean | mixed_dense         | rdoc_ndcg@10  |   0.009 |   0.009 | -0.018 |  0.036 | no     |
| emb_band_k32_b3_mean | mixed_dense         | drm@8         |  -0.04  |  -0.04  | -0.063 | -0.02  | yes    |

## Cluster quality

**selected**: largest 721, smallest 64, cohesion 0.957
**default**: largest 1999, smallest 360, cohesion 0.950

## Timing (index and extendibility)

```
{
  "chunks": 1074740,
  "embed_and_index_s": 14.705290282000533,
  "query_encode_ms_per_query": 11.151575088098763,
  "embed_index_selected_s": 6.791562399999748,
  "embed_index_default_s": 4.078905407000093,
  "add_one_document": {
    "embed_doc_ms": 121.7346375001398,
    "place_ms": 0.19869049992848886,
    "recluster_s": 6.726151849999951
  }
}
```

# E12 dev search on clerc: embedding pipeline document choice (5 dev queries, SMOKE)

Selected (most correct dev queries; ties -> smaller k, then b): `{'k': 8, 'b': 1, 'doc_score': 'mean'}`, dev doc recall@1 0.800; 23 setting(s) tied at the best. Pre-registered default: `{'k': 8, 'b': 2, 'doc_score': 'maxp'}`.

## Band (routed) settings

|   k |   b | doc_score   |   doc_recall@1 |   in_cluster |   searched |   r1_clerc |
|----:|----:|:------------|---------------:|-------------:|-----------:|-----------:|
|   8 |   1 | mean        |            0.8 |          0.8 |      0.184 |        0.8 |
|   8 |   2 | mean        |            0.8 |          0.8 |      0.404 |        0.8 |
|   8 |   3 | mean        |            0.8 |          1   |      0.52  |        0.8 |
|  16 |   3 | mean        |            0.8 |          0.8 |      0.24  |        0.8 |
|  16 |   2 | mean        |            0.8 |          0.8 |      0.168 |        0.8 |
|  16 |   1 | mean        |            0.8 |          0.8 |      0.064 |        0.8 |
|  32 |   1 | mean        |            0.8 |          0.8 |      0.04  |        0.8 |
|  32 |   2 | mean        |            0.8 |          0.8 |      0.112 |        0.8 |
|  64 |   2 | mean        |            0.8 |          0.8 |      0.04  |        0.8 |
|  64 |   3 | mean        |            0.8 |          0.8 |      0.06  |        0.8 |
|  64 |   1 | mean        |            0.8 |          0.8 |      0.02  |        0.8 |
|  32 |   2 | maxp        |            0.8 |          0.8 |      0.112 |        0.8 |
|  32 |   1 | maxp        |            0.8 |          0.8 |      0.04  |        0.8 |
|  32 |   3 | mean        |            0.8 |          0.8 |      0.168 |        0.8 |
| 128 |   3 | mean        |            0.8 |          0.8 |      0.06  |        0.8 |
|  64 |   3 | maxp        |            0.8 |          0.8 |      0.06  |        0.8 |
| 128 |   1 | mean        |            0.8 |          0.8 |      0.02  |        0.8 |
| 128 |   2 | mean        |            0.8 |          0.8 |      0.04  |        0.8 |
| 128 |   2 | maxp        |            0.8 |          0.8 |      0.04  |        0.8 |
| 128 |   1 | maxp        |            0.8 |          0.8 |      0.02  |        0.8 |
|  64 |   1 | maxp        |            0.8 |          0.8 |      0.02  |        0.8 |
|  64 |   2 | maxp        |            0.8 |          0.8 |      0.04  |        0.8 |
| 128 |   3 | maxp        |            0.8 |          0.8 |      0.06  |        0.8 |
|  16 |   3 | maxp        |            0.6 |          0.8 |      0.24  |        0.6 |
|  16 |   2 | maxp        |            0.6 |          0.8 |      0.168 |        0.6 |
|   8 |   3 | maxp        |            0.6 |          1   |      0.52  |        0.6 |
|   8 |   2 | maxp        |            0.6 |          0.8 |      0.404 |        0.6 |
|   8 |   1 | maxp        |            0.6 |          0.8 |      0.184 |        0.6 |
|  16 |   1 | maxp        |            0.6 |          0.8 |      0.064 |        0.6 |
|  32 |   3 | maxp        |            0.6 |          0.8 |      0.168 |        0.6 |

## Without clusters (router none = flat dense document choice)

| doc_score   |   doc_recall@1 |
|:------------|---------------:|
| mean        |            0.8 |
| maxp        |            0.6 |

## Oracle routing (gold document's cluster)

|   k | doc_score   |   doc_recall@1 |
|----:|:------------|---------------:|
|   8 | mean        |            0.8 |
|   8 | maxp        |            0.6 |
|  16 | mean        |            0.8 |
|  16 | maxp        |            0.6 |
|  32 | mean        |            1   |
|  32 | maxp        |            1   |
|  64 | mean        |            1   |
|  64 | maxp        |            1   |
| 128 | mean        |            1   |
| 128 | maxp        |            1   |

## Cluster quality per k

|   k |   cohesion |   largest |   smallest |   build_s |
|----:|-----------:|----------:|-----------:|----------:|
|   8 |      0.964 |        14 |          1 |     0.031 |
|  16 |      0.974 |        13 |          1 |     0.02  |
|  32 |      0.99  |         6 |          1 |     0.033 |
|  64 |      1     |         1 |          1 |     0.042 |
| 128 |      1     |         1 |          1 |     0.043 |

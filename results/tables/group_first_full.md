# Group-first vs flat retrieval on one mixed pool of 714 documents (full)

mixed_* = flat search over the whole pool (no routing). gf_<router>_b<B>_<inner> = search only the top-B groups. gf_oracle = the gold document's group (perfect routing). in_beam = share of queries whose gold group was searched. DRM lower is better.

## drm

|                                                            |   drm@1 |   drm@8 |   drm@64 |
|:-----------------------------------------------------------|--------:|--------:|---------:|
| ('contractnli', 'mixed_hybrid')                            |   0.74  |   0.904 |    0.97  |
| ('contractnli', 'mixed_docfirst')                          |   0.318 |   0.318 |    0.318 |
| ('contractnli', 'mixed_docfirst_local')                    |   0.318 |   0.318 |    0.318 |
| ('contractnli', 'mixed_docfirst_local_hdr')                |   0.306 |   0.306 |    0.306 |
| ('contractnli', 'mixed_docfirst_local_rrf')                |   0.301 |   0.301 |    0.301 |
| ('contractnli', 'gfc_oracle_b1_hybrid')                    |   0.712 |   0.874 |    0.956 |
| ('contractnli', 'gfc_oracle_b1_docfirst')                  |   0.242 |   0.242 |    0.242 |
| ('contractnli', 'gfc_oracle_b1_docfirst_local')            |   0.302 |   0.302 |    0.302 |
| ('contractnli', 'gfc_oracle_b1_docfirst_local_hdr')        |   0.25  |   0.25  |    0.25  |
| ('contractnli', 'gfc_oracle_b1_docfirst_local_rrf')        |   0.256 |   0.256 |    0.256 |
| ('contractnli', 'gfc_centroid_full_b2_hybrid')             |   0.74  |   0.903 |    0.969 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst')           |   0.302 |   0.302 |    0.302 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst_local')     |   0.286 |   0.286 |    0.286 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst_local_hdr') |   0.257 |   0.257 |    0.257 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst_local_rrf') |   0.261 |   0.261 |    0.261 |
| ('cuad', 'mixed_hybrid')                                   |   0.022 |   0.211 |    0.557 |
| ('cuad', 'mixed_docfirst')                                 |   0.024 |   0.024 |    0.024 |
| ('cuad', 'mixed_docfirst_local')                           |   0.024 |   0.024 |    0.024 |
| ('cuad', 'mixed_docfirst_local_hdr')                       |   0.023 |   0.023 |    0.023 |
| ('cuad', 'mixed_docfirst_local_rrf')                       |   0.022 |   0.022 |    0.022 |
| ('cuad', 'gfc_oracle_b1_hybrid')                           |   0.021 |   0.202 |    0.542 |
| ('cuad', 'gfc_oracle_b1_docfirst')                         |   0.024 |   0.024 |    0.024 |
| ('cuad', 'gfc_oracle_b1_docfirst_local')                   |   0.022 |   0.022 |    0.022 |
| ('cuad', 'gfc_oracle_b1_docfirst_local_hdr')               |   0.022 |   0.022 |    0.022 |
| ('cuad', 'gfc_oracle_b1_docfirst_local_rrf')               |   0.021 |   0.021 |    0.021 |
| ('cuad', 'gfc_centroid_full_b2_hybrid')                    |   0.022 |   0.211 |    0.556 |
| ('cuad', 'gfc_centroid_full_b2_docfirst')                  |   0.024 |   0.024 |    0.024 |
| ('cuad', 'gfc_centroid_full_b2_docfirst_local')            |   0.024 |   0.024 |    0.024 |
| ('cuad', 'gfc_centroid_full_b2_docfirst_local_hdr')        |   0.024 |   0.024 |    0.024 |
| ('cuad', 'gfc_centroid_full_b2_docfirst_local_rrf')        |   0.023 |   0.023 |    0.023 |
| ('maud', 'mixed_hybrid')                                   |   0.089 |   0.462 |    0.838 |
| ('maud', 'mixed_docfirst')                                 |   0.008 |   0.008 |    0.008 |
| ('maud', 'mixed_docfirst_local')                           |   0.008 |   0.008 |    0.008 |
| ('maud', 'mixed_docfirst_local_hdr')                       |   0.007 |   0.007 |    0.007 |
| ('maud', 'mixed_docfirst_local_rrf')                       |   0.007 |   0.007 |    0.007 |
| ('maud', 'gfc_oracle_b1_hybrid')                           |   0.095 |   0.47  |    0.83  |
| ('maud', 'gfc_oracle_b1_docfirst')                         |   0.008 |   0.008 |    0.008 |
| ('maud', 'gfc_oracle_b1_docfirst_local')                   |   0.008 |   0.008 |    0.008 |
| ('maud', 'gfc_oracle_b1_docfirst_local_hdr')               |   0.007 |   0.007 |    0.007 |
| ('maud', 'gfc_oracle_b1_docfirst_local_rrf')               |   0.007 |   0.007 |    0.007 |
| ('maud', 'gfc_centroid_full_b2_hybrid')                    |   0.089 |   0.462 |    0.838 |
| ('maud', 'gfc_centroid_full_b2_docfirst')                  |   0.008 |   0.008 |    0.008 |
| ('maud', 'gfc_centroid_full_b2_docfirst_local')            |   0.008 |   0.008 |    0.008 |
| ('maud', 'gfc_centroid_full_b2_docfirst_local_hdr')        |   0.007 |   0.007 |    0.007 |
| ('maud', 'gfc_centroid_full_b2_docfirst_local_rrf')        |   0.007 |   0.007 |    0.007 |
| ('privacy_qa', 'mixed_hybrid')                             |   0.113 |   0.251 |    0.641 |
| ('privacy_qa', 'mixed_docfirst')                           |   0.294 |   0.294 |    0.294 |
| ('privacy_qa', 'mixed_docfirst_local')                     |   0.294 |   0.294 |    0.294 |
| ('privacy_qa', 'mixed_docfirst_local_hdr')                 |   0.34  |   0.34  |    0.34  |
| ('privacy_qa', 'mixed_docfirst_local_rrf')                 |   0.351 |   0.351 |    0.351 |
| ('privacy_qa', 'gfc_oracle_b1_hybrid')                     |   0.108 |   0.213 |    0.585 |
| ('privacy_qa', 'gfc_oracle_b1_docfirst')                   |   0.258 |   0.258 |    0.258 |
| ('privacy_qa', 'gfc_oracle_b1_docfirst_local')             |   0.284 |   0.284 |    0.284 |
| ('privacy_qa', 'gfc_oracle_b1_docfirst_local_hdr')         |   0     |   0     |    0     |
| ('privacy_qa', 'gfc_oracle_b1_docfirst_local_rrf')         |   0.134 |   0.134 |    0.134 |
| ('privacy_qa', 'gfc_centroid_full_b2_hybrid')              |   0.108 |   0.225 |    0.602 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst')            |   0.278 |   0.278 |    0.278 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst_local')      |   0.258 |   0.258 |    0.258 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst_local_hdr')  |   0.155 |   0.155 |    0.155 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst_local_rrf')  |   0.139 |   0.139 |    0.139 |
| ('ALL', 'mixed_hybrid')                                    |   0.241 |   0.457 |    0.751 |
| ('ALL', 'mixed_docfirst')                                  |   0.161 |   0.161 |    0.161 |
| ('ALL', 'mixed_docfirst_local')                            |   0.161 |   0.161 |    0.161 |
| ('ALL', 'mixed_docfirst_local_hdr')                        |   0.169 |   0.169 |    0.169 |
| ('ALL', 'mixed_docfirst_local_rrf')                        |   0.17  |   0.17  |    0.17  |
| ('ALL', 'gfc_oracle_b1_hybrid')                            |   0.234 |   0.44  |    0.728 |
| ('ALL', 'gfc_oracle_b1_docfirst')                          |   0.133 |   0.133 |    0.133 |
| ('ALL', 'gfc_oracle_b1_docfirst_local')                    |   0.154 |   0.154 |    0.154 |
| ('ALL', 'gfc_oracle_b1_docfirst_local_hdr')                |   0.07  |   0.07  |    0.07  |
| ('ALL', 'gfc_oracle_b1_docfirst_local_rrf')                |   0.104 |   0.104 |    0.104 |
| ('ALL', 'gfc_centroid_full_b2_hybrid')                     |   0.24  |   0.45  |    0.741 |
| ('ALL', 'gfc_centroid_full_b2_docfirst')                   |   0.153 |   0.153 |    0.153 |
| ('ALL', 'gfc_centroid_full_b2_docfirst_local')             |   0.144 |   0.144 |    0.144 |
| ('ALL', 'gfc_centroid_full_b2_docfirst_local_hdr')         |   0.111 |   0.111 |    0.111 |
| ('ALL', 'gfc_centroid_full_b2_docfirst_local_rrf')         |   0.107 |   0.107 |    0.107 |

## char_r

|                                                            |   char_r@1 |   char_r@8 |   char_r@64 |
|:-----------------------------------------------------------|-----------:|-----------:|------------:|
| ('contractnli', 'mixed_hybrid')                            |      0.034 |      0.095 |       0.217 |
| ('contractnli', 'mixed_docfirst')                          |      0.098 |      0.465 |       0.681 |
| ('contractnli', 'mixed_docfirst_local')                    |      0.098 |      0.465 |       0.681 |
| ('contractnli', 'mixed_docfirst_local_hdr')                |      0.102 |      0.472 |       0.693 |
| ('contractnli', 'mixed_docfirst_local_rrf')                |      0.103 |      0.477 |       0.698 |
| ('contractnli', 'gfc_oracle_b1_hybrid')                    |      0.038 |      0.133 |       0.305 |
| ('contractnli', 'gfc_oracle_b1_docfirst')                  |      0.106 |      0.516 |       0.758 |
| ('contractnli', 'gfc_oracle_b1_docfirst_local')            |      0.097 |      0.474 |       0.697 |
| ('contractnli', 'gfc_oracle_b1_docfirst_local_hdr')        |      0.105 |      0.508 |       0.75  |
| ('contractnli', 'gfc_oracle_b1_docfirst_local_rrf')        |      0.103 |      0.504 |       0.744 |
| ('contractnli', 'gfc_centroid_full_b2_hybrid')             |      0.034 |      0.095 |       0.225 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst')           |      0.099 |      0.474 |       0.697 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst_local')     |      0.104 |      0.487 |       0.714 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst_local_hdr') |      0.106 |      0.504 |       0.742 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst_local_rrf') |      0.106 |      0.502 |       0.738 |
| ('cuad', 'mixed_hybrid')                                   |      0.005 |      0.111 |       0.343 |
| ('cuad', 'mixed_docfirst')                                 |      0.02  |      0.232 |       0.755 |
| ('cuad', 'mixed_docfirst_local')                           |      0.02  |      0.232 |       0.755 |
| ('cuad', 'mixed_docfirst_local_hdr')                       |      0.02  |      0.232 |       0.756 |
| ('cuad', 'mixed_docfirst_local_rrf')                       |      0.02  |      0.232 |       0.756 |
| ('cuad', 'gfc_oracle_b1_hybrid')                           |      0.006 |      0.113 |       0.359 |
| ('cuad', 'gfc_oracle_b1_docfirst')                         |      0.02  |      0.232 |       0.755 |
| ('cuad', 'gfc_oracle_b1_docfirst_local')                   |      0.019 |      0.232 |       0.757 |
| ('cuad', 'gfc_oracle_b1_docfirst_local_hdr')               |      0.02  |      0.233 |       0.758 |
| ('cuad', 'gfc_oracle_b1_docfirst_local_rrf')               |      0.02  |      0.233 |       0.758 |
| ('cuad', 'gfc_centroid_full_b2_hybrid')                    |      0.005 |      0.111 |       0.345 |
| ('cuad', 'gfc_centroid_full_b2_docfirst')                  |      0.02  |      0.232 |       0.755 |
| ('cuad', 'gfc_centroid_full_b2_docfirst_local')            |      0.02  |      0.232 |       0.755 |
| ('cuad', 'gfc_centroid_full_b2_docfirst_local_hdr')        |      0.02  |      0.232 |       0.755 |
| ('cuad', 'gfc_centroid_full_b2_docfirst_local_rrf')        |      0.02  |      0.232 |       0.756 |
| ('maud', 'mixed_hybrid')                                   |      0.002 |      0.013 |       0.058 |
| ('maud', 'mixed_docfirst')                                 |      0.021 |      0.153 |       0.412 |
| ('maud', 'mixed_docfirst_local')                           |      0.021 |      0.153 |       0.412 |
| ('maud', 'mixed_docfirst_local_hdr')                       |      0.021 |      0.153 |       0.412 |
| ('maud', 'mixed_docfirst_local_rrf')                       |      0.021 |      0.153 |       0.412 |
| ('maud', 'gfc_oracle_b1_hybrid')                           |      0.002 |      0.014 |       0.06  |
| ('maud', 'gfc_oracle_b1_docfirst')                         |      0.021 |      0.153 |       0.412 |
| ('maud', 'gfc_oracle_b1_docfirst_local')                   |      0.021 |      0.153 |       0.411 |
| ('maud', 'gfc_oracle_b1_docfirst_local_hdr')               |      0.021 |      0.153 |       0.412 |
| ('maud', 'gfc_oracle_b1_docfirst_local_rrf')               |      0.021 |      0.153 |       0.412 |
| ('maud', 'gfc_centroid_full_b2_hybrid')                    |      0.002 |      0.013 |       0.058 |
| ('maud', 'gfc_centroid_full_b2_docfirst')                  |      0.021 |      0.153 |       0.412 |
| ('maud', 'gfc_centroid_full_b2_docfirst_local')            |      0.021 |      0.154 |       0.412 |
| ('maud', 'gfc_centroid_full_b2_docfirst_local_hdr')        |      0.021 |      0.153 |       0.412 |
| ('maud', 'gfc_centroid_full_b2_docfirst_local_rrf')        |      0.021 |      0.153 |       0.412 |
| ('privacy_qa', 'mixed_hybrid')                             |      0.039 |      0.154 |       0.511 |
| ('privacy_qa', 'mixed_docfirst')                           |      0.049 |      0.237 |       0.671 |
| ('privacy_qa', 'mixed_docfirst_local')                     |      0.049 |      0.237 |       0.671 |
| ('privacy_qa', 'mixed_docfirst_local_hdr')                 |      0.039 |      0.22  |       0.624 |
| ('privacy_qa', 'mixed_docfirst_local_rrf')                 |      0.039 |      0.21  |       0.614 |
| ('privacy_qa', 'gfc_oracle_b1_hybrid')                     |      0.039 |      0.158 |       0.57  |
| ('privacy_qa', 'gfc_oracle_b1_docfirst')                   |      0.056 |      0.263 |       0.707 |
| ('privacy_qa', 'gfc_oracle_b1_docfirst_local')             |      0.049 |      0.241 |       0.682 |
| ('privacy_qa', 'gfc_oracle_b1_docfirst_local_hdr')         |      0.066 |      0.371 |       0.962 |
| ('privacy_qa', 'gfc_oracle_b1_docfirst_local_rrf')         |      0.06  |      0.306 |       0.83  |
| ('privacy_qa', 'gfc_centroid_full_b2_hybrid')              |      0.041 |      0.153 |       0.551 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst')            |      0.054 |      0.249 |       0.686 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst_local')      |      0.05  |      0.257 |       0.706 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst_local_hdr')  |      0.039 |      0.294 |       0.81  |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst_local_rrf')  |      0.048 |      0.313 |       0.825 |
| ('ALL', 'mixed_hybrid')                                    |      0.02  |      0.093 |       0.282 |
| ('ALL', 'mixed_docfirst')                                  |      0.047 |      0.272 |       0.63  |
| ('ALL', 'mixed_docfirst_local')                            |      0.047 |      0.272 |       0.63  |
| ('ALL', 'mixed_docfirst_local_hdr')                        |      0.045 |      0.269 |       0.621 |
| ('ALL', 'mixed_docfirst_local_rrf')                        |      0.045 |      0.268 |       0.62  |
| ('ALL', 'gfc_oracle_b1_hybrid')                            |      0.021 |      0.105 |       0.323 |
| ('ALL', 'gfc_oracle_b1_docfirst')                          |      0.051 |      0.291 |       0.658 |
| ('ALL', 'gfc_oracle_b1_docfirst_local')                    |      0.047 |      0.275 |       0.637 |
| ('ALL', 'gfc_oracle_b1_docfirst_local_hdr')                |      0.053 |      0.316 |       0.72  |
| ('ALL', 'gfc_oracle_b1_docfirst_local_rrf')                |      0.051 |      0.299 |       0.686 |
| ('ALL', 'gfc_centroid_full_b2_hybrid')                     |      0.021 |      0.093 |       0.295 |
| ('ALL', 'gfc_centroid_full_b2_docfirst')                   |      0.048 |      0.277 |       0.638 |
| ('ALL', 'gfc_centroid_full_b2_docfirst_local')             |      0.049 |      0.282 |       0.647 |
| ('ALL', 'gfc_centroid_full_b2_docfirst_local_hdr')         |      0.046 |      0.296 |       0.68  |
| ('ALL', 'gfc_centroid_full_b2_docfirst_local_rrf')         |      0.049 |      0.3   |       0.683 |

## doc_recall

|                                                            |   doc_recall@1 |   doc_recall@8 |   doc_recall@64 |
|:-----------------------------------------------------------|---------------:|---------------:|----------------:|
| ('contractnli', 'mixed_hybrid')                            |          0.26  |          0.43  |           0.735 |
| ('contractnli', 'mixed_docfirst')                          |          0.682 |          0.682 |           0.682 |
| ('contractnli', 'mixed_docfirst_local')                    |          0.682 |          0.682 |           0.682 |
| ('contractnli', 'mixed_docfirst_local_hdr')                |          0.694 |          0.694 |           0.694 |
| ('contractnli', 'mixed_docfirst_local_rrf')                |          0.699 |          0.699 |           0.699 |
| ('contractnli', 'gfc_oracle_b1_hybrid')                    |          0.288 |          0.54  |           0.842 |
| ('contractnli', 'gfc_oracle_b1_docfirst')                  |          0.758 |          0.758 |           0.758 |
| ('contractnli', 'gfc_oracle_b1_docfirst_local')            |          0.698 |          0.698 |           0.698 |
| ('contractnli', 'gfc_oracle_b1_docfirst_local_hdr')        |          0.75  |          0.75  |           0.75  |
| ('contractnli', 'gfc_oracle_b1_docfirst_local_rrf')        |          0.744 |          0.744 |           0.744 |
| ('contractnli', 'gfc_centroid_full_b2_hybrid')             |          0.26  |          0.434 |           0.738 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst')           |          0.698 |          0.698 |           0.698 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst_local')     |          0.714 |          0.714 |           0.714 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst_local_hdr') |          0.743 |          0.743 |           0.743 |
| ('contractnli', 'gfc_centroid_full_b2_docfirst_local_rrf') |          0.739 |          0.739 |           0.739 |
| ('cuad', 'mixed_hybrid')                                   |          0.978 |          1     |           1     |
| ('cuad', 'mixed_docfirst')                                 |          0.976 |          0.976 |           0.976 |
| ('cuad', 'mixed_docfirst_local')                           |          0.976 |          0.976 |           0.976 |
| ('cuad', 'mixed_docfirst_local_hdr')                       |          0.977 |          0.977 |           0.977 |
| ('cuad', 'mixed_docfirst_local_rrf')                       |          0.978 |          0.978 |           0.978 |
| ('cuad', 'gfc_oracle_b1_hybrid')                           |          0.979 |          1     |           1     |
| ('cuad', 'gfc_oracle_b1_docfirst')                         |          0.976 |          0.976 |           0.976 |
| ('cuad', 'gfc_oracle_b1_docfirst_local')                   |          0.978 |          0.978 |           0.978 |
| ('cuad', 'gfc_oracle_b1_docfirst_local_hdr')               |          0.978 |          0.978 |           0.978 |
| ('cuad', 'gfc_oracle_b1_docfirst_local_rrf')               |          0.979 |          0.979 |           0.979 |
| ('cuad', 'gfc_centroid_full_b2_hybrid')                    |          0.978 |          1     |           1     |
| ('cuad', 'gfc_centroid_full_b2_docfirst')                  |          0.976 |          0.976 |           0.976 |
| ('cuad', 'gfc_centroid_full_b2_docfirst_local')            |          0.976 |          0.976 |           0.976 |
| ('cuad', 'gfc_centroid_full_b2_docfirst_local_hdr')        |          0.976 |          0.976 |           0.976 |
| ('cuad', 'gfc_centroid_full_b2_docfirst_local_rrf')        |          0.977 |          0.977 |           0.977 |
| ('maud', 'mixed_hybrid')                                   |          0.911 |          0.986 |           1     |
| ('maud', 'mixed_docfirst')                                 |          0.992 |          0.992 |           0.992 |
| ('maud', 'mixed_docfirst_local')                           |          0.992 |          0.992 |           0.992 |
| ('maud', 'mixed_docfirst_local_hdr')                       |          0.993 |          0.993 |           0.993 |
| ('maud', 'mixed_docfirst_local_rrf')                       |          0.993 |          0.993 |           0.993 |
| ('maud', 'gfc_oracle_b1_hybrid')                           |          0.905 |          0.984 |           1     |
| ('maud', 'gfc_oracle_b1_docfirst')                         |          0.992 |          0.992 |           0.992 |
| ('maud', 'gfc_oracle_b1_docfirst_local')                   |          0.992 |          0.992 |           0.992 |
| ('maud', 'gfc_oracle_b1_docfirst_local_hdr')               |          0.993 |          0.993 |           0.993 |
| ('maud', 'gfc_oracle_b1_docfirst_local_rrf')               |          0.993 |          0.993 |           0.993 |
| ('maud', 'gfc_centroid_full_b2_hybrid')                    |          0.911 |          0.986 |           1     |
| ('maud', 'gfc_centroid_full_b2_docfirst')                  |          0.992 |          0.992 |           0.992 |
| ('maud', 'gfc_centroid_full_b2_docfirst_local')            |          0.992 |          0.992 |           0.992 |
| ('maud', 'gfc_centroid_full_b2_docfirst_local_hdr')        |          0.993 |          0.993 |           0.993 |
| ('maud', 'gfc_centroid_full_b2_docfirst_local_rrf')        |          0.993 |          0.993 |           0.993 |
| ('privacy_qa', 'mixed_hybrid')                             |          0.887 |          0.969 |           1     |
| ('privacy_qa', 'mixed_docfirst')                           |          0.706 |          0.706 |           0.706 |
| ('privacy_qa', 'mixed_docfirst_local')                     |          0.706 |          0.706 |           0.706 |
| ('privacy_qa', 'mixed_docfirst_local_hdr')                 |          0.66  |          0.66  |           0.66  |
| ('privacy_qa', 'mixed_docfirst_local_rrf')                 |          0.649 |          0.649 |           0.649 |
| ('privacy_qa', 'gfc_oracle_b1_hybrid')                     |          0.892 |          0.99  |           1     |
| ('privacy_qa', 'gfc_oracle_b1_docfirst')                   |          0.742 |          0.742 |           0.742 |
| ('privacy_qa', 'gfc_oracle_b1_docfirst_local')             |          0.716 |          0.716 |           0.716 |
| ('privacy_qa', 'gfc_oracle_b1_docfirst_local_hdr')         |          1     |          1     |           1     |
| ('privacy_qa', 'gfc_oracle_b1_docfirst_local_rrf')         |          0.866 |          0.866 |           0.866 |
| ('privacy_qa', 'gfc_centroid_full_b2_hybrid')              |          0.892 |          0.985 |           1     |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst')            |          0.722 |          0.722 |           0.722 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst_local')      |          0.742 |          0.742 |           0.742 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst_local_hdr')  |          0.845 |          0.845 |           0.845 |
| ('privacy_qa', 'gfc_centroid_full_b2_docfirst_local_rrf')  |          0.861 |          0.861 |           0.861 |
| ('ALL', 'mixed_hybrid')                                    |          0.759 |          0.846 |           0.934 |
| ('ALL', 'mixed_docfirst')                                  |          0.839 |          0.839 |           0.839 |
| ('ALL', 'mixed_docfirst_local')                            |          0.839 |          0.839 |           0.839 |
| ('ALL', 'mixed_docfirst_local_hdr')                        |          0.831 |          0.831 |           0.831 |
| ('ALL', 'mixed_docfirst_local_rrf')                        |          0.83  |          0.83  |           0.83  |
| ('ALL', 'gfc_oracle_b1_hybrid')                            |          0.766 |          0.878 |           0.961 |
| ('ALL', 'gfc_oracle_b1_docfirst')                          |          0.867 |          0.867 |           0.867 |
| ('ALL', 'gfc_oracle_b1_docfirst_local')                    |          0.846 |          0.846 |           0.846 |
| ('ALL', 'gfc_oracle_b1_docfirst_local_hdr')                |          0.93  |          0.93  |           0.93  |
| ('ALL', 'gfc_oracle_b1_docfirst_local_rrf')                |          0.896 |          0.896 |           0.896 |
| ('ALL', 'gfc_centroid_full_b2_hybrid')                     |          0.76  |          0.851 |           0.934 |
| ('ALL', 'gfc_centroid_full_b2_docfirst')                   |          0.847 |          0.847 |           0.847 |
| ('ALL', 'gfc_centroid_full_b2_docfirst_local')             |          0.856 |          0.856 |           0.856 |
| ('ALL', 'gfc_centroid_full_b2_docfirst_local_hdr')         |          0.889 |          0.889 |           0.889 |
| ('ALL', 'gfc_centroid_full_b2_docfirst_local_rrf')         |          0.893 |          0.893 |           0.893 |

## in_beam (gold group searched)

| method                                  |   contractnli |   cuad |   maud |   privacy_qa |   ALL |
|:----------------------------------------|--------------:|-------:|-------:|-------------:|------:|
| mixed_hybrid                            |         1     |      1 |      1 |            1 | 1     |
| mixed_docfirst                          |         1     |      1 |      1 |            1 | 1     |
| mixed_docfirst_local                    |         1     |      1 |      1 |            1 | 1     |
| mixed_docfirst_local_hdr                |         1     |      1 |      1 |            1 | 1     |
| mixed_docfirst_local_rrf                |         1     |      1 |      1 |            1 | 1     |
| gfc_oracle_b1_hybrid                    |         1     |      1 |      1 |            1 | 1     |
| gfc_oracle_b1_docfirst                  |         1     |      1 |      1 |            1 | 1     |
| gfc_oracle_b1_docfirst_local            |         1     |      1 |      1 |            1 | 1     |
| gfc_oracle_b1_docfirst_local_hdr        |         1     |      1 |      1 |            1 | 1     |
| gfc_oracle_b1_docfirst_local_rrf        |         1     |      1 |      1 |            1 | 1     |
| gfc_centroid_full_b2_hybrid             |         0.998 |      1 |      1 |            1 | 0.999 |
| gfc_centroid_full_b2_docfirst           |         0.998 |      1 |      1 |            1 | 0.999 |
| gfc_centroid_full_b2_docfirst_local     |         0.998 |      1 |      1 |            1 | 0.999 |
| gfc_centroid_full_b2_docfirst_local_hdr |         0.998 |      1 |      1 |            1 | 0.999 |
| gfc_centroid_full_b2_docfirst_local_rrf |         0.998 |      1 |      1 |            1 | 0.999 |

# Query routing per level (leak-safe document folds), question only

| split   | level   | router        | subset      |   items |   acc@1 |   acc@2 |   acc@3 | ci95@2         | ci95@1         | ci95@3         |
|:--------|:--------|:--------------|:------------|--------:|--------:|--------:|--------:|:---------------|:---------------|:---------------|
| full    | flat    | centroid      | contractnli |     977 |   0.924 |   0.924 |   1     |                |                |                |
| full    | flat    | centroid      | cuad        |    4042 |   0.062 |   0.096 |   0.139 |                |                |                |
| full    | flat    | centroid      | maud        |    1676 |   0     |   0.013 |   0.078 |                |                |                |
| full    | flat    | centroid      | privacy_qa  |     194 |   0.773 |   0.876 |   0.918 |                |                |                |
| full    | flat    | centroid      | ALL         |    6889 |   0.189 |   0.215 |   0.268 | [0.189, 0.246] |                |                |
| full    | flat    | vocab_lr      | contractnli |     977 |   0.924 |   0.924 |   0.924 |                |                |                |
| full    | flat    | vocab_lr      | cuad        |    4042 |   0.036 |   0.063 |   0.089 |                |                |                |
| full    | flat    | vocab_lr      | maud        |    1676 |   0     |   0     |   0     |                |                |                |
| full    | flat    | vocab_lr      | privacy_qa  |     194 |   0.134 |   0.155 |   0.191 |                |                |                |
| full    | flat    | vocab_lr      | ALL         |    6889 |   0.156 |   0.172 |   0.189 | [0.148, 0.199] |                |                |
| full    | flat    | band_lr       | contractnli |     977 |   1     |   1     |   1     |                |                |                |
| full    | flat    | band_lr       | cuad        |    4042 |   0.003 |   0.055 |   0.1   |                |                |                |
| full    | flat    | band_lr       | maud        |    1676 |   0     |   0     |   0     |                |                |                |
| full    | flat    | band_lr       | privacy_qa  |     194 |   0.036 |   0.077 |   0.113 |                |                |                |
| full    | flat    | band_lr       | ALL         |    6889 |   0.144 |   0.176 |   0.204 | [0.150, 0.206] |                |                |
| full    | flat    | nb_band       | contractnli |     977 |   0.703 |   0.93  |   0.969 |                |                |                |
| full    | flat    | nb_band       | cuad        |    4042 |   0.024 |   0.077 |   0.136 |                |                |                |
| full    | flat    | nb_band       | maud        |    1676 |   0.479 |   0.734 |   0.874 |                |                |                |
| full    | flat    | nb_band       | privacy_qa  |     194 |   0.289 |   0.469 |   0.536 |                |                |                |
| full    | flat    | nb_band       | ALL         |    6889 |   0.238 |   0.369 |   0.445 | [0.340, 0.400] |                |                |
| full    | flat    | nb_all        | contractnli |     977 |   0.952 |   0.983 |   1     |                |                |                |
| full    | flat    | nb_all        | cuad        |    4042 |   0.029 |   0.074 |   0.126 |                |                |                |
| full    | flat    | nb_all        | maud        |    1676 |   0.679 |   0.845 |   0.871 |                |                |                |
| full    | flat    | nb_all        | privacy_qa  |     194 |   0.356 |   0.608 |   0.711 |                |                |                |
| full    | flat    | nb_all        | ALL         |    6889 |   0.327 |   0.406 |   0.448 | [0.372, 0.438] |                |                |
| full    | flat    | centroid_full | contractnli |     977 |   0.924 |   0.924 |   0.924 |                |                |                |
| full    | flat    | centroid_full | cuad        |    4042 |   0.062 |   0.113 |   0.166 |                |                |                |
| full    | flat    | centroid_full | maud        |    1676 |   0.095 |   0.161 |   0.199 |                |                |                |
| full    | flat    | centroid_full | privacy_qa  |     194 |   0.918 |   0.948 |   0.964 |                |                |                |
| full    | flat    | centroid_full | ALL         |    6889 |   0.216 |   0.263 |   0.304 | [0.237, 0.294] |                |                |
| full    | flat    | nb_band_bin   | contractnli |     977 |   0.727 |   0.937 |   0.967 |                |                |                |
| full    | flat    | nb_band_bin   | cuad        |    4042 |   0.006 |   0.038 |   0.1   |                |                |                |
| full    | flat    | nb_band_bin   | maud        |    1676 |   0.418 |   0.896 |   0.934 |                |                |                |
| full    | flat    | nb_band_bin   | privacy_qa  |     194 |   0.144 |   0.278 |   0.381 |                |                |                |
| full    | flat    | nb_band_bin   | ALL         |    6889 |   0.213 |   0.381 |   0.434 | [0.346, 0.415] |                |                |
| full    | flat    | cnb_band      | contractnli |     977 |   0.267 |   0.462 |   0.49  |                |                |                |
| full    | flat    | cnb_band      | cuad        |    4042 |   0.042 |   0.095 |   0.137 |                |                |                |
| full    | flat    | cnb_band      | maud        |    1676 |   0.649 |   0.677 |   0.677 |                |                |                |
| full    | flat    | cnb_band      | privacy_qa  |     194 |   0.093 |   0.304 |   0.443 |                |                |                |
| full    | flat    | cnb_band      | ALL         |    6889 |   0.223 |   0.294 |   0.327 | [0.273, 0.318] |                |                |
| full    | flat    | fused         | contractnli |     977 |   1     |   1     |   1     |                |                |                |
| full    | flat    | fused         | cuad        |    4042 |   0.062 |   0.117 |   0.162 |                |                |                |
| full    | flat    | fused         | maud        |    1676 |   0.127 |   0.184 |   0.252 |                |                |                |
| full    | flat    | fused         | privacy_qa  |     194 |   0.51  |   0.691 |   0.758 |                |                |                |
| full    | flat    | fused         | ALL         |    6889 |   0.223 |   0.275 |   0.32  | [0.248, 0.304] |                |                |
| full    | coarse  | centroid      | contractnli |     977 |   0.983 |   1     |   1     |                |                |                |
| full    | coarse  | centroid      | cuad        |    4042 |   0.906 |   1     |   1     |                |                |                |
| full    | coarse  | centroid      | maud        |    1676 |   0     |   0.476 |   0.958 |                |                |                |
| full    | coarse  | centroid      | privacy_qa  |     194 |   0.799 |   0.959 |   0.995 |                |                |                |
| full    | coarse  | centroid      | ALL         |    6889 |   0.694 |   0.871 |   0.99  |                | [0.662, 0.725] |                |
| full    | coarse  | vocab_lr      | contractnli |     977 |   0.957 |   1     |   1     |                |                |                |
| full    | coarse  | vocab_lr      | cuad        |    4042 |   0.608 |   0.997 |   1     |                |                |                |
| full    | coarse  | vocab_lr      | maud        |    1676 |   0     |   0     |   0.069 |                |                |                |
| full    | coarse  | vocab_lr      | privacy_qa  |     194 |   0.052 |   0.144 |   1     |                |                |                |
| full    | coarse  | vocab_lr      | ALL         |    6889 |   0.494 |   0.731 |   0.774 |                | [0.453, 0.533] |                |
| full    | coarse  | band_lr       | contractnli |     977 |   0.827 |   1     |   1     |                |                |                |
| full    | coarse  | band_lr       | cuad        |    4042 |   0.379 |   1     |   1     |                |                |                |
| full    | coarse  | band_lr       | maud        |    1676 |   0     |   0     |   0.079 |                |                |                |
| full    | coarse  | band_lr       | privacy_qa  |     194 |   0     |   0     |   1     |                |                |                |
| full    | coarse  | band_lr       | ALL         |    6889 |   0.339 |   0.729 |   0.776 |                | [0.316, 0.363] |                |
| full    | coarse  | nb_band       | contractnli |     977 |   0.397 |   0.779 |   0.983 |                |                |                |
| full    | coarse  | nb_band       | cuad        |    4042 |   0.891 |   0.988 |   1     |                |                |                |
| full    | coarse  | nb_band       | maud        |    1676 |   0.266 |   0.549 |   0.933 |                |                |                |
| full    | coarse  | nb_band       | privacy_qa  |     194 |   0.222 |   0.418 |   0.835 |                |                |                |
| full    | coarse  | nb_band       | ALL         |    6889 |   0.65  |   0.835 |   0.976 |                | [0.624, 0.675] |                |
| full    | coarse  | nb_all        | contractnli |     977 |   0.924 |   1     |   1     |                |                |                |
| full    | coarse  | nb_all        | cuad        |    4042 |   0.908 |   1     |   1     |                |                |                |
| full    | coarse  | nb_all        | maud        |    1676 |   0.347 |   0.733 |   0.957 |                |                |                |
| full    | coarse  | nb_all        | privacy_qa  |     194 |   0.278 |   0.51  |   0.892 |                |                |                |
| full    | coarse  | nb_all        | ALL         |    6889 |   0.756 |   0.921 |   0.987 |                | [0.733, 0.778] |                |
| full    | coarse  | centroid_full | contractnli |     977 |   0.924 |   0.924 |   1     |                |                |                |
| full    | coarse  | centroid_full | cuad        |    4042 |   0.997 |   1     |   1     |                |                |                |
| full    | coarse  | centroid_full | maud        |    1676 |   0.237 |   0.788 |   1     |                |                |                |
| full    | coarse  | centroid_full | privacy_qa  |     194 |   0.954 |   0.99  |   0.995 |                |                |                |
| full    | coarse  | centroid_full | ALL         |    6889 |   0.801 |   0.937 |   1     |                | [0.774, 0.827] |                |
| full    | coarse  | nb_band_bin   | contractnli |     977 |   0.172 |   0.74  |   1     |                |                |                |
| full    | coarse  | nb_band_bin   | cuad        |    4042 |   0.988 |   0.997 |   1     |                |                |                |
| full    | coarse  | nb_band_bin   | maud        |    1676 |   0.127 |   0.476 |   0.96  |                |                |                |
| full    | coarse  | nb_band_bin   | privacy_qa  |     194 |   0.046 |   0.196 |   0.753 |                |                |                |
| full    | coarse  | nb_band_bin   | ALL         |    6889 |   0.636 |   0.811 |   0.983 |                | [0.600, 0.671] |                |
| full    | coarse  | cnb_band      | contractnli |     977 |   0.047 |   0.634 |   0.9   |                |                |                |
| full    | coarse  | cnb_band      | cuad        |    4042 |   0.656 |   0.689 |   0.694 |                |                |                |
| full    | coarse  | cnb_band      | maud        |    1676 |   0.658 |   0.666 |   0.694 |                |                |                |
| full    | coarse  | cnb_band      | privacy_qa  |     194 |   0.015 |   0.423 |   0.964 |                |                |                |
| full    | coarse  | cnb_band      | ALL         |    6889 |   0.552 |   0.668 |   0.731 |                | [0.530, 0.573] |                |
| full    | coarse  | fused         | contractnli |     977 |   0.762 |   0.983 |   1     |                |                |                |
| full    | coarse  | fused         | cuad        |    4042 |   0.915 |   1     |   1     |                |                |                |
| full    | coarse  | fused         | maud        |    1676 |   0.069 |   0.479 |   0.958 |                |                |                |
| full    | coarse  | fused         | privacy_qa  |     194 |   0.521 |   0.835 |   0.99  |                |                |                |
| full    | coarse  | fused         | ALL         |    6889 |   0.676 |   0.866 |   0.989 |                | [0.647, 0.704] |                |
| full    | fine    | centroid      | cuad        |    4042 |   0.063 |   0.099 |   0.146 |                |                |                |
| full    | fine    | centroid      | ALL         |    4042 |   0.063 |   0.099 |   0.146 |                |                | [0.124, 0.172] |
| full    | fine    | vocab_lr      | cuad        |    4042 |   0.046 |   0.088 |   0.13  |                |                |                |
| full    | fine    | vocab_lr      | ALL         |    4042 |   0.046 |   0.088 |   0.13  |                |                | [0.106, 0.155] |
| full    | fine    | band_lr       | cuad        |    4042 |   0.054 |   0.107 |   0.154 |                |                |                |
| full    | fine    | band_lr       | ALL         |    4042 |   0.054 |   0.107 |   0.154 |                |                | [0.127, 0.183] |
| full    | fine    | nb_band       | cuad        |    4042 |   0.078 |   0.146 |   0.202 |                |                |                |
| full    | fine    | nb_band       | ALL         |    4042 |   0.078 |   0.146 |   0.202 |                |                | [0.182, 0.221] |
| full    | fine    | nb_all        | cuad        |    4042 |   0.064 |   0.127 |   0.187 |                |                |                |
| full    | fine    | nb_all        | ALL         |    4042 |   0.064 |   0.127 |   0.187 |                |                | [0.167, 0.208] |
| full    | fine    | centroid_full | cuad        |    4042 |   0.062 |   0.113 |   0.167 |                |                |                |
| full    | fine    | centroid_full | ALL         |    4042 |   0.062 |   0.113 |   0.167 |                |                | [0.147, 0.188] |
| full    | fine    | nb_band_bin   | cuad        |    4042 |   0.077 |   0.15  |   0.215 |                |                |                |
| full    | fine    | nb_band_bin   | ALL         |    4042 |   0.077 |   0.15  |   0.215 |                |                | [0.191, 0.241] |
| full    | fine    | cnb_band      | cuad        |    4042 |   0.06  |   0.121 |   0.174 |                |                |                |
| full    | fine    | cnb_band      | ALL         |    4042 |   0.06  |   0.121 |   0.174 |                |                | [0.156, 0.193] |
| full    | fine    | fused         | cuad        |    4042 |   0.076 |   0.137 |   0.193 |                |                |                |
| full    | fine    | fused         | ALL         |    4042 |   0.076 |   0.137 |   0.193 |                |                | [0.170, 0.219] |
| mini    | flat    | centroid      | contractnli |     194 |   0.918 |   0.918 |   1     |                |                |                |
| mini    | flat    | centroid      | cuad        |     194 |   0.031 |   0.072 |   0.088 |                |                |                |
| mini    | flat    | centroid      | maud        |     194 |   0     |   0.01  |   0.072 |                |                |                |
| mini    | flat    | centroid      | privacy_qa  |     194 |   0.773 |   0.876 |   0.918 |                |                |                |
| mini    | flat    | centroid      | ALL         |     776 |   0.43  |   0.469 |   0.519 | [0.334, 0.586] |                |                |
| mini    | flat    | vocab_lr      | contractnli |     194 |   0.918 |   0.918 |   0.918 |                |                |                |
| mini    | flat    | vocab_lr      | cuad        |     194 |   0.108 |   0.139 |   0.155 |                |                |                |
| mini    | flat    | vocab_lr      | maud        |     194 |   0     |   0     |   0     |                |                |                |
| mini    | flat    | vocab_lr      | privacy_qa  |     194 |   0.134 |   0.155 |   0.191 |                |                |                |
| mini    | flat    | vocab_lr      | ALL         |     776 |   0.29  |   0.303 |   0.316 | [0.211, 0.407] |                |                |
| mini    | flat    | band_lr       | contractnli |     194 |   1     |   1     |   1     |                |                |                |
| mini    | flat    | band_lr       | cuad        |     194 |   0     |   0.046 |   0.144 |                |                |                |
| mini    | flat    | band_lr       | maud        |     194 |   0     |   0     |   0     |                |                |                |
| mini    | flat    | band_lr       | privacy_qa  |     194 |   0.036 |   0.077 |   0.113 |                |                |                |
| mini    | flat    | band_lr       | ALL         |     776 |   0.259 |   0.281 |   0.314 | [0.178, 0.398] |                |                |
| mini    | flat    | nb_band       | contractnli |     194 |   0.68  |   0.933 |   0.954 |                |                |                |
| mini    | flat    | nb_band       | cuad        |     194 |   0.005 |   0.015 |   0.046 |                |                |                |
| mini    | flat    | nb_band       | maud        |     194 |   0.49  |   0.753 |   0.892 |                |                |                |
| mini    | flat    | nb_band       | privacy_qa  |     194 |   0.289 |   0.469 |   0.536 |                |                |                |
| mini    | flat    | nb_band       | ALL         |     776 |   0.366 |   0.543 |   0.607 | [0.456, 0.626] |                |                |
| mini    | flat    | nb_all        | contractnli |     194 |   0.954 |   0.979 |   1     |                |                |                |
| mini    | flat    | nb_all        | cuad        |     194 |   0.005 |   0.015 |   0.052 |                |                |                |
| mini    | flat    | nb_all        | maud        |     194 |   0.665 |   0.845 |   0.881 |                |                |                |
| mini    | flat    | nb_all        | privacy_qa  |     194 |   0.356 |   0.608 |   0.711 |                |                |                |
| mini    | flat    | nb_all        | ALL         |     776 |   0.495 |   0.612 |   0.661 | [0.521, 0.692] |                |                |
| mini    | flat    | centroid_full | contractnli |     194 |   0.918 |   0.918 |   0.918 |                |                |                |
| mini    | flat    | centroid_full | cuad        |     194 |   0.01  |   0.062 |   0.124 |                |                |                |
| mini    | flat    | centroid_full | maud        |     194 |   0.093 |   0.165 |   0.201 |                |                |                |
| mini    | flat    | centroid_full | privacy_qa  |     194 |   0.918 |   0.948 |   0.964 |                |                |                |
| mini    | flat    | centroid_full | ALL         |     776 |   0.485 |   0.523 |   0.552 | [0.393, 0.635] |                |                |
| mini    | flat    | nb_band_bin   | contractnli |     194 |   0.701 |   0.938 |   0.964 |                |                |                |
| mini    | flat    | nb_band_bin   | cuad        |     194 |   0     |   0     |   0.015 |                |                |                |
| mini    | flat    | nb_band_bin   | maud        |     194 |   0.402 |   0.907 |   0.948 |                |                |                |
| mini    | flat    | nb_band_bin   | privacy_qa  |     194 |   0.144 |   0.278 |   0.381 |                |                |                |
| mini    | flat    | nb_band_bin   | ALL         |     776 |   0.312 |   0.531 |   0.577 | [0.435, 0.634] |                |                |
| mini    | flat    | cnb_band      | contractnli |     194 |   0.227 |   0.433 |   0.464 |                |                |                |
| mini    | flat    | cnb_band      | cuad        |     194 |   0.021 |   0.036 |   0.046 |                |                |                |
| mini    | flat    | cnb_band      | maud        |     194 |   0.66  |   0.686 |   0.686 |                |                |                |
| mini    | flat    | cnb_band      | privacy_qa  |     194 |   0.093 |   0.304 |   0.443 |                |                |                |
| mini    | flat    | cnb_band      | ALL         |     776 |   0.25  |   0.365 |   0.41  | [0.305, 0.429] |                |                |
| mini    | flat    | fused         | contractnli |     194 |   1     |   1     |   1     |                |                |                |
| mini    | flat    | fused         | cuad        |     194 |   0.021 |   0.031 |   0.052 |                |                |                |
| mini    | flat    | fused         | maud        |     194 |   0.108 |   0.18  |   0.242 |                |                |                |
| mini    | flat    | fused         | privacy_qa  |     194 |   0.51  |   0.691 |   0.758 |                |                |                |
| mini    | flat    | fused         | ALL         |     776 |   0.41  |   0.476 |   0.513 | [0.371, 0.565] |                |                |
| mini    | coarse  | centroid      | contractnli |     194 |   1     |   1     |   1     |                |                |                |
| mini    | coarse  | centroid      | cuad        |     194 |   0.897 |   1     |   1     |                |                |                |
| mini    | coarse  | centroid      | maud        |     194 |   0     |   0.459 |   0.969 |                |                |                |
| mini    | coarse  | centroid      | privacy_qa  |     194 |   0.799 |   0.959 |   0.995 |                |                |                |
| mini    | coarse  | centroid      | ALL         |     776 |   0.674 |   0.854 |   0.991 |                | [0.568, 0.770] |                |
| mini    | coarse  | vocab_lr      | contractnli |     194 |   0.954 |   1     |   1     |                |                |                |
| mini    | coarse  | vocab_lr      | cuad        |     194 |   0.722 |   1     |   1     |                |                |                |
| mini    | coarse  | vocab_lr      | maud        |     194 |   0     |   0     |   0.067 |                |                |                |
| mini    | coarse  | vocab_lr      | privacy_qa  |     194 |   0.052 |   0.144 |   1     |                |                |                |
| mini    | coarse  | vocab_lr      | ALL         |     776 |   0.432 |   0.536 |   0.767 |                | [0.317, 0.572] |                |
| mini    | coarse  | band_lr       | contractnli |     194 |   0.82  |   1     |   1     |                |                |                |
| mini    | coarse  | band_lr       | cuad        |     194 |   0.345 |   1     |   1     |                |                |                |
| mini    | coarse  | band_lr       | maud        |     194 |   0     |   0     |   0.072 |                |                |                |
| mini    | coarse  | band_lr       | privacy_qa  |     194 |   0     |   0     |   1     |                |                |                |
| mini    | coarse  | band_lr       | ALL         |     776 |   0.291 |   0.5   |   0.768 |                | [0.201, 0.398] |                |
| mini    | coarse  | nb_band       | contractnli |     194 |   0.356 |   0.763 |   0.979 |                |                |                |
| mini    | coarse  | nb_band       | cuad        |     194 |   0.897 |   0.995 |   1     |                |                |                |
| mini    | coarse  | nb_band       | maud        |     194 |   0.263 |   0.557 |   0.923 |                |                |                |
| mini    | coarse  | nb_band       | privacy_qa  |     194 |   0.222 |   0.418 |   0.835 |                |                |                |
| mini    | coarse  | nb_band       | ALL         |     776 |   0.434 |   0.683 |   0.934 |                | [0.371, 0.515] |                |
| mini    | coarse  | nb_all        | contractnli |     194 |   0.918 |   1     |   1     |                |                |                |
| mini    | coarse  | nb_all        | cuad        |     194 |   0.938 |   1     |   1     |                |                |                |
| mini    | coarse  | nb_all        | maud        |     194 |   0.351 |   0.727 |   0.954 |                |                |                |
| mini    | coarse  | nb_all        | privacy_qa  |     194 |   0.278 |   0.51  |   0.892 |                |                |                |
| mini    | coarse  | nb_all        | ALL         |     776 |   0.621 |   0.809 |   0.961 |                | [0.542, 0.719] |                |
| mini    | coarse  | centroid_full | contractnli |     194 |   0.918 |   0.918 |   1     |                |                |                |
| mini    | coarse  | centroid_full | cuad        |     194 |   1     |   1     |   1     |                |                |                |
| mini    | coarse  | centroid_full | maud        |     194 |   0.227 |   0.768 |   1     |                |                |                |
| mini    | coarse  | centroid_full | privacy_qa  |     194 |   0.954 |   0.99  |   0.995 |                |                |                |
| mini    | coarse  | centroid_full | ALL         |     776 |   0.774 |   0.919 |   0.999 |                | [0.685, 0.851] |                |
| mini    | coarse  | nb_band_bin   | contractnli |     194 |   0.165 |   0.727 |   1     |                |                |                |
| mini    | coarse  | nb_band_bin   | cuad        |     194 |   0.995 |   1     |   1     |                |                |                |
| mini    | coarse  | nb_band_bin   | maud        |     194 |   0.108 |   0.448 |   0.964 |                |                |                |
| mini    | coarse  | nb_band_bin   | privacy_qa  |     194 |   0.046 |   0.196 |   0.753 |                |                |                |
| mini    | coarse  | nb_band_bin   | ALL         |     776 |   0.329 |   0.593 |   0.929 |                | [0.246, 0.445] |                |
| mini    | coarse  | cnb_band      | contractnli |     194 |   0.052 |   0.624 |   0.892 |                |                |                |
| mini    | coarse  | cnb_band      | cuad        |     194 |   0.665 |   0.686 |   0.696 |                |                |                |
| mini    | coarse  | cnb_band      | maud        |     194 |   0.675 |   0.686 |   0.711 |                |                |                |
| mini    | coarse  | cnb_band      | privacy_qa  |     194 |   0.015 |   0.423 |   0.964 |                |                |                |
| mini    | coarse  | cnb_band      | ALL         |     776 |   0.352 |   0.604 |   0.816 |                | [0.264, 0.458] |                |
| mini    | coarse  | fused         | contractnli |     194 |   0.763 |   0.979 |   1     |                |                |                |
| mini    | coarse  | fused         | cuad        |     194 |   0.918 |   1     |   1     |                |                |                |
| mini    | coarse  | fused         | maud        |     194 |   0.067 |   0.469 |   0.969 |                |                |                |
| mini    | coarse  | fused         | privacy_qa  |     194 |   0.521 |   0.835 |   0.99  |                |                |                |
| mini    | coarse  | fused         | ALL         |     776 |   0.567 |   0.821 |   0.99  |                | [0.485, 0.646] |                |
| mini    | fine    | centroid      | cuad        |     194 |   0.036 |   0.072 |   0.088 |                |                |                |
| mini    | fine    | centroid      | ALL         |     194 |   0.036 |   0.072 |   0.088 |                |                | [0.027, 0.176] |
| mini    | fine    | vocab_lr      | cuad        |     194 |   0.072 |   0.113 |   0.222 |                |                |                |
| mini    | fine    | vocab_lr      | ALL         |     194 |   0.072 |   0.113 |   0.222 |                |                | [0.078, 0.389] |
| mini    | fine    | band_lr       | cuad        |     194 |   0.036 |   0.155 |   0.227 |                |                |                |
| mini    | fine    | band_lr       | ALL         |     194 |   0.036 |   0.155 |   0.227 |                |                | [0.075, 0.417] |
| mini    | fine    | nb_band       | cuad        |     194 |   0.031 |   0.052 |   0.088 |                |                |                |
| mini    | fine    | nb_band       | ALL         |     194 |   0.031 |   0.052 |   0.088 |                |                | [0.042, 0.137] |
| mini    | fine    | nb_all        | cuad        |     194 |   0.036 |   0.082 |   0.139 |                |                |                |
| mini    | fine    | nb_all        | ALL         |     194 |   0.036 |   0.082 |   0.139 |                |                | [0.072, 0.200] |
| mini    | fine    | centroid_full | cuad        |     194 |   0.01  |   0.062 |   0.129 |                |                |                |
| mini    | fine    | centroid_full | ALL         |     194 |   0.01  |   0.062 |   0.129 |                |                | [0.067, 0.197] |
| mini    | fine    | nb_band_bin   | cuad        |     194 |   0.01  |   0.031 |   0.077 |                |                |                |
| mini    | fine    | nb_band_bin   | ALL         |     194 |   0.01  |   0.031 |   0.077 |                |                | [0.029, 0.135] |
| mini    | fine    | cnb_band      | cuad        |     194 |   0.036 |   0.062 |   0.072 |                |                |                |
| mini    | fine    | cnb_band      | ALL         |     194 |   0.036 |   0.062 |   0.072 |                |                | [0.033, 0.115] |
| mini    | fine    | fused         | cuad        |     194 |   0.015 |   0.041 |   0.062 |                |                |                |
| mini    | fine    | fused         | ALL         |     194 |   0.015 |   0.041 |   0.062 |                |                | [0.015, 0.128] |

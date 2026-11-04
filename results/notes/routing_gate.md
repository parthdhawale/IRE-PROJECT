# Query routing go/no-go, per level

- **coarse: NO-GO** -- best router `centroid_full`, acc@1 = 0.933 (gate >= 0.95)
- **fine: NO-GO** -- best router `centroid`, acc@3 = 0.906 (gate >= 0.95)

End-to-end for CUAD queries (coarse top-1 correct AND contract type in fine top-3): `centroid` 0.900, `vocab_lr` 0.547, `band_lr` 0.570, `nb_band` 0.724, `nb_all` 0.758, `centroid_full` 0.757, `nb_band_bin` 0.566, `cnb_band` 0.808, `fused` 0.863

## Setup

- Mixed pool: 714 documents. flat = 28 groups (reference only); coarse = 4 subsets; fine = 25 CUAD contract types (CUAD types with < 5 docs merged into cuad/Other), trained on CUAD documents only.
- 5 document-level folds, stratified by group; 4 near-duplicate clusters kept inside one fold. Every level's routers are fit on training-fold documents only and scored on queries whose gold document is held out. Queries are never used for fitting.
- Routers: centroid (BAAI/bge-small-en-v1.5, first 2000 chars), vocab_lr (top-200 discriminative words + logistic regression), band_lr (band words 1%-50% of training docs + logistic regression), nb_band / nb_all (multinomial Naive Bayes on band / all words, alpha=1.0), fused (reciprocal rank fusion of centroid and nb_band, k=60, ties to centroid).
- Gate values were set after the flat (single-level) v1/v2 results had been seen: coarse top-1 because a coarse miss can mean searching the wrong 21% of the corpus, fine top-3 because three CUAD types cover ~4-14% of it.
- CI: 95% bootstrap over gold documents (queries of one document are correlated).

## Results

| split   | level   | router        | subset      |   items |   acc@1 |   acc@2 |   acc@3 | ci95@2         | ci95@1         | ci95@3         |
|:--------|:--------|:--------------|:------------|--------:|--------:|--------:|--------:|:---------------|:---------------|:---------------|
| full    | flat    | centroid      | contractnli |     977 |   0.997 |   0.997 |   1     |                |                |                |
| full    | flat    | centroid      | cuad        |    4042 |   0.739 |   0.855 |   0.904 |                |                |                |
| full    | flat    | centroid      | maud        |    1676 |   0.192 |   0.408 |   0.546 |                |                |                |
| full    | flat    | centroid      | privacy_qa  |     194 |   0.985 |   1     |   1     |                |                |                |
| full    | flat    | centroid      | ALL         |    6889 |   0.65  |   0.77  |   0.833 | [0.740, 0.797] |                |                |
| full    | flat    | vocab_lr      | contractnli |     977 |   0.991 |   0.997 |   0.997 |                |                |                |
| full    | flat    | vocab_lr      | cuad        |    4042 |   0.638 |   0.72  |   0.77  |                |                |                |
| full    | flat    | vocab_lr      | maud        |    1676 |   0     |   0     |   0     |                |                |                |
| full    | flat    | vocab_lr      | privacy_qa  |     194 |   0.124 |   0.144 |   0.18  |                |                |                |
| full    | flat    | vocab_lr      | ALL         |    6889 |   0.518 |   0.568 |   0.598 | [0.529, 0.606] |                |                |
| full    | flat    | band_lr       | contractnli |     977 |   1     |   1     |   1     |                |                |                |
| full    | flat    | band_lr       | cuad        |    4042 |   0.383 |   0.571 |   0.623 |                |                |                |
| full    | flat    | band_lr       | maud        |    1676 |   0     |   0     |   0     |                |                |                |
| full    | flat    | band_lr       | privacy_qa  |     194 |   0.021 |   0.155 |   0.186 |                |                |                |
| full    | flat    | band_lr       | ALL         |    6889 |   0.367 |   0.481 |   0.513 | [0.443, 0.519] |                |                |
| full    | flat    | nb_band       | contractnli |     977 |   0.699 |   0.923 |   0.947 |                |                |                |
| full    | flat    | nb_band       | cuad        |    4042 |   0.52  |   0.656 |   0.717 |                |                |                |
| full    | flat    | nb_band       | maud        |    1676 |   0.878 |   0.942 |   0.97  |                |                |                |
| full    | flat    | nb_band       | privacy_qa  |     194 |   0.68  |   0.902 |   0.948 |                |                |                |
| full    | flat    | nb_band       | ALL         |    6889 |   0.637 |   0.771 |   0.818 | [0.744, 0.797] |                |                |
| full    | flat    | nb_all        | contractnli |     977 |   0.989 |   0.994 |   0.997 |                |                |                |
| full    | flat    | nb_all        | cuad        |    4042 |   0.504 |   0.667 |   0.747 |                |                |                |
| full    | flat    | nb_all        | maud        |    1676 |   0.734 |   0.842 |   0.882 |                |                |                |
| full    | flat    | nb_all        | privacy_qa  |     194 |   0.83  |   0.923 |   0.954 |                |                |                |
| full    | flat    | nb_all        | ALL         |    6889 |   0.638 |   0.763 |   0.821 | [0.734, 0.791] |                |                |
| full    | flat    | centroid_full | contractnli |     977 |   0.992 |   0.994 |   0.995 |                |                |                |
| full    | flat    | centroid_full | cuad        |    4042 |   0.517 |   0.682 |   0.764 |                |                |                |
| full    | flat    | centroid_full | maud        |    1676 |   0.29  |   0.496 |   0.595 |                |                |                |
| full    | flat    | centroid_full | privacy_qa  |     194 |   1     |   1     |   1     |                |                |                |
| full    | flat    | centroid_full | ALL         |    6889 |   0.543 |   0.69  |   0.762 | [0.661, 0.718] |                |                |
| full    | flat    | nb_band_bin   | contractnli |     977 |   0.488 |   0.918 |   0.94  |                |                |                |
| full    | flat    | nb_band_bin   | cuad        |    4042 |   0.329 |   0.463 |   0.547 |                |                |                |
| full    | flat    | nb_band_bin   | maud        |    1676 |   0.696 |   0.807 |   0.852 |                |                |                |
| full    | flat    | nb_band_bin   | privacy_qa  |     194 |   0.134 |   0.232 |   0.351 |                |                |                |
| full    | flat    | nb_band_bin   | ALL         |    6889 |   0.436 |   0.605 |   0.671 | [0.571, 0.640] |                |                |
| full    | flat    | cnb_band      | contractnli |     977 |   0.2   |   0.349 |   0.463 |                |                |                |
| full    | flat    | cnb_band      | cuad        |    4042 |   0.619 |   0.765 |   0.804 |                |                |                |
| full    | flat    | cnb_band      | maud        |    1676 |   0.989 |   0.992 |   0.993 |                |                |                |
| full    | flat    | cnb_band      | privacy_qa  |     194 |   0.289 |   0.66  |   0.887 |                |                |                |
| full    | flat    | cnb_band      | ALL         |    6889 |   0.64  |   0.759 |   0.804 | [0.730, 0.786] |                |                |
| full    | flat    | fused         | contractnli |     977 |   0.962 |   0.983 |   0.993 |                |                |                |
| full    | flat    | fused         | cuad        |    4042 |   0.68  |   0.799 |   0.857 |                |                |                |
| full    | flat    | fused         | maud        |    1676 |   0.64  |   0.807 |   0.89  |                |                |                |
| full    | flat    | fused         | privacy_qa  |     194 |   0.912 |   0.995 |   0.995 |                |                |                |
| full    | flat    | fused         | ALL         |    6889 |   0.717 |   0.832 |   0.888 | [0.809, 0.855] |                |                |
| full    | coarse  | centroid      | contractnli |     977 |   0.997 |   1     |   1     |                |                |                |
| full    | coarse  | centroid      | cuad        |    4042 |   0.993 |   1     |   1     |                |                |                |
| full    | coarse  | centroid      | maud        |    1676 |   0.152 |   0.988 |   1     |                |                |                |
| full    | coarse  | centroid      | privacy_qa  |     194 |   0.99  |   1     |   1     |                |                |                |
| full    | coarse  | centroid      | ALL         |    6889 |   0.789 |   0.997 |   1     |                | [0.757, 0.818] |                |
| full    | coarse  | vocab_lr      | contractnli |     977 |   0.999 |   1     |   1     |                |                |                |
| full    | coarse  | vocab_lr      | cuad        |    4042 |   0.66  |   0.994 |   1     |                |                |                |
| full    | coarse  | vocab_lr      | maud        |    1676 |   0     |   0     |   0.067 |                |                |                |
| full    | coarse  | vocab_lr      | privacy_qa  |     194 |   0.052 |   0.134 |   1     |                |                |                |
| full    | coarse  | vocab_lr      | ALL         |    6889 |   0.53  |   0.729 |   0.773 |                | [0.491, 0.571] |                |
| full    | coarse  | band_lr       | contractnli |     977 |   0.869 |   1     |   1     |                |                |                |
| full    | coarse  | band_lr       | cuad        |    4042 |   0.848 |   1     |   1     |                |                |                |
| full    | coarse  | band_lr       | maud        |    1676 |   0     |   0     |   0.19  |                |                |                |
| full    | coarse  | band_lr       | privacy_qa  |     194 |   0     |   0     |   1     |                |                |                |
| full    | coarse  | band_lr       | ALL         |    6889 |   0.621 |   0.729 |   0.803 |                | [0.582, 0.657] |                |
| full    | coarse  | nb_band       | contractnli |     977 |   0.377 |   0.827 |   0.986 |                |                |                |
| full    | coarse  | nb_band       | cuad        |    4042 |   0.953 |   0.998 |   1     |                |                |                |
| full    | coarse  | nb_band       | maud        |    1676 |   0.82  |   0.958 |   0.991 |                |                |                |
| full    | coarse  | nb_band       | privacy_qa  |     194 |   0.665 |   0.83  |   0.979 |                |                |                |
| full    | coarse  | nb_band       | ALL         |    6889 |   0.831 |   0.96  |   0.995 |                | [0.807, 0.854] |                |
| full    | coarse  | nb_all        | contractnli |     977 |   0.95  |   1     |   1     |                |                |                |
| full    | coarse  | nb_all        | cuad        |    4042 |   0.99  |   1     |   1     |                |                |                |
| full    | coarse  | nb_all        | maud        |    1676 |   0.586 |   0.934 |   0.997 |                |                |                |
| full    | coarse  | nb_all        | privacy_qa  |     194 |   0.784 |   0.928 |   0.974 |                |                |                |
| full    | coarse  | nb_all        | ALL         |    6889 |   0.88  |   0.982 |   0.999 |                | [0.859, 0.901] |                |
| full    | coarse  | centroid_full | contractnli |     977 |   0.996 |   0.998 |   1     |                |                |                |
| full    | coarse  | centroid_full | cuad        |    4042 |   0.992 |   1     |   1     |                |                |                |
| full    | coarse  | centroid_full | maud        |    1676 |   0.748 |   1     |   1     |                |                |                |
| full    | coarse  | centroid_full | privacy_qa  |     194 |   1     |   1     |   1     |                |                |                |
| full    | coarse  | centroid_full | ALL         |    6889 |   0.933 |   1     |   1     |                | [0.918, 0.947] |                |
| full    | coarse  | nb_band_bin   | contractnli |     977 |   0.201 |   0.523 |   1     |                |                |                |
| full    | coarse  | nb_band_bin   | cuad        |    4042 |   0.919 |   0.993 |   0.999 |                |                |                |
| full    | coarse  | nb_band_bin   | maud        |    1676 |   0.271 |   0.778 |   0.98  |                |                |                |
| full    | coarse  | nb_band_bin   | privacy_qa  |     194 |   0.041 |   0.211 |   0.675 |                |                |                |
| full    | coarse  | nb_band_bin   | ALL         |    6889 |   0.635 |   0.852 |   0.985 |                | [0.600, 0.670] |                |
| full    | coarse  | cnb_band      | contractnli |     977 |   0.055 |   0.71  |   0.982 |                |                |                |
| full    | coarse  | cnb_band      | cuad        |    4042 |   0.968 |   0.99  |   0.991 |                |                |                |
| full    | coarse  | cnb_band      | maud        |    1676 |   0.918 |   0.994 |   0.994 |                |                |                |
| full    | coarse  | cnb_band      | privacy_qa  |     194 |   0.093 |   0.655 |   1     |                |                |                |
| full    | coarse  | cnb_band      | ALL         |    6889 |   0.801 |   0.942 |   0.991 |                | [0.769, 0.832] |                |
| full    | coarse  | fused         | contractnli |     977 |   0.843 |   1     |   1     |                |                |                |
| full    | coarse  | fused         | cuad        |    4042 |   0.994 |   1     |   1     |                |                |                |
| full    | coarse  | fused         | maud        |    1676 |   0.153 |   0.989 |   1     |                |                |                |
| full    | coarse  | fused         | privacy_qa  |     194 |   0.892 |   0.995 |   1     |                |                |                |
| full    | coarse  | fused         | ALL         |    6889 |   0.765 |   0.997 |   1     |                | [0.734, 0.793] |                |
| full    | fine    | centroid      | cuad        |    4042 |   0.739 |   0.855 |   0.906 |                |                |                |
| full    | fine    | centroid      | ALL         |    4042 |   0.739 |   0.855 |   0.906 |                |                | [0.880, 0.931] |
| full    | fine    | vocab_lr      | cuad        |    4042 |   0.659 |   0.749 |   0.792 |                |                |                |
| full    | fine    | vocab_lr      | ALL         |    4042 |   0.659 |   0.749 |   0.792 |                |                | [0.753, 0.828] |
| full    | fine    | band_lr       | cuad        |    4042 |   0.535 |   0.597 |   0.63  |                |                |                |
| full    | fine    | band_lr       | ALL         |    4042 |   0.535 |   0.597 |   0.63  |                |                | [0.582, 0.678] |
| full    | fine    | nb_band       | cuad        |    4042 |   0.549 |   0.682 |   0.754 |                |                |                |
| full    | fine    | nb_band       | ALL         |    4042 |   0.549 |   0.682 |   0.754 |                |                | [0.717, 0.790] |
| full    | fine    | nb_all        | cuad        |    4042 |   0.518 |   0.68  |   0.765 |                |                |                |
| full    | fine    | nb_all        | ALL         |    4042 |   0.518 |   0.68  |   0.765 |                |                | [0.732, 0.801] |
| full    | fine    | centroid_full | cuad        |    4042 |   0.517 |   0.682 |   0.764 |                |                |                |
| full    | fine    | centroid_full | ALL         |    4042 |   0.517 |   0.682 |   0.764 |                |                | [0.728, 0.798] |
| full    | fine    | nb_band_bin   | cuad        |    4042 |   0.418 |   0.537 |   0.616 |                |                |                |
| full    | fine    | nb_band_bin   | ALL         |    4042 |   0.418 |   0.537 |   0.616 |                |                | [0.578, 0.662] |
| full    | fine    | cnb_band      | cuad        |    4042 |   0.627 |   0.787 |   0.829 |                |                |                |
| full    | fine    | cnb_band      | ALL         |    4042 |   0.627 |   0.787 |   0.829 |                |                | [0.793, 0.860] |
| full    | fine    | fused         | cuad        |    4042 |   0.69  |   0.811 |   0.868 |                |                |                |
| full    | fine    | fused         | ALL         |    4042 |   0.69  |   0.811 |   0.868 |                |                | [0.839, 0.896] |
| mini    | flat    | centroid      | contractnli |     194 |   0.995 |   0.995 |   1     |                |                |                |
| mini    | flat    | centroid      | cuad        |     194 |   0.686 |   0.799 |   0.866 |                |                |                |
| mini    | flat    | centroid      | maud        |     194 |   0.113 |   0.433 |   0.613 |                |                |                |
| mini    | flat    | centroid      | privacy_qa  |     194 |   0.985 |   1     |   1     |                |                |                |
| mini    | flat    | centroid      | ALL         |     776 |   0.695 |   0.807 |   0.87  | [0.714, 0.880] |                |                |
| mini    | flat    | vocab_lr      | contractnli |     194 |   0.99  |   0.995 |   0.995 |                |                |                |
| mini    | flat    | vocab_lr      | cuad        |     194 |   0.753 |   0.814 |   0.82  |                |                |                |
| mini    | flat    | vocab_lr      | maud        |     194 |   0     |   0     |   0     |                |                |                |
| mini    | flat    | vocab_lr      | privacy_qa  |     194 |   0.124 |   0.144 |   0.18  |                |                |                |
| mini    | flat    | vocab_lr      | ALL         |     776 |   0.466 |   0.488 |   0.499 | [0.375, 0.624] |                |                |
| mini    | flat    | band_lr       | contractnli |     194 |   1     |   1     |   1     |                |                |                |
| mini    | flat    | band_lr       | cuad        |     194 |   0.392 |   0.613 |   0.639 |                |                |                |
| mini    | flat    | band_lr       | maud        |     194 |   0     |   0     |   0     |                |                |                |
| mini    | flat    | band_lr       | privacy_qa  |     194 |   0.021 |   0.155 |   0.186 |                |                |                |
| mini    | flat    | band_lr       | ALL         |     776 |   0.353 |   0.442 |   0.456 | [0.335, 0.574] |                |                |
| mini    | flat    | nb_band       | contractnli |     194 |   0.644 |   0.876 |   0.897 |                |                |                |
| mini    | flat    | nb_band       | cuad        |     194 |   0.418 |   0.495 |   0.577 |                |                |                |
| mini    | flat    | nb_band       | maud        |     194 |   0.82  |   0.902 |   0.959 |                |                |                |
| mini    | flat    | nb_band       | privacy_qa  |     194 |   0.68  |   0.902 |   0.948 |                |                |                |
| mini    | flat    | nb_band       | ALL         |     776 |   0.64  |   0.794 |   0.845 | [0.713, 0.864] |                |                |
| mini    | flat    | nb_all        | contractnli |     194 |   0.969 |   0.974 |   0.99  |                |                |                |
| mini    | flat    | nb_all        | cuad        |     194 |   0.448 |   0.603 |   0.655 |                |                |                |
| mini    | flat    | nb_all        | maud        |     194 |   0.753 |   0.861 |   0.907 |                |                |                |
| mini    | flat    | nb_all        | privacy_qa  |     194 |   0.83  |   0.923 |   0.954 |                |                |                |
| mini    | flat    | nb_all        | ALL         |     776 |   0.75  |   0.84  |   0.876 | [0.770, 0.893] |                |                |
| mini    | flat    | centroid_full | contractnli |     194 |   0.99  |   0.995 |   0.995 |                |                |                |
| mini    | flat    | centroid_full | cuad        |     194 |   0.495 |   0.639 |   0.732 |                |                |                |
| mini    | flat    | centroid_full | maud        |     194 |   0.294 |   0.438 |   0.5   |                |                |                |
| mini    | flat    | centroid_full | privacy_qa  |     194 |   1     |   1     |   1     |                |                |                |
| mini    | flat    | centroid_full | ALL         |     776 |   0.695 |   0.768 |   0.807 | [0.671, 0.851] |                |                |
| mini    | flat    | nb_band_bin   | contractnli |     194 |   0.438 |   0.876 |   0.902 |                |                |                |
| mini    | flat    | nb_band_bin   | cuad        |     194 |   0.237 |   0.351 |   0.407 |                |                |                |
| mini    | flat    | nb_band_bin   | maud        |     194 |   0.603 |   0.727 |   0.804 |                |                |                |
| mini    | flat    | nb_band_bin   | privacy_qa  |     194 |   0.134 |   0.232 |   0.351 |                |                |                |
| mini    | flat    | nb_band_bin   | ALL         |     776 |   0.353 |   0.546 |   0.616 | [0.447, 0.649] |                |                |
| mini    | flat    | cnb_band      | contractnli |     194 |   0.16  |   0.294 |   0.443 |                |                |                |
| mini    | flat    | cnb_band      | cuad        |     194 |   0.619 |   0.691 |   0.758 |                |                |                |
| mini    | flat    | cnb_band      | maud        |     194 |   0.995 |   1     |   1     |                |                |                |
| mini    | flat    | cnb_band      | privacy_qa  |     194 |   0.289 |   0.66  |   0.887 |                |                |                |
| mini    | flat    | cnb_band      | ALL         |     776 |   0.515 |   0.661 |   0.772 | [0.572, 0.749] |                |                |
| mini    | flat    | fused         | contractnli |     194 |   0.938 |   0.954 |   0.969 |                |                |                |
| mini    | flat    | fused         | cuad        |     194 |   0.562 |   0.716 |   0.789 |                |                |                |
| mini    | flat    | fused         | maud        |     194 |   0.66  |   0.809 |   0.918 |                |                |                |
| mini    | flat    | fused         | privacy_qa  |     194 |   0.912 |   0.995 |   0.995 |                |                |                |
| mini    | flat    | fused         | ALL         |     776 |   0.768 |   0.869 |   0.918 | [0.798, 0.920] |                |                |
| mini    | coarse  | centroid      | contractnli |     194 |   0.995 |   1     |   1     |                |                |                |
| mini    | coarse  | centroid      | cuad        |     194 |   0.995 |   1     |   1     |                |                |                |
| mini    | coarse  | centroid      | maud        |     194 |   0.191 |   0.99  |   1     |                |                |                |
| mini    | coarse  | centroid      | privacy_qa  |     194 |   0.99  |   1     |   1     |                |                |                |
| mini    | coarse  | centroid      | ALL         |     776 |   0.793 |   0.997 |   1     |                | [0.691, 0.879] |                |
| mini    | coarse  | vocab_lr      | contractnli |     194 |   0.995 |   1     |   1     |                |                |                |
| mini    | coarse  | vocab_lr      | cuad        |     194 |   0.634 |   1     |   1     |                |                |                |
| mini    | coarse  | vocab_lr      | maud        |     194 |   0     |   0     |   0.067 |                |                |                |
| mini    | coarse  | vocab_lr      | privacy_qa  |     194 |   0.052 |   0.134 |   1     |                |                |                |
| mini    | coarse  | vocab_lr      | ALL         |     776 |   0.42  |   0.534 |   0.767 |                | [0.305, 0.562] |                |
| mini    | coarse  | band_lr       | contractnli |     194 |   0.876 |   1     |   1     |                |                |                |
| mini    | coarse  | band_lr       | cuad        |     194 |   0.876 |   1     |   1     |                |                |                |
| mini    | coarse  | band_lr       | maud        |     194 |   0     |   0     |   0.139 |                |                |                |
| mini    | coarse  | band_lr       | privacy_qa  |     194 |   0     |   0     |   1     |                |                |                |
| mini    | coarse  | band_lr       | ALL         |     776 |   0.438 |   0.5   |   0.785 |                | [0.313, 0.573] |                |
| mini    | coarse  | nb_band       | contractnli |     194 |   0.325 |   0.814 |   0.985 |                |                |                |
| mini    | coarse  | nb_band       | cuad        |     194 |   0.969 |   1     |   1     |                |                |                |
| mini    | coarse  | nb_band       | maud        |     194 |   0.763 |   0.912 |   0.995 |                |                |                |
| mini    | coarse  | nb_band       | privacy_qa  |     194 |   0.665 |   0.83  |   0.979 |                |                |                |
| mini    | coarse  | nb_band       | ALL         |     776 |   0.68  |   0.889 |   0.99  |                | [0.603, 0.757] |                |
| mini    | coarse  | nb_all        | contractnli |     194 |   0.912 |   1     |   1     |                |                |                |
| mini    | coarse  | nb_all        | cuad        |     194 |   1     |   1     |   1     |                |                |                |
| mini    | coarse  | nb_all        | maud        |     194 |   0.485 |   0.907 |   0.99  |                |                |                |
| mini    | coarse  | nb_all        | privacy_qa  |     194 |   0.784 |   0.928 |   0.974 |                |                |                |
| mini    | coarse  | nb_all        | ALL         |     776 |   0.795 |   0.959 |   0.991 |                | [0.724, 0.856] |                |
| mini    | coarse  | centroid_full | contractnli |     194 |   0.995 |   0.995 |   1     |                |                |                |
| mini    | coarse  | centroid_full | cuad        |     194 |   1     |   1     |   1     |                |                |                |
| mini    | coarse  | centroid_full | maud        |     194 |   0.655 |   1     |   1     |                |                |                |
| mini    | coarse  | centroid_full | privacy_qa  |     194 |   1     |   1     |   1     |                |                |                |
| mini    | coarse  | centroid_full | ALL         |     776 |   0.912 |   0.999 |   1     |                | [0.849, 0.962] |                |
| mini    | coarse  | nb_band_bin   | contractnli |     194 |   0.175 |   0.454 |   1     |                |                |                |
| mini    | coarse  | nb_band_bin   | cuad        |     194 |   0.907 |   1     |   1     |                |                |                |
| mini    | coarse  | nb_band_bin   | maud        |     194 |   0.32  |   0.68  |   0.99  |                |                |                |
| mini    | coarse  | nb_band_bin   | privacy_qa  |     194 |   0.041 |   0.211 |   0.675 |                |                |                |
| mini    | coarse  | nb_band_bin   | ALL         |     776 |   0.361 |   0.586 |   0.916 |                | [0.270, 0.473] |                |
| mini    | coarse  | cnb_band      | contractnli |     194 |   0.062 |   0.696 |   0.99  |                |                |                |
| mini    | coarse  | cnb_band      | cuad        |     194 |   0.985 |   1     |   1     |                |                |                |
| mini    | coarse  | cnb_band      | maud        |     194 |   0.892 |   1     |   1     |                |                |                |
| mini    | coarse  | cnb_band      | privacy_qa  |     194 |   0.093 |   0.655 |   1     |                |                |                |
| mini    | coarse  | cnb_band      | ALL         |     776 |   0.508 |   0.838 |   0.997 |                | [0.389, 0.643] |                |
| mini    | coarse  | fused         | contractnli |     194 |   0.825 |   1     |   1     |                |                |                |
| mini    | coarse  | fused         | cuad        |     194 |   0.995 |   1     |   1     |                |                |                |
| mini    | coarse  | fused         | maud        |     194 |   0.165 |   0.979 |   1     |                |                |                |
| mini    | coarse  | fused         | privacy_qa  |     194 |   0.892 |   0.995 |   1     |                |                |                |
| mini    | coarse  | fused         | ALL         |     776 |   0.719 |   0.994 |   1     |                | [0.621, 0.802] |                |
| mini    | fine    | centroid      | cuad        |     194 |   0.686 |   0.799 |   0.866 |                |                |                |
| mini    | fine    | centroid      | ALL         |     194 |   0.686 |   0.799 |   0.866 |                |                | [0.759, 0.944] |
| mini    | fine    | vocab_lr      | cuad        |     194 |   0.747 |   0.804 |   0.814 |                |                |                |
| mini    | fine    | vocab_lr      | ALL         |     194 |   0.747 |   0.804 |   0.814 |                |                | [0.654, 0.930] |
| mini    | fine    | band_lr       | cuad        |     194 |   0.582 |   0.619 |   0.624 |                |                |                |
| mini    | fine    | band_lr       | ALL         |     194 |   0.582 |   0.619 |   0.624 |                |                | [0.403, 0.817] |
| mini    | fine    | nb_band       | cuad        |     194 |   0.433 |   0.515 |   0.598 |                |                |                |
| mini    | fine    | nb_band       | ALL         |     194 |   0.433 |   0.515 |   0.598 |                |                | [0.406, 0.752] |
| mini    | fine    | nb_all        | cuad        |     194 |   0.459 |   0.634 |   0.67  |                |                |                |
| mini    | fine    | nb_all        | ALL         |     194 |   0.459 |   0.634 |   0.67  |                |                | [0.483, 0.819] |
| mini    | fine    | centroid_full | cuad        |     194 |   0.495 |   0.639 |   0.732 |                |                |                |
| mini    | fine    | centroid_full | ALL         |     194 |   0.495 |   0.639 |   0.732 |                |                | [0.587, 0.861] |
| mini    | fine    | nb_band_bin   | cuad        |     194 |   0.325 |   0.402 |   0.443 |                |                |                |
| mini    | fine    | nb_band_bin   | ALL         |     194 |   0.325 |   0.402 |   0.443 |                |                | [0.255, 0.633] |
| mini    | fine    | cnb_band      | cuad        |     194 |   0.593 |   0.716 |   0.753 |                |                |                |
| mini    | fine    | cnb_band      | ALL         |     194 |   0.593 |   0.716 |   0.753 |                |                | [0.564, 0.892] |
| mini    | fine    | fused         | cuad        |     194 |   0.572 |   0.727 |   0.799 |                |                |                |
| mini    | fine    | fused         | ALL         |     194 |   0.572 |   0.727 |   0.799 |                |                | [0.659, 0.901] |

## Most frequent fine-level confusions (centroid, top-1)

- 53x `cuad/Collaboration` -> `cuad/Development`
- 42x `cuad/License` -> `cuad/Maintenance`
- 35x `cuad/Development` -> `cuad/License`
- 35x `cuad/IP` -> `cuad/License`
- 25x `cuad/Collaboration` -> `cuad/License`
- 24x `cuad/Development` -> `cuad/Collaboration`
- 24x `cuad/License` -> `cuad/Development`
- 23x `cuad/License` -> `cuad/IP`
- 18x `cuad/Manufacturing` -> `cuad/Supply`
- 18x `cuad/Marketing` -> `cuad/Distributor`

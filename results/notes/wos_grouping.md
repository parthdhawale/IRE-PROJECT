# Document grouping on Web of Science (WOS-46985): are unseen abstracts filed correctly?

- **coarse: NO-GO** -- best router `vocab_lr`, acc@1 = 0.834 (gate >= 0.95)
- **fine: GO** -- best router `vocab_lr`, acc@3 = 0.955 (gate >= 0.95)

End-to-end (coarse top-1 correct AND area in fine top-3): `centroid` 0.616, `vocab_lr` 0.803, `band_lr` 0.762, `nb_band` 0.618, `nb_all` 0.663, `fused` 0.627

## Setup

- 46985 abstracts, 7 domains, 137 (domain, area) labels; 2-750 abstracts per area (median 362), i.e. about 289 training abstracts per area per fold (CUAD: 8-32 per type).
- 5 document folds stratified by area; no duplicate abstracts, so no near-duplicate grouping (the all-pairs MinHash check does not scale to 47k documents).
- Same routers, routing parameters and gates as LegalBench-RAG (configs/default.yaml `routing`). Band = 1%-50% of each level's training documents: with ~37k training abstracts at the coarse level the 1% floor is ~375 documents, far higher in absolute terms than on LegalBench-RAG.
- fine: one classifier per domain, trained on that domain's training abstracts only, scored on its held-out abstracts (the gold domain is given, as CUAD is for the CUAD fine level).
- centroid embeds the first 2000 characters, which covers almost every abstract.

## Results

| level   | router   | subset       |   items |   acc@1 |   acc@2 |   acc@3 | ci95@1         | ci95@3         |
|:--------|:---------|:-------------|--------:|--------:|--------:|--------:|:---------------|:---------------|
| coarse  | centroid | CS           |    6514 |   0.714 |   0.844 |   0.938 |                |                |
| coarse  | centroid | Medical      |   14625 |   0.623 |   0.977 |   0.985 |                |                |
| coarse  | centroid | Civil        |    4237 |   0.63  |   0.839 |   0.969 |                |                |
| coarse  | centroid | ECE          |    5483 |   0.727 |   0.88  |   0.957 |                |                |
| coarse  | centroid | biochemistry |    5687 |   0.841 |   0.965 |   0.989 |                |                |
| coarse  | centroid | MAE          |    3297 |   0.645 |   0.91  |   0.974 |                |                |
| coarse  | centroid | Psychology   |    7142 |   0.763 |   0.865 |   0.942 |                |                |
| coarse  | centroid | ALL          |   46985 |   0.698 |   0.912 |   0.967 | [0.693, 0.702] |                |
| coarse  | vocab_lr | CS           |    6514 |   0.862 |   0.951 |   0.984 |                |                |
| coarse  | vocab_lr | Medical      |   14625 |   0.786 |   0.969 |   0.986 |                |                |
| coarse  | vocab_lr | Civil        |    4237 |   0.865 |   0.952 |   0.979 |                |                |
| coarse  | vocab_lr | ECE          |    5483 |   0.865 |   0.96  |   0.985 |                |                |
| coarse  | vocab_lr | biochemistry |    5687 |   0.868 |   0.969 |   0.993 |                |                |
| coarse  | vocab_lr | MAE          |    3297 |   0.856 |   0.961 |   0.984 |                |                |
| coarse  | vocab_lr | Psychology   |    7142 |   0.829 |   0.951 |   0.982 |                |                |
| coarse  | vocab_lr | ALL          |   46985 |   0.834 |   0.961 |   0.985 | [0.831, 0.838] |                |
| coarse  | band_lr  | CS           |    6514 |   0.823 |   0.93  |   0.975 |                |                |
| coarse  | band_lr  | Medical      |   14625 |   0.758 |   0.962 |   0.983 |                |                |
| coarse  | band_lr  | Civil        |    4237 |   0.825 |   0.938 |   0.976 |                |                |
| coarse  | band_lr  | ECE          |    5483 |   0.825 |   0.944 |   0.98  |                |                |
| coarse  | band_lr  | biochemistry |    5687 |   0.839 |   0.957 |   0.988 |                |                |
| coarse  | band_lr  | MAE          |    3297 |   0.786 |   0.935 |   0.977 |                |                |
| coarse  | band_lr  | Psychology   |    7142 |   0.802 |   0.936 |   0.973 |                |                |
| coarse  | band_lr  | ALL          |   46985 |   0.799 |   0.947 |   0.98  | [0.795, 0.803] |                |
| coarse  | nb_band  | CS           |    6514 |   0.796 |   0.889 |   0.934 |                |                |
| coarse  | nb_band  | Medical      |   14625 |   0.603 |   0.938 |   0.96  |                |                |
| coarse  | nb_band  | Civil        |    4237 |   0.644 |   0.871 |   0.965 |                |                |
| coarse  | nb_band  | ECE          |    5483 |   0.757 |   0.89  |   0.955 |                |                |
| coarse  | nb_band  | biochemistry |    5687 |   0.807 |   0.916 |   0.967 |                |                |
| coarse  | nb_band  | MAE          |    3297 |   0.685 |   0.9   |   0.973 |                |                |
| coarse  | nb_band  | Psychology   |    7142 |   0.737 |   0.877 |   0.939 |                |                |
| coarse  | nb_band  | ALL          |   46985 |   0.702 |   0.905 |   0.955 | [0.698, 0.707] |                |
| coarse  | nb_all   | CS           |    6514 |   0.839 |   0.912 |   0.962 |                |                |
| coarse  | nb_all   | Medical      |   14625 |   0.701 |   0.963 |   0.977 |                |                |
| coarse  | nb_all   | Civil        |    4237 |   0.723 |   0.906 |   0.978 |                |                |
| coarse  | nb_all   | ECE          |    5483 |   0.794 |   0.93  |   0.973 |                |                |
| coarse  | nb_all   | biochemistry |    5687 |   0.795 |   0.93  |   0.967 |                |                |
| coarse  | nb_all   | MAE          |    3297 |   0.621 |   0.876 |   0.964 |                |                |
| coarse  | nb_all   | Psychology   |    7142 |   0.786 |   0.91  |   0.952 |                |                |
| coarse  | nb_all   | ALL          |   46985 |   0.752 |   0.929 |   0.969 | [0.748, 0.755] |                |
| coarse  | fused    | CS           |    6514 |   0.751 |   0.88  |   0.942 |                |                |
| coarse  | fused    | Medical      |   14625 |   0.617 |   0.958 |   0.977 |                |                |
| coarse  | fused    | Civil        |    4237 |   0.641 |   0.867 |   0.969 |                |                |
| coarse  | fused    | ECE          |    5483 |   0.733 |   0.893 |   0.958 |                |                |
| coarse  | fused    | biochemistry |    5687 |   0.83  |   0.955 |   0.984 |                |                |
| coarse  | fused    | MAE          |    3297 |   0.657 |   0.918 |   0.978 |                |                |
| coarse  | fused    | Psychology   |    7142 |   0.757 |   0.87  |   0.942 |                |                |
| coarse  | fused    | ALL          |   46985 |   0.701 |   0.915 |   0.965 | [0.697, 0.705] |                |
| fine    | centroid | CS           |    6514 |   0.677 |   0.814 |   0.873 |                |                |
| fine    | centroid | Medical      |   14625 |   0.654 |   0.796 |   0.854 |                |                |
| fine    | centroid | Civil        |    4237 |   0.898 |   0.966 |   0.985 |                |                |
| fine    | centroid | ECE          |    5483 |   0.599 |   0.767 |   0.846 |                |                |
| fine    | centroid | biochemistry |    5687 |   0.591 |   0.781 |   0.876 |                |                |
| fine    | centroid | MAE          |    3297 |   0.732 |   0.875 |   0.935 |                |                |
| fine    | centroid | Psychology   |    7142 |   0.708 |   0.833 |   0.884 |                |                |
| fine    | centroid | ALL          |   46985 |   0.679 |   0.82  |   0.88  |                | [0.877, 0.883] |
| fine    | vocab_lr | CS           |    6514 |   0.819 |   0.931 |   0.964 |                |                |
| fine    | vocab_lr | Medical      |   14625 |   0.762 |   0.886 |   0.925 |                |                |
| fine    | vocab_lr | Civil        |    4237 |   0.944 |   0.987 |   0.995 |                |                |
| fine    | vocab_lr | ECE          |    5483 |   0.849 |   0.946 |   0.974 |                |                |
| fine    | vocab_lr | biochemistry |    5687 |   0.824 |   0.935 |   0.967 |                |                |
| fine    | vocab_lr | MAE          |    3297 |   0.881 |   0.96  |   0.986 |                |                |
| fine    | vocab_lr | Psychology   |    7142 |   0.804 |   0.911 |   0.947 |                |                |
| fine    | vocab_lr | ALL          |   46985 |   0.819 |   0.923 |   0.955 |                | [0.953, 0.957] |
| fine    | band_lr  | CS           |    6514 |   0.814 |   0.926 |   0.962 |                |                |
| fine    | band_lr  | Medical      |   14625 |   0.731 |   0.86  |   0.901 |                |                |
| fine    | band_lr  | Civil        |    4237 |   0.939 |   0.983 |   0.993 |                |                |
| fine    | band_lr  | ECE          |    5483 |   0.838 |   0.942 |   0.971 |                |                |
| fine    | band_lr  | biochemistry |    5687 |   0.817 |   0.931 |   0.965 |                |                |
| fine    | band_lr  | MAE          |    3297 |   0.872 |   0.959 |   0.985 |                |                |
| fine    | band_lr  | Psychology   |    7142 |   0.787 |   0.896 |   0.936 |                |                |
| fine    | band_lr  | ALL          |   46985 |   0.802 |   0.911 |   0.945 |                | [0.943, 0.947] |
| fine    | nb_band  | CS           |    6514 |   0.694 |   0.826 |   0.887 |                |                |
| fine    | nb_band  | Medical      |   14625 |   0.575 |   0.711 |   0.772 |                |                |
| fine    | nb_band  | Civil        |    4237 |   0.879 |   0.954 |   0.974 |                |                |
| fine    | nb_band  | ECE          |    5483 |   0.694 |   0.833 |   0.9   |                |                |
| fine    | nb_band  | biochemistry |    5687 |   0.68  |   0.844 |   0.915 |                |                |
| fine    | nb_band  | MAE          |    3297 |   0.771 |   0.9   |   0.954 |                |                |
| fine    | nb_band  | Psychology   |    7142 |   0.699 |   0.825 |   0.882 |                |                |
| fine    | nb_band  | ALL          |   46985 |   0.678 |   0.81  |   0.868 |                | [0.865, 0.871] |
| fine    | nb_all   | CS           |    6514 |   0.687 |   0.825 |   0.883 |                |                |
| fine    | nb_all   | Medical      |   14625 |   0.597 |   0.725 |   0.785 |                |                |
| fine    | nb_all   | Civil        |    4237 |   0.886 |   0.961 |   0.981 |                |                |
| fine    | nb_all   | ECE          |    5483 |   0.686 |   0.821 |   0.883 |                |                |
| fine    | nb_all   | biochemistry |    5687 |   0.685 |   0.855 |   0.923 |                |                |
| fine    | nb_all   | MAE          |    3297 |   0.778 |   0.906 |   0.954 |                |                |
| fine    | nb_all   | Psychology   |    7142 |   0.712 |   0.837 |   0.892 |                |                |
| fine    | nb_all   | ALL          |   46985 |   0.687 |   0.817 |   0.872 |                | [0.869, 0.875] |
| fine    | fused    | CS           |    6514 |   0.695 |   0.833 |   0.896 |                |                |
| fine    | fused    | Medical      |   14625 |   0.632 |   0.771 |   0.832 |                |                |
| fine    | fused    | Civil        |    4237 |   0.894 |   0.965 |   0.985 |                |                |
| fine    | fused    | ECE          |    5483 |   0.637 |   0.816 |   0.889 |                |                |
| fine    | fused    | biochemistry |    5687 |   0.63  |   0.832 |   0.915 |                |                |
| fine    | fused    | MAE          |    3297 |   0.751 |   0.902 |   0.952 |                |                |
| fine    | fused    | Psychology   |    7142 |   0.71  |   0.843 |   0.895 |                |                |
| fine    | fused    | ALL          |   46985 |   0.685 |   0.83  |   0.889 |                | [0.886, 0.892] |

## Hardest areas (vocab_lr, acc@3)

| area                                |   docs |   centroid@3 |   vocab_lr@3 |   band_lr@3 |   nb_band@3 |   nb_all@3 |   fused@3 |
|:------------------------------------|-------:|-------------:|-------------:|------------:|------------:|-----------:|----------:|
| Civil/Bamboo as a Building Material |      2 |         1    |         0    |        0    |        0    |       0    |      0.5  |
| Medical/Schizophrenia               |     38 |         0.61 |         0.45 |        0.34 |        0.08 |       0    |      0.24 |
| Medical/Depression                  |    130 |         0.39 |         0.62 |        0.63 |        0.19 |       0.12 |      0.32 |
| Medical/Rheumatoid Arthritis        |    188 |         0.82 |         0.81 |        0.76 |        0.56 |       0.35 |      0.7  |
| Medical/Multiple Sclerosis          |    253 |         0.75 |         0.82 |        0.8  |        0.67 |       0.66 |      0.74 |
| Medical/Psoriasis                   |    128 |         0.86 |         0.85 |        0.83 |        0.7  |       0.22 |      0.78 |
| Medical/Mental Health               |    222 |         0.88 |         0.86 |        0.86 |        0.79 |       0.43 |      0.87 |
| Medical/Heart Disease               |    291 |         0.81 |         0.86 |        0.85 |        0.6  |       0.69 |      0.75 |
| Medical/Dementia                    |    237 |         0.74 |         0.86 |        0.83 |        0.62 |       0.57 |      0.69 |
| Medical/Asthma                      |    317 |         0.81 |         0.87 |        0.81 |        0.68 |       0.76 |      0.77 |

Run time 2648s.

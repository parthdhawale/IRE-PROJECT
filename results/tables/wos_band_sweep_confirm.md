# Band-edge sensitivity of document placement: Web of Science (WOS-46985) (held-out documents)

Sensitivity only: the band used everywhere else (1%-50%) was fixed before any result was seen and is NOT changed by this table. `df_min..df_max` = the document-frequency range the band means on fold 0 (training documents); `vocab` = mean band size; `macro@1` = top-1 accuracy averaged over groups; `mrr` = mean reciprocal rank of the gold group. Scored folds: [1, 2, 3, 4] of 0-4.

## coarse level, band_lr

|   low |   high |   df_min |   df_max |   vocab |   acc@1 |   acc@2 |   acc@3 |   mrr |   macro@1 | fixed        |
|------:|-------:|---------:|---------:|--------:|--------:|--------:|--------:|------:|----------:|:-------------|
| 0.001 |   0.25 |       38 |     9397 |    9021 |   0.843 |   0.964 |   0.987 | 0.914 |     0.851 |              |
| 0     |   0.1  |        1 |     3758 |  110766 |   0.839 |   0.962 |   0.987 | 0.912 |     0.848 |              |
| 0.01  |   0.5  |      376 |    18794 |    1935 |   0.8   |   0.947 |   0.979 | 0.889 |     0.81  | <- band used |

## coarse level, nb_band

|   low |   high |   df_min |   df_max |   vocab |   acc@1 |   acc@2 |   acc@3 |   mrr |   macro@1 | fixed        |
|------:|-------:|---------:|---------:|--------:|--------:|--------:|--------:|------:|----------:|:-------------|
| 0.001 |   0.25 |       38 |     9397 |    9021 |   0.735 |   0.921 |   0.965 | 0.85  |     0.752 |              |
| 0     |   0.1  |        1 |     3758 |  110766 |   0.752 |   0.929 |   0.969 | 0.861 |     0.754 |              |
| 0.01  |   0.5  |      376 |    18794 |    1935 |   0.702 |   0.904 |   0.954 | 0.829 |     0.718 | <- band used |

## fine level, band_lr

|   low |   high |   df_min |   df_max |   vocab |   acc@1 |   acc@2 |   acc@3 |   mrr |   macro@1 | fixed        |
|------:|-------:|---------:|---------:|--------:|--------:|--------:|--------:|------:|----------:|:-------------|
| 0.001 |   0.25 |       12 |     2925 |    9069 |   0.808 |   0.918 |   0.951 | 0.882 |     0.788 |              |
| 0     |   0.1  |        1 |     1170 |   56327 |   0.767 |   0.89  |   0.933 | 0.855 |     0.756 |              |
| 0.01  |   0.5  |      118 |     5850 |    1986 |   0.802 |   0.91  |   0.945 | 0.877 |     0.778 | <- band used |

## fine level, nb_band

|   low |   high |   df_min |   df_max |   vocab |   acc@1 |   acc@2 |   acc@3 |   mrr |   macro@1 | fixed        |
|------:|-------:|---------:|---------:|--------:|--------:|--------:|--------:|------:|----------:|:-------------|
| 0.001 |   0.25 |       12 |     2925 |    9069 |   0.7   |   0.83  |   0.886 | 0.802 |     0.667 |              |
| 0     |   0.1  |        1 |     1170 |   56327 |   0.675 |   0.81  |   0.868 | 0.782 |     0.625 |              |
| 0.01  |   0.5  |      118 |     5850 |    1986 |   0.678 |   0.809 |   0.868 | 0.784 |     0.648 | <- band used |


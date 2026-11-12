# Grouping of held-out documents, per level

| level   | router        | subset      |   items |   acc@1 |   acc@2 |   acc@3 | ci95@2         | ci95@1         | ci95@3         |
|:--------|:--------------|:------------|--------:|--------:|--------:|--------:|:---------------|:---------------|:---------------|
| flat    | centroid      | contractnli |      95 |   0.989 |   0.989 |   0.989 |                |                |                |
| flat    | centroid      | cuad        |     462 |   0.801 |   0.89  |   0.929 |                |                |                |
| flat    | centroid      | maud        |     150 |   1     |   1     |   1     |                |                |                |
| flat    | centroid      | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| flat    | centroid      | ALL         |     714 |   0.87  |   0.927 |   0.952 | [0.909, 0.945] |                |                |
| flat    | vocab_lr      | contractnli |      95 |   1     |   1     |   1     |                |                |                |
| flat    | vocab_lr      | cuad        |     462 |   0.662 |   0.788 |   0.855 |                |                |                |
| flat    | vocab_lr      | maud        |     150 |   1     |   1     |   1     |                |                |                |
| flat    | vocab_lr      | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| flat    | vocab_lr      | ALL         |     714 |   0.782 |   0.863 |   0.906 | [0.836, 0.888] |                |                |
| flat    | band_lr       | contractnli |      95 |   1     |   1     |   1     |                |                |                |
| flat    | band_lr       | cuad        |     462 |   0.63  |   0.76  |   0.838 |                |                |                |
| flat    | band_lr       | maud        |     150 |   1     |   1     |   1     |                |                |                |
| flat    | band_lr       | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| flat    | band_lr       | ALL         |     714 |   0.761 |   0.845 |   0.895 | [0.819, 0.870] |                |                |
| flat    | nb_band       | contractnli |      95 |   0.916 |   0.926 |   0.968 |                |                |                |
| flat    | nb_band       | cuad        |     462 |   0.604 |   0.755 |   0.794 |                |                |                |
| flat    | nb_band       | maud        |     150 |   1     |   1     |   1     |                |                |                |
| flat    | nb_band       | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| flat    | nb_band       | ALL         |     714 |   0.732 |   0.832 |   0.863 | [0.805, 0.859] |                |                |
| flat    | nb_all        | contractnli |      95 |   0.968 |   0.989 |   0.989 |                |                |                |
| flat    | nb_all        | cuad        |     462 |   0.489 |   0.626 |   0.69  |                |                |                |
| flat    | nb_all        | maud        |     150 |   1     |   1     |   1     |                |                |                |
| flat    | nb_all        | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| flat    | nb_all        | ALL         |     714 |   0.665 |   0.756 |   0.798 | [0.724, 0.786] |                |                |
| flat    | centroid_full | contractnli |      95 |   0.905 |   0.916 |   0.916 |                |                |                |
| flat    | centroid_full | cuad        |     462 |   0.548 |   0.712 |   0.805 |                |                |                |
| flat    | centroid_full | maud        |     150 |   1     |   1     |   1     |                |                |                |
| flat    | centroid_full | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| flat    | centroid_full | ALL         |     714 |   0.695 |   0.803 |   0.863 | [0.775, 0.831] |                |                |
| flat    | nb_band_bin   | contractnli |      95 |   0.979 |   1     |   1     |                |                |                |
| flat    | nb_band_bin   | cuad        |     462 |   0.455 |   0.589 |   0.658 |                |                |                |
| flat    | nb_band_bin   | maud        |     150 |   1     |   1     |   1     |                |                |                |
| flat    | nb_band_bin   | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| flat    | nb_band_bin   | ALL         |     714 |   0.644 |   0.734 |   0.779 | [0.700, 0.766] |                |                |
| flat    | cnb_band      | contractnli |      95 |   0.663 |   0.853 |   0.916 |                |                |                |
| flat    | cnb_band      | cuad        |     462 |   0.509 |   0.693 |   0.773 |                |                |                |
| flat    | cnb_band      | maud        |     150 |   1     |   1     |   1     |                |                |                |
| flat    | cnb_band      | privacy_qa  |       7 |   0     |   1     |   1     |                |                |                |
| flat    | cnb_band      | ALL         |     714 |   0.627 |   0.782 |   0.842 | [0.751, 0.812] |                |                |
| flat    | fused         | contractnli |      95 |   0.979 |   0.989 |   0.989 |                |                |                |
| flat    | fused         | cuad        |     462 |   0.751 |   0.853 |   0.903 |                |                |                |
| flat    | fused         | maud        |     150 |   1     |   1     |   1     |                |                |                |
| flat    | fused         | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| flat    | fused         | ALL         |     714 |   0.836 |   0.903 |   0.936 | [0.882, 0.924] |                |                |
| coarse  | centroid      | contractnli |      95 |   0.989 |   1     |   1     |                |                |                |
| coarse  | centroid      | cuad        |     462 |   0.991 |   1     |   1     |                |                |                |
| coarse  | centroid      | maud        |     150 |   0.993 |   1     |   1     |                |                |                |
| coarse  | centroid      | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| coarse  | centroid      | ALL         |     714 |   0.992 |   1     |   1     |                | [0.985, 0.997] |                |
| coarse  | vocab_lr      | contractnli |      95 |   0.989 |   1     |   1     |                |                |                |
| coarse  | vocab_lr      | cuad        |     462 |   0.981 |   1     |   1     |                |                |                |
| coarse  | vocab_lr      | maud        |     150 |   1     |   1     |   1     |                |                |                |
| coarse  | vocab_lr      | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| coarse  | vocab_lr      | ALL         |     714 |   0.986 |   1     |   1     |                | [0.976, 0.994] |                |
| coarse  | band_lr       | contractnli |      95 |   0.979 |   1     |   1     |                |                |                |
| coarse  | band_lr       | cuad        |     462 |   0.996 |   1     |   1     |                |                |                |
| coarse  | band_lr       | maud        |     150 |   1     |   1     |   1     |                |                |                |
| coarse  | band_lr       | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| coarse  | band_lr       | ALL         |     714 |   0.994 |   1     |   1     |                | [0.989, 0.999] |                |
| coarse  | nb_band       | contractnli |      95 |   0.926 |   0.979 |   1     |                |                |                |
| coarse  | nb_band       | cuad        |     462 |   0.942 |   1     |   1     |                |                |                |
| coarse  | nb_band       | maud        |     150 |   1     |   1     |   1     |                |                |                |
| coarse  | nb_band       | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| coarse  | nb_band       | ALL         |     714 |   0.952 |   0.997 |   1     |                | [0.936, 0.968] |                |
| coarse  | nb_all        | contractnli |      95 |   0.853 |   1     |   1     |                |                |                |
| coarse  | nb_all        | cuad        |     462 |   0.95  |   1     |   1     |                |                |                |
| coarse  | nb_all        | maud        |     150 |   1     |   1     |   1     |                |                |                |
| coarse  | nb_all        | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| coarse  | nb_all        | ALL         |     714 |   0.948 |   1     |   1     |                | [0.931, 0.964] |                |
| coarse  | centroid_full | contractnli |      95 |   0.926 |   0.979 |   1     |                |                |                |
| coarse  | centroid_full | cuad        |     462 |   0.92  |   1     |   1     |                |                |                |
| coarse  | centroid_full | maud        |     150 |   1     |   1     |   1     |                |                |                |
| coarse  | centroid_full | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| coarse  | centroid_full | ALL         |     714 |   0.938 |   0.997 |   1     |                | [0.920, 0.955] |                |
| coarse  | nb_band_bin   | contractnli |      95 |   0.853 |   1     |   1     |                |                |                |
| coarse  | nb_band_bin   | cuad        |     462 |   0.97  |   1     |   1     |                |                |                |
| coarse  | nb_band_bin   | maud        |     150 |   1     |   1     |   1     |                |                |                |
| coarse  | nb_band_bin   | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| coarse  | nb_band_bin   | ALL         |     714 |   0.961 |   1     |   1     |                | [0.948, 0.975] |                |
| coarse  | cnb_band      | contractnli |      95 |   0     |   0.958 |   1     |                |                |                |
| coarse  | cnb_band      | cuad        |     462 |   0.952 |   1     |   1     |                |                |                |
| coarse  | cnb_band      | maud        |     150 |   1     |   1     |   1     |                |                |                |
| coarse  | cnb_band      | privacy_qa  |       7 |   0     |   1     |   1     |                |                |                |
| coarse  | cnb_band      | ALL         |     714 |   0.826 |   0.994 |   1     |                | [0.800, 0.852] |                |
| coarse  | fused         | contractnli |      95 |   0.979 |   1     |   1     |                |                |                |
| coarse  | fused         | cuad        |     462 |   0.996 |   1     |   1     |                |                |                |
| coarse  | fused         | maud        |     150 |   0.993 |   1     |   1     |                |                |                |
| coarse  | fused         | privacy_qa  |       7 |   1     |   1     |   1     |                |                |                |
| coarse  | fused         | ALL         |     714 |   0.993 |   1     |   1     |                | [0.987, 0.999] |                |
| fine    | centroid      | cuad        |     462 |   0.801 |   0.89  |   0.929 |                |                |                |
| fine    | centroid      | ALL         |     462 |   0.801 |   0.89  |   0.929 |                |                | [0.905, 0.950] |
| fine    | vocab_lr      | cuad        |     462 |   0.671 |   0.803 |   0.861 |                |                |                |
| fine    | vocab_lr      | ALL         |     462 |   0.671 |   0.803 |   0.861 |                |                | [0.829, 0.892] |
| fine    | band_lr       | cuad        |     462 |   0.63  |   0.768 |   0.838 |                |                |                |
| fine    | band_lr       | ALL         |     462 |   0.63  |   0.768 |   0.838 |                |                | [0.805, 0.870] |
| fine    | nb_band       | cuad        |     462 |   0.615 |   0.753 |   0.803 |                |                |                |
| fine    | nb_band       | ALL         |     462 |   0.615 |   0.753 |   0.803 |                |                | [0.766, 0.838] |
| fine    | nb_all        | cuad        |     462 |   0.535 |   0.665 |   0.74  |                |                |                |
| fine    | nb_all        | ALL         |     462 |   0.535 |   0.665 |   0.74  |                |                | [0.701, 0.779] |
| fine    | centroid_full | cuad        |     462 |   0.556 |   0.723 |   0.812 |                |                |                |
| fine    | centroid_full | ALL         |     462 |   0.556 |   0.723 |   0.812 |                |                | [0.777, 0.846] |
| fine    | nb_band_bin   | cuad        |     462 |   0.47  |   0.604 |   0.677 |                |                |                |
| fine    | nb_band_bin   | ALL         |     462 |   0.47  |   0.604 |   0.677 |                |                | [0.636, 0.721] |
| fine    | cnb_band      | cuad        |     462 |   0.617 |   0.766 |   0.833 |                |                |                |
| fine    | cnb_band      | ALL         |     462 |   0.617 |   0.766 |   0.833 |                |                | [0.801, 0.866] |
| fine    | fused         | cuad        |     462 |   0.742 |   0.846 |   0.903 |                |                |                |
| fine    | fused         | ALL         |     462 |   0.742 |   0.846 |   0.903 |                |                | [0.874, 0.931] |

## Fine level, per contract type (top-1)

| type                    |   docs |   centroid@1 |   vocab_lr@1 |   band_lr@1 |   nb_band@1 |   nb_all@1 |   centroid_full@1 |   nb_band_bin@1 |   cnb_band@1 |   fused@1 |
|:------------------------|-------:|-------------:|-------------:|------------:|------------:|-----------:|------------------:|----------------:|-------------:|----------:|
| cuad/License            |     41 |         0.71 |         0.63 |        0.61 |        0.73 |       0.88 |              0.59 |            0.8  |         0.78 |      0.8  |
| cuad/Sponsorship        |     31 |         0.97 |         0.87 |        0.74 |        0.71 |       0.58 |              0.52 |            0.58 |         0.84 |      0.94 |
| cuad/Distributor        |     29 |         0.93 |         0.9  |        0.9  |        0.86 |       0.86 |              0.79 |            0.86 |         0.9  |      0.97 |
| cuad/Strategic Alliance |     29 |         0.79 |         0.66 |        0.52 |        0.48 |       0.52 |              0.41 |            0.52 |         0.24 |      0.72 |
| cuad/Development        |     27 |         0.67 |         0.44 |        0.33 |        0.56 |       0.67 |              0.44 |            0.63 |         0.37 |      0.56 |
| cuad/Collaboration      |     26 |         0.73 |         0.38 |        0.38 |        0.35 |       0.35 |              0.27 |            0.38 |         0.62 |      0.58 |
| cuad/Service            |     26 |         0.77 |         0.62 |        0.58 |        0.58 |       0.62 |              0.58 |            0.5  |         0.54 |      0.85 |
| cuad/Maintenance        |     26 |         0.88 |         0.69 |        0.54 |        0.46 |       0.5  |              0.46 |            0.5  |         0.54 |      0.62 |
| cuad/Endorsement        |     24 |         0.92 |         0.96 |        1    |        0.83 |       0.46 |              0.75 |            0.71 |         0.83 |      0.83 |
| cuad/Co-Branding        |     21 |         0.95 |         0.95 |        0.9  |        0.67 |       0.67 |              0.67 |            0.48 |         0.71 |      0.86 |
| cuad/Outsourcing        |     17 |         0.76 |         0.53 |        0.29 |        0.35 |       0.24 |              0.35 |            0.24 |         0.59 |      0.65 |
| cuad/Supply             |     17 |         0.94 |         0.47 |        0.59 |        0.59 |       0.65 |              0.59 |            0.29 |         0.35 |      0.88 |
| cuad/IP                 |     16 |         0.69 |         0.88 |        0.88 |        0.75 |       0.62 |              0.62 |            0.5  |         0.81 |      0.62 |
| cuad/Hosting            |     15 |         0.8  |         0.73 |        0.67 |        0.4  |       0.13 |              0.33 |            0.13 |         0.4  |      0.53 |
| cuad/Manufacturing      |     14 |         0.71 |         0.64 |        0.71 |        0.57 |       0.57 |              0.57 |            0.14 |         0.5  |      0.79 |
| cuad/Transportation     |     13 |         1    |         1    |        1    |        0.77 |       0.77 |              0.92 |            0.54 |         1    |      0.92 |
| cuad/Promotion          |     12 |         0.83 |         0.33 |        0.42 |        0.5  |       0.25 |              0.25 |            0    |         0.5  |      0.58 |
| cuad/Agency             |     12 |         0.67 |         0.67 |        0.67 |        0.67 |       0.67 |              0.67 |            0.58 |         0.67 |      0.67 |
| cuad/Franchise          |     11 |         0.82 |         0.91 |        0.91 |        1    |       0.91 |              1    |            0.82 |         1    |      1    |
| cuad/Consulting         |     11 |         0.91 |         1    |        1    |        0.91 |       0    |              0.82 |            0    |         0.91 |      1    |
| cuad/Marketing          |     10 |         0.2  |         0    |        0    |        0.1  |       0.1  |              0.3  |            0    |         0.1  |      0.2  |
| cuad/Reseller           |     10 |         0.9  |         0.8  |        0.5  |        0.8  |       0    |              0.6  |            0    |         0.8  |      0.8  |
| cuad/Joint Venture      |     10 |         0.7  |         0.7  |        0.9  |        0.8  |       0.5  |              0.7  |            0.2  |         0.3  |      0.7  |
| cuad/Affiliate          |     10 |         0.9  |         0.1  |        0.1  |        0.3  |       0    |              0.6  |            0    |         0.3  |      0.5  |
| cuad/Other              |      4 |         0    |         0    |        0    |        0.25 |       0    |              0    |            0    |         0    |      0    |

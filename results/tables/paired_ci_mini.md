# Paired bootstrap CIs (mini, drm@8, a - b; negative = a lower)

Macro mean over subsets; 1000 resamples. CI(q) resamples queries; CI(doc) resamples gold documents (questions about one document move together). A difference counts only if CI(doc) excludes 0.

| a | b | contractnli | cuad | maud | privacy_qa | macro | CI(q) | CI(doc) | real? | what |
|---|---|---|---|---|---|---|---|---|---|---|
| docfirst_hdr | docfirst | -0.031 | +0.000 | +0.000 | -0.284 | -0.079 | [-0.095, -0.062] | [-0.148, -0.017] | yes | separate pools: header-only document choice |
| mixed_docfirst | mixed_hybrid | -0.526 | -0.220 | -0.325 | +0.043 | -0.257 | [-0.281, -0.230] | [-0.337, -0.164] | yes | mixed pool: doc-first vs flat hybrid |
| gfc_centroid_full_b2_docfirst_local | mixed_docfirst | -0.031 | +0.000 | +0.000 | -0.036 | -0.017 | [-0.028, -0.005] | [-0.034, -0.002] | yes | mixed pool: routing + local index |
| gfc_centroid_full_b2_docfirst_local_rrf | mixed_docfirst | -0.036 | +0.000 | +0.005 | -0.155 | -0.046 | [-0.063, -0.030] | [-0.117, +0.004] | no | mixed pool: final method vs flat doc-first |
| gfc_centroid_full_b2_docfirst_local_rrf | gfc_centroid_full_b2_docfirst_local | -0.005 | +0.000 | +0.005 | -0.119 | -0.030 | [-0.045, -0.015] | [-0.090, +0.012] | no | mixed pool: header+full RRF document choice |
| gfc_centroid_full_b2_docfirst_local_hdr | gfc_centroid_full_b2_docfirst_local | -0.005 | +0.005 | +0.005 | -0.103 | -0.024 | [-0.043, -0.008] | [-0.107, +0.044] | no | mixed pool: header-only document choice |

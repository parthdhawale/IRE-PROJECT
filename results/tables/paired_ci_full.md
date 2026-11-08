# Paired bootstrap CIs (full, drm@8, a - b; negative = a lower)

Macro mean over subsets; 1000 resamples. CI(q) resamples queries; CI(doc) resamples gold documents (questions about one document move together). A difference counts only if CI(doc) excludes 0.

| a | b | contractnli | cuad | maud | privacy_qa | macro | CI(q) | CI(doc) | real? | what |
|---|---|---|---|---|---|---|---|---|---|---|
| docfirst | hybrid | -0.561 | -0.181 | -0.443 | +0.055 | -0.283 | [-0.299, -0.265] | [-0.341, -0.209] | yes | separate pools: doc-first vs best flat chunk method |
| docfirst_hdr | docfirst | -0.054 | +0.001 | -0.002 | -0.284 | -0.085 | [-0.101, -0.069] | [-0.158, -0.025] | yes | separate pools: header-only document choice |
| leaf_hybrid | hybrid | -0.006 | +0.010 | +0.050 | +0.055 | +0.027 | [+0.022, +0.033] | [+0.016, +0.041] | yes | separate pools: section leaves vs 500-char chunks |
| mixed_docfirst | mixed_hybrid | -0.586 | -0.187 | -0.454 | +0.043 | -0.296 | [-0.311, -0.280] | [-0.352, -0.232] | yes | mixed pool: doc-first vs flat hybrid |
| gfc_centroid_full_b2_docfirst_local | mixed_docfirst | -0.033 | +0.001 | +0.000 | -0.036 | -0.017 | [-0.027, -0.007] | [-0.030, -0.005] | yes | mixed pool: routing + local index |
| gfc_centroid_full_b2_docfirst_local_rrf | mixed_docfirst | -0.057 | -0.000 | -0.001 | -0.155 | -0.053 | [-0.070, -0.039] | [-0.122, -0.004] | yes | mixed pool: final method vs flat doc-first |
| gfc_centroid_full_b2_docfirst_local_rrf | gfc_centroid_full_b2_docfirst_local | -0.025 | -0.001 | -0.001 | -0.119 | -0.036 | [-0.051, -0.023] | [-0.095, +0.006] | no | mixed pool: header+full RRF document choice |
| gfc_centroid_full_b2_docfirst_local_hdr | gfc_centroid_full_b2_docfirst_local | -0.029 | -0.000 | -0.001 | -0.103 | -0.033 | [-0.050, -0.017] | [-0.110, +0.034] | no | mixed pool: header-only document choice |

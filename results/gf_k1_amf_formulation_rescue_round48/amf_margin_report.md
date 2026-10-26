# AMF offline margin report

Primary offline gate: **FAIL**.

| State | phi_L | phi_R | S_AM | S_AMF | Margin | AM | AMF | Expected |
|---|---:|---:|---:|---:|---:|---|---|---|
| H1 | 0.109324759 | 0.0179034975 | 0.0493403851 | 0.0670361833 | -0.0121138167 | native-target | native-target | retain |
| H2 | 0.113168724 | 0 | 0 | 0.0220982953 | -0.0570517047 | exact-close | exact-close | retain |
| H3 | 0.109324759 | 0.0253231642 | 0.0274258093 | 0.0515120158 | -0.0276379842 | native-target | native-target | startup_retain_diagnostic |
| B1 | 0.108414239 | 0 | 0 | 0.0170045546 | -0.0621454454 | exact-close | exact-close | split |
| B2 | 0.110561056 | 0 | 1.53694673e-17 | 0.0153774447 | -0.0637725553 | exact-close | exact-close | split |
| B3 | 0.0965517241 | 0.000905532006 | 0.149656052 | 0.162505495 | 0.083355495 | split | split | split |
| B4 | 0.0954391892 | 0.00437171449 | 0.0864677356 | 0.111716301 | 0.0325663013 | split | split | split |
| U1 | 0.116487455 | 0 | 8.95608413e-17 | 0.0239660901 | -0.0551839099 | exact-close | exact-close | midpoint_beneficial_exact_work_reduction |
| T1 | 0.094017094 | 0.00160353099 | 0.051820588 | 0.0635385022 | -0.0156114978 | native-target | native-target | midpoint_exact_retain_capped_beneficial_divergence |

The frozen, equal-weight profile preserves H1/H2 and the existing B3/B4 splits, but it does not move B1 or B2 across tau. No family, tau, or threshold was tuned after observing this result. Round 48 therefore follows the mandatory bounded-negative path.

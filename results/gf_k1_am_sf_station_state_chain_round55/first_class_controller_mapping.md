
# First-class K1-AM-SF controller mapping

The paper preset now declares K1-AM-SF directly. `SolveOptions` carries the
ten paper-facing fields below, `configurePaperK1AmSfOverrides` assigns their
frozen values, and `solvePaperExternalGiniTree` resolves geometry, score,
eligibility, native targets, and exact closure from those fields. Historical
Round/C6 fields remain serialized compatibility adapters but are neutral in
the paper preset (`round40_c6_coarse_start=off`,
`round47_c6_adaptive_mass=off`) and are not consulted by the first-class path.

| Field | Frozen value | Runtime consumer |
|---|---:|---|
| `initial_gini_interval_count` | `1` | `controller_initial_interval_count` |
| `split_point_rule` | `midpoint` | `splitLegacyFrontierInterval` |
| `split_score_rule` | `balanced-normalized-closure` | `evaluateC6AdaptiveMassSplitDecision` |
| `split_threshold` | `0.08` | `controller_split_threshold` |
| `maximum_split_depth` | `8` | `legacyAdaptiveSplitEligible` |
| `minimum_interval_width` | `1e-4` | `legacyAdaptiveSplitEligible` |
| `split_factor` | `2` | `splitLegacyFrontierInterval` |
| `child_infeasibility_policy` | `exact` | `evaluateC6AdaptiveMassSplitDecision` |
| `native_target_policy` | `existing-k1-am-sf` | `runC6NativeTarget` |
| `exact_parent_closure` | `true` | `PaperTerminalMip` |

The accepted controller is validated before backend creation. The direct K0=1
geometry, midpoint children, balanced normalized closure score at tau=0.08,
depth/width eligibility, exact infeasibility handling, and exact parent
closure are covered by `Round55StationStateChainTests`.

# Round 45 completion erratum

The classifications `validated_adaptive_timing`,
`validated_k4_adaptive_midpoint`, and `midpoint_not_improved` in the original
Round 45 report are provisional and are not accepted as final.

The original counterfactual dataset contained only eight initial K4 leaves from
two instances. Its strong-control L3 “beneficial split” label was inferred from
a Round 44 overlay trajectory whose full-instance `split_count` was zero. That
label is withdrawn and must not be treated as a verified split counterfactual.

Although the frozen complex panel contains twelve V20/V50 instances, the prior
runtime screen covered only four instances, two arms, and approximately 300
seconds. It was not the required 48-row, 3600-second common-horizon matrix.
PMM/FPMM were tested on only two startup-scale instances, not on every live
development split leaf.

All old raw files remain immutable historical evidence. Evidence below
`completion/` is non-destructive and supersedes only the old derived
classifications. Until every completion gate passes, PR #95 remains draft, C6
remains the broad validated mainline, all Round 45 behavior remains default-off,
and the adaptive preset is experimental rather than promoted.

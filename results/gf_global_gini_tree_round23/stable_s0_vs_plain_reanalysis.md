# Stable S0 versus plain reanalysis

This is a no-solve Round 23 analysis of immutable Round 22 evidence. Different
horizons are reported as repeated measurements, not new instances. There are
14 unique instances, 14 900-second
pairs, 8 1,800-second pairs, and
2 selected 3,600-second pairs. There are
2 shared-strict pairs and 3 one-sided-strict
pairs.

Every noncertified comparison was recomputed twice: once using the verified
plain incumbent as U for both arms, and once using the frozen common U in
`comparison_ub_manifest.csv`. AUC was recomputed from raw retained events;
arm-specific Round 22 normalized AUC values were not reused.

Under the fixed hierarchy and excluding the invalidated moderate4301 Round 22
S0 row, S0 wins 23 pairs, plain wins 0, ties occur in
0, and 0 are unavailable. The non-anomalous
plain-over-S0 counterexamples are: none.

The tested evidence supports comparative statements only for these retained
instances, horizons, executable, and manifests. It does not prove universal
dominance. Rows with large remaining common-UB gaps remain far from exact
closure even when S0 has the stronger final lower bound. Moderate4301 is
correctness-resolved by Round 23 live gates, but its contradictory Round 22 S0
900-second row remains excluded rather than retroactively repaired.

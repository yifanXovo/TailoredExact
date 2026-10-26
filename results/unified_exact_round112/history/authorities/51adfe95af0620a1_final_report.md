# Round 36 final report

## Outcome

Classification: `decomposition_geometry_dominant`.

Decomposition geometry is the dominant identified interaction.

Round 36 has 56/56 checksum-complete official rows, with
33 strict certificates,
23 valid noncertificates, and
0 false certificates.

## Causal comparisons

| comparison | rows | right_wins | left_wins | ties | downstream_sequence_changes | actual_split_decision_changes | pre_split_divergences |
|---|---|---|---|---|---|---|---|
| HH_vs_BW-P_geometry | 14 | 4 | 10 | 0 | 11 | 10 | 11 |
| BW-P_vs_BW-A_normalization | 14 | 6 | 3 | 5 | 3 | 0 | 1 |
| wide-proof_vs_best-proof_fixed-anchor | 14 | 5 | 8 | 1 | 13 | 4 | 13 |

HH versus BW-P is treated as a clean geometry intervention only where HGA is
the best proof incumbent.  BW-P versus BW-A holds proof and geometry fixed and
changes only the selected split-normalization denominator.  The fixed-anchor
proof table compares the wide self-arm with BW-A, so geometry and the effective
anchor normalization remain fixed while the verified proof cutoff strengthens.

## Decision gates

| validity_gate_passed | complete_56_row_stage_b | geometry_exposed_rows | geometry_exposed_pattern_count | geometry_downstream_changed_rows | geometry_downstream_changed_fraction | geometry_directionally_assessable_rows | geometry_direction_match_rows | geometry_direction_match_fraction | geometry_weaker_simple_faster_evidence | geometry_v50_regression_evidence | geometry_mechanism_supported | normalization_exposed_rows | normalization_split_decision_changed_rows | normalization_supporting_rows_no_pre_split_divergence | normalization_supporting_pattern_count | normalization_material_consequence_rows | split_normalization_mechanism_supported |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| True | True | 13 | 4 | 11 | 0.8462 | 12 | 8 | 0.6667 | True | True | True | 13 | 0 | 0 | 0 | 0 | False |

The numeric gate definition was recorded in `analysis_gate_definition.md`
after the V12_M1 integration pilot and before the remaining matrix completed.

## Explicit causal questions

### A. Decomposition geometry

The predeclared geometry gate passes. There are
13 clean geometry
exposures, with
11 downstream
sequence changes and
8 frozen-pattern
direction matches.

### B. Split normalization

The predeclared split-normalization gate does not pass. The comparison has
13 denominator
exposures and
0
actual split-decision changes.

### C. Whether splitting can cause the observed effect

The geometry comparison contains
3
zero-split trajectory divergences and
11
pre-split divergences. The normalization comparison contains
1
and
1,
respectively. Such observations are not attributed to rho.

### D. Stronger proof incumbent with geometry fixed

Across 13
fixed-anchor proof exposures, the stronger proof arm improves or preserves the
final common-UB gap in
9
rows, common-window proof AUC in
4
rows, and unresolved open-leaf count in
12
rows. Universal wall-clock monotonicity is not claimed.

## Correctness and interpretation boundary

- All-row exactness/certificate audit: True.
- False certificates: 0.
- K remains 4, rho remains 0.01, and all commands use Seed 0 and one thread.
- Proof cutoffs and certificates use verified `U_proof`; `U_anchor` is confined
  to launch-frozen decomposition geometry and the explicit diagnostic
  normalization selector.
- Timing, Work, and nodes are reported as outcomes and are excluded from all
  deterministic sequence hashes.
- AUC uses common observed windows with left-continuous values, no
  interpolation, and no post-last-event extension.

## Recommendation

Keep C6-HGA-FULL unchanged and freeze best-proof + wide-anchor + proof-normalization as a candidate for broader Stage C validation.

No new mainline is promoted automatically.

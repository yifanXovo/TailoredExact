# Invalidated completion-runner preflight

The first harness preflight for
`cf__round39_small_hard_V10_M3_Q20_slot04_seed1145042375__k4__L0__retain`
wrote to the repository-level `completion/runs/` directory because the runner
interpreted the frozen `run_directory` relative to the repository rather than
the Round 45 result root. It is outside the official completion evidence area,
is not referenced by the matrix audit, and is invalidated.

The raw preflight files are intentionally preserved. The runner now resolves
matrix run directories relative to
`results/gf_adaptive_timing_parametric_partition_round45/` and the row is rerun
there before any analysis.

That first correctly located rerun exposed a second preflight defect: the
paper-external solver rejected an intentionally restricted parent range as an
incomplete original-problem root range. The invalid result was moved intact to
`completion/invalidated_attempts/invalid_configuration_cf_V10_L0_retain/`.
Counterfactual mode now explicitly permits a restricted diagnostic root while
remaining ineligible for an original-problem certificate. The runner also
rejects invalid-configuration results instead of sealing them.

The next correctly located preflight solved the restricted parent but exposed
a third defect: its terminal fields still inherited the original-problem
strict-certificate label. That raw result is preserved intact at
`completion/invalidated_attempts/incorrect_original_certificate_cf_V10_L0_retain/`
and is invalidated. Counterfactual terminal status now reports only local
restricted-parent exactness (or its time-limit/non-exact counterpart), forces
`strict_certified_original_problem=false`, and is recorded separately by the
completion runner.

The following matched retain/midpoint smoke pair then exposed two evidence
assembly defects: the legacy split-decision ledger was copied before the richer
Round 45 timing-decision ledger, and the parent-state facet hash included facets
created later for a split child. Both raw runs are preserved intact at
`completion/invalidated_attempts/incomplete_parent_state_cf_V10_L0_retain/` and
`completion/invalidated_attempts/incomplete_parent_state_cf_V10_L0_midpoint/`.
The runner now prefers the timing ledger, restricts inherited facet signatures
to the frozen parent, and requires every forced split to produce exactly two
children whose intervals form the exact parent union.

The first PMM smoke arm then exposed a solver-path defect guarded by the atomic
scheduler: Round 44 had merged a strengthened bound into the live parent, while
the split builder initialized PMM children from a stale pre-merge parent copy.
The scheduler rejected the split with
`child_did_not_inherit_parent_bound`. Its raw evidence is preserved at
`completion/invalidated_attempts/stale_parent_bound_cf_V10_L0_pmm/`. Split
children now inherit the authoritative live parent lower bound after every
valid strengthening merge.

That correction changed the executable hash. The otherwise valid preceding
retain/midpoint pair is therefore excluded from the final matched comparison
and preserved at
`completion/invalidated_attempts/pre_stale_bound_fix_cf_V10_L0_retain/` and
`completion/invalidated_attempts/pre_stale_bound_fix_cf_V10_L0_midpoint/`.
Every official arm is regenerated from the repaired binary.

The first replay of source parent `L1` then showed an audit mapping defect:
restricted parent intervals are deliberately re-rooted as runtime leaf `L0`,
but the validity checker compared runtime events with the source atlas ID.
The exact solver evidence is preserved at
`completion/invalidated_attempts/replay_parent_id_mapping_cf_V10_L1_retain/`
and
`completion/invalidated_attempts/replay_parent_id_mapping_cf_V10_L1_midpoint/`.
Parent artifacts now record both the immutable source ID/depth and the replay
root ID; event, point, facet, and coverage validation uses the latter.

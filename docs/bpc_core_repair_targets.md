# BPC Core Repair Targets

This round freezes a fixed set of BPC leaves before changing pricing or tree
logic.  The target manifest is
`results/bpc_core_repair_round/target_leaf_manifest.csv`.

The target set is intentionally BPC-first:

- `v12_m2_control`: controlling unresolved leaf from the unified
  `paper-gf-bpc-core` V12 M2 run.
- `v12_m1_control`: controlling unresolved leaf from the unified
  `paper-gf-bpc-core` V12 M1 run.
- `moderate_seed3301_control`: lowest-LB unresolved V20/M3 leaf from the
  realigned paper-core run.
- `high_imbalance_seed3202_control`: lowest-LB relevant unresolved leaf from
  the realigned paper-core run.
- `v12_m2_forced_bpc_diagnostic`: a small diagnostic leaf used only to force
  BPC behavior when relaxation screening would normally dominate.

Each target records the instance hash, gamma range, incumbent cutoff,
inherited relaxation lower bound, gap to cutoff, and the relaxation reason for
not closing.  BPC closure is accepted only when exact pricing closure is
visible in the result JSON and audit output.  The forced diagnostic target is
not paper-core certificate evidence by itself.

# Objective Convention Audit Round 2

The objective convention audit now unwraps `results` arrays and tolerates
wrapper-finalized `model_size_limit` rows as noncertified diagnostics.

The audit checks controlled exact and benchmark rows for input metadata,
sealed provenance, and no BPC/known-UB/archive contamination in compact-BC
paper rows.

Output:
`results/gf_compact_bc_strengthening_round2/objective_convention_audit.csv`.

Round 2 result: passed.


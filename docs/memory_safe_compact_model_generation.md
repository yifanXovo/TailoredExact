# Memory-Safe Compact Model Generation

The compact-BC path now records model-size policy and model-size stop reasons.
For large diagnostics, paper rows must finish as either normal noncertified JSON
or explicit `model_size_limit` JSON.

Round 2 large-V behavior:

- V50 compact-BC rows hit `std_bad_alloc`; emergency noncertified JSON was
  written by the solver.
- V100 compact-BC rows hit native access violation before solver finalization;
  wrapper-finalized noncertified JSON records process return code
  `-1073741819`.
- Plain CPLEX benchmark V50/V100 rows are separate benchmark-only evidence.

CSV:
`results/gf_compact_bc_strengthening_round2/model_size_audit.csv`.

Large-V remains diagnostic scalability work, not a paper certification claim.


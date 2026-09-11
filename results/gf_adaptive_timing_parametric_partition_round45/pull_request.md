## Outcome

Round 45 implements and audits a unified adaptive Gini interval decomposition:

- Part I selects a uniform K0=4 gamma-veto timing rule,
  `old_C6_split AND Gamma_sum >= 0.012`.
- Part II implements midpoint, PMM, and FPMM point policies with deterministic,
  exact-coverage, fail-closed ledgers. PMM/FPMM did not improve the controlled
  counterfactuals, so midpoint remains selected.
- The selected algorithm passes the frozen small development, validation, and
  unopened holdout protocol. C6 remains the broad validated mainline.
- Frozen V20/V50 atlases are structurally valid and selective. Targeted 300 s
  runtime screens improved gap integrals but do not support scale claims.

## Validation

- Independent clean Release/Gurobi build
- 23/23 CTest targets
- 104/104 Python protocol tests
- Executable-backed implicit-versus-explicit Round 45 default-off sentinel
- Zero false certificates in the reported small candidate rows

The compact evidence archive, manifests, ledgers, reports, and reproduction
commands are in `results/gf_adaptive_timing_parametric_partition_round45/`.

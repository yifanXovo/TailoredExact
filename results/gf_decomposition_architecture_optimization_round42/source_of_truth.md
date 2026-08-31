# Round 42 source of truth

- Existing repository only; source is verified Round 41 commit `75fe23e591a39b54f7940eb0012a245e3a92d955`.
- Research branch: `codex/round42-decomposition-architecture-optimization`.
- Frozen benchmark: all 24 Round 39 instances, partitioned 10/7/7 before any
  Round 42 candidate execution.
- Split signature: `13a9158d40f5cb9f5fb2969f448af0d0ccafb600f20782002bf482e7645f7382`.
- Solver contract: verified HGA-FULL start, Threads 1, Seed 0, Gurobi Presolve
  Auto, zero relative and absolute MIP gaps.
- Primary performance metric: exact-phase Gurobi Work. Secondary: shifted
  exact-phase time ratio `(candidate+1)/(C6+1)`.
- Validated default remains `C6-HGA-FULL, K=4, rho=0.01`.
- Every Round 42 mechanism is explicit and default-off.
- Official executable SHA-256:
  `82178ffbbb8106c06661fcec8fd57ce7fe63b1fb9b6340b9d85bd269fc013fbe`.
- Default-off equivalence: all three frozen sentinels match implicit versus
  explicit off and match their Round 41 deterministic trajectory SHA-256.
- Contemporary reference evidence comprises C6-HGA-FULL-K4, the existing exact
  C6-K1-SINGLE policy, External-K2-Fixed, and ST-K2-P-Core. P-GRB was not rerun
  because no candidate passed development or supported a repaired-C6 claim
  requiring new adjudication.
- Final outcome: `bounded_systematic_negative_result`. All six Family A/B/C
  base/refinement candidates completed development; none passed every frozen
  gate, so validation was ineligible and the final holdout remained sealed.
- Compact result: no stable improvement was found within the tested
  static-single-tree, paired-block, and terminal-sibling-coalescing families.
- Raw runs remain under `results/gf_decomposition_architecture_optimization_round42/runs/`;
  compact manifests, hashes, audits, and reports are the committed evidence.

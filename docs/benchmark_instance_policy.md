# Benchmark Instance Policy

The current V12 M1/M2 results are regenerated engineering benchmarks, not
confirmed historical paper target files.

## Current Regenerated Instances

| case | path | instance hash | SHA256 | scope |
|---|---|---|---|---|
| V12 M1 average | `reference/regen_candidate_V12_M1_average.txt` | `a154aff570ee4405` | recorded in result JSON | regenerated_engineering |
| V12 M2 average | `reference/regen_candidate_V12_M2_average.txt` | `52a1bbf5593d7d3f` | `0BB0416CC9540FFFBB91299D5C9ED3D6C2363906424005B1C40B4E3829DDF4F0` | regenerated_engineering |

Generated V8/V10/V20/V50/V100 files under `reference/generated/` are
deterministic engineering benchmarks unless their source is later matched to
historical data.

## Capacity/Inventory Variants

Round heuristic-relaxation-dataset adds deterministic variants under:

```text
reference/generated_variants/
reference/generated_variants/manifest.csv
```

The generator preserves the base network, distances, vehicle count, route
duration convention, lambda convention, weights, and station ordering. It
regenerates capacities and initial/target inventories using recorded seeds and
stores SHA256 hashes for every output file. These variants are explicitly
`regenerated_engineering` benchmarks.

## Reporting Rule

- Historical paper target: use only if the original source file is recovered and
  its hash is recorded.
- Regenerated engineering benchmark: use for algorithm engineering evidence,
  with path/hash and generator manifest.
- Smoke test: small correctness/certificate regression tests.
- Diagnostic large generated case: scalability diagnostics, never reported as
  optimal unless full certificate fields prove it.

No regenerated instance result should be described as reproducing a historical
paper benchmark.

Archive-incumbent rows are also not paper-core default evidence. They may be
used as diagnostic UB comparisons only, with route plans independently verified
and with no lower-bound contribution.
## Current Round Note

The V12 M1/M2 rows in `results/primal_ub_improvement_round/` use regenerated
engineering instances:

- `reference/regen_candidate_V12_M1_average.txt`;
- `reference/regen_candidate_V12_M2_average.txt`.

The generated variant rerun uses files in `reference/generated_variants/` and
remains engineering-only evidence.

## Hard V20/M3 Stress Suite

`reference/hard_stress/V20_M3/` contains six regenerated engineering stress
instances generated for exact-phase primal and lower-bound convergence tests.
They use V=20, M=3, Q=30, deterministic seeds, capacities in `[20,50]`,
positive targets, and a three-cluster metric coordinate pattern. Stress classes
are `tight_T`, `high_imbalance`, and `moderate`.

These files are diagnostic engineering benchmarks only. They must not be
reported as historical paper targets.

New relaxation-bound round outputs classify these rows as
`hard_generated_v20_m3`. Any older summary that labelled them
`historical_target` should be treated as a metadata bug, not as a benchmark
claim.

## Relaxation Closure Round Metadata

The `results/relaxation_closure_round/` V20/M3 rows keep the same policy:

- `instance_scope=hard_generated_v20_m3`;
- route-mask all-subset enumeration is not certifying;
- no V20/M3 result is a historical paper target;
- noncertified rows are lower-bound stress diagnostics unless all original
  certificate fields are satisfied.

The V12 rows in the same result directory use regenerated engineering candidate
files:

- `reference/regen_candidate_V12_M1_average.txt`;
- `reference/regen_candidate_V12_M2_average.txt`.

## V20 Replication Round Policy

`results/v20_replication_round/` keeps the same benchmark classification:

- V20/M3 rows are `hard_generated_v20_m3`;
- V12 rows are `regenerated_engineering`;
- V4 rows are `smoke`;
- no V20 stress row is a historical paper target.

The round certifies `high_imbalance_seed3202` reproducibly and adds
`tight_T_seed3101` as a second certified V20/M3 stress row.  These are
engineering stress certificates for the exact algorithm, not historical paper
benchmark claims.  Noncertified rows must be reported with their unresolved
intervals and gaps rather than omitted or converted into historical-target
status.

## Sealed Paper Pipeline Round Policy

`results/sealed_paper_pipeline_round/` keeps the same benchmark
classification:

- V20/M3 rows are `hard_generated_v20_m3`;
- V12 rows are `regenerated_engineering`;
- V4 rows are `smoke`.

The sealed round is designed as a paper-candidate reproducibility package. It
uses one command template with `--paper-run-sealed true`; no row may use
archive scanning, external incumbent JSON, known UB injection, manually focused
intervals, or instance-specific solver settings. Certified V20 rows remain
engineering stress evidence unless and until the corresponding historical paper
target files are identified and hashed.
## Sealed Completion Round Classification

`results/sealed_pipeline_completion_round/` uses the regenerated engineering
and hard stress policy:

- V4 smoke is a smoke test.
- V12 M1/M2 regenerated rows are regenerated engineering benchmarks.
- V20/M3 rows under `reference/hard_stress/V20_M3/` are
  `hard_generated_v20_m3` stress instances, not historical paper targets.

The evidence package includes both certified and noncertified final JSONs. A
noncertified row with a final checkpoint JSON is an audited algorithm outcome,
not a skipped historical target.

## Sealed Closure Round Classification

`results/sealed_closure_round/` preserves the same classification:

- V4 smoke is a smoke test.
- V12 M1/M2 regenerated rows are regenerated engineering benchmarks.
- V20/M3 rows under `reference/hard_stress/V20_M3/` are
  `hard_generated_v20_m3` stress instances.

This round is not a historical paper benchmark. It is a sealed engineering
stress test for finalization, all-leaf oracle processing, and interval-level
diagnosis. Certified V20 rows are exact certificates for those generated stress
instances only.

## Oracle Closure Round Classification

`results/oracle_closure_round/` follows the same policy:

- V4 smoke is a smoke test.
- V12 M1/M2 rows are regenerated engineering benchmarks.
- V20/M3 rows under `reference/hard_stress/V20_M3/` are
  `hard_generated_v20_m3` stress instances.

The round contains both certified and noncertified sealed rows. Noncertified
rows with positive gaps are not historical benchmark failures; they are
engineering stress diagnoses for exact interval cutoff MIP and BPC leaf
closure.

## Oracle Bound Merge Round Classification

`results/oracle_bound_merge_round/` follows the same regenerated engineering
policy:

- V12 M1/M2 rows are regenerated engineering benchmarks.
- V20/M3 rows under `reference/hard_stress/V20_M3/` are
  `hard_generated_v20_m3` stress instances.
- The missing V4 smoke input is recorded as a skipped smoke row for this
  checkout, not as a benchmark result.

The round is an exact interval-oracle lower-bound experiment, not a historical
paper benchmark. `moderate_seed3301` remains noncertified with audited gap
`0.0280667552335`; this is a valid generated-stress result, not a historical
paper target claim.

## Strengthened Oracle Round Classification

`results/strengthened_oracle_round/` follows the same regenerated engineering
policy:

- V12 M1/M2 rows are regenerated engineering benchmarks.
- V20/M3 rows under `reference/hard_stress/V20_M3/` are
  `hard_generated_v20_m3` stress instances.
- Plain compact CPLEX rows are benchmark comparisons only.

The round certifies `moderate_seed3301` as a generated hard-stress instance.
This is a valid exact certificate for that generated file and hash, not a
historical paper target claim.

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

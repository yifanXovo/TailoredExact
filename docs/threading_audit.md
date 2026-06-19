# Threading Audit

Date: 2026-06-12.

## Host

- CPU: 12th Gen Intel(R) Core(TM) i7-12700KF
- Physical cores reported by WMI: 12
- Logical processors reported by WMI: 20
- `NUMBER_OF_PROCESSORS`: 20
- `[Environment]::ProcessorCount`: 20

## Observed Run Settings

The reproduced benchmark commands in this pass used:

- plain CPLEX CLI `--threads 1`, therefore actual CPLEX command-line setting `set threads 1`;
- BPC sequential reproduction `--threads 1`, `--bpc-workers 1`, `--pricing-threads 1`;
- BPC parallel tests `--threads 1`, `--bpc-workers 4`, `8`, `12`, and `16`, `--pricing-threads 1`, `--parallel-frontier true`, `--parallel-nodes false`.

## Plain CPLEX Baseline

`src/CplexBaseline.cpp` writes a CPLEX command file containing:

```text
set threads max(1, options.threads)
set timelimit options.solve_time_limit
set mip tolerances mipgap 1e-8
```

So plain CPLEX does not use an unmodified CPLEX default thread count in the current code. It explicitly uses the CLI `--threads` value. This behavior existed before the current threading audit; it was not changed except for adding a note to result JSONs.

## Strengthened Compact / Tailored Fallback

The tailored compact portfolio can call `solveCplexBaseline` for the strengthened compact fallback. In that path it inherits the same explicit CPLEX thread setting:

```text
set threads max(1, options.threads)
```

Other tailored exact subroutines already had limited parallelism:

- route-load materialized enumeration uses `std::async` over first-station partitions;
- final-inventory proof search uses `std::async` over root-domain partitions.

Those are auxiliary `original_compact` paths, not BPC.

## BPC Before This Pass

Before this pass, the full `gcap-frontier` BPC path was effectively sequential at the frontier and branch-node levels. It could invoke CPLEX command-line solves internally, but those internal solves were single-threaded:

- restricted coverage master diagnostic: `set threads 1`
- fixed-Gini restricted master: `set threads 1`
- final-inventory / route-mask relaxation bound: `set threads 1`

Exact route-load pricing is implemented in C++ label/DP code in `src/Pricing.cpp`; it does not call CPLEX.

## BPC After This Pass

New CLI options:

```text
--bpc-workers N
--pricing-threads M
--parallel-frontier true|false
--parallel-nodes true|false
```

Current implementation:

- `--parallel-frontier true` with `--bpc-workers N>1` parallelizes the initial independent Gini frontier interval pass.
- Scheduling is a deterministic dynamic queue ordered by proximity to the incumbent Gini value.
- Each worker uses a fixed incumbent cutoff copied before the parallel pass.
- Shared incumbent, frontier ledger, counters, and notes are updated only after all futures join, in interval-index order.
- Internal restricted-master CPLEX and route-mask bound CPLEX calls remain `set threads 1`.
- Exact route-load pricing remains native C++ and currently ignores `--pricing-threads`; the option is recorded to support future pricing-level parallelism.
- `--parallel-nodes` is accepted and logged, but branch-node parallelism is disabled in this build because branch-node scheduling would require a more invasive shared incumbent/open-node synchronization design.

The V4 parallel smoke run:

- result: `results/frontier_parallel_smoke_v4.json`
- status: `optimal`
- `bpc_workers=2`
- `pricing_threads=1`
- `parallel_frontier=true`
- `parallel_nodes=false`
- `parallel_tasks=4`
- `certified_original_problem=true`

## Oversubscription

Nested parallelism is limited by keeping internal CPLEX calls at one thread per BPC worker. With `--bpc-workers 4`, expected CPLEX worker pressure is about four single-threaded internal CPLEX processes plus native pricing work. With `--bpc-workers 8` or `12`, this can still fit on a 20-logical-processor i7-12700KF, but concurrent command-line CPLEX processes plus native pricing may contend for memory and process startup overhead.

The solver logs an oversubscription warning when:

```text
bpc_workers * pricing_threads > hardware_concurrency
```

Since `pricing_threads` is currently recorded but not used internally, this warning is conservative.

## Audit Decision

The current BPC parallelization is safe but limited. It parallelizes independent initial frontier intervals and does not alter certificate conditions. Branch-node and pricing-level parallelism remain disabled pending a more careful shared-state design.

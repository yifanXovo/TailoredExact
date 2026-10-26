# Round 47 final build and tests

## Build and test results

- Exactly one clean official Release/Gurobi build: `build/official-round47-283f576/`.
- Source-freeze commit/tree: `283f576d002370ec596c8b9f11e3e3c36d6c172f` / `fc5ee5de610e2931a846eb80a84c359279cf0309`.
- Official executable SHA-256: `541c496881c7a0f79ffaf50cbdf4acc3bdf106dd86031990c0e6cf56c3deaa16` (5,848,450 bytes).
- Toolchain: GNU g++ 14.2.0; CMake 3.30.5; Gurobi 13.0.2 build v13.0.2rc1; machine `WIN-3NO58RVQ4VC`.
- Final CTest: **25/25 passed** in 2.04 seconds.
- Dedicated `Round47AdaptiveMassTests`: passed, including all 28 assertions in the frozen unit-test inventory.
- Historical plus Round 47 Python protocol discovery: **135/135 passed** in 33.687 seconds.
- Round 47 protocol tests: **8/8 passed** as part of that discovery.
- Default-off old-C6 equivalence sentinel: **17/17 fields passed**; this is a 120-second correctness sentinel, not a benchmark row.

The first shell-level CTest attempt found no `ctest` on `PATH` and ran no tests; the final invocation used the exact CMake-bundled executable recorded in `CMakeCache.txt`. The first captured Python protocol invocation used Round 46's non-hash-qualified default lookup and stopped at setup because that convenience path is absent. The supported rerun set `EXACTEBRP_ROUND46_EXE` and `EXACTEBRP_ROUND47_EXE` to their sealed official executables and passed all 135 tests.

## Official evidence audit

- Official rows: **108** (40 Stage 3, 40 Stage 4, 28 Stage 5).
- Strict certificates: **65** (18 Stage 3, 28 Stage 4, 19 Stage 5).
- False certificates: **0**.
- Exact one-child contractions: **44** (14 Stage 3, 14 Stage 4, 16 Stage 5).
- Extra score LP queries: **0**; extra score MIP queries: **0**.
- Unique executable hashes: **1**.
- Independently rehashed sealed row artifacts: **5,711**, zero missing, size-mismatched, or hash-mismatched files.
- Independently rehashed Stage 0 files: **11/11**.
- Top-level final-evidence inventory: **48 files** before the inventory itself, zero mismatches.
- Missing mandatory rows: none.
- V50 rows: 0; caps above 1,800 seconds: 0; watchdog failures: 0.
- Active forbidden mechanisms in official identities: 0.
- Baseline benchmark arms in Round 47 runs: 0; all comparator rows are historical references.
- Bound/coverage certificate audit: zero false certificates and zero bound-order violations.

## Source, secret, license, and preservation audit

- Source scope is limited to the Round 47 option/result plumbing, C6 evaluator/scheduler behavior, the dedicated C++ target, Round 47 scripts/protocol tests, and `results/gf_c6_adaptive_mass_contraction_round47/` top-level evidence.
- The official executable was frozen before candidate runtime. Post-freeze changes affect orchestration, tests, aggregation, auditing, and reporting only; no algorithmic source changed after freeze.
- Credential-pattern scan over all intended new/changed source and committed evidence: passed with no GitHub, OpenAI, AWS, or private-key patterns.
- License audit: no new third-party source, binary, solver dependency, or vendored code; build products and raw run trees remain uncommitted.
- The three pre-existing tracked user modifications remain unstaged and unchanged by Round 47 publication:
  - `results/gf_compact_bc_round/handling_convention_test/handling_convention.json`
  - `results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv`
  - `results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json`
- Pre-existing untracked user paths are preserved. No re-clone, reset, destructive cleanup, or V50 run occurred.

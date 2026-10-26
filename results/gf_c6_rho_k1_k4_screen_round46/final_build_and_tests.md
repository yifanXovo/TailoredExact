# Round 46 final build and tests

## Results

- Official clean build: passed (full Release/Gurobi build)
- CTest: **24/24 passed**
- Round46C6RhoTests: passed (15 checks)
- Historical Python protocol suites Round 25–45: all passed
- Round 46 Python protocol tests: **7/7 passed**
- Implicit versus explicit rho=0.01 equivalence: **17/17 passed**
- `git diff --check`: recorded in final publication audit

## Official-row audit

- Official rows: 232 (110 Stage 3, 70 Stage 4, 52 Stage 5)
- Unique executable hashes: 1 (`d574b38b2f44ae2aacf92bf685f439354b5a08dbe257b6c399045b98a157871b`)
- V50 rows: 0
- Caps over 1800 seconds: 0
- Watchdog failures: 0
- Missing completion markers: 0
- Active forbidden mechanisms: 0
- False certificates: 0
- Bound-order violations: 0
- Artifact manifests independently verified: 232/232, zero missing or hash-mismatched files
- Source-scope audit: Round 46 implementation/tests/scripts and `results/gf_c6_rho_k1_k4_screen_round46/` only; three pre-existing tracked user modifications remain unstaged and unchanged by publication
- Secret scan: no GitHub/OpenAI/AWS/private-key credential patterns in new source or committed evidence
- License audit: no new third-party source or binary dependency; build products remain uncommitted
- `git diff --check`: passed (line-ending advisory only)

The initial Round 46 protocol invocation used its default non-hash-qualified lookup and was immediately rerun with `EXACTEBRP_ROUND46_EXE` pointing to the sealed executable; the supported override passed all checks and no second build/copy was created.

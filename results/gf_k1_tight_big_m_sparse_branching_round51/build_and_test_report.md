# Round 51 build and test report

Status: **pass**.

- Environment: Windows 10 19045, Intel i7-12700KF, GCC 14.2.0 MSYS2 UCRT64, CMake 3.30.5-msvc23, Gurobi 13.0.2.
- Configuration: Release, MinGW Makefiles, single-threaded solver contract.
- Full build: `cmake --build build/round51-m1 -j 4` reached 100% and built every configured target.
- Complete configured suite: `ctest --test-dir build/round51-m1 --output-on-failure` passed 29/29 tests, with zero failures.
- Round 51 experiment executable SHA-256: `b5e12cd23699d8ea2177381e3e154eb4c385873b4ec180699f71270c81803cd4`.
- The only build diagnostic was a pre-existing unused-function warning for `readAll` in `tests/round27_paper_scheduling_tests.cpp`; there were no Round 51 compilation or test diagnostics.

The suite includes the new row-specific Big-M, negative/nonfinite rejection, target-row construction, V>12 default path, policy parsing, semantic-family selection, deterministic candidate budget/tie-break, floor/ceil bound, infeasible/invalid probe, sparse priority, top-one revision, fallback, and accounting tests. Runtime model-lifecycle/readback checks are separately frozen in `adaptive_branching_correctness_smoke_audit.json` and `adaptive_branching_revision_correctness_smoke_audit.json`.

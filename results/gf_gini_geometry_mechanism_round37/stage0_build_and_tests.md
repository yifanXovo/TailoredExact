# Round 37 Stage 0 build and tests

The clean Release/Gurobi build passed. The validated executable is
`build_round37/official/gurobi/ExactEBRP.exe` (5,231,731 bytes, SHA-256
`1df031f903f9d4cc8559ff29f886d1a6a660ed73c19a9f3efc68f52a3b545b63`).

- C++ tests: 15 passed, 0 failed.
- Python test scripts: 28 passed, 0 failed.
- Contemporaneous old/new C6 equivalence: 18/18 component comparisons passed
  on V12_M1 and a short V20/M2 split witness.

The first compile invocation was invalidated because a short command watchdog
left concurrent make processes and one truncated object. After those processes
exited, the newly created `build_round37` directory was verified, removed, and
configured from empty. Only that second clean build is accepted here.

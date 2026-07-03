# Tailored BC Callback Blockers

The blocker is architectural, not mathematical:

1. The production path writes LP/script files and starts `cplex.exe` as a separate process.
2. CPLEX callbacks require in-process solver API access.
3. This workstation has CPLEX headers but only MSVC import libraries, while the repository build currently uses MinGW/g++.

To unblock true callbacks, one of these changes is required:

- add a supported MSVC build that links Concert or the CPLEX C API;
- add a MinGW-compatible CPLEX import layer if available and supported;
- create a separate callback-enabled helper executable with a stable JSON/LP exchange contract.

Until then, the final callback-round status must remain:

`FAILED GOAL: remained static CPLEX-backed compact MIP; not a true tailored branch-and-cut callback implementation.`

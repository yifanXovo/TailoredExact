# CPLEX Boundary for Tailored BC

`paper-gf-tailored-bc` is intended to be a CPLEX-managed tailored branch-and-cut mode with user-cut, lazy, incumbent, and branching callbacks.

Current repository state:

- The checked-in executable is built with MinGW/g++.
- `src/CplexBaseline.cpp` generates LP/script files and invokes `cplex.exe -f ...` through a command-file process boundary.
- IBM CPLEX headers are present on this workstation, but the available import libraries are MSVC `.lib` files and the MSVC compiler is not available on `PATH`.

Therefore the current executable cannot host in-process CPLEX callbacks. Rows using `paper-gf-tailored-bc` are labelled `static_fallback` unless a future build links against the CPLEX C or Concert API.

Static/root cut rows are still valid compact-BC strengthening when their proofs hold, but they are not callback evidence.

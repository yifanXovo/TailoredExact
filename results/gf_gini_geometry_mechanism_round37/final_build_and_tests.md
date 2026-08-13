# Round 37 final build and tests

The final source tree was configured in a new empty directory and built in
Release mode with GNU 14.2.0 and Gurobi 13.0.2. All **16/16 C++ tests** and
**28/28 Python test scripts** pass.

The independent clean executable has 5,246,159 bytes and SHA-256 `98b16849...`.
The official experiment executable has the same byte size and SHA-256
`90689ced...`. The PE links are not byte-identical, so this report makes no
reproducible-link claim. The official experiment binary remains independently
frozen in every stage manifest, command, completion marker, and final audit.

After the candidate was implemented, the official experiment executable also
passed **18/18 contemporaneous default-off C6 equivalence comparisons** against
the frozen Round 36 executable. The comparison covers startup, proof range and
four intervals, parent/child LPs, controlling-leaf sequence, targets, requeues,
lookahead, splits, closures, and final certificate fields while excluding clocks
and solver-effort counters.

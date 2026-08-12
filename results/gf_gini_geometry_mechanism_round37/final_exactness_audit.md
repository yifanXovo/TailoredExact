# Round 37 final exactness and provenance audit

Final audit passed: **True**.

- Runs: 22 (6 strict certificates, 16 valid non-certificates).
- False certificates: 0.
- Root coverage, atomic parent-child coverage, monotone leaf/global bounds, verifier consistency, lifecycle balance, optimize counters, and round-trip Work/node ledgers pass on every run.
- All 11 pairs use identical commands except the explicit geometry policy and run-local paths.
- Every executable and runner source hash still matches its stage freeze. The pre-result hypothesis status and protocol rendering were updated after experiments; their original hashes remain in the immutable freezes and the changes are separately classified.
- Post-implementation default C6 equivalence: 18/18 components.
- Canonical raw models: 170 files, 980558839 bytes retained locally. Their paths, sizes, and SHA-256 hashes are committed; frozen commands recreate them. Compact exact ledgers and result artifacts are published.

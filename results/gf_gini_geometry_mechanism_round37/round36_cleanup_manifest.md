# Round 36 local-artifact cleanup manifest

The committed Round 36 evidence package was not modified. Cleanup was
restricted to explicitly enumerated untracked top-level files. No directory
was recursively removed.

- Execution status: `removed_verified_redundant_files_and_restored_test_dependency`
- Candidate files: 80
- Candidate bytes: 36390599
- Removed files: 79
- Removed bytes: 17209698
- Trajectory identity verified: `true`
- Protected user files unchanged: `true`

The 19,180,901-byte uncompressed trajectory was initially classified as a
duplicate because it exactly restores from the committed deterministic gzip.
The full test sweep proved that frozen Round 36 schema tests consume its local
path directly. It was restored byte-for-byte (SHA-256
`5b665120c62f115d1370e0ee56c47a4bdcc891aa738d177baceb50def25fe310`) and
is retained as an operational test fixture.

## Retained provenance directories

| Path | Files | Bytes | Reason |
|---|---:|---:|---|
| `results/gf_incumbent_decomposition_causal_round36/runs` | 2374 | 2042266628 | raw, invalidated, equivalence, or representative provenance |
| `results/gf_incumbent_decomposition_causal_round36/stage_c_runs` | 1874 | 2643646608 | raw, invalidated, equivalence, or representative provenance |
| `results/gf_incumbent_decomposition_causal_round36/invalidated_rows` | 37 | 8169289 | raw, invalidated, equivalence, or representative provenance |
| `results/gf_incumbent_decomposition_causal_round36/stage_c_invalidated_attempt_1_contract_bug` | 754 | 467608757 | raw, invalidated, equivalence, or representative provenance |
| `results/gf_incumbent_decomposition_causal_round36/baseline_equivalence_runs` | 101 | 19325595 | raw, invalidated, equivalence, or representative provenance |
| `results/gf_incumbent_decomposition_causal_round36/stage_c_contract_fix_equivalence_runs` | 68 | 12885784 | raw, invalidated, equivalence, or representative provenance |
| `results/gf_incumbent_decomposition_causal_round36/representative_raw` | 280 | 1115175 | raw, invalidated, equivalence, or representative provenance |

The per-file SHA-256 inventory and replacement rationale are in
`round36_cleanup_manifest.csv` and `round36_cleanup_manifest.json`.

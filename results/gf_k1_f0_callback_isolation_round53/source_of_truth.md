# Round 53 source of truth

The base repository identity is Round 52 commit
`44ed4057cc4d2ce67b86d623b57500e95cad5058` and tree
`5e2f5a144b8f3f31439c1010ef07c8926d061d68`. The outer controller is exactly
the committed Round 52 `k1_am_controller_freeze.json`; its source SHA-256 is
`169e4b7a509a307fa90d3075523f4b42e81cc8530a22592e1ce501bf35d9a64a`.

Fixed state identities and reconstruction data come only from Round 50
`fixed_interval_state_manifest.csv` and
`fixed_interval_state_reconstruction_audit.csv`. F0-CLEAN is defined only by
`f0_mathematical_contract.json` and the explicit named policy. Historical
`f0-no-rank3-support-duration` remains an alias for reproduction.

The sealed panel identities are the deterministic Stage-0 JSON/CSV manifests
under this evidence root and the hashed inputs under
`reference/round53_sealed_v12/`. Solver results remain sealed until the final
backend, integration decision, source commit, official build directory, and
executable SHA-256 are frozen. Compact committed ledgers are authoritative;
inventoried native logs are local reproduction evidence only.

# Round 53 evidence storage audit

- Committed compact-root files inventoried: 73
- Committed compact-root bytes inventoried: 32279562
- Local-only groups inventoried: 16
- Local-only files inventoried: 5546
- Local-only bytes inventoried: 817523661
- Exact executable SHA-256: `b49cc5a5e631c6a8ce7a8bd4d0e6da44162800c97996494b1ee6a04071286c85`
- Fixed-interval harness SHA-256: `7f8bc2b5c36d552d5d9c405cb85bac64ce68e6fa4eae91b4dff33ad7f7a0de52`

`compact_evidence_inventory.csv` contains per-file SHA-256 identities for every
compact root file except the three storage-audit files themselves and
`final_evidence_inventory.csv`, avoiding recursive cross-hashes. The final
inventory hashes all three storage-audit files. `local_raw_evidence_inventory.csv`
contains one row per
local-only top-level group under `local_raw/` and `dev_smoke/`. Its deterministic
tree identity is SHA-256 over sorted records of
`relative-path\0byte-count\0file-sha256\n`.

Native logs, models, solutions, progress streams, and command directories remain
local-only. Each official local group points to a committed representative
ledger and records the frozen executable hashes. `dev_smoke/` is explicitly
development-only and is excluded from every official claim. No historical raw
evidence was modified or committed by this audit.

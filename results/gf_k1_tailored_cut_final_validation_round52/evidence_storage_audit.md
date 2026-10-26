# Round 52 evidence storage audit

Native logs, solver traces, and full artifact trees remain local under `local_raw/`; Git tracks no file below that directory. Each official final run has its own `artifact_manifest.csv` and completion marker. The committed `local_raw_evidence_inventory.csv` additionally binds every top-level raw evidence group to a deterministic tree hash over relative path, byte size, and file SHA-256.

Compact CSV/JSON/Markdown ledgers, frozen manifests, proofs, source, tests, and reproduction commands are committed. `compact_evidence_inventory.csv` hashes each compact evidence file; `final_evidence_inventory.csv` joins those entries to the local raw group hashes. The inventory files exclude themselves to avoid recursive hashes.

The two incomplete P-GRB fingerprint-discovery attempts remain local, are explicitly invalidated by `final_panel_preflight_invalidation_audit.json`, and are excluded from every official row count and metric.

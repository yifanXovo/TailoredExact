# Round 52 source of truth

The authoritative decision is `final_decision.json`; the human-readable interpretation is `final_report.md`.

- Frozen base: `c6d7109bf69f50bd459174e8f05242b478e57d85`
- Algorithm/executable freeze: `52ccf3e713e1c57484ac2ec9ba96baf3cb8c8026`
- Executable SHA-256: `d245c76f6397c757894610d8f5238cfeb971761ff7e05edf51058e451d810151`
- Tau/controller: 0.08, K0=1, complete interval, midpoint, adaptive mass
- Final inner backend: historical production v0; tailored cuts off
- Official final rows: 24 validation + 24 holdout = 48
- Certificates: validation P-GRB 3, K1 7; holdout P-GRB 3, K1 6
- Missing rows: none
- False certificates: zero
- Severe P-GRB regressions: 0
- Final benchmark/scale: `pgrb_advantage_supported` / `v12_v20_supported_v50_mixed`

Raw evidence is intentionally local-only. Use `compact_evidence_inventory.csv`, `local_raw_evidence_inventory.csv`, and `reproduction_commands.md` to bind compact claims to native artifacts.

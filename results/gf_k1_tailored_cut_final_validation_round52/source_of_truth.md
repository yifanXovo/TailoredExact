# Round 52 source of truth

The authoritative K1-AM action source is the Round 47 adaptive-mass decision
ledger, not inferred labels in later counterfactual summaries:

- `results/gf_c6_adaptive_mass_contraction_round47/adaptive_mass_action_replay.csv`
- `results/gf_c6_adaptive_mass_contraction_round47/adaptive_mass_score_census.csv`
- `results/gf_c6_adaptive_mass_contraction_round47/tau_freeze.json`

All available Round 47--51 adaptive-mass decision ledgers are replay inputs;
raw historical files are immutable. Corrections are additive errata. The
Round 50 fixed-state identity source is
`results/gf_k1_interval_mip_vnext_round50/fixed_interval_state_manifest.csv`.
The Round 51 v0/M1 affected-state and experiment ledgers under
`results/gf_k1_tight_big_m_sparse_branching_round51/` are the telemetry-audit
inputs. Plain continuous LP solves, rather than MIP callback telemetry, define
the v0/M1 LP monotonicity audit.

Historical decisions are fixed by each round's `final_decision.json` and
`stage0_freeze_manifest.json` under the Round 47--51 evidence roots. The Round
52 validation/holdout identities are the Stage-0 JSON/CSV manifests generated
from the Round 51 base commit without solver observation. Committed compact
ledgers are authoritative for conclusions; inventoried native logs are local
reproduction evidence only.

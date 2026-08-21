
# Round 46 source of truth

The immutable Stage 0 contract consists of this file, `research_contract.md`,
`solver_contract.json`, `dataset_freeze.json`, `rho_grid_freeze.json`,
`arm_definition.json`, `build_policy.json`,
`historical_reference_manifest.csv`, `pgrb_equivalence_manifest.csv`,
`promotion_gates.json`, `official_start_record.json`, and
`stage0_freeze_manifest.json`.

Official runtime evidence is valid only when a completion marker and an
artifact manifest bind it to the single frozen official executable. Candidate
selection is authoritative only in `stage3_candidate_freeze.json`; finalist
selection is authoritative only in `stage4_finalist_freeze.json`. Final claims
are authoritative only in `final_decision.json` after all completion gates
pass. Raw run directories are immutable after sealing.

Historical Round 31/40/45 files are auxiliary references by path, commit, and
SHA-256. They are never candidate rows and never change the frozen rho grid.

# Round 36 completion requirements audit

- All requirements achieved: True.
- Achieved: 34.
- Incomplete: 0.
- Missing: 0.
- Contradicted: 0.

| section | status | requirement | evidence |
|---|---|---|---|
| 0_git_workspace | achieved | dedicated Round 36 branch is active | git branch --show-current = codex/round36-incumbent-decomposition-causal-study |
| 0_git_workspace | achieved | existing GitHub remote is used | origin = https://github.com/yifanXovo/TailoredExact.git |
| 0_git_workspace | achieved | pre-existing user work is preserved | Round 35 inherited preexisting_worktree_manifest.csv |
| 1_default_c6 | achieved | clean licensed build and relevant tests pass | stage_a_build_and_tests.json |
| 1_default_c6 | achieved | default-off and explicit HH are decision-equivalent | baseline_equivalence_audit.csv |
| 1_default_c6 | achieved | new causal controls default to off/proof | include/Instance.hpp |
| 2_proof_anchor | achieved | U_proof and U_anchor are explicit and separately used | PaperExternalGiniTree.cpp; main.cpp |
| 2_proof_anchor | achieved | semantic dataflow audit excludes anchor from proof consumers | semantic_separation_audit.json |
| 3_anchor_coverage | achieved | anchor grid intersects the proof-relevant range | GiniFrontierGeometry.cpp; round36_causal_tests |
| 4_split_normalization | achieved | proof and anchor denominator sources are explicit | PaperExternalGiniTree.cpp; split_decision_ledger.csv |
| 5_startup_values | achieved | HGA and SIMPLE starts are independently verified | main.cpp; per_arm_results.csv |
| 6_causal_arms | achieved | HH/SS/BW-P/BW-A are balanced and explicit | round36_official_matrix.csv |
| 7_frozen_panel | achieved | 14-row representative panel is predeclared | frozen_causal_panel.csv |
| 7_frozen_panel | achieved | freeze identity precedes and matches official start | round36_frozen_manifest.json; official_start_record.json |
| 8_stage_a | achieved | anchor safety/equivalence/certificate tests are included | tests/round36_causal_tests.cpp; stage_a_build_and_tests.json |
| 9_stage_b | achieved | all 56 official rows are checksum-complete | runs/*/completion_marker.json |
| 9_stage_b | achieved | all official rows pass lifecycle, exactness, and certificate audits | exactness_certificate_audit.csv |
| 10_metrics | achieved | required per-arm, trajectory, split, target and closure metrics exist | derived causal CSV package |
| 11_causal_questions | achieved | Questions A-D have explicit machine-readable answers | final_audit_decision.json |
| 12_decision_gates | achieved | geometry and normalization gates are evaluated | analysis_gate_definition.md; final_audit_decision.json |
| 13_stage_c | achieved | positive mechanism receives separately frozen broader validation | Stage C frozen design, comparisons, and checksum manifest |
| 14_rho | achieved | rho remains fixed at 0.01 with no sweep | round36_frozen_manifest.json; command freeze |
| 15_K | achieved | K remains four in every official command | round36_command_freeze.json |
| 16_no_dispatch | achieved | no V/M/scenario startup dispatch is introduced | main.cpp; explicit arm matrix |
| 17_no_hga_light_mixing | achieved | HGA-LIGHT is not mixed into this causal study | main.cpp; round36_command_freeze.json |
| 17_reproducibility | achieved | frozen commands and completed rows exclude warm/resume contamination | round36_command_freeze.json; runner_row_summary.csv |
| 17_reproducibility | achieved | split and native-action control is hardware-independent and unsliced | semantic_separation_audit.json; PaperExternalGiniTree.cpp |
| 18_mathematics | achieved | three requested safety propositions are documented | theory_and_mechanism_note.md |
| 19_reporting | achieved | full compact evidence package is present | final evidence files |
| 19_reporting | achieved | repository evidence respects the file-size preflight | evidence_package_summary.json |
| 20_conclusion | achieved | one required research conclusion is recorded | final_audit_decision.json; final_report.md |
| 21_git_completion | achieved | current committed branch is pushed | HEAD=691965111cfa210fb6f91cc999d2f902632ab2d5; upstream=691965111cfa210fb6f91cc999d2f902632ab2d5 |
| 21_git_completion | achieved | draft PR 83 is open and unmerged | github_pr_record.json; GitHub connector |
| 21_git_completion | achieved | draft PR record attests the current head or its attestation parent | recorded=691965111cfa210fb6f91cc999d2f902632ab2d5; HEAD=691965111cfa210fb6f91cc999d2f902632ab2d5; HEAD^=6419643fdcfb98648e9ff5b003fba8e2f1419cbf |

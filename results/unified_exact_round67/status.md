# Recovery status

Round67 experiments, analysis and packaging are complete on
codex/round67-log-inventory-states, base7c3b189, owned checkout
E:/codes/ExactEBRP-round66. Draft PR: https://github.com/yifanXovo/TailoredExact/pull/128 .
Implementation/evidence commit: 1aa398ef31d8de22bc62049ca08f3adad0affd09. The original
user-owned Round61 checkout remains untouched. Overall goal active and unmet.

Read final_report.md and the four role screens. VD-P certifies D4 in39.891s and
C2 in132.656s, nearly matches P-GRB's D6 gap, but loses most K1's D3 protection.
LOG improves D4/C2 versus K1/P, but loses VD-P's C2 certificate and is materially
worse than P on D6. Both remain default-off; no unified adoption or confirmation.

Frozen binary build/round67/ExactEBRP.exe SHA256:
45e1ab05aff870660136102e554c8e0d3ec4cd5e1144dc651ebe9c111339a83e.
22 completed runs:16 performance+6 micro,113 experiment native calls,
5157.483s paid process wall, zero failures.44/44 final CTests passed in1.77s,
two preflight failures separately disclosed. Six build-only exports,0.376s.
Offline mapping:84 models,34 incompatible Gini ranges,50 feasible mappings,
404337 rows, zero failures.254 compact evidence artifacts packaged and hashed.
All source/binary hashes still match the measured freeze. No optimizer active.

Next: branch a new stage from this completed PR and isolate native
Start reuse of the already-paid full verified witness with VD-P. Read
provisional_integration_question.md and gurobi_start_api_review.md; existing
Round44/61 work does not already establish the proposed retained-model path.
Do not inherit LOG, ARC, prefix-construction budgets, or any time/Work switching.
Declare the new bounded plan before optimization. No3600/7200 or confirmation
phase is opened here. Preserve current evidence; do not rerun packaging after
editing solver source for a new stage.

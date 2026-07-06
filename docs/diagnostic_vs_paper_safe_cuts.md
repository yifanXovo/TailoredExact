# Diagnostic vs Paper-Safe Cuts

This project separates cut usefulness from certificate admissibility. A row can be mathematically plausible and empirically useful while still being excluded from paper-core evidence until its assumptions and merge rules are audited.

## Category A: Paper-Safe Globally Valid Cuts

These inequalities are valid for every feasible solution of the original fixed-interval compact model without untracked assumptions. They may enter `paper-gf-tailored-bc` evidence after implementation and audit checks pass.

Examples include local station-wise centering, local q-centering when the `q_i` semantics are enforced, subset cross-H centering, basic transfer cutsets, and required external-source rows when `R_D` comes from valid final-inventory lower bounds.

## Category B: Conditional Valid Inequalities

These rows are valid only when their condition is encoded in the model or fully covered by an audited split ledger.

S-bucket rows are valid inside a child bucket `S_L <= sum_i r_i <= S_U`. A parent Gini interval can be closed by S-buckets only if all buckets exactly cover the parent S-domain and every bucket is closed or fathomed by valid evidence.

Compatible-source transfer rows are valid only when the compatibility set is a superset of all feasible external pickup sources. If a compatibility filter may exclude a feasible source, the row is diagnostic only.

Conditional rows may become paper-core evidence only when the condition is enforced or fully covered, the condition is derived from valid model/domain data, every conditional region is accounted for in an audit, and every emitted row logs proof and audit status.

## Category C: Diagnostic Only

These mechanisms can guide development but cannot close paper-core leaves.

Examples include S-bucket closure without full parent S-domain coverage, Benders-like transfer-network rows without a complete projection proof, compatibility-filtered transfer rows with unproven source sets, checkpoint-only bounds without an accepted merge rule, and LP-pattern-derived cuts without a formal validity proof.

## Category D: LP-Pattern Heuristics

Rows suggested only by a specific LP solution are diagnostic until converted into a globally valid inequality family. Cutting a fractional solution is not enough for paper evidence.

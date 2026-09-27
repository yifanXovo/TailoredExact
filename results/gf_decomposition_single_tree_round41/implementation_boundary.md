# Implementation boundary

Round 41 stays in the deterministic canonical model-construction layer. `writeCanonicalCompactModel` generates one CPLEX-LP-format artifact containing all original variables and rows plus every segment selector, indicator, perspective auxiliary, selected continuous copy, and strengthening row. Gurobi reads this immutable artifact, verifies its SHA-256 fingerprint against the request, sets the frozen parameters, and calls optimize once.

The LP writer's indicator form is read as native Gurobi general constraints. No new Gurobi symbols were needed: the existing dynamic backend reads, relaxes, optimizes, queries, and frees the model. Native smoke evidence records nonzero `NumGenConstrs`, showing that the indicator objects survived model loading.

Stable auxiliary names are:

- `seg_z_k`, selector;
- `seg_G_k`, selected Gini;
- `seg_w_i_b_k` and `seg_q_i_b_k`, perspective bit activation/product;
- `seg_S_k`, `seg_P_k`, `seg_H_k`, and `seg_WSP_k`, Extended copies.

The existing decoder reads the original routing, pickup/drop, visit, inventory, and objective variables by their stable names and ignores the `seg_` auxiliaries. The independent verifier recomputes feasibility and objective in the original problem. Certification additionally checks model/hash identity, zero-gap parameter roundtrip, native finalization, exact native bound, one environment/model/optimize/free lifecycle, and objective agreement within `1e-7` relative scale.

Root relaxation uses Gurobi's relaxation model and one optimize. It records original and presolved model size, group fractionality, and McCormick ambiguity, then explicitly rejects certificate issuance. Exact execution uses `PaperTerminalMip`, disables warm starts/model retention, and requires exactly one terminal MIP optimize and zero LP or partial-MIP optimizes.

The implementation does not disaggregate route, arc, pickup, drop, or visit variables. It does not modify the model in a callback, does not set selector branch priority, and does not contain instance-, seed-, dimension-, runtime-, Work-, node-, or hardware-based dispatch.

VD-P left already-paid, physically valid outer witnesses out of its retained native MIPs. This stage adds a default-off complete Start path: equal-capacity vehicle normalization, full state-column mapping, actual bound/type/row/objective checks, value readback, native acceptance and MIPSOL observation. It preserves full HGA/AM, the exact formulation and the single whole-run deadline. Original P-GRB remains unchanged.

Matched development results with the same Gurobi13.0.2 build/settings:

- D3: VD-S certifies in84.172s; P-GRB, K1-R and VD-P remain open at300s.
- D6 at600s: gap .01140292 versus P .01225529 (6.95%, below the frozen material threshold);17.72% improvement over K1-R. Full HGA still costs about323s.
- C2: certification retained at123.640s versus VD-P132.531s; P/K1-R open at300s.
- D4:54.453s versus VD-P40.062s, a material local regression, while preserving strong protection over K1-R129.657s and open P-GRB.

45/45 CTests passed. All20 declared experiments completed:94 native calls,4735.860s paid wall, zero failures. All8 actual MIP Starts were accepted and fully observed; independent route, submitted-vector and full-coverage checks pass.278 compact evidence artifacts carry hashes; full models/binaries remain local. A shared empty-expression LP serialization defect was fixed before measurements; failed qualification attempts and costs are disclosed.

Stacked on Round67 PR128 / a47e86a57a1f68ca6e515877193cb8696d1aa13e. See results/unified_exact_round68/final_report.md, algorithm.md and reproduce.md. This is a useful research candidate, not final adoption or overall-goal completion. No independent confirmation or3600/7200 comparison yet; a limited repeat and broader validation need a separate bounded plan.

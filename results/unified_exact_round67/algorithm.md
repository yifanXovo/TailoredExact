# Round67 formal algorithm and scope

LOG uses preset `research-round67-log-vdp`. It retains canonical K1-AM's full
paid HGA and AM organization, with verified candidate retention and immediate
zero-objective termination. K1-R uses `research-round65-k1-h` with that same
reliability setting. VD-P uses `research-round67-vdp`, identical to LOG except
for one-hot binary selectors and no code variables. These are experimental
controls; a per-instance portfolio is not the proposed algorithm.

1. Begin the whole-run clock, parse the original input, and check the metric
   travel assumptions of retained route-derived domains. Unsupported matrices
   are rejected explicitly by the new presets before HGA/optimization.
2. Run canonical HGA: seed20260626, population24, decoder10, stagnation2000.
   Verify and retain original route-operation witnesses. A verified zero
   objective closes the problem against its universal zero lower bound.
3. Build the complete initial Gini interval cover, K0=1. Use inherited bound
   contraction and midpoint AM with normalized closure threshold0.08, depth
   cap8 and width floor1e-4. Unresolved domains at those logical limits go to
   complete native MIP; they are not discarded.
4. For each required LP/MIP use the unchanged node-load, order, route, time,
   objective/cutoff and F0 strengthening blocks, with the VD-P state product
   block. Replace its selector integrality with uniform natural binary offset
   codes as proved in mathematics.md. Keep original inventory integrality.
5. Gurobi performs the complete native MIP search. Mathematical proof targets
   may close an obligation; retain full coverage of every remaining interval.
   Publish original-route UB and only a frontier-supported global LB.
6. Close when every obligation meets the existing numerical certificate. At
   the single experimental deadline end the entire run, saving valid partial
   results. No local time/Work budgets, credit, restart or fallback decisions.

All ARC, VD-J, Round62/63/64 extra formulations, Round65 budgets/projection and
Round61 candidate construction are off. Native defaults, Threads1, Seed0,
PresolveAuto and zero requested gaps are unchanged. Code width follows the
proved state count and adds no tuning parameter. Metric checks and the full
HGA/probe/build/search/verification/exit costs remain in end-to-end timing.

P-GRB remains the original compact model and native default heuristics, with no
starts/cuts/HGA or imported bound. Its model fingerprint is rebuilt without
optimization and checked at launch. Every arm is rebound to the same new
binary; shared zero-handling repair is disclosed in preflight_issue_1.md.

This is a component equivalence proof plus finite numerical validation, not a
strict rational certificate or a runtime dominance theorem. The new presets'
metric scope does not qualify older strengthened methods for nonmetric input.

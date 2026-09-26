# Conditional proof question — no new variant opened

Read in this stage: Round47 final_report.md and mathematical_single_child_
contraction.md, plus Round49 final_report.md. Historical timings/Work are context,
not new strictly paired Round69 evidence. No historical output is modified.

The existing K1 AM path already splits and removes a strictly infeasible
midpoint sibling. Round47 AMC mainly made that transition an atomic one-child
replacement; its historical benefit was sparse, especially for K1. Simply
enabling that old representation is not an evidenced fix for D6's next decision.

The completed Round68 D6 VD-S decision at L0.0 has Gini range
[0,0.078541565551587075], parent/left LP bound about0.13138946503971005,
right LP bound0.15359912829456174 and verified U0.15708313110317415.
Both child LPs are feasible. The normalized weakest-child gain is essentially
zero, the average normalized closure gain is0.4322011347075424, and AM's product
score is4.6688515550507141e-16. It therefore retains the parent for exact MIP.
This is the actual unresolved decision; another infeasible-half shortcut cannot
remove the right child, whose lower bound is still below U.

If the frozen Round69 long comparison still exposes a proof deficit, a next
study can examine whether the weakest-child/product proxy rejects a useful
partition despite a large reduction in the integrated child proof gap. This is
an efficiency hypothesis, not a reason to omit either child or clip its bound.
A replacement proxy would need an explicit mathematical meaning and complete
cost/coverage comparison, including the existing small and medium protections.

Do not blindly substitute average gain for the product score or restore all
old rescues. Round49's reduced-cost-domain rescue changed24 of32 decisions and
damaged the old major root while only locally helping tight3102. Its old
mandatory action gate is not today's automatic acceptance criterion, but the
negative runtime evidence remains relevant. It does not establish that all
future problem-structured gates must fail, either.

No Round69 solver or gate has changed, and its candidate D6 long run remains
pending at the time of this analysis. Startup descent and proof-gate revision
are separate hypotheses; choose a bounded next stage after the actual long
results, rather than silently combining untested mechanisms.

Additional read-only arithmetic, with no optimization, is retained in
provisional_stock_arithmetic.json. Let B=sum(b_i), D=sum(D_i), and
g=gcd(D_i). Empty departure and capacity-limited loaded return imply
B-sum(Q_k) <= sum(Y_i) <= B, also sum(Y_i)>=0. If all integer final
inventories have the same ratio, that ratio is k/g for an integer k, so
sum(Y_i)=k*D/g. D6 has B=353, D=401, three Q=30 vehicles, and g=1:
its necessary final-stock interval [263,353] contains no such multiple.
D7 has B=677, D=769, four Q=30 vehicles, g=1, and interval [557,677],
again with no multiple. Thus exactly G=0 is physically impossible on both
original inputs, including exclusion of the all-zero inventory state.

This arithmetic does not yet give a practically useful positive G bound or
an efficient inventory-only integer oracle. It supplies neither a physical
UB nor a routing certificate. It is not a reason to prune a neighborhood
of zero without a quantified valid inequality. A new model exploiting it
would require its own proof and cost study.

The Round54 inventory-route separator design and cut validity proof were
also read for this question. That existing mechanism separates directed
capacity-boundary inequalities by deterministic maximum closure; it does not
establish a discrete common-ratio or inventory-only exact bound. Its earlier
runtime evidence remains separate from this unimplemented arithmetic idea.

Completed-stage update: VD-S improves the D6 long-window P deficit and D7
protection in the frozen comparison, with the stated timing limits. The
conditional proof-gate idea below/above was not implemented or measured;
startup remains the immediate next target. See final_report.md.

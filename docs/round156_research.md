# Round156: fixed inventory objective and paid proof refinement

The [goal](../results/unified_exact_round156/goal.md) shifts the main study
to the original inventory objective already consumed by E. The
[mathematical account](../results/unified_exact_round156/mathematical_analysis.md)
keeps beta=1 and the original penalty, preserves signed and zero handling,
and restricts an independent inventory proof domain using its own checked
inventory upper. The restriction preserves the original objective optimum;
it does not assert equal residual minima or cut the physical BRP.

The [matched oracle comparison](../results/unified_exact_round156/reports/oracle_comparison.csv)
answers the main precision question on the saved RX35 scope. RN16384 reaches
width 8.333844e-5 in 53.111 outer seconds. The unconditioned residual leaves
width .0138591314 after 316.555 seconds. Upper-conditioned aggregate products
prove one midpoint and leave width .0065614399 after 645.015 seconds. The
strengthening helps this residual model, but the unchanged RN model with a
larger allowance is substantially more efficient here. Full actual matrices,
true stocks, conservative common-cost trajectories and failed startup
attempts remain in the evidence.

The [frozen producer decision](../results/unified_exact_round156/candidate_decision.json)
selects one RN capacity of 16384 with the original price gap target and exact
DP first. It has no instance-specific branch, 4096-node restart or timed
mechanism switch. Five from-zero checks include the preselected historical
CITI K20 role, whose interval remains unresolved at the capacity. This is a
finite portability limit; no replacement example is selected.

The nine complete arms in the
[frozen matrix](../results/unified_exact_round156/confirmation_matrix.json)
compare B/E/E+ on RX35 and E/E+ on NB35, RB35 and RX20. Every arm pays its
own H and floor on the same rebuilt PE and preserves its original physical
parameters. E+ continues to use the R154 proof-only consumer. Native BRP
rows, AM, ordering and splitting are unchanged. Stable GI-TBC/B remains the
mainline and E/E+ remain research candidates.

All nine complete arms and their separate price readback have passed.
RX35 retains the common physical upper .2996694007364017; E+ raises the
supported lower from E's .22226257992032944 to .2360521029074557, reducing
the complete absolute gap by .013789522987126268. Neither hard method
certifies. The other three paired roles preserve their physical uppers and
supported lowers, with small recorded timing differences. NB35's slightly
different raw search lower is retained. See the
[complete pairs](../results/unified_exact_round156/reports/complete_pairs.csv),
[final report](../results/unified_exact_round156/final_report.md) and
[scientific review](../results/unified_exact_round156/review/final_scientific_review.md).

The [R155 errata](../results/unified_exact_round156/r155_errata.md) records the
actually executed but unresolved level experiment and re-exports all 18
checkpoints with the exact producer outer origin. One RX35-B bound at 4800
seconds changes; endpoints and costs do not. The
[paper insertion](../results/unified_exact_round156/manuscript.tex) separates
expression strength, individual prices, full inventory coupling and paid
physical-algorithm results. The
[reproduction instructions](../results/unified_exact_round156/reproducibility.md)
explain fixed-commit/member references, exact incremental matrices and
source/PE/runtime identity. See
[RESUME](../results/unified_exact_round156/RESUME.md) for the actual state.

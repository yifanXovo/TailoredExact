# D3 repeat and historical small validation

All ten planned short launches completed with the identical frozen VD-S
executable. Total197.830s,33 experiment Optimize calls, zero process or audit
failures. Six no-opt reference exports took0.641s separately. Qualification
is the inherited Round68 45-test result; no new CTest batch is claimed.

| Role | P-GRB full wall | K1-R full wall | VD-S full wall | VD-S HGA |
|---|---:|---:|---:|---:|
| E7,120 cap |1.313|5.657|5.657|4.3667|
| S12,120 cap |5.156|40.938|39.672|38.3825|
| N12,120 cap |3.906|7.203|3.641|1.7484|

All nine are certified at the original numerical standard, at the same
per-role objective. N12 P's signed UB-minus-LB is about-1.1e-16; this is
preserved as a numerical-tolerance discrepancy, never silently clipped.
Paired K1-R and VD-S start with exactly the same independently checked routes.

E7 remains a material P regression (+4.344s) and matches K1-R. Its post-HGA
wall is about1.290s versus P1.313s; this subtraction is attribution only.
S12 remains a severe P regression (+34.516s), with post-HGA wall about1.290s.
The Start representation alone cannot remove its38.382s HGA startup. VD-S's
1.266s gain versus K1-R is below the frozen practical threshold.
N12 is materially faster than K1-R by3.562s, while its0.265s P difference is
below the practical threshold. Post-HGA wall falls from about5.462s to1.893s;
the former non-startup small-role deficit is repaired on this one validation.
No claim of statistical equivalence or general small-instance superiority.

D3's single fresh VD-S repeat certifies in84.687s, versus84.172s in Round68,
at UB0.04500155005562836 and LB0.04500155005562828. Same initial route identity
and final objective; the0.515s variation does not erase the original large
certificate gain. This is a repeat of design data, not independent confirmation.
No new D3 control runs were opened merely to recreate prior measurements.

Independent physical, actual bound/type/row/objective and complete-frontier
checks passed. All five actual Start decisions are eligible, accepted in native
logs, and observed as full submitted vectors in MIPSOL. Six control runs have
no explicit new Start. The21 initial-witness model checks include seven
incompatible Gini intervals and zero unexpected failures.

Event logs show S12 first attained its eventual objective at generation153,
about2.835s into HGA; E7 at generation27,about0.116s. These are observations,
not stopping rules, and objective equality does not prove an identical retained
route at that earlier event. A separate subsequent full-content SHA and
generation-completion audit links all seven retained HGA routes to their
historical verified events; see hga_witness_provenance.json. No native final
witness is backdated, and no retrospectively selected prefix or time limit
is introduced. A future startup candidate needs a separately declared,
uniform algorithmic rule and new development/validation separation.

D6 and D7 long comparisons remain pending. These short results neither prove
nor refute their long-window performance. Overall goal remains unmet.

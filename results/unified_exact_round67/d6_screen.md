# D6: current P-GRB proof deficit and inventory representation

All four600-second whole runs completed without failure; raw artifacts,
independent route verification, native parameters and original-range/tree
coverage passed. Same paid initial routes across K1-R/VD-P/LOG. No confirmation
or long-run extension is opened by this intermediate report.

| Arm | Process wall | UB | LB | Signed absolute gap |
|---|---:|---:|---:|---:|
| P-GRB |597.828|0.1572411758522922|0.14498588325431813|0.01225529259797406|
| K1-R |597.078|0.15708313110317415|0.14334096616313421|0.01374216494003994|
| VD-P |597.078|0.15708313110317415|0.14482251277766844|0.01226061832550571|
| LOG |597.078|0.15708313110317415|0.13956388051994786|0.01751925058322629|

None certifies. K1-R's gap is12.13%/.00148687 worse than P-GRB. VD-P removes
most of this short-window loss: its gap is .00000533 larger than P, below the
frozen practical threshold. VD-P has slightly better UB and slightly worse LB
than P, so this is a mixed bound tradeoff, not a stronger-LB claim or statistical
equivalence. Its improvement versus K1-R meets the frozen material criterion.
LOG's gap is42.95%/.00526396 larger than P and materially worse than K1-R/VD-P.
It has not repaired the primary role. No per-point K1 veto is being applied.

The5 LP calls cost only about1.49/1.84/2.24 native seconds for K1-R/VD-P/LOG.
Their HGA costs are319.448/319.744/322.855s. All exclude the infeasible upper
half and retain the lower parent. K1-R additionally runs a0.710s mathematical
child-bound target MIP; VD-P and LOG directly enter terminal MIP. Terminal
times are273.095/273.133/269.613s, with3140/1033/1455 nodes. Removing that tiny
target call cannot account for the VD-P-versus-LOG proof difference.

Root model rows/columns: K1-R29923/6991, VD-P30485/8273, LOG30641/8429. The
logged initial LP values are0.1256918309,0.1313894650,0.1313894650. The common
VD-P/LOG LP projection did not produce common native cut/search behavior.
LOG adds156 code rows/columns. Native node/Work statistics are attribution,
never switching rules. Full trajectories are retained for further inspection.

After this queue, an offline encoding-aware mapping checked all compatible
initial witnesses against the actual generated models across micros/D4/D6.
Of60 model checks,25 have incompatible Gini ranges and35 pass all bounds,
integer types,301793 total linear rows and objective reconstruction. Maximum
row violation is about6e-15. Zero optimizer calls,2.969s offline audit. Mapping
removes empty routes and reorders only equal-capacity vehicles by served count,
then re-verifies the same physical objective. Original witness bytes remain
unchanged. This finite evidence does not replace the equivalence proof, but
confirms that the retained D6 witness has a legal native encoding; lack of an
observed native incumbent is not evidence that the witness is unavailable in
the model. No native start was submitted by this audit.

Continue the declared D3/C2 panel before candidate selection. In particular,
VD-P's near-P600 result does not establish correction of the historical3600
proof deficit. LOG's D4 improvement does not cancel its D6 loss.

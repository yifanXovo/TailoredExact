# E finite pre-execution scope: coverage and evidence-capture increment

Decision: ACCEPT_FINITE_EXECUTION_SCOPE, with execution/results still pending. This is the same independent internal reviewer. No enumeration, H, LP/MIP, compilation, model export, carrier traversal or solver loading was performed by this review.

Final reviewed E plan SHA256: `d8de4cba395f475c83b8f22e8fc0abd31c887ffe0fdb6c289ce0af626adad7dd`.

Final reviewed E runner SHA256: `8d0d723a32a8f11dcd240778e44d6f172c44f02fe5c65e05c706d13b9ceafdf6`.

The original four micro cases all had total initial inventory4, equal to total target4, and a direct target-restoring route within the fixed time budgets. Thus their original objective comparison risked being dominated by an analytically attainable zero. Before any owned E enumeration, H, native LP or support result was exposed, J2/J3 were corrected once to initial inventory`[2,1,0,0]`, capacities`[1,2]`, and time240/360 respectively. J1 remains the balanced control and J4 the startup-zero control. Total inventory3 is below target4, so these two cases now represent unavoidable shortage with positive penalty. They do not inherit a positive optimum claim from a balanced-case observation.

The resource domains differ analytically. At240seconds each vehicle may pick up at most2units; at360seconds the Q2 vehicle can serve pickup2 at station1, drop2 at station3, pickup1 at station2, drop1 at station4, with prefix loads`2,0,1,0` and cumulative pickup3. This demonstrates a domain distinction without enumerating or inspecting a performance result.

`engineering/E_shortage_coverage_amendment/` retains the previous plan and runner bytes, their hashes, the before/after declarations, and the failed intermediate plan serialization. The before record explicitly limits its absence claim to owned E outputs/fees and records that D/C results were not used for case selection. The corrected plan preserves every prior non-UTC/non-case field, including`zero_cutoff`,`proof_binding`,`control_policy`. The final runner differs from the retained pre-correction runner only in the two inventories and making those already-existing textual contracts reproducible by`freeze()`. No formal D/C binding changed. Four cases,64directions per case,8event controls, all caps and the reference definition are unchanged.

The evidence-capture increment adds the actual exact binary64 joint-matrix snapshot and saved original-objective primal/RC/row-Pi/quality receipts for the same existing two objective LP returns. It adds no Optimize. Missing native quality is null. A pure reader can check primal/dual numerical consistency and the complete joint-column extension using those snapshots. These checks do not convert a floating LP optimum into strict rational optimality. A strict support witness still requires exact feasibility of a rational point in every row/bound of the full reference plus the exact support maximum over the complete joint universe.

The idle/frozen-asset identity capture before enumeration, contradiction guards for INFEASIBLE/event-rank/objective monotonicity, incremental sealing, and bounded rational recovery remain in force. Finite unseparated normals or a zero original-objective increment do not establish hull equality. Exact tiny threshold ranks are not the historical R101 necessary-resource ranks. No real-role E2–4 extension is admitted until a full-universe upper-bound interface includes all outside supply and receiver stations.

The portable checker's small-plan preflight accepted this final binding in`review/portable_preflight.json`, without importing an evidence reader or reading raw. Final raw and mathematical evidence checks remain gated on the complete84arm closeout and closed experiment sequence.

# Mechanism lineage and interpretation

Only post-Round55 incumbent-epoch correction is eligible as a current runtime
baseline. Earlier paired numbers below identify what was tested; none are
pooled into Round59 performance. `historical_pr_index.json` records the actual
PR base/head relationships, including duplicate branch-to-main review PRs.

| Rounds / research PRs | Mechanism and corrected interpretation |
|---|---|
| 34–36 / #81 #82 #83 | HGA versus the old three-candidate greedy SIMPLE altered both cutoff and geometry. Round36 found pre-split divergences and zero-split divergences, so effects cannot all be assigned to split scoring. Its final geometry conclusion supersedes a simple startup-only interpretation. Round59 empty routes are a different startup definition. |
| 40 / #87 | Actual Gurobi Presolve was Auto despite the legacy global-tree label. Fragmentation hurt the major witness, but the strongest control needed narrow intervals. The CPLEX control does not restrict Gurobi. |
| 41–42 / #88 #89 | Static segmented single-tree formulations were feasible and exact under strict verification, but failed protected controls. Fewer native jobs did not imply lower root or integer-search cost. Round59 Single-S is one full interval, not the old multi-segment one-tree model. |
| 43–45 / #91 #93 #95 | Envelope refinement, tail repair and parametric split experiments did not establish a uniform replacement. These explain controller lineage; no threshold, timing rule or cut point from them is searched here. |
| 46–49 / #97 #99 #101 #102 | Pure rho failed to replace gamma information; adaptive-mass selected K1/K4 candidates. Formulation- and reduced-cost-based split rescue remained bounded negative. Current first-class K1 uses midpoint, balanced normalized closure and tau=.08, not inert historical K4 fields. |
| 50–51 / #104 #106 | B1/B2/B3 were whole-family priorities, A1/A1R sparse probing. Improved coefficients, removed duplicate rows and symmetry all changed search and sometimes lost strict verification/certificates. Native optimal status alone was insufficient. |
| 52 / #108 | Dynamic support-duration generated 1,705,140 candidates but only four violated observations. Static congestion was avoided but runtime qualification failed. These are root-dominated experiments, not evidence that no nonroot violation exists. |
| 53 / #110 | C0-C5 separated PreCrush, callback entry, dry-run enumeration and real submission. The conclusion was mixed callback regression. F0 removed only the exhaustive subset-duration block, preserving the original integer feasible set and passing that round's integration. |
| 54 / #112 | Exact inventory-route separation improved many roots but lost certificates on D1/D13. The untested one-pass alternative cannot be ruled out by full-closure results. P-GRB fingerprint correction raised qualified certificates from 0/12 to 9/12 without changing solver trajectories. |
| 55 / #113 | Epoch-key bug fixed; pre-fix performance is not comparable. MC4 and VD-J strengthened many roots but failed protected states. VD-P passed fixed-interval gates and gained certificates in full K1, but severely regressed major. Penalty-cover live tests never opened, so they are untested, not a negative empirical result. |
| 58 / #117 #118 | Corrected stable K1 had lower Work on many pairs but was slower on 24 of 31 jointly certified instances. Wall time and Work must be separated; the representative study does not reopen the 50-instance panel or the 910 reserves. |

Primary local sources are each round's `final_report.md`, Round55
`mathematical_model_audit.md`, `k1_split_action_diff.csv`, fixed-interval and
integration paired ledgers; Round53 `callback_isolation_pairwise_effects.csv`;
Round58 `common_horizon_comparisons.csv` and `official_final_results.csv`.

## Objective and feasibility boundary

`Evaluator.cpp` independently reconstructs Y=b+sum(d-p), computes r=Y/D,
S=sum(r), H=sum absolute pair differences and F=H/(nS)+lambda*sum(w*|r-1|).
The existing S=0 convention sets G=0; it is unchanged. Station targets must
be positive as required by the parser. Station inventory capacities, single
service, nonzero unidirectional operations, route load and duration are
checked. `min_ratio` is explicitly a parsed compatibility field in Instance;
this round does not reinterpret it as a new service constraint.

The verifier computes operation cost as c_pick*pick+c_drop*station_drop+
c_drop*depot_unload. Since depot_unload=pick-station_drop for empty starts,
this equals (c_pick+c_drop)*pick, including loaded returns exactly once.
No station-total conservation or empty-return restriction is added.

The original compact G*Y representation, F0 strengthening, strict improving
cutoff and diagnostic restricted model are kept distinct. All added Round59
pool rows are global consequences of actual routing and operation constraints;
they require neither an imported incumbent nor a subtree assumption. Necessary
Gini/product/feasibility rows never enter the optional pool.

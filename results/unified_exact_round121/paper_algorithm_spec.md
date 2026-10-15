# Round121 frozen native proof disjunction

Production identity remains R120 source355eefd2be3fe5651195681faf7b3a63ee4032f8 / PE5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba. The full inherited method and D1 contract follow verbatim below. R121 evaluates three predeclared new inputs from the same safe city source and two known Seed1 blocks; it defines no new algorithm. ENS-C remains default. This is prospective setup; performance and stage are pending.

# Round120 candidate extension on the frozen integrated method

Current performance source 355eefd2be3fe5651195681faf7b3a63ee4032f8, PE SHA 5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba, Gurobi13.0.2 DLL 9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88. All current arms use this same build. ENS-C remains default; MB-PC remains stopped. The inherited method specification below is retained as its historical definition; its old source/PE paragraph does not identify a current arm.

# Frozen integrated redistribution algorithm: a paper specification

This specification describes production source `d0014a7163e3996fe120471420e56b089c9715ae`, PE SHA256 `a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8`, and Gurobi 13.0.2 DLL SHA256 `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`. ENS-C is the default; M-B is the finite R111 research candidate; cold P-GRB is the primary benchmark; P-S is the independently paid contribution control. The same method definition applies throughout routine V≤50. No method dispatch depends on V, stock regime, elapsed seconds, stagnation or observed role results.

## Original problem and physical objective

Service stations are indexed 1..V; depot 0 is excluded from every stock, ratio and weight sum. Station i has integer capacity C_i, initial stock b_i and positive integer target D_i≤C_i. Vehicles k have capacities Q_k and the same physical horizon T. They leave empty. A station can be visited by at most one vehicle, once, for one nonzero one-way integer pickup p_ki or drop d_ki. Unvisited quantities are zero. Final inventory and ratios are

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\quad 0\le Y_i\le C_i,\qquad r_i=Y_i/D_i.
\]

Every load prefix, including return, is in [0,Q_k]. Loaded return is allowed and unloading at the depot is paid. Therefore a complete route has duration travel+t_pick*total_pickup+t_drop*(station_drops+return_load), equivalently travel+(t_pick+t_drop)*total_pickup. Q limits simultaneous load, not cumulative pickups. `min_ratio` is a compatibility field and supplies no lower inventory constraint. Distances are the original C++ Parser's Euclidean metric/1.5 from serialized station/depot points.

Write S=Σr_i and H_ratio=Σ_{i<j}|r_i-r_j|. The physical objective is

\[
G_{\mathrm{true}}=H_{\mathrm{ratio}}/(VS)\ (S>0),\qquad
F=G_{\mathrm{true}}+\lambda\sum_i\omega_i|r_i-1|.
\]

The original evaluator sets G_true=0 when S=0 and retains the penalty. This is Gini of inventory-to-target ratios plus two-sided relative target deviation. It is not just unmet stock and not a measured rental/return failure objective. Station totals need not be conserved: ΣY_i+Σreturn_load_k=Σb_i. The current input has B=239, Dsum=279 and strict shortage40; `positive_objective_proof.md` proves its optimum is positive while the no-service empty fleet remains feasible. Its arithmetic bounds are explanatory only.

The native model's `G` is an epigraph variable. It is not assumed equal to a decoded fleet's G_true in every relaxation or every local solution. Every accepted Start/callback/final candidate is reconstructed as a complete original physical fleet and evaluated with the original objective. A solver objective, scalar inventory vector, partial fleet or epigraph value cannot substitute for that replay.

## One complete ENS-C/M-B procedure

```text
Input: original instance and physical parameters; one absolute process deadline.
Parse and check the instance and the original symmetric-metric assumptions.
Keep only independently verified complete physical fleets in the own UB store.

H := joint insertion construction;
initialize the original 24 orders with Seed20260626;
append the constructive vehicle/order assignment as seed25;
fully decode and perform guided strict descent for every seed;
retain the best verified fleet, including construction;
alternate strict insertion/quantity/R76 closure with the union of
  R78 balanced relocation and R83 equal-net served-block exchange;
adopt a union move only under the original sorted-duration improvement rule;
stop H when that finite closure ends or the absolute work deadline is reached.
Apply the original outer objective-improvement handoff to the retained fleet.

If the original verified-zero predicate closes against F≥0, serialize and end.
Otherwise establish every relevant true-G interval obligation under the own U.
For each selected controlling obligation:
  build the original scoped VD-P/F0 model and the applicable inventory domains;
  obtain only paid, returned LP/MIP evidence bound to this model/domain/cutoff;
  apply the original AM child-bound/frontier test;
  keep the parent, run it toward a mathematical target, or atomically replace
    it by both midpoint children with complete parent/child coverage;
  before a needed MIP, clear prior explicit Starts and map one eligible own
    verified fleet to all actual columns; check and submit/read back the vector;
  accept a new U only after original physical/objective verification;
  update bounds and closure only on scopes actually proved and still applicable;
  requeue every unresolved obligation instead of dropping it.
At the single deadline, stop native work, close all mandatory original output,
  supervise normal cleanup and seal the producer.
Return an original-domain numerical certificate only if the full cover closes.
After the seal, independently verify the recorded evidence; revoke damaged
  claims/dependencies without producing a new fleet or invoking a solver.
```

H outputs a complete physical fleet, original F/Y/vehicle assignment, and its actual construction/descent/closure/exchange traces. The decoder is `nGreedyLU_RA_compact_full`, compaction mode1; its legacy `max_iter=10` field is ignored by that function and is not an operative ten-pass algorithm. The original bounded decoded-order cache and deterministic tie rules are retained. Neutral moves decrease the complete sorted duration tuple; finite integer services and route orders give finite closure absent the deadline. This is neighborhood closure, not original-problem optimality. The outer witness store still requires objective improvement >1e-10, so a neutral-only H change need not become the actual native Start.

The controller outputs a complete obligation ledger, atomic split/coverage transitions, scoped bounds and own primal records. The final verification outputs qualification or a precise unresolved/rejected dependency, not improved optimization results. H, failed probes, model/Start work, callbacks and all native calls consume the same deadline. No seconds/Work quota switches an internal mechanism.

## Representation and quantity integrality

For an already valid integer inventory domain, VD-P uses binary s_iy, Σ_y s_iy=1, Y_i=Σ_y y s_iy; γ_L s_iy≤q_iy≤γ_U s_iy, Σ_y q_iy=G, and Z_i=Σ_y y q_iy. At the selected y=Y_i, q_iy=G and Z_i=G*Y_i. Conversely an original permitted integer inventory/product point has that extension. This is exactness of the inventory-product block conditional on valid domain/interval construction, not an integer-hull theorem for the full route-coupled LP.

| Actual column family | ENS-C | M-B | Cold P/P-S |
|---|---|---|---|
| Final inventory Y and prefix/return load | Integer | Integer | Original compact types |
| Inventory state s, service z and direction m | Binary | Binary | Original compact types/auxiliaries |
| Pickup/delivery p,d | Integer declarations | **Continuous declarations** | Original integer declarations |
| Existing A/B linking rows | Absent | Present, two per service station | Absent |
| Independent ENS-Q switch | false | false | false |

M-B's p/d integrality follows from unique service, one binary direction and integer b/Y. If no vehicle serves i, all quantities vanish. For the unique serving vehicle, pickup direction gives d=0 and p=b−Y; drop direction gives p=0 and d=Y−b. Both are integers. The nonzero-service row excludes a visit when Y=b. This implication needs neither A/B nor integer load as an additional premise; it does not extend to split service, simultaneous pickup/drop, fractional direction/assignment, fractional initial stock or fractional Y.

Existing A states Σ_k(p_ki+d_ki)=Σ_y|b_i−y|s_iy. Existing B states Σ_k z_ki=1−s_i,b_i, with the original omitted-state convention when b_i is outside the proven domain. They follow from the same original integer feasible solutions and are valid strengthening. They are not necessary to the implicit-integrality proof and do not guarantee a strictly better LP bound or a faster search. Actual p/d declarations must be checked from saved model/native type evidence; ENS-Q=false alone does not establish their types. Finite native decoding retains the original integer tolerance and full physical replay.

The frozen F0 families, original propagation rules and AM are retained. The static support families use size≤3 and at most50000 generated subsets. These bound strengthening generation and do not remove a necessary original feasibility or proof obligation. No exhaustive extra subset search, dynamic new cut or custom branch rule is introduced.

## Scope, coverage, cutoff and termination correctness

An obligation concerns physical true G in [γ_L,γ_U], the complete original problem, and an explicit non-strict objective cutoff. Its model identity is the complete immutable canonical SHA, not a leaf name, logfile name or objective value. Inventory-domain tightening must preserve every improving original physical point in that obligation. A physical point in its true-G interval has the original objective-preserving model embedding; every candidate used as U is separately replayed. A high epigraph G for a decoded point outside the physical interval does not establish a same-domain counterexample.

With nonnegative penalty, F≥G_true and F≥0. Once an own verified U exists, the improving domain can be restricted to G_true≤min((V−1)/V,U) and F≤U. The cutoff complement cannot improve U; it remains an explicit analytic obligation when forming a global bound. A local OPTIMAL/INFEASIBLE return closes only its actual model/domain/cutoff. Bound transfer requires a proved containing domain and an applicable cutoff; a tighter new model cannot retroactively prove a larger old domain.

Atomic midpoint children cover the complete parent interval. Empty children require qualified proofs. All live regions and the cutoff complement remain represented. The global lower bound uses the minimum of justified regional bounds over a complete cover, with the applicable complement; sibling bounds are never combined by taking their maximum. Repeated leaf labels across cutoff/cache epochs do not establish identity. The cache keys include complete canonical content and the original epoch; LP relaxation must restore the captured original native VType array before integer MIP.

For parent bound B_p, own U and valid complete child LP bounds b0,b1, AM uses gap=max(U−B_p,max(certificate_tolerance,1e−12)), g_j=clip((b_j−B_p)/gap,0,1), η=min(g0,g1), μ=(g0+g1)/2 and score ημ. Its threshold is0.08 with the original numerical comparison. Child infeasibility invokes the existing two-child handling. No strict child-disjunction gain leads to exact parent closure; sufficient score commits the split; a smaller positive gain runs the parent toward min(b0,b1) and requeues it. Frontier targets are justified bounds of other relevant obligations. K0=1, midpoint, depth8 and width1e−4 are uniform. Legacy telemetry fields are not additional active policies.

An unresolved region at a logical limit is sent to complete MIP, retained open at deadline, or closed by an actually qualified proof. Certification requires own physical U, qualified returned calls, valid original-domain cover, lifecycle completion and the unchanged 1e−7 numerical closure policy. These are floating-point numerical certificates, not rational exact optimality proofs. A single good-looking gap, hash match or local status is insufficient.

## P-S and native Starts

P-S independently pays the same full ENS H. Its original cold canonical compact has the identical numeric rows, columns, VTypes, bounds and objective, with strengthened=false. The mapper fills all actual columns, including unvisited/empty vehicles and auxiliaries, normalizes vehicle labels only within equal-Q classes, checks every row/bound/type/objective and submits one complete Start with full API readback. Before/after native matrices must be identical. Equal U does not establish equal Y, capacity-assigned fleets, accepted H actions or full25-seed semantics.

If H closes under the inherited verified-zero rule, no backend is exposed. Otherwise, with remaining original work time, P-S runs one complete original compact MIP. A mapped/submitted Start with no remaining window is an explicit `not_started`, not a returned Optimize. A declaration lacking actual start/disposition remains unresolved. Cold P uses its original cold entry without H, external U, Start or hint. ENS/M-B map paid own Starts only when their current physical scope/cutoff admits the fleet; a Start does not create a lower bound.

## Numerical evidence, cost and contribution boundaries

All methods use Seed0, Threads=mip_threads=1, PresolveAuto, requested MIPGap=MIPGapAbs=0, original affinity and tolerances (FeasibilityTol/OptimalityTol1e−6, IntFeasTol1e−5), plus the original1e−7 physical/consistency policy. Each arm's H, U, bound, Start and cache are independent. The current producer clock includes all online work, native cleanup, supervision, serialization and sealing. Serial post-seal T_verify is disclosed separately; T_total uses the same origin. Native API Runtime is only a component timer. No component subtraction manufactures a new method result or an unknown final certification time.

Round118's read-only call view pairs every actual Optimize segment with its serial call, immutable model SHA, leaf/true-G interval/cutoff, complete ledger and return, and records raw-file and byte-span hashes. Parameters, model size, available fingerprint/type evidence and terminal values are checked per call on healthy and rejected paths. Numeric epoch IDs absent from raw are not invented; scope/cutoff/model identity and recorded serial history remain explicit. Unresolved identity/model/return/log mapping does not pass via floor0. A same-domain contradiction revokes that call and dependent closure; a valid own fleet/floor may remain source-reduced open, with no native nonzero proof credit. These repairs concern evidence correctness, not algorithm speed.

Fingerprint comparison must use the same attribute state. The frozen P-S API reference fingerprint is read before Start submission, whereas the Optimize log includes the submitted Start attributes; those fingerprints may differ even with unchanged mathematical rows/columns. P-S instead requires complete native before/after matrix equality and all-column Start validation/readback, alongside the canonical SHA and the pre-Start reference check. The log fingerprint is retained at its actual later state; an unpersisted post-Start API fingerprint is not invented. Cold no-Start fingerprints retain their same-state equality check. [Gurobi's official fingerprint explanation](https://support.gurobi.com/hc/en-us/articles/41809886403217-Why-is-my-model-fingerprint-different) explicitly includes MIP Starts among attributes that can change it.

The paper can discuss the integrated original formulation, selected exact inventory representation, physical H composition and verified scoped native integration as the project's defined method, assessed by finite results. General multistart, relocation, disjunction, MIP Start, implicit integrality and the shortage inequality are existing mathematical/technical ideas, not new general theory. Specific F0/A/B activity, AM causality or representation/search interaction needs evidence beyond a one-role table.

The proof/definition authorities are indexed in `historical_authority_refs.json`: R83 `unified_method.md`, R100 `mathematical_algorithm.md`, R112 `mathematical_algorithm.md`, and the R117 scoped evidence/cost statements. Historical source/PE versions in those documents remain their original identities; this specification pins the current common production identity above.

## Explicit candidate, not an adopted default

MB-D1 adds one binary root selector and three ordinary linear rows before the first integer Optimize, using only this run's two complete optimal root-child LP returns. Root beta_j=min(ell_j,c_j) is reduced by the inherited1e-7 margin and guarded under actual coefficient serialization; scopes, actual objective constant and every all-column Start are checked. MB-D0 retains the same two links and common floor, removing only conditionality. This adds neither descendant selectors nor proof-triggered interrupts/probes/contractions. Original AM, target/terminal and necessary epoch lifecycles persist; entire search-tree retention is not claimed. Full mathematical/physical/native qualification and current full-method pairs govern one finite stage exit. Standard disjunction/convexification is not presented as new general theory.

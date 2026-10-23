# Round132 E: finite pre-execution internal review

Scope: light reading of `round132_joint.py`, its frozen plan, the relevant original canonical exporter/factory conditions, and the R54 cut implementation. The reviewer did not call the enumerator, construct a native model, start Optimize, compile, or derive any observed separation/result. This is an internal static review, not external reproduction.

Disposition after local repairs: the planned complete four-station/two-vehicle comparison has a sound set definition and support-upper-bound construction. No remaining mathematical obstacle was identified to executing this finite plan. Actual enumeration completeness, native statuses, rational witnesses and objective results remain to be checked after execution. No new direction, instance or large separator is requested by this review.

## Sets and validity

For the declared full four-station universe, service at a station is either absent or one nonzero integral pickup/drop within its original inventory/room and the vehicle's single-operation capacity. Final return is constrained to [0,Q]. Handling is 120 times cumulative pickup, including the return unload, and prefix feasibility is tested over service orders. Cumulative pickup is not incorrectly capped by Q. For example a Q=1 route can alternate two one-unit pickups with two deliveries at handling cost 240 while never exceeding load 1.

Every physical route in this co-located universe induces one of the enumerator's service vectors and one of its tested permutations. Conversely a retained vector's stored order supplies a feasible route: all travel is zero, prefixes satisfy capacity, inventory changes obey bounds, and handling meets T. Thus the construction can cover the full single-vehicle service-vector projection of this stated universe, rather than a restricted route-column pool. It retains the first feasible order for each service vector; it does not output every feasible route permutation. That distinction should be kept in the note.

The Cartesian product filtered by disjoint positive service contains every admissible two-vehicle service pair. Both the separated and joint formulations use these same R_k sets. The exact integer support maximum over all such pairs is a valid upper bound for every full tiny fleet. It is not a maximum over a restricted column sample. The empty pair is included.

These coverage statements are analytic source checks. For these data, each station has at most three operation choices, so each car has at most 3^4=81 raw service vectors and the two-car product has at most 6561 raw pairs before filtering. These are elementary upper bounds, not observed enumeration counts.

## Complete reference and comparison coordinates

The reference starts with the current S2 canonical root, changing only variable types to continuous, and retains its routing, inventory, Gini/state-product, cutoff/domain and resource rows. Per-car convex combinations link the actual p,d,z columns to complete R_k mixtures. R98-style theta variables link each eligible noninitial state to vehicle ownership and quantities. Because every physical fleet selects its own car plans and corresponding theta states, these rows admit the required physical extension in their actual canonical domain.

The rank construction includes every nonempty station-distinct selection of one threshold event per station. With two possible signed thresholds per station, there are at most 3^4-1=80 such combinations. Their RHS is the exact maximum over complete joint pairs. This is an additional tiny-domain exact rank reference. It may be stronger than historical R101 ranks derived from necessary resources. The study must not identify the two domains without a separate containment proof or advertise a first introduction of multi-vehicle coupling.

For each of the 15 nonempty station subsets, the reference adds mixed IR-IN and IR-OUT with depot in the complement: net inventory gain is bounded by Q-weighted incoming arcs, and net loss by outgoing arcs. The signs match the original R54 mixed cut families. This gives 30 mixed rows; it is not a claim to instantiate every optional projected R54 variant.

The tested common projection is the 24-dimensional vector (p,d,z) for both vehicles and all four stations. Maximizing a support direction on the full reference allows every routing, state, H, product, theta and mixture auxiliary to readjust. A strict reference extension outside the exact joint support bound therefore establishes a projected difference, rather than merely failure of a fixed auxiliary assignment.

## Required evidence hierarchy

The 64 integer support directions and the eight event controls are fixed before observing outcomes. An exact integer joint RHS follows only after the complete enumeration is actually sealed and verified. A numerical reference optimum above it is a candidate. It becomes a strict projected witness only when the recovered rational extension passes every actual retained row and column bound and its exact integer-weighted p,d,z support is strictly above the RHS.

The repaired code retains separate best-numerical and best-strict records, so failure to rationalize the largest numerical gap does not suppress later already-fixed directions before a strict witness is obtained. A recovered exact extension with nonpositive exact gap is not a strict witness. The actual binary64 B_ref row/bound snapshot and complete enumeration SHA are bound into each proof. This permits independent rational checking of the values without relying on assumptions about the readable LP writer's precision.

The active-basis procedure is a bounded witness-recovery attempt, not a complete rational feasibility algorithm. Near-bound variables may be fixed to the exact bound, and active rows are chosen numerically; rejection, rank deficiency, more than 90 free columns or the 45-second exit must remain an explicit obstacle. Success is protected by the subsequent complete rational row/bound checks. Failure does not establish that an extension or strict separator is impossible.

Reference versus full-joint original-objective optima are a separate numerical experiment. The joint columns impose the complete enumerated joint p,d,z hull, beyond merely adding the best queried inequality. Adding them cannot lower the exact minimization optimum. A signed drop beyond 1e-7 is now treated as a contradiction to investigate. Positive, zero or small signed numerical differences must retain their actual status and tolerance; they are not automatically rational objective certificates.

No separating direction among this finite collection does not prove equality of the full projected polytopes. A zero target-objective increment does not disprove other structural differences. A strict tiny witness also does not validate deleting outside donors or receivers from a real role.

## Degeneracies, repair and execution limits

J4 begins at its synthetic target, so its empty fleet has U=beta=0. Frozen production S2 would terminate on its qualified startup-zero branch. The canonical factory requires a positive verified incumbent to emit its cutoff/SP block, so actual cutoff and W presence must be recorded instead of assumed. The repaired `canonical_scope.json` does that and labels the artificial J4 root as non-production backend exposure. It must not supply backend-performance attribution.

The first reviewed version had three local execution/reporting risks, now corrected in the reviewed source: event controls had no contradiction policy; a failed largest-gap rational attempt could mask a smaller strict candidate; and budget/basis exits could discard the current in-memory observations. The repaired version records PASS/UNKNOWN/CONTRADICTION controls, separates the two best-candidate classes, seals stages/queries/cases incrementally, checks the rational deadline through back substitution and full validation, and reports PARTIAL_BUDGET on the finite time guard. Rank or objective monotonicity contradictions are preserved and stop the affected work.

The source's 10000-second pre-query guard leaves a portion of the 10800-second E allowance for the final original/joint objective calls and output. It is not a promise that every planned query finishes for every solver behavior. Any missing mandatory planned positions remain partial, not an equivalence or scientific negative result. A single exact-arithmetic operation is not preempted by the loop deadline; actual costs still belong to E and need the outer receipt. All LPs, enumeration, rank maxima, rational work and output inside this E process remain G1 E costs, rather than static-review costs.

At run start the actual original exporter/DLL/source identity and the plan/runner bytes should be captured, then referred to by the case records. Recording only their hashes at the end would not by itself show which bytes began the run. The reviewer requested that lightweight identity closure; it requires no additional solver or enumeration. A native infeasible reference would also need investigation against the known empty-fleet embedding, rather than being scientifically grouped with an ordinary time-limit UNKNOWN.

The real-role gate remains closed unless a support upper bound covers the complete original station universe and the same full R_k, including all outside sources/sinks. The current tiny plan supplies no such interface and explicitly declines E2-E4. That is a legitimate conditional non-entry when this finite step completes, independent of the sign of its findings.

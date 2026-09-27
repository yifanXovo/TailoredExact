# JI: joint position and integer-quantity construction, then complete VD-S proof

Research preset: research-round73-vds-joint-insertion. This version is default
off and has no performance claim until the declared experiments are audited.
It inherits the R68 verified full-Start/one-hot VD-P representation and AM
proof organization with tau0.08, midpoint splits, one initial interval, depth8
and minimum width1e-4. R65 resource budgets/projection, ARC and later resource
cut experiments remain off. P-GRB receives none of this startup information.

```
R := empty route set; independently verify R and original F
while the whole-run deadline has not been reached:
    enumerate unvisited pickup/drop pairs and single pickup or drop stations
    for each motif and vehicle, enumerate every ordered insertion placement
    compute its legal maximum positive integer quantity from stock, station
        capacity, every affected load prefix, and original route duration
    for each quantity, retain a feasible placement of minimum added travel
    score its original F improvement per added physical route duration
        (nonpositive duration additions form a separate priority class)
    if exhaustive enumeration finds no gain > 1e-12: stop construction
    materialize the best motif; independently verify all routes and F
    accept only an actual original-objective improvement; record the step
pass the paid physical witness to unchanged complete VD-S/AM exact proof
```

There is one deterministic construction, no random restarts or seed search.
Each accepted motif adds at least one previously unvisited station, so at most
V steps can be accepted. The legacy round34 startup container remains named
hga-full for shared controller plumbing; actual primal_heuristic is
joint-insertion, stop is motif-exhaustion, runs1 and HGA generations0. The
isolated preset is explicitly admitted by the shared startup, AM and coarse
initialization guards; unrelated historical startup restrictions remain.

Actual inventory bounds are0 <= Y_i <= capacity_i. Targets determine ratios
in F, not legal operation limits. Original parser weights, positive targets,
optional visits, one nonzero unidirectional service per visited station, empty
departure and loaded return are retained. Under common pickup/drop times,
duration equals travel + (pickup_time + drop_time)*total_pickup because
return cargo is unloaded at depot. A single new drop transfers an existing
unload from depot to station, adding travel but no net handling duration.
Vehicle Q constrains load prefixes, not cumulative pickups.

For a pair on original legs a<=b, the added q is present from its pickup to
drop, and q <= Q_k - max(load[a..b]). For a single pickup the affected suffix
maximum applies; for a single drop q <= min(suffix loads). Pairs on one leg
replace before->after with before->pickup->drop->after. Distinct-leg deltas
add; existing operations remain unchanged. q is further bounded by station
inventory/capacity and remaining original route duration. With zero handling,
there is no division by handling time. The original1e-7 physical duration
tolerance is used, followed by the independent original verifier.

For fixed station(s) and q, F is independent of vehicle/insertion placement.
The minimum-travel feasible placement minimizes added duration. If gain>0,
it maximizes gain/duration among positive-duration placements and cannot lose
an available nonpositive-duration placement. Group placements by qmax, then
take suffix minima to select the best placement for each q without repeating
the objective calculation. Deterministic ties use gain, duration, station IDs,
q, vehicle and leg indices. This preserves the specified local score; it is
not a dominance theorem for the complete BRP or a claim of optimal loading.

F is the original normalized pairwise Gini plus weighted target deviation.
Inventory deltas update only affected ratios/pairs in O(V); near cancellation
the original full formula is recomputed, including its G=0 convention when
S=0. Every selected motif is checked again with verifySolution. A score change
cannot publish an infeasible UB or change exact proof coverage. The1e-12
positive-gain threshold governs this heuristic only; native certificate and
feasibility tolerances are not relaxed. Deadline interruption is distinct from
exhaustive absence of an improving motif. No CPU/Work decision changes the
mathematical task, and there is no fallback after an internal slice.

This constructor can be myopic: it never revises an already served station's
quantity or moves an existing visit. It need not dominate decoded descent or
HGA. Stronger initial UB, lower startup cost and full exact performance are
separate questions. Finite insertion, relocation and greedy construction are
not claimed as new theory. The R72 literature scope remains applicable to
why a different loading theorem cannot certify this objective's greedy moves.

Validation uses an independent brute-force oracle that explicitly materializes
every candidate quantity at every placement and recomputes complete physical
feasibility/F. Initial37 comparisons cover2741 feasible motifs, heterogeneous
capacities, cumulative pickups above Q, loaded return, zero handling, S=0,
three lambda values, nonuniform target/weights, empty/partial/terminal routes.
Native CLI qualification and real-input startup diagnostics are separate and
their actual pass/fail state is in qualification and diagnostic ledgers.

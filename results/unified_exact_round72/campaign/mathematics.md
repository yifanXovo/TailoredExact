# Correctness and design scope

DS-X enlarges the finite guided neighborhood by moving one station between
vehicle sequences, preserving its unique assignment. Full deterministic
greedy decoding rechecks the resulting operation plan; the independently
verified physical witness alone can update the UB. Neither candidate ordering
nor a route-window proxy certifies feasibility or objective improvement.
Accept only decoded fitness gain greater than1e-12, and exhaust every generated
candidate before declaring a terminal pass. Strict improvement on the finite
route-assignment/order state space prevents cycles, for the fixed decode map.
Cache use must agree with full fresh decoding. Whole-run interruption must
not be reported as completion of all24 seed neighborhoods.

Cross-route tail relocation can expose useful service/vehicle capacity that
intra-route moves cannot access. This is a BRP design hypothesis, not a speed
or approximation guarantee. Only a limited generated neighborhood is searched;
it omits many relocations/swaps, and local exhaustion does not prove global
routing or inventory optimality. All original capacities, one unidirectional
nonzero service per station, empty departures, allowed loaded returns and
travel plus current handling semantics remain unchanged.

No proof constraint, interval, incumbent cutoff rule or Gurobi numerical
standard changes. The unchanged exact one-hot model and full frontier preserve
the original optimum after a verified startup UB, independently of heuristic
quality. Actual native Starts supply primal points and never justify a bound
by themselves. A pre-proof deadline can retain the universal LB0 only under
the original nonnegative objective premises; it is not a tree certificate.
Numerical certification remains distinct from a rational certificate. The
constituent relocation, greedy decode and multi-start techniques are not
claimed as new theory; empirical net benefit remains to be established.

# Frozen M-B and the original physical problem

The actual argv uses `--algorithm-preset research-round83-vds-equal-net-exchange` and appends `--round98-state-service m-binary`. Effective reporting identity is `research-round99-ensc-discrete-structure-m-binary`. ENS-Q's `--round100-continuous-quantities` is absent and remains false. M-BL, projected and vehicle-state modes are excluded.

ENS-C declares x/load/Y integer and s/z/m binary; p/d are integer. M-B preserves every declaration except p/d become continuous, and retains the original R100 two station rows:

    sum_k(p_ki+d_ki) = sum_(y in S_i) abs(b_i-y)*s_iy
    sum_k z_ki = 1-s_i,b_i

An absent initial state selector is fixed zero, never invented. Original nonnegative quantity bounds, single visit, binary direction upper bounds, nonzero service, inventory, route, prefix load and duration rows remain. Empty/singleton domains and zero quantity upper bounds retain the old writer contract.

Integer b/Y with at most one nonzero single-direction service implies pickup p=b-Y or delivery d=Y-b, and all other vehicle quantities are zero. Thus p/d integrality does not depend on A/B. This proof does not cover split services, simultaneous pickup/drop or fractional b/Y. A/B are valid state/service strengthening rows, not R106/R107 route-conflict certificates. The inherited R100 factor evidence is not reidentified by this round's three methods.

Vehicles leave the depot empty. Each station receives at most one nonzero single-direction integer service by one vehicle. Every prefix and return load lies in [0,Q_k]; loaded return is legal. Station total inventory equals original station stock minus the sum of depot return loads. Cumulative pickups may exceed Q. Closed duration equals travel plus (pickup_seconds+drop_seconds)*total pickup, including unloading return stock. Original metric, speed, min ratios, weights, tolerances and evaluator apply.

    Y_i = b_i + sum_k(d_ki-p_ki), r_i=Y_i/D_i
    F = G_true + lambda*sum_i omega_i*abs(r_i-1)
    G_true = sum_(i<j)abs(r_i-r_j)/(n*sum_i r_i)

The evaluator sets G=0 at zero denominator and preserves the penalty. Every published physical UB needs its own complete fleet and all quantity columns finite, within their original bounds and the original integer tolerance, including unvisited columns. LP/child-LP p/d may be fractional. Original LP/MIP type restoration and actual Start mapping bind the complete canonical matrix/domain/epoch.

The full original ENS outer framework, VD-P/F0, self-paid 24+1 startup/closure/handoff, AM .08, original depth/width/coverage, cutoff epoch, child-cache, milestone and terminal rules are preserved. One local OPTIMAL or near-zero signed gap does not establish the original global certificate. P remains cold unstrengthened compact with native default policies and no ENS Start or row help. Subsequent default-off R96/R97, LP-G, R101–R107 research paths stay off. Production has no instance, SHA, size, known-optimum, clock, Work, stagnation or node/car-time dispatcher. Experimental caps and the global shutdown reserve manage only experiment termination.

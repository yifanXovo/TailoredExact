# Exact scalar quantity search: proposal, not implementation

Status: coordinator derivation independently reviewed below; exact-oracle and implementation qualification remain pending. No performance claim. This does not reopen Round75's already exhausted neighborhood as though it were new: that stage found no improving single/pair quantity move in its five tested endpoints. Its potential uses are an equivalent implementation improvement, or the quantity subproblem of a separately justified new route/assignment neighborhood.

## Piecewise fractional-quadratic structure

Fix a route/assignment template and an integer inventory direction v. Let Y_i(t)=Y_i(0)+v_i t for integer t in its physical domain. For the original objective write H(t)=sum_{i<j}|Y_i(t)/D_i-Y_j(t)/D_j|, S(t)=sum_i Y_i(t)/D_i and P(t)=sum_i w_i|Y_i(t)/D_i-1|, so F(t)=H(t)/(n S(t))+lambda P(t) when S(t)>0.

Partition the scalar domain at all ratio crossings, all target crossings and all operation-zero points. On an open piece with fixed signs and positive S,

H(t)=A t+B, S(t)=C t+D, P(t)=E t+J.

Then

F'(t)=(A D-B C)/(n(C t+D)^2)+lambda E.

On that piece, F' is monotone (or constant), because its derivative has the constant sign of -C(A D-B C). Unless F is constant, there is at most one stationary point. When C != 0 and lambda E != 0, a stationary point can exist only if -(A D-B C)/(n lambda E)>0, and the positive-denominator branch is

t*=(sqrt(-(A D-B C)/(n lambda E))-D)/C.

If C=0, F is affine on the piece. If lambda E=0 or A D-B C=0, use the original derivative directly; do not divide by zero. A stationary maximum is harmless to include.

It follows that the exact integer minimizer on a feasible closed piece is among its first/last integers and the floor/ceiling of any stationary point inside it. Include feasible integer breakpoints explicitly. One may instead test the neighboring integers on both sides of every rational breakpoint; this avoids losing an isolated feasible operation-zero state. For a flat piece, retain the original deterministic tie-break, which need not select the smallest t (for example, the no-move value may be excluded). This is an exact finite candidate theorem for the specified scalar subproblem, not convexity or global BRP optimality.

## Physical domains and zero denominator

For a fixed order and assignment, station bounds and every load-prefix bound are affine inequalities in t. On a piece where operation signs and the set of nonzero stops are fixed, travel is constant and handling plus loaded-return time is affine. Their intersection is an interval. At operation-zero breakpoints the route omits a stop and its travel can change discontinuously; evaluate such points separately with the original physical verifier. This argument does not rely on a triangle inequality. Reappearance of a deleted stop requires a declared fixed template and must not silently enlarge the inherited Round75 neighborhood.

S(t)=0 cannot use the formula. With nonnegative inventories it means all inventories are zero; evaluate it using the original Gini-zero convention and physical verifier. Near-zero positive S is not interchangeable with zero. The model's original objective weights, handling convention, verification and certificate tolerances remain unchanged.

## Admission requirements

Independent review must check all derivative cases and the integer-candidate argument, then compare against exhaustive rational evaluation on generated tiny domains, including heterogeneous targets, positive/negative/zero C, flat pieces, stationary minima, zero inventory and discontinuous deletion travel. A production implementation needs certified/conservative breakpoint and root rounding (or a correctness-preserving fallback), and exact agreement with the existing tie-break and acceptance order; ordinary floating-point rounding alone is insufficient to claim an equivalent acceleration.

Even a proven reduction in quantity evaluations may lose wall time on small capacities. First diagnose actual counts and cost. A changed neighborhood must have separate mathematics, fixtures and complete-run acceptance; it cannot inherit a speed or solution-quality claim from this scalar theorem.

## Independent mathematical review (Sol, 2026-09-26)

The scalar candidate theorem is correct under its stated fixed-template assumptions. `src/Result.cpp:109–128` confirms the original objective `H/(V S)+lambda P` for `S>0`, with `G=0` when `S=0`; `src/Evaluator.cpp:40–115` confirms route travel plus pickup, station-drop and depot-unload handling. On a fixed-sign positive-`S` piece, with `K=AD−BC`, differentiation gives `F'=K/[n(Ct+D)^2]+lambda E` and `F''=−2CK/[n(Ct+D)^3]`. Thus the derivative is monotone; it has at most one zero unless `F` is constant. The positive square-root branch in the proposal is the only admissible stationary solution. If `C=0`, `K=0`, `lambda E=0`, or a square-root argument is nonpositive, direct derivative evaluation covers the degeneracy. A continuous minimum on each *physically feasible closed subinterval* is at an endpoint or that stationary point; the neighboring integers, separately checked integer kinks, and isolated operation-zero values therefore contain the discrete optimum. Flat-piece tie-breaking must scan the mathematically tied integer range according to the declared deterministic rule, with `t=0` treated exactly as the old neighborhood does.

The feasibility partition needs explicit endpoints from **every** station-inventory bound, every vehicle prefix-load bound, route-duration bound, and `S(t)=0`, in addition to the listed sign/kink breakpoints. Within a fixed operation-sign/nonzero-stop pattern, the route travel is constant; pickup, drop, final depot unload and duration are affine in `t`, so intersecting their inequalities yields an interval. At an operation-zero integer the route topology and travel can jump, and only the resulting actual route passed through `verifySolution` determines feasibility and value. This is particularly important because `Round75QuantityDescent.cpp` removes zero-operation stops and uses the original duration tolerance. The theorem does not justify introducing a stop absent from the fixed template, or discarding an old candidate solely from rounded breakpoint/root estimates.

For an *equivalent* acceleration, candidate generation must be conservative under numerical ambiguity: if a breakpoint, feasible integer endpoint, stationary root, objective ordering or strict-improvement threshold cannot be certified, evaluate the entire uncertain integer neighborhood or fall back to the original enumeration. The existing Round75 loop compares approximate incremental double values, uses a `1e-12` strict-improvement gate and lexicographic `(first,second,delta)` ties (`src/Round75QuantityDescent.cpp`); mathematical minimizer equivalence alone does not establish bitwise equality of that path's selections. Qualification should compare the **verified original objective and physical route**, record any old numeric tie discrepancy, and keep the unchanged full proof stage. This is a scalar search theorem, not evidence that the already tested single/pair neighborhood has new improving moves or that fewer evaluations yield lower wall time.

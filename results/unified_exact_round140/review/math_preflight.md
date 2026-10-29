# Independent mathematical preflight

Reviewer: `/root/independent_review`, distinct from the primary implementer.
Scope: the authorized Round140 goal, the existing R134 TC constructor,
the canonical writer and R138 stock rows. No Optimize, commercial runtime,
compilation or historical raw restoration was performed.

**Verdict: mathematical design passes, subject to the implementation and
actual-matrix checks below.** This is a design review, not qualification of
code that has not yet been implemented.

1. With empty departures, elementary depot-closed physical routes and
   prefix loads in `[0,Q_k]`, telescoping gives
   `R_k=sum_i(p_ki-d_ki)` equal to the final load. Thus
   `0<=R_k<=Q_k` and `max(0,B-sum Q)<=sum Y<=B` are integer-valid.
   The current writer explicitly emits `R_k>=0`; its final-load block does
   not emit the matching aggregate `R_k<=Q_k`. Do not ascribe that explicit
   row to the inherited LP. This does not invalidate the integer-valid
   inventory budget used to derive TC2.
2. The threshold identity is exact for finite nonnegative inventories and
   positive loaded coefficients. For each pair, threshold intervals on
   which exactly one station is high telescope to the absolute ratio
   difference. The zero inventory case needs no division.
3. The R134 `count_coefficients` implementation uses actual support minima,
   forced-high stations and sorted minimum optional increments to derive
   `u`, but its aggregated chord is exactly `(n-u)K`. It is not TC2.
   Replacing `B+` by its intersection with the sum of support maxima is
   equivalent for the supported domain; every such tightening must be
   documented and bound to that domain.
4. For the lower count, forced-high/forced-low stations can contribute at
   most their support maxima. An inactive optional contributes at most its
   greatest strictly-low support value. Activating at most `q` optionals
   increases this sum by at most the `q` largest positive deficits.
   Therefore the proposed minimal `q` and `ell=|H|+q` are valid necessary
   bounds. This reasoning permits support holes and ties. It does not
   establish route realizability. Unreachable lower budgets or `ell>u`
   require infeasibility/error handling, never clamping.
5. The chord residual is `(K-ell)(u-K)`. Hence its sum is integer-valid.
   Relative to the old zero-lower chord the difference is `ell(u-K)`,
   which can be negative when a fractional point has `K>u`. Keep the old
   aggregate TC row. The constant `sum Delta*ell*u` and negative selector
   coefficients are essential.
6. Derive ratios from the binary64 `c_i` in the actual original
   `r_i-c_i Y_i=0` rows. The writer also contains selector rows computed
   from `y/target`; these are not a license to substitute decimal targets
   or merge nearby thresholds. Directed downward rounding of every RHS
   selector coefficient and its constant is valid because selectors are
   nonnegative. Once terms move to the left, their signs reverse. Avoid
   the generic writer's `1e-12` omission/unit-abbreviation behavior for the
   new coefficients; check Native readback and any positive row scaling.
7. The supplied rational block witness independently checks exactly:
   `K=(2,1)`, `tau=3`, old TC RHS `2`, TC2 RHS `6`, `g=1/6`,
   `J=1/2`, `H=2=4J`. Set `q_iy=g*s_iy`; then the true common product
   satisfies every valid stock envelope on any declared interval containing
   `g` and any inventory interval containing `tau`. Old TC plus stock is
   satisfied and TC2 is violated. This is strict separation of the stated
   relaxation block, with no asserted BRP optimum improvement.
8. A pure offline permutation check confirms that all twelve permutations
   of `(2,1,0,0)` are physically reachable from `(2,2,1,0)` by one
   empty-departure capacity-two route, returning exactly two. One route
   visits changed stations only; prefix loads stay in `[0,2]`. Uniform
   mixing therefore supplies the stated selector marginals for the route
   block. This is only a useful starting point: all original matrix rows,
   objective cutoff and retained controls still require direct checking.
   In particular, the feasible balanced all-one vector can yield a tight
   objective cutoff that removes this fractional witness. Do not promote
   physical route extendability into a complete cutoff-domain strictness
   claim without that check.

Before expensive runs, separately review the actual implementation and
root/child/cutoff-refresh/Native artifacts, feature-off equivalence and
retention of old TC. No implementation or performance conclusion is
certified by this preflight alone.

# Round92 isolated static handling/activation row — source-only handoff

**Status:** the separate integration candidate is now present in source, with
default-off wiring and zero-Optimize G1 test sources; none has been built,
imported, optimized or run. The mathematical helper is unchanged in scope.
See `integration_implementation.md` for the applied source and test gate.
The only proposed inequality is, for each vehicle `k`,

`sum_i p_{k,i} <= B_k sum_{j>=1} x_{k,0,j}`,

where the exact mathematical limit is
`B*_k=max(0,floor((T_k-ell_min,k)/c_k))` and the emitted coefficient
`B_k=max(0,floor(q_upper,k))>=B*_k` uses a rigorously outward quotient upper
bound. The current canonical model has
common `T`, `c` and arc coefficients for all vehicles, but the plan retains the
per-vehicle name to avoid implying that this is a fleet aggregate cut. It is
default off, uniform over instances, and mutually exclusive with A1, native B1
and LP-G. No continuous B-arm or adaptive bound family is proposed for the
method candidate.

## Mathematical and serialization contract

`CplexBaseline.cpp:1493–1505` writes binary depot-out degree at most one and
return balance. Its F0 connectivity block at `1521–1564`, station visit flow,
and `p<=pmax*z` exclude a positive-service disconnected route. The duration
row at `1800–1808` writes exactly one coefficient for each allowed directed
`x_{k,i,j}` and each `p_{k,i}`, with RHS `T`. The physical verifier includes
drop handling for a loaded return (`Evaluator.cpp:106–116`); no step assumes
`total pickup<=Q`. Extra visits cannot reduce nonnegative travel or service
time. For an active depot-closed route visiting station `i`, its directed
travel is at least `d*(0,i)+d*(i,0)`, hence at least the minimum of those
round trips. With `c>0`, integer `P_k` satisfies `P_k<=B_k`; inactive routes
have `P_k=0`. This is an elementary integer rounding/activation row, not a
claim about the convex hull of routing or about mathematical novelty.

The helper accepts **the coefficients that will be written into the same
original canonical duration row**, not input coordinates or nominal distances.
`CplexBaseline.cpp:208–234` removes `|coef|<=1e-12`, emits unit coefficients
when `||coef|-1|<=1e-12`, and otherwise writes `max_digits10` binary64. The
candidate-only writer must normalize each coefficient once and use that same
object both for the old duration row and this proof; a suppressed nonnegative
arc remains an allowed zero-cost arc, whereas `nullopt` denotes an unavailable
arc. Negative/nonfinite raw travel is rejected before normalization. The
default-off writer path stays byte-for-byte untouched. The emitted candidate
duration row must be read back in G1 against the helper input before any solve.

`Round92HandlingActivation.cpp` uses nonnegative **directed** Floyd paths.
Compilation rejects fast-math; runtime rejects non-nearest rounding and
FTZ/DAZ using volatile arithmetic and bitwise subnormal checks. Each sum is enclosed one binary64 step outward (with exactly
representable small-integer operations retained exactly). It encloses
`ell_min`, subtracts from the exact emitted RHS in the correct directions,
then divides by the positive emitted `c` in both directions. It returns the
safe **upper floor** uniformly, with an `exact_integer_floor` flag only when
the clipped lower and upper floors agree. If they differ, the same method
still emits a valid potentially weaker row, rather than changing algorithm
or retrying. `B<=2^53` makes its coefficient exactly binary64. Overflow,
non-IEC559 arithmetic, malformed matrix, negative/nonfinite arc and identity
contradictions are invalid/fail-closed. A canonical emitted `c=0` is a valid
no-row mathematical case: duration imposes no handling quantity limit. No
depot-closed station path gives the valid `P=0` row **only** under the audited
F0/depot/visit arc-support contract. `T<ell_min` also gives `B=0` when the
upper floor is zero. This construction needs no metric assumption and never
uses a name/size/time rule to choose a different method.

The helper is pure and records elapsed preparation time plus arc count. In
future integration, own an explicit cache in the ENS-C run/model-construction
context. Its key is the complete normalized directed matrix **including arc
presence**, normalized `c`, RHS `T`, and a construction-version tag. Compare
keys exactly and only reuse after exact equality; `G` interval, leaf ID and
incumbent epoch are irrelevant to this static physical row. Report cache hit,
lookup time, once-per-distinct-key O(V^3) preparation time, `B`, interval,
rows written, resulting LP SHA and readback status. Do not create an implicit
global cache or an arbitrary capacity/round threshold. Current code merely
supplies the pure preparation function; it has not claimed an integrated
cross-leaf cache.

## Historical and evidence boundary

R7/R8 already used integer operation budgets and route-mask travel bounds;
some valid mask rows harmed finite MIP performance. R63 studied continuous
travel/resource rows (not this floor) and observed root-LP benefits without
stable full-MIP gains. R91 fixed historical L0 diagnostics gave D3 A=B=C
`0.0282826776207786`; C2 A `0.602666467698065`, B continuous
`0.620202596583893`, C rounded `0.622642579074402`. The extra C−B
`0.002439982490509` is the observed rounding contribution, not the entire
C−A gain. Those are numerical LP observations, not a strict rational dual
proof or performance result. See `handling_real_decision.md` and
`handling_real_independent_evidence_review.md` in Round91.

## Future finite gates (not authorized to run now)

1. **G1 pure:** add the new helper to a fresh Round92 build, run only its pure
   fixture plus appropriate frozen R83/R88/R89/R90 regression tests. Confirm
   directed nonmetric travel, zero/negative quotient, exact/near-integer upper
   boundary, writer suppression/near-one normalization, nonpositive `c`,
   unreachable paths under true x-column support, inactive route, and an independent
   two-station route oracle. Add an actual `Evaluator` route fixture with total
   pickup `P>Q`, intermediate delivery and loaded depot return; the current
   pure helper test checks only row arithmetic. Compare actual exported duration/new-row
   coefficients, variable domains, F0 and depot rows without Optimize. Repeat
   the same normalized key across two leaf exports; changing one coefficient
   must invalidate the explicit run-local cache. Off must emit no Round92 row
   or ledger and match the frozen model identity; incompatible switches fail.
2. **G2 micro validity:** finite native original-model integer fixtures for
   `a=0/1`, pickups through `B` and just above it where the original duration
   is infeasible. Preserve full original physical verifier and source/LP
   hashes. Every emitted floor must have a valid upper enclosure; an interval
   crossing an integer is reported as conservative rather than exact.
3. **G3 early method screen only if G1/G2 pass and root signs a new lease:**
   contemporary ENS-C off/on with the *same new binary*, complete whole-run
   costs and certificate/physical/coverage audits. Preselect integration E8,
   S12, positive-root C2, zero-root D3, and historical protection D6/F2;
   their time caps, order, inputs and seed must be frozen from approved
   research manifests before launch. Do not rerun/choose cases after seeing
   outcomes. Use the existing severe-regression stop and no automatic retries.
   Root-LP gain alone does not promote the method or license a long panel.

The exact pending source edits and fail-closed writer hook are in
`integration_patch.md`. Source-only tests are in
`tests/round92_handling_activation_tests.cpp`; none has executed yet.

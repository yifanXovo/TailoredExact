# Round 21 strict-certificate policy

## Scope and authority

This policy applies to every fresh Round 21 global-tree and plain-CPLEX solve that is intended to support an original-problem optimality claim. It separates a native CPLEX proof, a CPLEX tolerance stop, a valid finite-time bound, and a project-level independent proof. A displayed zero gap, a rounded JSON value, or an `optimal` substring is never enough by itself.

The authoritative installed-CPLEX audit is [cplex_strict_status_and_gap_semantics.md](cplex_strict_status_and_gap_semantics.md). The executable policy is represented by `include/StrictCertificate.hpp` and `src/StrictCertificate.cpp`; `tests/strict_certificate_tests.cpp` exercises the positive and fail-closed cases. If this document and the implementation ever diverge, an official run must be classified as rejected until they are reconciled and retested.

`strict_certified_original_problem` is an optimal-solution certificate flag. It is true only for one of the three proof routes defined below. The separate `infeasible` class records native integer infeasibility and does not set this optimal-solution flag.

## Native status map

The numeric code is the native `CPXgetstat` result after the one `CPXmipopt`. The status text is retained independently and is a consistency cross-check, not a substitute for the code.

| Code | Installed CPLEX symbol | Meaning used by this policy |
|---:|---|---|
| 101 | `CPXMIP_OPTIMAL` | CPLEX reports that it proved an optimal integer solution. This is the only status that can enter the native exact-optimal route without a separate proof module. |
| 102 | `CPXMIP_OPTIMAL_TOL` | The solution has not been proved optimal; it appears optimal within a relative or absolute MIP-gap tolerance. This status is never strict by itself. |
| 103 | `CPXMIP_INFEASIBLE` | CPLEX reports integer infeasibility. |
| 107 | `CPXMIP_TIME_LIM_FEAS` | Time limit with a native incumbent. The native best bound may still be a valid finite-time lower bound. |
| 108 | `CPXMIP_TIME_LIM_INFEAS` | Time limit without an integer incumbent. The suffix `INFEAS` does not prove model infeasibility. |
| 115 | `CPXMIP_OPTIMAL_INFEAS` | Optimal with unscaled infeasibilities; rejected for a strict certificate. |

The current code/text check is case-insensitive and requires the expected status category. Code 101 must contain `optimal` but neither `tolerance` nor `infeas`; code 102 must contain both `optimal` and `tolerance`; code 103 must contain `infeas` but not `time`; codes 107 and 108 must identify a time limit, with code 108 also identifying no integer solution or infeasibility; code 115 must identify optimality with infeasibilities. An empty, unsupported, or category-inconsistent text/code pair fails closed as `certificate_rejected`.

## Immutable run inputs

Every run record must preserve the following independently. “Raw” means the full finite `double` returned by the named native call, before display formatting, gap computation, status interpretation, or wrapper rewriting.

| Quantity | Required retained fields and validity rule |
|---|---|
| Native status | Numeric status code and full native status text. They must be mutually consistent. |
| Native incumbent objective, `U_native` | `CPXgetobjval` return code, availability flag, and value. It is valid only when the return code is zero, availability is true, and the value is finite. It is an incumbent value, not a lower bound. |
| Native best bound, `L_native` | `CPXgetbestobjval` return code, availability flag, and value. It is valid only when the return code is zero, availability is true, the value is finite, and its magnitude is below the installed `CPX_INFBOUND=1.0E+20` threshold. For this minimization model it is the sole native lower-bound source. A documented infinite/no-information proxy is unavailable even when the getter return code is zero. |
| Independently verified incumbent, `U_verified` | Availability, full-precision independently reconstructed original objective, and verifier outcome. A finite recorded value can support diagnostic gap computation, but it is a valid original-problem upper bound and can support a strict proof only when the same-run original-solution verifier passes. |
| Strict gap parameters | For each of the relative and absolute MIP gaps: parameter ID, requested value, setter return code, getter return code, and effective readback value. |
| Lifecycle | Whether native solver finalization was reached and whether the required one-environment, one-problem, one-model-read, one-`CPXmipopt` lifecycle completed without an invalidating error. |
| Search state | Native processed-node count, open-node count, solution count, finalization state, and any final-bound source diagnostics. These do not create a certificate, but must remain available for audit. |
| Optional proof route | Proof-condition result and nonempty module name, recorded separately for bound equality and for any independent exact certificate. |

The native incumbent, verified incumbent, and native lower bound are distinct quantities even if their printed decimal representations match. No value may be copied into another field merely because CPLEX returned status 101 or 102.

## Gap definitions and denominators

All gap numerators are calculated from retained full-precision values. They do not modify either source value.

When `U_native` and `L_native` are valid,

```text
native_absolute_gap
    = max(0, U_native - L_native)

native_relative_gap
    = native_absolute_gap / max(1, |U_native|)

native_cplex_denominator_relative_gap
    = native_absolute_gap / (1e-10 + |U_native|)
```

The second expression is the Round 21 stable reporting convention. The third records the denominator used by the installed CPLEX relative-MIP-gap definition. It is retained to explain native stopping behavior and must not be conflated with `native_relative_gap`.

When `U_verified` and `L_native` are finite and available,

```text
verified_absolute_gap
    = max(0, U_verified - L_native)

verified_relative_gap
    = verified_absolute_gap / max(1, |U_verified|)
```

The project also retains its historical denominator convention separately:

```text
verified_project_relative_gap
    = verified_absolute_gap / |U_verified|,       if |U_verified| > 1e-12
    = 0,                                          if the absolute gap is 0
    = +infinity,                                  otherwise
```

Unavailable gap quantities are represented as unavailable/nonfinite decision outputs, not as zero. Gap arithmetic uses `max(0, U-L)` only for reporting. The signed residuals `U_native-L_native` and `U_verified-L_native`, plus explicit inversion flags, are retained beside the clamped gaps; the clamp is not an equality proof and cannot hide or repair a raw bound/upper-bound inversion. Any such inversion rejects the current status-101 strict route.

Serialization has the following non-negotiable invariants:

- `lower_bound` equals the retained valid `L_native` returned by `CPXgetbestobjval` for that solve. It is never replaced by `U_native`, `U_verified`, or a status-dependent value.
- A serialized original-problem upper bound comes from the same-run independently verified incumbent. The native incumbent remains separately recorded.
- A serialized `gap` is recomputed from the serialized retained lower and upper bounds under its explicitly named denominator convention. It is not set to zero because of status 101/102 or display precision.
- Raw values and gaps are emitted with round-trip-safe floating-point precision. Formatting may create a human-readable column, but that column cannot feed classification.
- Classification and serialization do not round `L_native` upward, force it to equal an incumbent, or mutate it after the certificate decision.

## Strict gap-parameter round trip

Both fresh Tailored and fresh plain-CPLEX strict-policy runs request and verify:

| Parameter | Required ID | Requested value | Required effective value |
|---|---:|---:|---:|
| Relative MIP gap | `CPXPARAM_MIP_Tolerances_MIPGap` = 2009 | exactly `0.0` | exactly `0.0` |
| Absolute MIP gap | `CPXPARAM_MIP_Tolerances_AbsMIPGap` = 2008 | exactly `0.0` | exactly `0.0` |

For both records, `CPXsetdblparam` and `CPXgetdblparam` must return zero. The IDs, requested values, return codes, and readbacks must all be retained. The current classifier deliberately uses exact comparisons to zero: there is no project epsilon for the round trip.

Any wrong ID, nonzero requested value, failed setter, failed getter, nonzero or nonfinite readback, or missing record yields `certificate_rejected` with `strict_gap_parameter_round_trip_failed`. The run does not fall back to the CPLEX defaults and cannot be rescued by a small observed gap. Setting only the relative gap to zero is insufficient because the installed default absolute gap is positive.

Effective zero/zero prevents the documented positive-gap tolerance stopping rules from being intentionally requested, but it does not authorize rewriting an observed status. If CPLEX nevertheless returns code 102, the observed code remains tolerance-only unless a separate named proof module establishes closure.

## Certificate classes

All classes are mutually distinguishable. The classifier applies the common fail-closed gates before accepting any strict route: consistent code/text, valid strict-parameter round trip, completed native finalization and lifecycle, and (except for the native infeasibility class) a finite successful native best-bound retrieval.

### `native_exact_optimal`

This class sets `strict_certified_original_problem=true` only when all of the following hold:

1. The native status is code 101 with consistent text.
2. Both gap parameters passed the exact zero set/readback policy.
3. Solver finalization was reached and the required lifecycle is complete.
4. `CPXgetbestobjval` succeeded and retained a finite native best bound.
5. `CPXgetobjval` succeeded and retained a finite native incumbent objective.
6. The independently reconstructed solution passes the original-problem verifier.
7. The successful final `CPXgetmiprelgap` observation is exactly zero.
8. The retained native objective and native best bound have exact zero signed/absolute residual and no bound inversion.
9. The retained native best bound and independently verified original upper bound have exact zero signed/absolute residual and no bound inversion.

Code 101 is treated as CPLEX's installed native optimality proof under its documented numerical semantics. Round 21 adds exact retained-value consistency gates because official original-problem output may not report a positive gap or hide `L_native > U_verified` behind `max(0,U-L)`. No project epsilon can satisfy these two gates. Code 101 is not redefined as an arbitrary-precision rational proof, and it does not permit the raw native lower bound to be replaced by the incumbent. The equality here is a fail-closed model/incumbent mapping gate attached to status 101; it is not used to upgrade code 102 or a time limit.

### `native_bound_equality_closed`

This is a separate proof route and sets the strict flag only when all common gates pass, a finite verified upper bound is available, the original-solution verifier passes, the retained values satisfy exact floating-point equality `L_native == U_verified`, and both of these module fields are valid:

- `bound_equality_proof_conditions_passed=true`;
- `bound_equality_proof_module` is nonempty and names the module that discharged the conditions.

Exact floating-point equality is necessary in the current classifier but is not sufficient. The named module must document and audit why the native bound and verified objective refer to the same full original objective, why the native value is a valid global lower bound, why the verified value is a valid feasible upper bound, and why equality is exact rather than the product of solver tolerance, binary rounding, decimal formatting, or an arbitrary project epsilon. A boolean set by the wrapper without that module evidence is invalid. This route may classify a run whose native status is 102 or a time-limit status, but it does not derive its proof from that status.

### `independent_exact_certificate`

This route sets the strict flag only when all common gates pass, the original-solution verifier passes, and both of these fields are valid:

- `independent_exact_certificate_conditions_passed=true`;
- `independent_exact_certificate_module` is nonempty and names the proof module.

The module must prove closure for the complete original feasible set and full original objective, using exact conditions appropriate to that proof; map the verified candidate back to the original instance; record reproducible proof evidence; and establish that no better feasible original solution exists. A second floating-point solve, a historical objective, a displayed zero gap, or a wrapper assertion is not an independent exact certificate. In the current decision ordering, a valid independent proof is labelled with this class even if the native status would otherwise be code 101, 102, or a time-limit result.

### `native_tolerance_optimal_only`

This class is assigned to consistent code 102 after the common gates when neither a valid independent module nor a valid named bound-equality module has closed the problem. It never sets the strict flag.

A positive retained native or verified gap makes the non-strict conclusion direct. A numerically equal raw bound and upper bound still do not make code 102 strict without the named equality proof and its conditions. Likewise, a gap that prints as `0`, rounds to zero in a table, or is smaller than an invented project tolerance remains tolerance-only. IBM's installed definition explicitly says that code 102 has not proved optimality; requesting or reading back zero gap parameters does not change the meaning of the status actually returned.

### `time_limit_valid_bound`

Absent a valid named independent/equality proof, codes 107 and 108 are non-strict time-limit classes when finalization/lifecycle and the strict-parameter gates pass and `L_native` is successfully retained as a finite value. Code 107 may also have a native incumbent. That incumbent is not a certified original-problem upper bound until the independent verifier passes. Code 108 has no native integer incumbent and is not an infeasibility proof. A verifier-passing incumbent plus a positive gap remains non-strict.

### `infeasible`

Consistent code 103 is classified as native integer infeasibility after the status, strict-parameter, finalization, and lifecycle gates pass. It is distinct from code 108. The current optimal-solution flag remains false. Model-to-original-problem identity and lifecycle evidence must be retained wherever an original-problem infeasibility claim is reported.

### `invalid_or_unavailable_bound`

This class covers a failed `CPXgetbestobjval`, an unavailable or nonfinite best-bound value (including the documented infinite no-information value), and otherwise unsupported native statuses that have not already triggered a stronger rejection. It does not set the strict flag and must not serialize a fabricated zero or incumbent-derived lower bound.

### `certificate_rejected`

This fail-closed class covers a code/text inconsistency, a strict gap-parameter round-trip failure, incomplete solver finalization or lifecycle, verifier failure on a proposed exact route, missing native objective on code 101, failed native gap retrieval for a proposed strict route, a positive retained status-101 gap, a signed native-bound/verified-UB inversion, failure of the verifier for a proposed independent certificate, and code 115 (`optimal with unscaled infeasibilities`). Its `rejection_reason` must remain visible. Rejection is not converted into tolerance-only or time-limit success merely because some bound or incumbent is numerically useful.

## Exact-status, verifier, and lifecycle rule

The native exact route is the conjunction

```text
status 101
AND status-code/text consistency
AND exact zero relative-gap parameter round trip
AND exact zero absolute-gap parameter round trip
AND native finalization reached
AND required one-solve lifecycle complete
AND finite successful CPXgetobjval
AND finite successful CPXgetbestobjval
AND successful finite CPXgetmiprelgap observation
AND independent original-solution verifier pass
AND exact U_native == L_native with no signed inversion
AND exact U_verified == L_native with no signed inversion.
```

Every term is mandatory. Status 101 with a verifier failure, a missing objective, an incomplete callback/finalization lifecycle, or a failed parameter readback is `certificate_rejected`. Conversely, a verifier pass does not upgrade code 102 or a time-limit status: the verifier proves feasibility and the candidate objective, not global optimality.

For any proposed strict route, the final `CPXgetmiprelgap` call must also succeed (API return code zero) and supply a finite, nonnegative observed value. Failure or an unavailable/infinite output yields `certificate_rejected` with `native_mip_relative_gap_unavailable_for_strict_certificate`. Codes 103 and 108 do not fabricate a gap when no incumbent exists; this extra success gate applies to a proposed optimality certificate, not to honest infeasibility/no-incumbent classification.

The production adapters also compare the independently recomputed native-candidate objective with `CPXgetobjval`, retaining the signed residual. Their `1e-8*max(1,|U_verified|,|U_native|)` floating recomputation check is solely a solution-mapping/verifier consistency gate. It is not a bound-equality rule, is never applied to `L_native`, and cannot turn code 102, a time limit, or a positive retained gap into strict closure. Global optimality in the current production route still comes exclusively from native status 101 after every common gate passes.

The equality and independent routes use the same common native integrity gates in the current implementation and additionally require their named proof module and module-specific proof conditions. No unnamed exception is permitted.

## Objective-lattice and exact-rational policy

No production objective-lattice, exact-rational separation, bound-equality, or independent exact-certificate module is present in the source snapshot audited for this document. The only module names found in the strict-certificate tests are explicitly toy fixtures; they are not admissible in official results. Therefore official inputs currently leave both proof-condition flags false and both module names empty unless a separately reviewed production module is added.

In particular, raw floating-point equality is not an objective-lattice proof. Any future lattice/separation module must use exact rational arithmetic for the full original objective and prove a strictly positive separation that accounts for the Gini denominator and target ratios, `lambda`, every weight, and the penalty terms. It must apply uniformly across the supported problem family, not only V12 or named instances, and it must have independent exhaustive and adversarial tests. Until source and evidence satisfy those requirements, no objective-lattice argument is available and neither the equality nor independent class may cite one.

## Required audit invariants

An official result package must make these checks mechanically reproducible:

1. Installed numeric status and parameter IDs match the compiled constants.
2. Both zero gap parameters were set and read back successfully.
3. Native objective and native best-bound return codes, availability, and full-precision values are retained independently.
4. Serialized `lower_bound` equals the retained native best bound and is unchanged by status handling.
5. Every serialized gap recomputes from its retained source bounds under the labelled denominator.
6. A sub-display positive gap remains positive in raw data.
7. Code 102 with no named valid proof is tolerance-only, including at numeric or displayed gap zero.
8. A time-limit result with a positive gap is non-strict even when its incumbent verifies.
9. Code 101 fails closed on verifier, objective, parameter, status-consistency, finalization, or lifecycle failure.
10. Equality and independent classes identify a real production module and retain its proof-condition audit.
11. Missing, failed, infinite, or nonfinite best-bound retrieval never becomes a fabricated lower bound.
12. Classification, raw values, rejection reason, node counts, and finalization state survive serialization unchanged.

Historical files are not rewritten under this policy. They are reclassified in a separate audit from whatever raw status, bounds, parameter evidence, verifier evidence, and lifecycle evidence they actually retained; missing evidence results in a non-strict or unavailable classification rather than reconstruction by assumption.

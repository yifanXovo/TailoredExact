# CPLEX 22.1.1 strict status and MIP-gap semantics

## Scope and authoritative installation

This audit uses only the locally installed IBM CPLEX headers and IBM HTML reference documentation. It does not rely on remembered parameter identifiers, blogs, forum posts, or secondary summaries.

The audited installation is:

`C:\Program Files\IBM\ILOG\CPLEX_Studio2211`

The installed header identifies the release as CPLEX 22.1.1.0: `CPX_VERSION=22010100`, with version, release, modification, and fix components `22`, `1`, `1`, and `0`, respectively.

Source: `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\cplex\include\ilcplex\cpxconst.h`, lines 409-421.

## Native MIP solution statuses

The native status for a completed `CPXmipopt` call is obtained with `CPXgetstat`. IBM documents that `CPXgetstat` returns the solution status of the most recent optimization; zero means either an error condition or that a later model change may have invalidated that status.

Source: `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\cpxapi\getstat.html`, lines 120-134.

The relevant MIP statuses are distinct from the LP/simplex status `CPX_STAT_OPTIMAL=1`. A MIP strict-certificate path must interpret the MIP-specific `CPXMIP_*` values returned after `CPXmipopt`.

| Numeric code | Symbol | Installed IBM meaning | Round 21 certificate interpretation |
|---:|---|---|---|
| 101 | `CPXMIP_OPTIMAL` | An optimal integer solution has been found; CPLEX has proven optimality. | The only native optimal-status candidate for `native_exact_optimal`. It still requires successful lifecycle/finalization and independent verification of the reconstructed original solution. |
| 102 | `CPXMIP_OPTIMAL_TOL` | The current solution has not been proven optimal, but appears optimal within the relative or absolute MIP-gap tolerance. | `native_tolerance_optimal_only`; never strict merely because the displayed gap is zero. |
| 103 | `CPXMIP_INFEASIBLE` | The problem is integer infeasible. | `infeasible`, subject to the normal native lifecycle and status-consistency gates. |
| 107 | `CPXMIP_TIME_LIM_FEAS` | The time limit was exceeded, but an integer solution exists. | A positive-gap incumbent/bound result, not strict optimality. It can be `time_limit_valid_bound` when the retained native bound is available and valid. |
| 108 | `CPXMIP_TIME_LIM_INFEAS` | The time limit was exceeded and no integer solution exists at termination. | No incumbent is available. The `INFEAS` suffix does **not** prove that the model is infeasible; proof of integer infeasibility is code 103. |
| 115 | `CPXMIP_OPTIMAL_INFEAS` | The problem is optimal with unscaled infeasibilities. | Not the clean code-101 certificate and must be rejected for strict certification. |

The numeric definitions are in `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\cplex\include\ilcplex\cpxconst.h`, lines 2140-2174. The individual official meanings are documented at:

- `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\macros\CPXMIP_OPTIMAL.html`, lines 34-66. In particular, lines 47-56 say that CPLEX returns 101 when it has proven optimality and give exact incumbent/dual-bound equality as one example; lines 59-66 contrast this with tolerance status 102.
- `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\macros\CPXMIP_OPTIMAL_TOL.html`, lines 34-62. Lines 46-55 state that the solution has not been proven optimal and ties the status to the relative or absolute MIP-gap tolerance.
- `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\macros\CPXMIP_TIME_LIM_FEAS.html`, lines 34-47.
- `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\macros\CPXMIP_TIME_LIM_INFEAS.html`, lines 34-47.
- `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\macros\CPXMIP_INFEASIBLE.html`, lines 34-47.
- `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\macros\CPXMIP_OPTIMAL_INFEAS.html`, lines 34-48.

Status 101 is a native CPLEX proof under CPLEX's documented floating-point feasibility, integrality, and optimality tolerances; it is not a claim of arbitrary-precision rational arithmetic. This is why Round 21 additionally requires independent original-problem verification and complete lifecycle/finalization evidence.

## Relative and absolute MIP-gap parameters

| Purpose | Current C symbol | Legacy symbol | Numeric ID | Allowed values | Default |
|---|---|---|---:|---|---:|
| Relative MIP gap | `CPXPARAM_MIP_Tolerances_MIPGap` | `CPX_PARAM_EPGAP` | 2009 | `0.0` through `1.0` | `1e-4` |
| Absolute MIP gap | `CPXPARAM_MIP_Tolerances_AbsMIPGap` | `CPX_PARAM_EPAGAP` | 2008 | Any nonnegative number | `1e-6` |

The installed header definitions are at `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\cplex\include\ilcplex\cpxconst.h`, lines 2357-2361; the legacy aliases and the same numeric IDs are at lines 2559-2562.

The relative-gap reference identifies the C parameter and ID at `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\CPLEX\Parameters\topics\EpGap.html`, lines 59-63 and 122-126. Its stopping metric is documented at lines 135-139 as

```text
|bestbound - bestinteger| / (1e-10 + |bestinteger|)
```

and its range/default are documented at lines 154-156.

The absolute-gap reference identifies the C parameter and ID at `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\CPLEX\Parameters\topics\EpAGap.html`, lines 57-61 and 120-124. Lines 133-137 say that optimization stops when the absolute difference between the best integer objective and best remaining-node objective falls below the parameter; lines 138-140 give its allowed values and default.

Consequently, setting only relative MIP gap to zero is insufficient for strict gap closure: the default positive absolute tolerance of `1e-6` can still terminate a run with status 102.

The CPLEX relative-gap formula above is not the same as Round 21's reporting convention

```text
max(0, U_native - L_native) / max(1, |U_native|).
```

Both values must therefore be retained and labelled. The CPLEX convention explains solver termination; the Round 21 convention is a separate stable reporting metric. Neither may overwrite the raw objective or bound.

### Parameter set and readback semantics

`CPXsetdblparam` returns zero on success and nonzero on error. `CPXgetdblparam` obtains the current effective double-parameter value and likewise returns zero on success and nonzero on error.

Sources:

- `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\cpxapi\setdblparam.html`, lines 75-81 and 139.
- `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\cpxapi\getdblparam.html`, lines 75-80 and 138.

A run intended for strict certification must retain the requested value, setter return code, getter return code, and effective readback value for both IDs 2009 and 2008. A request alone is not evidence that the parameter became effective.

## Can tolerance-optimal status occur with zero requested gaps?

There are two cases to distinguish.

1. **Zero was only requested.** Status 102 can still occur if either setter failed, readback failed, or an effective value is nonzero. Therefore the requested values alone cannot establish strict semantics.
2. **Both effective readback values are exactly zero.** The installed reference ties status 102 to an unproven solution satisfying the relative or absolute MIP-gap tolerance (`CPXMIP_OPTIMAL_TOL.html`, lines 46-55). Both documented gap quantities are nonnegative and their parameter pages say that stopping occurs when the quantity falls below the parameter (`EpGap.html`, lines 135-139; `EpAGap.html`, lines 133-137). A positive gap cannot fall below zero. The status-101 page associates proven equality with status 101 (`CPXMIP_OPTIMAL.html`, lines 49-56).

The installed documentation does not separately state an unconditional API theorem that code 102 can never be emitted at effective zero/zero. The fail-closed conclusion is therefore:

- effective zero/zero eliminates documented positive-gap tolerance termination;
- strictness is still determined from the observed numeric status and retained raw values, not inferred from parameter intent;
- any observed code 102 remains `native_tolerance_optimal_only` (or `certificate_rejected` if inconsistent with its recorded parameters), even if the requested and effective gaps are zero or display formatting prints a zero gap.

## Other relevant numerical tolerances

Round 21's primary arms do not change these parameters merely to force a different status.

| Purpose | Symbol | ID | Allowed values | Default | Official semantics relevant to certificates |
|---|---|---:|---|---:|---|
| Simplex feasibility | `CPXPARAM_Simplex_Tolerances_Feasibility` | 1016 | `1e-9` through `1e-1` | `1e-6` | Allowable basic-variable bound violation. It does not relax the model's bounds or right-hand sides. |
| MIP integrality | `CPXPARAM_MIP_Tolerances_Integrality` | 2010 | `0.0` through `0.5` | `1e-5` | Amount by which an integer-variable value may differ from an integer and still be feasible. Zero is permitted, but CPLEX only attempts to meet it and roundoff may remain. |
| Simplex optimality | `CPXPARAM_Simplex_Tolerances_Optimality` | 1014 | `1e-9` through `1e-1` | `1e-6` | Reduced-cost tolerance used to decide whether a reduced cost is nonnegative for optimality. |

Header IDs: `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\cplex\include\ilcplex\cpxconst.h`, lines 2359 and 2435-2437; legacy aliases are at lines 2474-2477.

Detailed parameter references:

- Feasibility name/ID: `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\CPLEX\Parameters\topics\EpRHS.html`, lines 53-59 and 116-122. Semantics and range/default: lines 129-146. In particular, the tolerance permits a computed basic variable to violate a bound; it does not relax bounds or right-hand sides.
- Integrality name/ID: `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\CPLEX\Parameters\topics\EpInt.html`, lines 58-64 and 121-126. Semantics: lines 135-150. Lines 138-146 warn that even a zero setting is only attempted and describe roundoff plus the optimal-infeas status; range/default: lines 154-157.
- Optimality name/ID: `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\CPLEX\Parameters\topics\EpOpt.html`, lines 55-61 and 118-124. Reduced-cost semantics and range/default: lines 133-150.

## `CPXgetobjval` guarantee

`CPXgetobjval` accesses the solution objective value. Its output location receives a `double`. The routine returns zero if successful and nonzero if no solution exists.

Source: `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\cpxapi\getobjval.html`, lines 41-46, 70-76, 115-120, and 132-135.

Certificate implications:

- retain the return code separately from the value;
- a nonzero return code means the output must be treated as unavailable, not as zero or as the best bound;
- under status 107 the value is the native incumbent objective, not a proof of optimality;
- under status 108 there is no integer incumbent, so a native incumbent objective must not be fabricated;
- `CPXgetobjval` does not itself certify optimality or provide the global lower bound.

## `CPXgetbestobjval` guarantee

`CPXgetbestobjval` accesses the currently best known bound among remaining open branch-and-cut nodes. For minimization, IBM defines it as the minimum objective value among remaining unexplored nodes; for maximization, the analogous maximum. For a regular MIP optimization using `CPXmipopt`, IBM states that this is also the best known bound on the optimal MIP objective.

When the tree is empty after optimal solution, CPLEX returns its best known finite dual bound rather than an infinite empty-tree proxy. IBM explicitly warns that this value typically matches the optimal solution objective but can differ depending on how optimality was determined. Thus even a code-101 result does not authorize replacing the raw returned bound with the incumbent objective.

For a MIP the routine always returns a value, even if no solution information has yet been computed. Its no-information convention is negative infinity for minimization and positive infinity for maximization. The routine's return code is zero on success and nonzero on error.

In the installed callable-library constants, `CPX_INFBOUND` is `1.0E+20`, and any bound larger in magnitude is treated as infinity. The Round 21 capture layer therefore preserves the raw getter outcome but does not mark a value with magnitude at least `CPX_INFBOUND` as an available finite certificate bound. Source: `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\cplex\include\ilcplex\cpxconst.h`, lines 423-426.

Source: `C:\Program Files\IBM\ILOG\CPLEX_Studio2211\doc\html\en-US\refcallablelibrary\mipapi\getbestobjval.html`, lines 41-48, 71-106, and 161-164.

Certificate implications:

- retain the getter return code and the full-precision returned value separately;
- a zero return code alone does not make the bound usable, because the documented no-information value may be infinite;
- require a finite, directionally valid native bound before classifying a positive-gap result as `time_limit_valid_bound`;
- preserve the returned value as the serialized lower-bound source for this minimization problem;
- never silently substitute the incumbent or independently verified upper bound for the native lower bound;
- compute native and verified gaps from retained values without altering either source value.

## Fail-closed status policy implied by the installed references

For the Round 21 original-problem certificate path:

- `101` plus native finalization/lifecycle success and an independently verified original solution is the native exact-optimal route;
- independently established native-bound/verified-upper-bound equality is a separate certificate route and must not be inferred from status 102 or display rounding;
- `102` is tolerance-only, regardless of status text formatting or a rounded printed gap;
- `107` is a time-limit result with an incumbent, not strict optimality;
- `108` is a time-limit result without an incumbent, not proof of infeasibility;
- `103` is the MIP infeasibility status;
- missing/error/nonfinite best-bound output makes the native bound unavailable;
- status-code/text inconsistency, gap-parameter set/readback failure, verifier failure, or incomplete lifecycle causes strict certification to fail closed.

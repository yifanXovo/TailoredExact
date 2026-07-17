# Round 21 certificate-discrepancy root-cause analysis

## Scope and evidence boundary

This report analyzes the strict-certificate discrepancy only. It uses the installed-CPLEX semantics in [cplex_strict_status_and_gap_semantics.md](cplex_strict_status_and_gap_semantics.md), the executable policy in [strict_certificate_policy.md](strict_certificate_policy.md), the no-rerun Round 20 audit in [historical_certificate_reclassification.csv](historical_certificate_reclassification.csv), and fresh Stage 0--2 records in [native_gap_and_status_audit.csv](native_gap_and_status_audit.csv). The fresh records were produced by the frozen executable whose SHA-256 is `dfd67bcf4e4dd19cf7096bf5fa16c100d5a6ccefd3bb6df8a30547de39f7136a`.

Stage 3 has no V12 case, so it cannot change the V12 certificate conclusions below. This report does not reinterpret a CPLEX floating-point proof as an arbitrary-precision rational proof, and it does not infer missing historical parameter readbacks.

## Conclusion

The certificate discrepancy has two distinct causes.

1. The Round 20 false zero-gap presentation was a project-side status-classification and serialization defect. The pre-hardening code treated any status text containing `optimal` as optimal, so native status 102 text (`integer optimal, tolerance`) entered the same path as status 101. It then accepted native-bound/verified-objective differences up to a project `1e-6` scale tolerance, replaced the native lower bound with the verified objective, set both bounds equal, and emitted `gap=0`. Twelve-digit JSON formatting hid additional low-order detail. CPLEX itself had retained and reported positive native gaps in the three affected rows.
2. The fresh Round 21 status-101 rejections are a separate, intentional fail-closed outcome. In those rows CPLEX reports status 101, its native objective equals its native best bound, and `CPXgetmiprelgap` is zero; however, the independently reconstructed original objective differs from that bound by a small positive residual or lies slightly below it. Round 21 preserves both values and rejects the project-level original-problem certificate because exact retained-value equality is not established. This is an objective-mapping/representation closure limitation, not a tolerance-status misclassification and not evidence that CPLEX returned status 102.

Of the four audited Round 20 V12 rows, three former public `gap=0` rows are reclassified `tolerance_only`; the fourth is only a `historical_strict_candidate`, not a hardened Round 21 certificate. Among the 13 fresh V12 rows through Stage 2, two obtain `native_exact_optimal` certificates, both on V12_M1 (`stage2 F0` and `stage2 plain`). No fresh V12_M2 row is strictly certified.

## Exact status versus tolerance status

The installed CPLEX 22.1.1 headers and local reference distinguish the relevant codes:

| Code | Symbol | Certificate meaning used here |
|---:|---|---|
| 101 | `CPXMIP_OPTIMAL` | CPLEX reports a proved optimal integer solution under its documented numerical semantics. It may enter the native exact route, but Round 21 still requires all parameter, lifecycle, raw-value, native-gap, and original-solution verification gates. |
| 102 | `CPXMIP_OPTIMAL_TOL` | The solution has not been proved optimal and is within the relative or absolute MIP-gap tolerance. Without a separately named proof module, it is tolerance-only even if a displayed gap is zero. |
| 107 | `CPXMIP_TIME_LIM_FEAS` | Time limit with a native incumbent; a retained finite native bound remains useful, but the result is not strict. |
| 108 | `CPXMIP_TIME_LIM_INFEAS` | Time limit without a native integer incumbent; it is neither strict optimality nor proof of infeasibility. |
| 103 | `CPXMIP_INFEASIBLE` | Native integer infeasibility, distinct from status 108 and from an optimal-solution certificate. |

The relative MIP-gap parameter is ID 2009 and the absolute MIP-gap parameter is ID 2008. Setting only relative gap zero is insufficient because the installed default absolute gap is `1e-6`. For every one of the 59 fresh Stage 0--2 rows, both IDs are recorded, both requested values are exactly zero, both setter return codes are zero, both getter return codes are zero, and both effective readbacks are exactly zero. All 59 also have consistent status code/text, completed lifecycle/finalization, `lower_bound_matches_native=True`, and `serialized_gap_consistent=True`.

No fresh Stage 0--2 row returned status 102. That observation is not promoted to a theorem that status 102 can never occur at effective zero/zero: the policy classifies the status actually returned and would keep any future code-102 row non-strict absent a separately audited proof module.

## Round 20 source-level failure chain

The pre-hardening source snapshot at `239d82772161acf7b86353fcfc8b7c3fc9f39e1f` makes the historical behavior reproducible:

- `src/TailoredBCCplexApi.cpp` defined relative-gap ID 2009 and set it to `1e-8` in the global-tree solve. It did not configure absolute-gap ID 2008, so under the installed defaults the positive `1e-6` absolute tolerance remained. The global-tree path did not retain set/readback evidence for both parameters.
- `statusIsOptimal` in `src/CplexBaseline.cpp` returned true whenever the status text contained `optimal`; it did not distinguish code 101 from text containing `optimal, tolerance`.
- The global-tree acceptance path used `statusIsOptimal(api.status)` and accepted `abs(U_verified-L_native) <= 1e-6 * max(1, abs(U_verified), abs(L_native))`.
- On acceptance, that path assigned `lower_bound=objective`, `upper_bound=objective`, and `gap=0.0`, discarding the native best bound as the public lower-bound source.
- `src/Result.cpp` serialized doubles with precision 12, which further collapsed visible low-order differences.

The retained historical numbers are consistent with absolute-gap tolerance termination: each of the three status-102 rows has an absolute native gap below `1e-6`, while its audit-derived CPLEX-denominator relative gap is above the source-requested `1e-8`. Because Round 20 did not retain the effective readback of either parameter, this is strong source-and-data evidence for the mechanism, not a retroactive per-run readback proof.

### Historical V12 reclassification

| Round 20 row | Native code | Retained native incumbent | Retained native best bound | Absolute native gap | Public Round 20 LB / UB / gap | Hardened historical class |
|---|---:|---:|---:|---:|---|---|
| V12_M1 baseline | 102 | 0.35720058320768794 | 0.35719986149047245 | 7.2171721549e-7 | 0.357200583208 / 0.357200583208 / 0 | `tolerance_only` |
| V12_M1 root flow | 102 | 0.35720058320768378 | 0.35720026683430645 | 3.1637337733e-7 | 0.357200583208 / 0.357200583208 / 0 | `tolerance_only` |
| V12_M2 baseline | 101 | 0.71850407075533274 | 0.71850407075533274 | 0 | 0.718504070755 / 0.718504070755 / 0 | `historical_strict_candidate` |
| V12_M2 root flow | 102 | 0.71850407075532763 | 0.71850361622922809 | 4.5452609954e-7 | 0.718504070755 / 0.718504070755 / 0 | `tolerance_only` |

The one status-101 row is not promoted to a Round 21 certificate because the historical schema omitted the two parameter set/readback records and the native status/objective/best-bound/gap API return-code evidence now required. Missing evidence is not reconstructed from a rounded JSON value.

## Hardened data path and why it fails closed

The current official plain and global-tree paths share `classifyStrictCertificate` in `src/StrictCertificate.cpp`. `src/CplexBaseline.cpp` stores the successful raw `CPXgetbestobjval` value directly in `lower_bound`; `src/Result.cpp` uses round-trip-safe `max_digits10` output. The classifier retains three distinct quantities:

```text
U_native    = CPXgetobjval
L_native    = CPXgetbestobjval
U_verified  = independently reconstructed original objective
```

For reporting it computes `max(0, U-L)`, but it also retains the signed residual and an explicit inversion flag. Therefore a clamped zero is not an equality test. The native status-101 route requires all of the following to be exact in the retained doubles: native `CPXgetmiprelgap == 0`, `U_native-L_native == 0` with no inversion, and `U_verified-L_native == 0` with no inversion. No project epsilon can close either residual.

The production verifier does have a separate `1e-8 * scale` check between the reconstructed candidate objective and `CPXgetobjval`. That check establishes that the decoded solution maps consistently enough to be verified; it does not establish lower-bound equality and cannot make a certificate strict. There is no production objective-lattice, exact-rational separation, bound-equality, or independent exact-certificate module that can bridge a nonzero residual.

This separation is why the fresh evidence can honestly say both of the following:

- CPLEX returned code 101 with zero native objective/best-bound residual and zero native CPLEX gap.
- The project did not certify the original problem because its independently reconstructed upper bound was not exactly equal to the preserved native bound.

## Fresh V12 outcomes through Stage 2

`r = U_verified-L_native` below is signed. `gap` is the serialized project-relative gap based on the preserved lower bound and verified upper bound. A status-108 row has no native incumbent even when a separate same-run verified heuristic upper bound is available.

| Run | Code | Class | Strict | `L_native` | `r` | Serialized gap |
|---|---:|---|:---:|---:|---:|---:|
| Stage0 V12_M1 F2, 30 s | 108 | `time_limit_valid_bound` | no | 0.3296291876604862 | 2.757139554792931e-2 | 7.718743149935522e-2 |
| Stage0 V12_M2 F2, 30 s | 108 | `time_limit_valid_bound` | no | 0.6653107250513270 | 5.319334570364387e-2 | 7.403346462289456e-2 |
| Stage1 V12_M2 F0, 300 s | 101 | `certificate_rejected` | no | 0.7185040707549651 | 5.773159728050814e-15 | 8.034971495686369e-15 |
| Stage1 V12_M2 F1, 300 s | 107 | `time_limit_valid_bound` | no | 0.7164002762715835 | 2.103794483387378e-3 | 2.928020270193887e-3 |
| Stage1 V12_M2 F2, 300 s | 108 | `time_limit_valid_bound` | no | 0.7091473669724021 | 9.356703782568810e-3 | 1.302247845685442e-2 |
| Stage1 V12_M2 F3, 300 s | 108 | `time_limit_valid_bound` | no | 0.7062257728245096 | 1.227829793046131e-2 | 1.708869640440568e-2 |
| Stage1 V12_M2 off, 300 s | 108 | `time_limit_valid_bound` | no | 0.7081037277152368 | 1.040034303973414e-2 | 1.447499528959654e-2 |
| Stage2 V12_M1 F0, 900 s | 101 | `native_exact_optimal` | yes | 0.3572005832084155 | 0 | 0 |
| Stage2 V12_M1 F3, 900 s | 101 | `certificate_rejected` | no | 0.3572005832084154 | 1.110223024625157e-16 | 3.108122093903122e-16 |
| Stage2 V12_M1 plain, 900 s | 101 | `native_exact_optimal` | yes | 0.3572005832084155 | 0 | 0 |
| Stage2 V12_M2 F0, 900 s | 101 | `certificate_rejected` | no | 0.7185040707549651 | 5.773159728050814e-15 | 8.034971495686369e-15 |
| Stage2 V12_M2 F3, 900 s | 101 | `certificate_rejected` | no | 0.7185040707549712 | -3.330669073875470e-16 | 0 |
| Stage2 V12_M2 plain, 900 s | 107 | `time_limit_valid_bound` | no | 0.5866640018892041 | 1.318400688657668e-1 | 1.834924452511944e-1 |

The four rejected status-101 rows all record native objective equal to native best bound and native `CPXgetmiprelgap=0`. Their common rejection reason is `exact_status_native_bound_not_equal_verified_upper_bound`:

- Stage1 and Stage2 V12_M2 F0 retain the same positive verified residual, `5.773159728050814e-15`.
- Stage2 V12_M1 F3 retains a positive residual of `1.1102230246251565e-16`.
- Stage2 V12_M2 F3 retains a negative residual of `-3.3306690738754696e-16`; `L_native > U_verified`, so `verified_bound_inversion=True`. Its reporting gap is zero only because reporting clamps a negative numerator, while the inversion gate independently rejects the certificate.

These last-bit differences are compatible with a floating-point model/objective reconstruction boundary, but the retained evidence does not isolate one arithmetic operation as their cause. They do not establish a different mathematical optimum, nor may they be discarded as harmless: without an audited exact-rational or bound-equality module, treating them as equality would recreate an arbitrary project tolerance.

## Implications of the former `gap=0` rows

- Three Round 20 V12 rows formerly presented as zero-gap optimal results are tolerance-only. They must not count toward strict-certificate totals or time-to-strict-certificate claims.
- Their independently verified incumbents remain evidence of feasible upper bounds, and their retained native best bounds remain useful finite lower-bound evidence. The invalid part is the strict closure claim and the public replacement of those bounds, not the existence of the incumbent or bound.
- The Round 20 V12_M2 baseline remains a historical candidate only. A fresh run is required because the missing strict-parameter and native-getter evidence cannot be recovered by assumption.
- A serialized numeric zero is never sufficient evidence by itself. The fresh V12_M2 F3 row deliberately demonstrates why: its clamped gap is zero, but its signed residual is negative and its inversion flag rejects strict certification.
- Fresh V12_M1 F0 and plain results demonstrate the positive case: code 101, exact zero parameter readbacks, complete lifecycle, verifier pass, raw native gap zero, and exact retained equality all coincide.
- No raw native lower bound is overwritten in the fresh Stage 0--2 package: all 59 rows preserve `serialized_lower_bound == L_native`. No lower bound is rounded upward to manufacture equality.

## Root-cause classification

| Component | Classification | Evidence strength | Finding |
|---|---|---|---|
| Round 20 CPLEX stopping configuration | Incomplete strict configuration | Strong, but historical effective readbacks are absent | Relative gap was requested as `1e-8`; absolute gap was not set and the installed default is `1e-6`. The three positive absolute gaps are below `1e-6` and their relative gaps exceed `1e-8`, matching absolute-tolerance status 102. This is not a CPLEX defect. |
| Round 20 status interpretation | Definitive semantic bug | Source-proven and data-matched | Substring matching collapsed status 102 text into the status-101 path. |
| Round 20 acceptance rule | Definitive certificate-policy bug | Source-proven and data-matched | A `1e-6 * scale` project tolerance was treated as closure even though no exact/lattice proof existed. |
| Round 20 serialization | Definitive provenance bug | Source-proven and data-matched | The native lower bound was replaced by the objective, gap was forced to zero, and precision 12 obscured low-order differences. |
| Round 20 evidence schema | Definitive auditability gap | Historical audit | Both gap-parameter set/readbacks and native getter return codes were not retained, preventing hardened retroactive certification. |
| Fresh rejected status-101 rows | Fail-closed original-objective mapping limitation | Direct raw evidence; exact arithmetic origin unresolved | Native closure is internally zero, but the preserved native bound and independently reconstructed original upper bound differ at retained-double precision or invert. No production proof module closes that boundary. |

Overall, the historical discrepancy is classified as a mixed project-side status-semantics, acceptance, serialization, and evidence-contract failure, enabled by a non-strict solver gap configuration. The fresh discrepancies are not repetitions of that defect: they are correctly exposed floating-point mapping residuals that the hardened policy refuses to erase. The supported remedy is the implemented one--numeric status handling, exact zero set/readback for both gap parameters, raw native-bound preservation, round-trip-safe serialization, signed residual/inversion retention, and fail-closed classification--not another numerical epsilon.


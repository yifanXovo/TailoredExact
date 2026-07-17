# Round 21 final report: strict certificates and normalized root flow

## Executive conclusion

Round 21 achieved the certificate-hardening objective and proved the
mathematical validity of all four connectivity-flow variants. It did **not**
justify making normalized root flow the default.

The strict policy now distinguishes CPLEX status 101 (exact optimality) from
status 102 (optimal within tolerance), sets and reads back both native gap
parameters at zero, preserves `CPXgetbestobjval` as the lower bound, retains
signed residuals and inversions, and never uses display rounding or a project
epsilon as an exact proof. Across 80 fresh official rows, 7 are
`native_exact_optimal`, 6 are fail-closed `certificate_rejected`, and 67 are
positive-gap `time_limit_valid_bound`; no fresh row returned status 102. All
80 preserve the raw native lower bound and all 80 serialize a gap consistent
with their retained bounds.

The normalized-start-coupled variant F3 was selected using Stage 1 only. On
`moderate_seed3301`, it almost exactly recovers the no-flow 300-second lower
bound and increasingly outperforms F0 through 3,600 seconds. At one hour its
native lower bound is `0.047358383204777726`, versus
`0.04645929906778639` for F0 and `0.04096078249212643` for plain CPLEX.
Nevertheless, F3 loses to F0 on three of the six V20 cases in the 900-second
matrix and on three of five cases at 1,800 seconds. It therefore remains an
explicit optional research variant. F0, F1, F2, F3, and no-flow remain
available; there is no instance-dependent activation.

The two root-cause classifications are separate:

- The Round 20 certificate discrepancy was a **project-side mixed status,
  stopping-configuration, acceptance, serialization, and evidence-contract
  failure**. It was not a CPLEX defect. Three status-102 rows had positive
  native gaps that the wrapper replaced with public bound equality.
- The `moderate_seed3301` regression is a **mixed mechanism**, dominated by
  the formulation-strength/throughput trade-off and simplex work per node.
  F0's depot-cycle circulation face is real and unusually wide, but removing
  return flow alone does not recover performance. F3 recovers it through
  start coupling and a better downstream LP/search path.

## Evidence ledger, run counts, and reproducibility

All official rows use the frozen release executable with SHA-256
`dfd67bcf4e4dd19cf7096bf5fa16c100d5a6ccefd3bb6df8a30547de39f7136a`.
The branch is `codex/round21-strict-certificate-normalized-flow`. Runs were
serial, one-threaded, and continuous at each horizon, with finalization reserve
inside the nominal wall budget.

Five plain-wrapper process walls finished slightly beyond their nominal label
despite bounded native deadlines and reserved finalization: the 900-second
`moderate_seed3301` and `moderate_seed3302` rows exceeded by 0.320 and 2.570
seconds (native deadline 882 seconds), the corresponding 1,800-second rows by
0.599 and 2.368 seconds (native deadline 1,770 seconds), and the 3,600-second
`moderate_seed3301` row by 3.460 seconds (native deadline 3,570 seconds). All
are within the runner's explicit 1% process allowance; no native limit exceeded
3,570 seconds and there was no unbounded shutdown. The maximum nominal budget
remained 3,600 seconds. This is an engineering timing caveat, not an extra
optimization interval.

| Stage | Design | Official rows | Status 101 / 107 / 108 | Strict / rejected / valid positive-gap |
|---|---|---:|---:|---:|
| 0 | Five exact V2 toy arms plus five 30-second F2 integration gates | 10 | 5 / 0 / 5 | 5 / 0 / 5 |
| 1 | Five instances x off/F0/F1/F2/F3 at 300 seconds | 25 | 1 / 1 / 23 | 0 / 1 / 24 |
| 2 | Eight instances x F0/F3/plain at 900 seconds | 24 | 5 / 7 / 12 | 2 / 3 / 19 |
| 3 | Five instances x F0/F3/plain at 1,800 seconds | 15 | 0 / 5 / 10 | 0 / 0 / 15 |
| 4 | `moderate_seed3301` and V12_M2 x F0/F3/plain at 3,600 seconds | 6 | 2 / 2 / 2 | 0 / 2 / 4 |
| **Total** |  | **80** | **13 / 15 / 52** | **7 / 6 / 67** |

The 67 valid time-limit rows all have a strictly positive serialized project
gap (range `0.002928020270193887` to `0.8969892551895279`). No time-limit
row is strict. The 13 status-101 rows split into 7 exact certificates and 6
rejections; a native status alone is no longer enough.

Stage 0 ran eight test commands successfully. The five C++ suites report
10 strict-certificate groups, 6 flow groups, 3 serialization groups, 8 global
tree groups, and 30 scheduler groups; the Round 20 Python regression suite
adds 6 groups, for 63 reported deterministic groups. The static audit is
29/29 PASS, the flow projection/dominance audit is 43/43 pass, the final
exactness audit is 13/13 PASS, and the active-run validator is 80/80 PASS.
The largest retained commit artifact is 11,404,998 bytes, below the package's
94,371,840-byte safe limit. See [exactness_audit.csv](exactness_audit.csv),
[flow_projection_and_dominance_audit.csv](flow_projection_and_dominance_audit.csv),
and the `audits/` directory.

## Mathematical validity

For an integral elementary route
`0=v_0,v_1,...,v_s,v_{s+1}=0`, the canonical connectivity flow is

\[
f_{v_t v_{t+1}}=s-t,\qquad t=0,\ldots,s,
\]

so the return flow is zero. The station balances consume one unit each, the
depot supplies `s`, and every value respects the universal bounds. In F0,
adding the same `c` to all used route arcs preserves all balances for
`0 <= c <= V-s`; this is the avoidable depot-cycle coordinate. F1 deletes the
return columns and makes the fixed-route canonical lift unique. F2 adds valid
`f>=x` links into stations and tightens internal upper bounds to `V-1`. F3
adds the linear departure/visit-count coupling. Thus

\[
Q_{F3}\subseteq Q_{F2}\subseteq Q_{F1}\hookrightarrow Q_{F0},
\]

while every original integral route has a lift in every variant. No tighter
instance-specific visit bound was used. The universal `V` and `V-1` bounds
remain.

Exhaustive enumeration covered every elementary route for V=1,2,3,4,
including 2, 5, 16, and 65 routes respectively, plus unused-vehicle,
one-station, full-route, balance, link, and dominance checks. The exact V2 toy
objective is zero and is strictly certified under off, F0, F1, F2, and F3.
For V=20 and M=3, the extensions are:

| Variant | Flow columns | Flow rows | Flow nonzeros |
|---|---:|---:|---:|
| F0 | 1,260 | 1,323 | 5,160 |
| F1 | 1,200 | 1,263 | 4,920 |
| F2 | 1,200 | 2,463 | 7,320 |
| F3 | 1,200 | 2,583 | 9,900 |

The source scans find no seed, instance name, V12/V20 switch, scale tier,
route-mask enumeration, restricted pool, or production auxiliary solve in the
normalized formulation. The complete proof is in
[root_connectivity_flow_normalization_proof.md](root_connectivity_flow_normalization_proof.md).

## CPLEX certificate semantics

The installed CPLEX 22.1.1 meanings used by the policy are:

| Code | Symbol | Meaning and Round 21 treatment |
|---:|---|---|
| 101 | `CPXMIP_OPTIMAL` | CPLEX proved an optimal integer solution; it is only a strict candidate until every parameter, lifecycle, raw-gap, and original-verifier gate passes. |
| 102 | `CPXMIP_OPTIMAL_TOL` | Not proved optimal; within relative or absolute gap tolerance. Never strict by status alone. |
| 103 | `CPXMIP_INFEASIBLE` | Integer infeasible, distinct from time limit without an incumbent. |
| 107 | `CPXMIP_TIME_LIM_FEAS` | Time limit with native incumbent; may retain a valid bound, never strict at positive gap. |
| 108 | `CPXMIP_TIME_LIM_INFEAS` | Time limit without a native integer incumbent; the suffix does not prove infeasibility. |
| 115 | `CPXMIP_OPTIMAL_INFEAS` | Optimal with unscaled infeasibilities; rejected as a clean strict certificate. |

The relative gap parameter is ID 2009, allowed in `[0,1]`, default `1e-4`.
The absolute gap parameter is ID 2008, allowed for all nonnegative values,
default `1e-6`. Every fresh row requested zero for both, obtained setter and
getter return code zero for both, and read back exactly zero for both: 80/80
successful round trips. The installed documentation does not offer an
unconditional theorem that code 102 can never appear at effective zero/zero,
so any future code-102 row still fails closed. See
[cplex_strict_status_and_gap_semantics.md](cplex_strict_status_and_gap_semantics.md).

## Gap conventions and retained bounds

For a valid lower bound `L` and upper bound `U`, this package keeps the
absolute residual `d=max(0,U-L)` and reports both:

\[
g_{\max 1}=d/\max(1,|U|),\qquad
g_{\mathrm{project}}=d/|U|.
\]

The second is undefined at a zero nonclosed denominator and is only emitted
under the documented zero/positive-denominator rules. The serialized
top-level `gap` uses the project denominator; checkpoint and threshold traces
use `g_max1`. For native stopping diagnostics, the package also records the
installed CPLEX-style denominator `1e-10+|U_native|`. These quantities are
never conflated.

This distinction matters for `moderate_seed3301`, where the verified Tailored
upper bound is `0.04915255266474515`. F3 at 3,600 seconds has residual and
`g_max1` `0.0017941694599674235` (0.179417%), while its project gap is
3.650206%. F0's corresponding values are `0.00269325359695876` (0.269325%)
and 5.479377%; plain CPLEX's are `0.01316866642631998` (1.316867%) and
24.328100%.

All 80 fresh rows satisfy `serialized_lower_bound == native_best_bound` at
round-trip precision and pass the serialized-gap recomputation. Reporting
clamps a negative numerator to zero but separately retains the signed residual
and inversion flag, so a displayed zero cannot prove equality.

## Strict certificates, tolerance-only outcomes, and valid bounds

The 7 fresh strict certificates are the five V2 toy arms and the Stage 2
V12_M1 F0 and plain rows. V12_M1 F0 becomes strict at 123.0761028 seconds;
plain CPLEX becomes strict at 618.7442733 seconds. F0 therefore obtains the
matched strict certificate 495.6681705 seconds sooner. F3 does not obtain a
strict V12 certificate.

There are 16 fresh V12 rows: 2 strict, 6 rejected, and 8 valid time-limit
bounds. The two strict rows both solve V12_M1 at 900 seconds with exact
retained equality `L=U=0.3572005832084155`. The key fail-closed rows are:

- V12_M1 F3 at 900 seconds: status 101, but
  `U_verified-L_native=1.1102230246251565e-16`; rejected.
- V12_M2 F0 at 300, 900, and 3,600 seconds: status 101, but the retained
  residual is `5.773159728050814e-15`; rejected each time.
- V12_M2 F3 at 900 and 3,600 seconds: status 101, but the signed residual is
  `-3.3306690738754696e-16`, an explicit bound inversion; the reporting gap is
  clamped to zero but the certificate is rejected.

No fresh row is `native_tolerance_optimal_only` because no fresh row returned
status 102. Historically, however, three of four Round 20 zero-gap V12 rows
are tolerance-only:

| Historical row | Code | Native incumbent | Native best bound | Absolute gap | Round 21 class |
|---|---:|---:|---:|---:|---|
| V12_M1 baseline | 102 | 0.35720058320768794 | 0.35719986149047245 | `7.2171721549e-7` | tolerance-only |
| V12_M1 F0 | 102 | 0.35720058320768378 | 0.35720026683430645 | `3.1637337733e-7` | tolerance-only |
| V12_M2 baseline | 101 | 0.71850407075533274 | 0.71850407075533274 | 0 | historical strict candidate only |
| V12_M2 F0 | 102 | 0.71850407075532763 | 0.71850361622922809 | `4.5452609954e-7` | tolerance-only |

All four historical public files serialized equal LB/UB and gap zero. The
three positive-gap rows therefore lose their former strict claim. The one
code-101 row remains only a candidate because Round 20 did not retain both
gap-parameter set/readbacks and all native getter return codes. Historical
JSON was not rewritten. See
[historical_certificate_reclassification.csv](historical_certificate_reclassification.csv)
and [native_gap_and_status_audit.csv](native_gap_and_status_audit.csv).

## Certificate-discrepancy root cause

Round 20 requested relative gap `1e-8` but did not set the absolute gap, whose
installed default is `1e-6`. Its wrapper then matched the word `optimal` in
status text, collapsing status 102 into the status-101 path. It accepted
native-bound/verified-objective differences under a project `1e-6` scale
tolerance, replaced the native LB with the verified objective, forced gap
zero, and serialized with 12-digit precision. The three affected absolute
gaps are below `1e-6`, matching the status-102 mechanism.

The fresh status-101 rejections are different. CPLEX's native objective,
native bound, and native reported gap close internally, but the independently
reconstructed original objective differs in the last retained bits or lies
slightly below the native bound. Round 21 exposes rather than erases this
mapping boundary. No production exact-rational, objective-lattice,
bound-equality, or independent exact-certificate module exists, so no epsilon
may bridge it. The detailed classification is in
[certificate_discrepancy_root_cause.md](certificate_discrepancy_root_cause.md).

## Direct degeneracy evidence

The diagnostic-only solves hold the original objective on the same F0
root-optimal face within `1e-9` and vary only auxiliary flow. They never feed a
production bound or certificate.

| Instance | Return-flow min / max / range | Total-flow min / max / range |
|---|---:|---:|
| `moderate_seed3301` | 0 / 52.14171823360466 / 52.14171823360466 | 7.858281766397566 / 429.21499139586626 / 421.3567096294687 |
| `tight_T_seed3101` | 0 / `9.488776209987115e-6` / same | 24.04665373019381 / 165.4389620354449 / 141.39230830525108 |
| `high_imbalance_seed3202` | 0 / `1.3481491089040176e-6` / same | 17.293385964643253 / 123.21214528516457 / 105.91875932052132 |

The original-objective target optimizer happened to select zero return flow,
so the claim is not that its production basis necessarily carried a positive
return. The same root-optimal face nevertheless admits 52.14 units of return
flow: the maximizing solution has 16 positive return columns and maximum
return value 12.16. All 1,260 F0 flow columns have zero reduced cost in the
target's original-objective diagnostic basis, and an extreme face reaches
basis kappa about `5.68e8`. Positive return flow is therefore present on the
F0 root-optimal face and the face is exceptionally wide on the regression
target. The much smaller return ranges on the two controls make it relevant,
but not sufficient as a performance explanation. See
[flow_degeneracy_diagnostics.csv](flow_degeneracy_diagnostics.csv).

## Causal ablation on `moderate_seed3301`

All Stage 1 arms use verified UB `0.04915255266474515` and differ only in the
flow option.

| Arm | Native LB at 300 s | Project gap | Nodes | Simplex/node | Nodes/s | Post-cut root LB |
|---|---:|---:|---:|---:|---:|---:|
| off | 0.0454344348342471 | 7.564445% | 3,758 | 294.52 | 12.77 | 0.0347290398 |
| F0 | 0.04498820632518879 | 8.472289% | 2,172 | 295.49 | 7.38 | 0.0345379801 |
| F1 | 0.04459936063941346 | 9.263389% | 1,496 | 607.48 | 5.09 | 0.0344641919 |
| F2 | 0.04465179592578673 | 9.156710% | 1,549 | 676.56 | 5.27 | **0.0347725614** |
| F3 | 0.04543053543516233 | 7.572378% | 2,512 | **221.22** | **8.54** | 0.0347230454 |

F0 reproduces the Round 20 regression: its LB is
`0.00044622850905831` below no-flow. F1 removes all 60 return columns but
loses another `0.00038884568577533` versus F0 and roughly doubles simplex
work per node. F2 gives the strongest post-cut root but remains below F0 at
300 seconds; stronger root geometry does not compensate for 676.56
simplex iterations per node. F3 adds 120 start-coupling rows to F2, raises the
LB by `0.00077873950937560`, cuts simplex work per node by 67%, and raises
throughput by 62%. It finishes just `3.89939908477e-6` below no-flow while
beating F0 by `0.00044232910997354`.

The target model dimensions also reject a raw-size-only explanation. F0 has
11,925 rows, 3,378 columns, and 67,136 nonzeros; F3 has 13,185 rows, 3,318
columns, and 71,876 nonzeros. F1 is smaller and slower. Native cuts change
materially: at one hour F0 reports cover/flow/MIR/implied counts
`137/175/42/2685`, whereas F3 reports `75/43/43/1523` and still has the better
bound. The effect is a changed fractional geometry, basis and cut path—not
simply more cuts or fewer rows.

## Performance and regressions

On the regression target, F3's advantage over F0 grows with the horizon:

| Horizon | F0 LB | F3 LB | Plain LB | F3-F0 | F3 project gap | F0 project gap | Plain project gap |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 300 s | 0.04498820632518879 | 0.04543053543516233 | not run | 0.00044232910997354 | 7.572378% | 8.472289% | -- |
| 900 s | 0.04582865871585926 | 0.04644363580241004 | 0.04056839676271183 | 0.00061497708655078 | 5.511243% | 6.762404% | 24.317098% |
| 1,800 s | 0.0461521427018867 | 0.04693616279343923 | 0.040714606912686906 | 0.00078402009155253 | 4.509206% | 6.104281% | 30.446310% |
| 3,600 s | 0.04645929906778639 | 0.047358383204777726 | 0.04096078249212643 | 0.00089908413699134 | 3.650206% | 5.479377% | 24.328100% |

At one hour F3 performs 2,815,883 simplex iterations over 19,167 nodes
(146.91 per node), versus F0's 6,235,304 over 18,224 nodes (342.15 per node).
It leaves 7,185 rather than 8,517 open nodes and peaks at 1,938.18 rather than
2,270.19 MB of tree memory. This is 55% fewer total simplex iterations, 57%
fewer per node, 5% more processed nodes, 16% fewer open nodes, and 15% less
peak tree memory. Long Gini sibling delays remain and are sometimes worse
under F3, so queue interaction is a residual amplifier rather than the proven
cause of recovery.

The broader evidence is mixed. The following entries are native-LB differences
for F3 at the same horizon; positive is better.

| Instance | F3-F0 at 900 s | F3-plain at 900 s | F3-F0 at 1,800 s | F3-plain at 1,800 s |
|---|---:|---:|---:|---:|
| V12_M1 | `-1.1102230246251565e-16` | `-1.1102230246251565e-16` | -- | -- |
| V12_M2 | `6.106226635438361e-15` | 0.13184006886576716 | -- | -- |
| `high_imbalance_seed3201` | 0.007248608570725512 | 0.3160639450362619 | -- | -- |
| `high_imbalance_seed3202` | -0.011818427444283852 | 0.6034785885719174 | -0.0091366137303317 | 0.5958822501081411 |
| `moderate_seed3301` | 0.0006149770865507762 | 0.005875239039698207 | 0.0007840200915525258 | 0.006221555880752322 |
| `moderate_seed3302` | 0.0005713969842661148 | 0.020455207158493374 | 0.0026301752506657228 | 0.02312225099253036 |
| `tight_T_seed3101` | -0.0008732330841247776 | 0.02912775071410393 | -0.0005058338518676708 | 0.02955792226571208 |
| `tight_T_seed3102` | -0.0013013349034868282 | 0.22917821548483253 | -0.004517279589557832 | 0.22772221052149721 |

At 900 seconds F3 is strictly above plain CPLEX on seven cases and reaches
the same original V12_M1 optimum to the last-bit mapping boundary on the
eighth; at 1,800 seconds it is strictly above plain on all five cases. Against
F0, however, F3 improves three and regresses three V20 cases at 900 seconds,
then improves two and regresses three at 1,800 seconds. The Round 20 advantage
over plain CPLEX is broadly preserved, but F0's gains are not uniformly
preserved. This is why target recovery is not enough for promotion.

All target horizon endpoints remain valid positive-gap bounds. The Tailored
rows have status 108 and use the separately verified original incumbent only
as a valid UB; they do not invent a native incumbent. Plain rows have status
107. No target time to gap zero is inferred.

## Blockers and excluded engineering attempts

There is no active exactness, lifecycle, run-validation, or artifact-size
blocker: every official gate passes. The remaining blockers are scientific:

- no exact-rational or named independent proof module bridges the fresh V12_M2
  retained-double mapping residuals;
- F3's mixed control behavior fails broad non-regression and gain-preservation
  criteria;
- no target or V12_M2 row obtains strict closure by 3,600 seconds;
- plain CPLEX's final callable result does not retain an exact final simplex
  count, so its displayed log counter is kept as log evidence rather than
  treated as an API endpoint metric;
- the existing eight instances are not a held-out generalization suite.

Four pre-freeze engineering directories remain visible under `stage0/` but
are excluded from every fresh table: an initial mixed-object ABI heap failure,
its debugger reproduction, a successful rebuild smoke test predating the
final signed-gap policy, and a successful global F2 smoke test predating the
frozen executable and authoritative dimension reporting. The clean rebuild
and official runner validate 10/10 Stage 0 rows. No excluded attempt enters
the 80-row count.

## Promotion decision

F3 is **selected for analysis but not promoted**. It passes mathematical,
certificate, source, lifecycle, and target-recovery gates and beats plain
CPLEX on valid LB convergence. It fails the promotion rule requiring broad
900-second non-regression and preservation of the major F0 control gains; it
also produces no fresh strict V12 certificate of its own. Normalized root flow
therefore remains optional. F3 is not rejected as invalid—the proof and toy
optima are exact—but it is not a default candidate on the present evidence.

## Required causal questions: explicit answers

1. **What codes mean exact and tolerance optimality?** Code 101,
   `CPXMIP_OPTIMAL`, is the native exact-optimal candidate. Code 102,
   `CPXMIP_OPTIMAL_TOL`, is unproved tolerance optimality and is never strict
   by itself.
2. **Were both gap parameters set and read back at zero?** Yes: relative ID
   2009 and absolute ID 2008 have requested/set/get/effective zero in all
   80/80 fresh rows.
3. **How are Round 20 V12 rows reclassified?** Three status-102 zero-gap rows
   become tolerance-only; the status-101 V12_M2 baseline is merely a
   historical strict candidate because required readback/getter evidence is
   missing.
4. **Does a fresh V12 run obtain a strict native certificate?** Yes. Stage 2
   V12_M1 F0 and plain are strict at objective `0.3572005832084155`. No fresh
   V12_M2 or F3 row is strict.
5. **Is any raw native LB overwritten or rounded upward?** No. All 80 fresh
   rows preserve `CPXgetbestobjval` exactly at round-trip precision.
6. **How many former gap-zero rows become tolerance-only?** Three of the four
   audited Round 20 rows.
7. **Does F0 exhibit positive return flow at the root relaxation?** Yes on the
   target's root-optimal face: the maximum is 52.14171823360466. The particular
   original-objective optimizer selected zero, which is reported rather than
   hidden.
8. **How wide is the forensic auxiliary face?** On `moderate_seed3301`, the
   return-flow range is 52.14171823360466 and total-flow range is
   421.3567096294687. The matched return ranges are only
   `9.488776209987115e-6` and `1.3481491089040176e-6` on the two controls.
9. **Does F1 eliminate the proved circulation freedom?** Yes. Deleting return
   columns and using the direct depot equation removes the fixed-route
   depot-cycle coordinate; it does not claim to eliminate every fractional
   multi-arc cycle.
10. **Does F2 dominate F1 while preserving every route?** Yes. F2 adds valid
    lower links and tighter internal upper links, so `Q_F2` is a subset of
    `Q_F1`, and exhaustive V=1..4 projections preserve every original route.
11. **Does F3 add measurable strength?** Not as a universally better post-cut
    root bound: on the target F2 is best (`0.0347725614`) and F3 is
    `0.0347230454`. F3 does add measurable finite-search strength/throughput:
    it beats F2's 300-second LB by `0.00077873950937560` with 67% fewer
    simplex iterations per node.
12. **Which variant gives the best root bound?** F2 on the regression target.
    Root winners vary by instance; no variant is universally strongest.
13. **Which gives the best bound per unit wall time?** Among flow variants on
    the target, F3. At 300 seconds no-flow is still higher by only
    `3.89939908477e-6`; from 900 through 3,600 seconds F3 increasingly beats
    F0. There is no universal five-instance winner.
14. **Which gives the lowest simplex iterations per node?** F3 on the target:
    221.22 at 300 seconds and 146.91 at one hour, versus F0's 295.49 and
    342.15. It is also below the 300-second no-flow value 294.52.
15. **Why did Round 20 F0 regress on `moderate_seed3301`?** A mixed mechanism:
    an unusually wide degenerate flow face contributes, but the dominant
    finite-time effects are formulation strength versus throughput and LP
    simplex work per node, mediated by changed cuts and amplified by queue
    delays.
16. **Does zero-return alone recover it?** No. F1 is worse than F0 at 300
    seconds (`0.04459936063941346` versus `0.04498820632518879`).
17. **Do lower links and tighter upper bounds help?** They strengthen the
    target root under F2 but harm finite-time convergence: F2 ends at
    `0.04465179592578673` and reaches 676.56 simplex iterations per node.
18. **Are changes degeneracy, cuts, or model size?** Mixed. Degeneracy is real;
    cut families change and mediate the path; raw size is not sufficient
    because larger-row F3 wins while smaller F1 loses. Simplex work and the
    strength/throughput trade-off are the strongest measured causes.
19. **Are Round 20 gains on other V20 instances preserved?** Relative to plain
    CPLEX, yes broadly. Relative to F0, no: F3 improves 3/6 and regresses 3/6
    V20 cases at 900 seconds, then improves 2/5 and regresses 3/5 at 1,800.
20. **Does selected F3 beat plain at 900 and 1,800 seconds?** By valid native
    LB, it is strictly higher on 7/8 at 900. On V12_M1 it is lower by only
    `1.11e-16` and has the same verified original optimum, but its positive
    residual is correctly rejected rather than called a tie certificate. It is
    strictly higher on 5/5 at 1,800.
21. **Does any run reach strict gap zero sooner than plain?** Yes: V12_M1 F0
    is strict at 123.0761028 seconds versus plain at 618.7442733. No selected
    F3 row reaches strict closure.
22. **Default, optional, or rejected?** Optional. F3 is valid and useful on the
    regression target but fails broad non-regression, so it is not promoted
    and is not mathematically rejected.
23. **What is the next task?** Further unified formulation/throughput work is
    first, with queue-order behavior as a preregistered causal sub-experiment.
    Held-out validation should follow only after a candidate is stabilized;
    testing the current mixed arm on a large held-out suite would be premature.

## Next recommended round

The next round should seek a uniform formulation/throughput improvement that
retains F3's target recovery without losing F0's high-imbalance and tight-T
controls. It should isolate start coupling, node-LP basis reuse, native cut
mix, and Gini sibling service order in small preregistered arms; it must not
introduce named-instance activation. Queue-order optimization is a justified
secondary causal arm because long sibling delays remain, but the evidence does
not support calling queue order the primary Round 21 cause.

Only after that candidate is stable should a preregistered held-out random
suite test generalization and default promotion. Until then, the defensible
shipping state is the hardened certificate path plus explicit optional
off/F0/F1/F2/F3 flow controls.

Primary data sources are [native_gap_and_status_audit.csv](native_gap_and_status_audit.csv),
[flow_variant_300s_ablation.csv](flow_variant_300s_ablation.csv),
[matched_900s_comparison.csv](matched_900s_comparison.csv),
[selected_1800s_convergence.csv](selected_1800s_convergence.csv),
[conditional_3600s_convergence.csv](conditional_3600s_convergence.csv),
[time_to_strict_certificate.csv](time_to_strict_certificate.csv),
[time_to_gap_thresholds.csv](time_to_gap_thresholds.csv), and
[moderate_seed3301_root_cause.md](moderate_seed3301_root_cause.md).

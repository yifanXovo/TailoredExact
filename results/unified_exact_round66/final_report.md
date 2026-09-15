# Round66: arc-load replacement

## Decision

The replacement is mathematically admissible and implemented in the complete
K1 controller, but it is **not a qualified final unified algorithm**. It improves
D4 certificate time and C2's common-budget gap, while failing to repair the
principal D6 CitiBike proof deficit. Keep it default-off. No confirmation panel
or 3600-second expansion was opened. The overall research goal remains unmet;
the next substantive stage will investigate inventory-state representation.

Baseline: Round65 PR126, commit `112d6b26905848557048d52083d3709b46e15750`.
Branch: `codex/round66-arc-load-replacement`, published as
[draft PR127](https://github.com/yifanXovo/TailoredExact/pull/127).
All measured arms use the same
frozen Release executable, SHA256
`f0b1fba4dcebdd358a03a8a01c22872ebf12dd95398f4969797ae8e039201d2e`.
The source snapshot and build manifest identify its then-uncommitted source.

## Complete-run results

Times below include startup, model creation, every necessary solve, verification
and process exit. E7/E8 use cap120; D4 cap300. All entries in this table certified
the same original objective for the given role, under the existing numerical
standard.

| Role | P-GRB seconds | K1-R seconds | ARC seconds | Q-PLUS seconds |
|---|---:|---:|---:|---:|
| E7, V12 M2 T3600 | 1.312 | 5.766 | 5.766 | — |
| E8, V12 M3 T3600 | 1.688 | 7.359 | 7.281 | — |
| D4, V12 M3 T2400 | not rerun | 129.391 | 107.375 | 152.766 |

D4 gains 22.016 seconds (17.0%) over K1-R and 45.391 seconds (29.7%) over
Q-PLUS. This is an established protection role; its historical P-GRB comparison
is context, not a fresh same-build timing pair. The E7/E8 total-time losses
remain. Their old Round39 C6 non-startup losses do not reproduce as large current
K1 losses: current HGA accounts for most of the time. This is reclassification,
not an ARC repair. Eleven historical small CitiBike losses were separately
attributed from R58; they also largely reflect startup, with some modest
non-startup residuals. Those data are not substituted for new timing pairs.

All following entries remain uncertified. Gap means UB minus global LB, without
silently clipping numerical discrepancies. Each role has a common complete-run
cap; actual deadline exits were about cap minus the common 3-second reserve.

| Role / cap | Arm | Original UB | Global LB | Absolute gap |
|---|---|---:|---:|---:|
| D3 / 300 | K1-R | .045054162 | .043897930 | .001156231 |
| D3 / 300 | ARC | .045001550 | .044098148 | .000903402 |
| D6 / 600 | P-GRB | .157241176 | .144985883 | .012255293 |
| D6 / 600 | K1-R | .157083131 | .143249369 | .013833763 |
| D6 / 600 | ARC | .157083131 | .142530086 | .014553045 |
| C2 / 300 | P-GRB | .829963413 | .771439164 | .058524249 |
| C2 / 300 | K1-R | .829963413 | .797724208 | .032239206 |
| C2 / 300 | ARC | .829963413 | .806814149 | .023149264 |

D3 improves slightly in both UB and LB, below the frozen material threshold.
No fresh P-GRB D3 run was opened. C2 improves gap by 28.2% versus K1-R and 60.4%
versus P-GRB, preserving and expanding that nonzero short-T protection. D6 has
slightly better UB than P-GRB but 18.7% larger gap; this is a material failure
to repair the primary target. ARC's loss versus K1-R there is below the frozen
material threshold. These are practical, single-seed development comparisons,
not statistical-equivalence or universal-speed claims.

## Mechanism and attribution

ARC replaces `2 M V^2` node-load Big-M recurrences with station-origin arc loads,
including loaded return, and makes node load a derived continuous variable.
The original routes, operations, inventory objective, order, duration and F0
interval/cutoff blocks remain. The proof in mathematics.md gives forward/reverse
integer correspondence and shows that Q-PLUS's old recurrences are implied even
in the continuous relaxation. The Q-PLUS and ARC LP projections coincide.
Commodity-flow modeling is established literature; no new general flow theorem
or inequality is claimed.

D4's root models have 4136 rows (K1-R), 4640 (Q-PLUS), and 3776 (ARC). ARC and
Q-PLUS share the paid initial original routes and UB, as do all paired warm
arms. Their runtime difference is **not identified as pure row-deletion cost**:
numerically different LP optima (about 5.5e-7 apart) caused Q-PLUS to take one
0.195-second bound-target MIP before its terminal MIP; ARC directly entered the
terminal MIP. Node-load integrality also differs. These lifecycle and branching
effects remain part of the complete algorithm's measured outcome. The exact
LP-projection proof does not imply identical numerical solver trajectories.

On D6, HGA cost is closely matched (321.286 versus 321.570 seconds). Both warm
arms make five LP and two MIP calls with one split; all LP calls complete quickly.
The root LP objective stays about .125691831. Thus this screen does not support
a root-bound gain or an LP-starvation explanation. ARC's terminal MIP advances
the bound less, despite fewer nodes/Work; those counters do not override the
full-time gap comparison. The 600-second comparison includes substantial startup
opportunity cost; the separate historical 3600-second P-GRB proof advantage is
still unresolved, not retested or disproved by this screen.

## Stage acceptance and recovery

**Evidence:** 43/43 CTests passed. All 19 charged runs passed independent original
route/inventory/load/duration/objective checks, parameter/model audits and
recomputed interval-union checks. Original P-GRB fingerprints match fresh
build-only exports and available historical bindings. The two native micros
certify 5/24; ARC exercises eight splits. They are correctness evidence only.
Tiny signed LB/UB discrepancies remain in runs.csv and are identified as within
the existing numerical tolerance. No rational certification was implemented.

**Architecture:** one uniform explicit ARC flag; full paid canonical HGA and
K1-AM controller. K1-R and ARC share verified event retention and zero stopping.
All Round65 resource-credit/projection controls are off. Only the common whole-run
deadline ends computation; no component time/Work slicing or instance dispatch
is part of ARC. See algorithm.md and the actual command ledger.

**Resources:** 17 performance runs plus two native micros, 94 experiment LP/MIP
calls, 3696.157 seconds total process wall. Seven build-only exports cost 0.485
seconds and launch no optimizer. CTests cost 4.40 seconds separately; their native
unit-test calls are outside the experiment-call count. Declared worst-case
experiment allowance was 4960 seconds after two recorded pre-launch revisions.
There were no failed/invalid performance runs. All opened runs are retained.

The compact evidence, hashes, source identity, witness checks and reproducible
entry points are committed. Raw logs/models and the binary stay at the local
paths in reproduce.md. D7 and broader confirmation remain untested by ARC, so
this stage cannot establish stable medium/large superiority or overall success.
The next stage will start with ARC off and compare VD-P with a logarithmically
encoded version of the same inventory disjunction, against current K1-R and
official P-GRB. The observed sensitivity of near-zero AM gains is an additional
open issue, not grounds for silently changing certificate tolerances.

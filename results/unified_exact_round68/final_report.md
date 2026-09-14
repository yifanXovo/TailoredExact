# Round68 — complete existing-witness Starts for VD-P

Base: completed Round67 PR128, a47e86a57a1f68ca6e515877193cb8696d1aa13e.
Branch: codex/round68-vdp-verified-start. Stage experiments complete; publication
identity is recorded separately. The overall research goal remains unmet.

## Implemented method

VD-S (`research-round68-vdp-start`) supplies the currently best, already-paid,
physically verified route-operation witness to each required native VD-P MIP,
including retained LP-to-MIP models. Canonical full HGA, AM, the one-hot model
and proof coverage remain unchanged. Equal-Q vehicle normalization removes
empty routes and selects an interchangeable representative; it changes no route
operation, inventory, travel or objective. The complete map includes every
actual inventory-state selector and its Gini perspective coordinate.

Before submission, the backend rechecks physical feasibility, actual column
bounds/types, every linear row and objective. It sets one complete Start and
reads every value back. Incompatible intervals/cutoffs skip the witness while
keeping the full proof obligation; unexpected mapping/API failures fail closed.
Native log acceptance and MIPSOL vector observation are distinct from successful
API submission. The only refreshed time allowance is the same whole-run deadline,
so mapping, checking, telemetry and all optimization remain paid.

This reuses established MIP Start technology. The contribution here is a working,
audited complete-witness integration with the actual VD-P/retained-model path
and its measured BRP effects, not a new general theorem or a guarantee of faster
proof. Round44's different envelope/reload starts and Round61's separately
constructed PREFIX candidates do not establish this current integration. The
official API review is in Round67/gurobi_start_api_review.md; algorithm.md and
mathematics.md give the uniform rule, original-variable correspondence and limits.

A preflight fixture also exposed an LP serialization defect: a bare zero left
side became an unintended variable named `0`. The common writer now emits `0 G`,
an exact zero linear term using the existing G column. This preserves intended
constant rows, including contradictions. All arms use the same repaired build;
the correction is separate from Start performance. The finite prior-stage audit
found42 bare-zero rows and no potentially relaxed false constant row. Detailed
failed attempts and repairs are preserved in preflight.md and qualification.json.

## Matched development results

All arms use Gurobi13.0.2, Threads1, Seed0, PresolveAuto, requested gaps0 and
the original numerical standards. P-GRB is the original compact model with native
defaults, no external starts/cuts/HGA/imported bounds. K1-R is full canonical
HGA/AM with the same verified-candidate retention and immediate zero termination.
VD-P differs from VD-S only by the new Start path. Every K1 pair acquires the
same initial route witness; their actual VD-P/VD-S exported model hashes match
throughout the four roles. All roles are exposed development data.

| Role and whole-run cap | P-GRB | K1-R | VD-P | VD-S |
|---|---|---|---|---|
| D3,300 | open, gap .00347140 | open, gap .00115107 | open, gap .00318228 | certified84.172s |
| D6,600 | open, gap .01225529 | open, gap .01385898 | open, gap .01226062 | open, gap .01140292 |
| C2,300 | open, gap .05852425 | open, gap .03221121 | certified132.531s | certified123.640s |
| D4,300 | open, gap .31046400 | certified129.657s | certified40.062s | certified54.453s |

The table uses paid process wall for certifications and signed absolute UB-LB
for open runs. Full UB/LB, dimensions, input/build identities, classifications
and mixed-bound outcomes are in runs.csv/pairs.csv. See the four screen notes.

D3 is the clear gain: VD-S certifies the original problem at F=.04500155005562836
while all three current references remain open. The unchanged VD-P control again
loses most K1 protection, so the repair is attributable to actual integration,
not selection of a favorable historical time. All three K1 arms start at the same
F=.049468682614419446 and pay about2s HGA. VD-P has no printed native incumbent
until241s. VD-S begins with the Start, reports the final rounded objective at26s
of terminal MIP and proves the problem in84.172s total. Intermediate printed
incumbents remain native telemetry, not independently retained full event vectors.

On CitiBike D6, VD-S improves both UB and LB against P, but the6.95%/.00085237
gap reduction is below the predeclared material threshold. Its17.72%/.00245606
gain over K1 is material. The large-model Start is actually accepted and fully
observed, checking8273 columns and30485 rows, with.01115s mapping/submission
cost inside paid wall. This removes native incumbent absence without establishing
stable major P superiority. Full HGA still costs about323s. The completed HGA
event log reaches its final objective much earlier; that observation alone does
not justify a time-based stop or prove a shortened algorithm would behave alike.

C2 retains VD-P's certificate gain over P and K1; the8.891s time reduction is
below the frozen material threshold. D4 retains strong K1/P protection but is
14.391s/35.92% slower than VD-P, a material local regression. VD-S still improves
58% over K1 and certifies where P is open. This tradeoff is reported rather than
applying a per-instance fastest-variant veto or claiming monotone Start benefits.

## Qualification, cost and scope

The measured executable SHA256 is
ad6f29736c3f10a51339f07a3b7e2160964815e855b91ba8e60db27caeb49340.
build_v1.json freezes source, executable, driver, shared helper and qualification;
machine.json records the environment.45/45 CTests passed after one disclosed
build failure and two test failures. The new native integration test executed
6 Optimize calls across failed and successful attempts (1+2+3). Existing native
unit-test calls are not claimed to be included in that new-test count. These
qualification costs are separate from formal experiments, never subtracted from
the latter. Six no-optimization reference exports took.374s and matched earlier
official P fingerprints where comparable. Four correctness micros certify5/24.

All20 declared runs completed:16 performance+4 micros,94 experiment Optimize
calls,4735.860s paid process wall, zero failures, within the6080s worst-case plan.
No optimizer ran alongside a build or heavy audit. Independent checks recompute
original inventories, loads, travel/handling, allowed loaded return and F; they
check native settings, type restoration, initial Gini range and retained frontier
coverage. No inconsistent LB is silently clipped. Numerical discrepancies such
as C2's1.65e-8 remain explicit; zero requested native gaps are not a rational
certificate.

All8 actual VD-S MIP Start decisions are eligible, submitted, read back, accepted
in native logs and observed as complete MIPSOL vectors. Independent CSV/model
audits check the submitted point against every bound, type, row and objective.
The MIPSOL comparison flags themselves come from the qualified C++ observer;
full native event vectors were not separately archived.66 offline initial-witness
model checks include26 incompatible intervals and40 valid mappings, no failures.
The final full scans cost3.860s for retained witnesses and1.156s for actual Starts,
with zero optimizer calls; these are post-experiment QA scan times.278 compact
evidence artifacts retain ledgers, lossless trajectories, witnesses, Start vectors,
acceptance logs and hashes. Full model files/binaries stay local. reproduce.md
describes a fresh bounded source/binary binding and automatic output audit.

## Stage decision and next work

Accept VD-S as a useful default-off research candidate. It repairs D3's important
loss of K1 protection, retains C2/D4 certificate advantages, and has a modest
aligned D6 improvement with a fully active mechanism. Preserve the D4 ablation
regression and all startup costs. This stage neither adopts a production default
nor completes the user's overall goal.

The candidate has not had an independent confirmation or a3600/7200 comparison.
D3's large gain needs a limited fresh repeat; the historical small/nonzero
CitiBike regression set and broader medium/large roles remain unqualified. The
next stage should first test the frozen VD-S candidate beyond these four design
roles and resolve an informative common long-window comparison, with a separate
bounded plan. Startup reduction is another concrete hypothesis, but must use
an admissible uniform mathematical/algorithmic rule rather than cutting HGA
at the observed12-second point. Do not tune a new rule on confirmation results
and continue calling those results independent.

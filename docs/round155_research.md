# Round155 complete inventory coupling and independent proof floors

**Completed scientific study with unresolved hull precision.** The
substantive continuations, six-arm panel and final factual checks have
closed. The [final report](../results/unified_exact_round155/final_report.md)
and [scientific review](../results/unified_exact_round155/review/final_scientific_review.md)
give the finite endpoint and its limits. The
[continuation record](../results/unified_exact_round155/RESUME.md) identifies
the actual publication, public recovery and cleanup status.

The [adopted goal](../results/unified_exact_round155/goal.md) retains stable
GI-TBC and asks two separate questions: how much the complete integer
inventory coupling can advance from the actual Round154 pools, and whether
the existing independent proof-floor candidate E retains its benefit in
longer complete runs. The unchanged production PE and unchanged own-floor
producer are identified in the
[production record](../results/unified_exact_round155/production_identity.json).
E and J remain research-only and default OFF.

## Mathematical object and evidence

The [mathematical account](../results/unified_exact_round155/mathematical_analysis.md)
and [manuscript section](../results/unified_exact_round155/manuscript.tex)
separate four questions: formulation strength, whole-domain price strength,
the value of the complete inventory hull coupled to free Q, and complete
algorithm performance. A full-Q RMP primal bounds the coupled LP value;
it is not a physical route incumbent. A fixed direction's price ceiling
does not bound the full hull. Every lower certificate retains the original-Q
residual correction and the true current-column price correction.

The optimal-dual-face explanation is classical LP geometry. A negative
column can remove the current dual point while another point on the old
optimal face preserves the RMP value. Persistent masters, basis
reoptimization, midpoint selection and multiple incumbent columns already
exist in Round153. The
[finite history table](../results/unified_exact_round155/history_dedup.md)
retains those attributions and the earlier routing/loading research.

## Audited matched screens

Each comparison starts from the same original Round154 pool, supports,
complete Q, retained upper witness and accumulated lower. The first-return
arm and bounded multiple-column arm own their respective new results.
Both use qualified current basic duals, so neither pays an auxiliary
selection LP. The bounded arm uses the declared 256-node allowance,
up to 20 incumbent solutions and the same per-price safety cap.

| Domain | Return rule | Feedback iterations | New columns | Strictly negative new columns | Outer seconds |
|---|---|---:|---:|---:|---:|
| K35 | First counterexample | 12 | 13 | 12 | 248.109 |
| K35 | Bounded multiple columns | 12 | 156 | 155 | 394.261 |
| NC20 | First counterexample | 12 | 12 | 12 | 129.537 |
| NC20 | Bounded multiple columns | 12 | 109 | 109 | 190.990 |

These four screens show no material interval improvement and no observed
positive weight above 1e-10 for their new columns in the recorded subsequent
primal solutions. Extra returned columns and lower selection overhead are
distinct from a stronger hull bound. These finite screens are neither
saturation evidence nor a population performance claim. Exact identities,
cost categories, duplicates and true-price information are in the
[matched comparison](../results/unified_exact_round155/reports/matched_loop_comparisons.csv)
and [column-quality record](../results/unified_exact_round155/reports/column_quality.csv).

## Substantive continuation and finite endpoint

The [single fixed-level adjustment](../results/unified_exact_round155/review/level_adjustment.md)
tests persistent feasible selection with a separate exact corrected gate.
Its [observed exits](../results/unified_exact_round155/review/level_stop_and_remaining_capacity.md)
do not resolve a level. Subsequent basic-dual work supplies the substantive
opportunity: K35 has112 initial and333 further bounded feedback steps plus18
level steps; NC20 has45 bounded and653 later first-return steps plus one
level step. Actual deep costs are about4.08h and2.23h. Capacities are adjusted
under goal D1/D3; eight hours per domain was not charged as time spent.

K35 finishes with40585 columns/565 supports and interval
[.2828596948801708,.287326162801573]; NC20 has55398/774 and
[.18332184845553887,.18986770309524809]. Neither reaches1e-4 width. All-support
free-Q replays retain the same lowers. Sustained complete-loop stagnation,
the single level adjustment and final usage evidence support a finite stop
for these tested policies, with no full-hull saturation claim. Unspent
capacity does not by itself justify more identical runs.

A later K35 continuation observation records14 tracked new columns with
total weight about3.97e-9 and a numerical upper change about5.02e-10.
Five columns originated in the earlier deep phase and nine in the current
continuation. These tiny recorded values are retained explicitly and are
not called material hull progress. The
[observation note](../results/unified_exact_round155/review/remaining_tiny_usage_observation.md)
distinguishes this later use from nonuse within the earlier completed
phases. The final usage reader passes1220 observations, including27 full
saved-primal projections and1193 tracking-only observations. K's main branch
has48 columns ever recorded above1e-10 (28 from the last phase,20 earlier),
with maximum weight6.445603339705698e-10. NC's1163 added main-branch columns
have no recorded use above that threshold. None of these numerical
observations proves rationally exact zero or a material hull improvement.

The actual level-price readback exposed tiny state-cost coefficients
omitted by Native. The [targeted repair](../results/unified_exact_round155/review/pricing_native_omissions.md)
retains the original numerical guard and subtracts an additional exact
one-sided residual error. Actual-cost DP extrema independently establish
that the saved product bounds still cover the entire inventory domain.
Seven K35 local price/support lowers require one binary64 step downward;
the retained full-hull interval and all columns are unchanged. Both domains'
complete price/Q, selector and corrected-support readbacks now pass.
The raw failed check and original results remain preserved. The remaining
substantive loops start from each branch's own corrected, replayed supports.

The [frozen complete panel](../results/unified_exact_round155/confirmation_matrix.json)
contains independent B/E runs for NB35 and R-X35-S-T2 at 7200 seconds each,
and R-X20-S-T1 at 1200 seconds each. It uses the original paid own-H and
own-floor identities; offline columns and another arm's incumbent are not
inputs. All six actual arms are now verified in the
[panel completion](../results/unified_exact_round155/panel_completion.json).
The [within-run checkpoints](../results/unified_exact_round155/reports/common_checkpoints.json)
use the latest already committed qualified information at2400,3600,4800
and7200 seconds for the hard arms, and record early certification for the
fast pair. Exact-time running snapshots are unavailable and are explicitly
marked. Historical short windows are not same-budget controls for these
longer runs.

The now-closed NB35 7200-second pair has the same physical upper
0.4297444110493129 and the same raw search lower 0.39074482582731757.
E retains the independently supported lower 0.3959564087240911, reducing
the endpoint gap from 0.038999585221995314 to 0.03378800232522178.
Neither arm certifies. This supports persistence of the proof-floor benefit
in this pair.

The newly tested R-X35-S-T2 pair also has a common physical upper
0.2996694007364017 and raw search lower0.21420555388926832. Its independently
paid E floor supports lower0.22226257992032944; neither arm certifies.
E's helper costs35.2585302 seconds, already included in its outer fee.
NB35 E's corresponding helper costs15.523269 seconds.

The fast R-X20-S-T1 pair certifies at the same physical upper
0.6453250303858205. Recorded T_cert is22.58451223722659 seconds for B and
23.813784520840272 for E; total production-plus-verification time is
23.544061937136576 and25.888221420813352 seconds, respectively. E pays
1.1278163 seconds for its helper. This is a finite cost-control observation;
the two difficult-pair gains do not establish a universal default policy.
The immutable availability chain records the NB35 floor by20.157s and the
R-X35 floor by38.953s; each remains above the raw search lower at the endpoint.
For R-X20, the floor is recorded by1.860s and raw search first exceeds it
in the observation batch available at3.078s. That batch shares its
availability timestamp with the preceding below-floor observation, so it
does not establish an exact Native crossing instant. The
[dispatch recovery record](../results/unified_exact_round155/review/panel_dispatch_failure_and_recovery.md)
preserves a subsequent pre-Native startup failure and its paid, bounded repair.

The final closed [cost ledger](../results/unified_exact_round155/cost_report.json)
is54336.51933150017 seconds (about15.09h), including eight failed metered
children and necessary checks. All1210 completed prices and10 support
replays receive the declared independent readbacks. The source record
preserves launch-specific versions and156 inherited static Python
dependencies, including explicit exact checkout newline mappings.
The [delivery record](../results/unified_exact_round155/RESUME.md) separately
records the actual normal English Draft PR, new-only public recovery and
bounded cleanup. All new work remains under ExactEBRP-work; preexisting
paths are excluded from staging and cleanup.

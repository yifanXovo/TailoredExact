# Round148: shared-denominator low GD affine rows

Decision: **RESEARCH_ONLY_SHARED_S_AFFINE_ROOT_NO_PROMOTION**. Retain as research only; do not recommend the current shared-S one-row root mechanism as a uniform paper enhancement. The common-first-moment family is valid, strictly stronger than isolated GD, and supplies clear reoptimized LP information on every saved diagnostic domain. K35 adds useful final bound/gap information at a small incumbent cost. However, the serious RB35 incumbent/signed-gap regression fails the required retention question and is not offset by its small L gain. Keep the default-off implementation and reproducible evidence as a completed research result. Preserve R147 standalone D as its previously limited paper candidate and R137 as the stable default. Do not replace defaults or merge automatically.

## Mathematical and optimized information

The shared-S affine family retains a common denominator first moment in
each station's conditional mixture. The low-only oracle needs at most
three nodes per state. An exact two-station fixture gives g>=|a-d|/6
where both old GD rows are zero; it is an isolated-block strictness result
consistent with pair-CDF, not a full-model novelty or routing-hull theorem.
The exact oracle/convexification argument is in
[mathematical_analysis.md](mathematical_analysis.md), and the paper-ready
LaTeX section is [manuscript.tex](manuscript.tex).

Five saved GD points, belonging to three physical instances, are strictly
separated. One newly appended row improves every matched full-domain LP:
K20 BASE/joint/STOCK by .002269286408/.002459563403/.004554385894;
K35 BASE by .005381130879; RX20 BASE by .016631649658. Old optima and
all original objective/constants/support/bounds/cutoff/rows are reused
without baseline Optimize. No old variable is frozen. All new numerical
LP optima pass the existing quality policy; neither old nor new optima
are represented as exact rational certificates. The coefficient direction
is checked exactly. See [LP_report.md](LP_report.md) for construction,
Native/outer costs, row NZ, transport loss and remaining separation.
There are no optional closure rounds or rank/eta experiments. The goal's
reported prior negative rank/eta screen is historical context, not a
newly replicated claim when its review attachment is unavailable.

## Complete same-new-PE experiment

The frozen mechanism adds at most one uniform low affine/moment row
and one root LP on standalone D. Its slopes come from the arm's own
normal root point, never an injected saved historical point. Both arms
pay complete own-H, construction, solving and necessary validation.
The original physical horizon and lambda, H seed20260626, Gurobi Seed0,
Threads1, M-B/VD-P, pair-only, AM=.08, depth8, minimum width1e-4 and AP-off
policies remain. New-PE D is the actual incremental control.

The same-new-PE K35 pair gives a real bound/incumbent tradeoff. D returns U/L .676798845196/.545729444783; the candidate returns .679917519727/.558283855657. Supported L rises .012554410874 (2.300483%), physical U is .003118674531 worse (.460798%), and relative gap falls from 19.366079% to 17.889473% (-1.476606 percentage points). The signed gap falls .009435736343. Both remain open. Their accepted T_total values are 2378.764522/2379.834894s; this 1.070373s difference is not convergence or certification speed. The complete comparison justified one RB35 pressure pair, not promotion.

RB35-T2 answers that pressure question adversely. D returns U/L .335883588950/.219663876370; the candidate returns .371420783400/.220898439927. L rises only .001234563557 (.562024%), while physical U is .035537194450 worse (10.580212%). The signed gap grows from .116219712580 to .150522343473 (+.034302630893, about 29.52%); relative gap grows from 34.601188% to 40.526096% (+5.924908 percentage points). Both remain open. The accepted complete totals are 2378.591470/2379.626412s; their small difference is not a speed result. This is a serious regression under the inherited double-open rule: U loss exceeds max(.001,5% of D U), and signed-gap loss exceeds max(.005,25% of D signed gap).

All four formal arms retain their full cap2400 windows, complete independent own H and Seed0/Threads1. The candidate pays its normal root, construction/transport and one added root LP. Both roles have zero committed outer splits; Native target/search paths, Work, simplex and nodes remain separate observations. K35 initial LP increases .204187028164 to .209568159043, whereas printed Native root-after-cuts values are .44681/.44808. RB35 own-root LP increases .135292103721 to .1365597514 (rounded log value). These layers do not imply a monotone final search bound or incumbent. Native/trajectory changes locate observed gains and losses, without uniquely attributing them to a static row, a particular branch or AM. Candidate final U is worse on both roles, so neither candidate trajectory ever beats the corresponding D final U; saved committed trajectories retain the chronology.

| Role | Method | U | External supported L | Gap % | T produce | T cert | T verify | T total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K-35-U | D | 0.676798845196 | 0.545729444783 | 19.366079 | 2371.178974 | open | 7.585548 | 2378.764522 |
| K-35-U | D_SHARED_S | 0.679917519727 | 0.558283855657 | 17.889473 | 2371.124699 | open | 8.710195 | 2379.834894 |
| R-B35-S-T2 | D | 0.335883588950 | 0.219663876370 | 34.601188 | 2371.218436 | open | 7.373034 | 2378.591470 |
| R-B35-S-T2 | D_SHARED_S | 0.371420783400 | 0.220898439927 | 40.526096 | 2371.060045 | open | 8.566367 | 2379.626412 |


| Role/method | Initial LP | After added row LP | Printed Native root-after-cuts | Final Native ObjBoundC | Simplex total | Native Work | Terminal nodes | Outer splits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K-35-U/D | 0.20418702816386647 | 0.20418702816386647 | 0.44681 | 0.545729444783031 | 7815897.0 | 4732.459564719136 | 16122.0 | 0 |
| K-35-U/D_SHARED_S | 0.20418702816386647 | 0.20956815904262074 | 0.44808 | 0.5582838556571678 | 8737024.0 | 4812.367583713739 | 18102.0 | 0 |
| R-B35-S-T2/D | 0.13529210372054312 | 0.13529210372054312 | 0.18147 | 0.21966387636958412 | 6351038.0 | 5658.236263830439 | 6816.0 | 0 |
| R-B35-S-T2/D_SHARED_S | 0.13529210372054312 | 0.13655975143426088 | 0.18179 | 0.22089843992694513 | 7499830.0 | 5779.7587135007325 | 8323.0 | 0 |

Open T_cert remains null. Caps, slightly different total/verification
times and unfinished searches are not convergence times. Printed Native
root-after-cuts values are log observations at their printed precision;
they do not replace either initial LP or final external supported L.
Native returned bounds, physical G/penalty, target paths, complete Work,
simplex, nodes and outer splits remain separate machine-readable fields
in [reports/full.json](reports/full.json). Committed, physically verified
incumbent trajectories use producer availability clocks in
[reports/verified_U_trajectories.csv](reports/verified_U_trajectories.csv).
No unique causal allocation among static rows, Native branching and AM
is inferred from this complete comparison.

The per-arm T_produce/T_verify/T_total retain the accepted R134 reader's
clock boundary. The separate fee_outer_seconds also covers current entry
startup, wrapper checks and necessary supplementary validation; all of
that elapsed outer cost is charged once in G1. The inherited clock fields
are not silently widened between stages, and their small differences on
open arms are not presented as proof-speed changes.

## Historical counterpoints retained

R147 D remains a limited uniform paper-enhancement candidate, not the
historical strongest or broadly robust algorithm. Its Seed0 K35 and
RB35 incumbents improve over B by about 3.13% and 2.54%, but K35 supported
L decreases, K20 does not certify and RX20 certifies about 2.34s later.
The same-old-PE K20 STOCK/STOCK+GD certificates at about 94.261/74.916s
remain strong. R140 old TC+STOCK has K35 U/L about .650438712/.5682885263
and RB35-T2 about .3190804927/.2339272621, both stronger endpoints than
R147 D. Its Seed1 adverse evidence and source/PE/V2-transport differences
remain disclosed; those results are not a pure seed-only intervention.
R144 RN-P's K35 gains, R145's strict complementarity/root-preservation
conclusions and R138-R142's mixed results are retained. No per-instance
best-version switching or fresh full historical factorial is proposed.

## Qualification, failures, identity and cost

Focused qualification covers the low three-node oracle, actual finite
slopes and signed conservative coefficients, positive-S/zero-old-GD,
fixed/omitted domains, compatible sub-support, old GD SHA migration,
actual Native signed readback, complete and nonminimal epigraph Starts,
and OFF matrix identity. The short K20 cap90 lifecycle producer has
six returned calls and four unique models. Its initial reader attempt
encountered an old one-LP/one-control-status assumption. A narrow view
excludes only the original root's never-installed bound from cover
reconstruction. All calls remain in model/Native/quality/lifecycle/cost
audits, and the same sealed producer was reverified without Optimize.
Other CLI/qualification/reviewer-script failures are retained and charged.
No failed search is rerun to obtain a better endpoint.

After K35, a targeted zero-GD context correction selects the current
immutable source by its SHA, avoiding ambiguous generation/suffix sorting.
Fixtures include a real saved zero-lower model and an explicitly incomplete
positive-S support schema; synthetic call-binding unit stubs are not Native
or performance evidence. A real sealed sample verifies SHA/leaf/log and
actual controller-LP kind: the raw pre-relaxation integer-precondition flag
is 1 and must not be misread as a non-LP solve. An attempted full reentry of
an already closed short qualification was refused. No closeout was deleted
or bypassed; the replacement only checks saved call/ledger and immutable
hashes. The legacy wrapper had regenerated one auxiliary root-row evidence
file before its old guard, with identical domain/coefficients and a new
arithmetic timing. This derivative change is disclosed in
[the disposition](engineering/reader_closed_reentry_disposition.json);
producer seals and accepted verification component hashes remain unchanged.
An early R148 guard now rejects closed reentry before such derivative writes.

All 28 entered complete/qualification Native calls returned; five standalone diagnostic LP calls are separate. Charged new outer cost is **9670.619385001s / 18000s**, including all own-H, construction, solve, failure and necessary verification costs once. Builds are 45.500213800s separately. The charge includes conservative reviewer enclosing intervals and a disclosed 5s allowance for unmeasured startup/serialization, rather than pretending those are exact process timings. Nested Native runtime/Work is not charged twice. Pure offline mathematics, document authoring and public I/O are separate; old R146/R147 fees remain historical.

Production source is `d5868014c8868cdc305e6ed798bf0d5c86a1bda9`; PE SHA256 is `4beb12f8a3de992691fc4ae229fdaff43e35ef00ce29f9f2bd3cb139af792ac2`. The three changed TUs were rebuilt from verified inherited dependencies. The [manifest](candidate_manifest.json) records the compiler, source, objects, PE and DLL. Production, wrapper, fixed-science and late-delivery commits have separate identities. Stable R137, old D/SD entries/profiles and all prior results retain their bytes. Original user modifications are protected.

## Scope and closeout

This closes the tested uniform one-row/one-added-own-root-LP implementation direction, not the entire mathematical common-S family. Two known Seed0 hard-role pairs are a finite selection study, not broad validation or a robustness claim. K20/RX20 complete proof pairs, extra seeds, more root cuts, high-deviation variants, RN/STOCK combinations and AM parameter rescues are not needed to overturn the observed important RB35 loss and are not queued. Unused experimental capacity is not unfinished work. The optional AM/no-strict information-retention question remains a separate possible future study; historical R47/R52 negative anchors and prior threshold experiments remain intact and are not rerun here.

The [independent final review](review/final_scientific_review.json),
[cost report](cost_report.json), [reuse index](reuse_index.json) and
[RESUME](RESUME.md) give the scientific and actual delivery status.
Only necessary new evidence is packaged. Fixed old carrier/member hashes
avoid copying historical large bundles. Normal push and an English Draft
PR are followed by bounded anonymous public byte/member recovery and
current-round-only metadata screening/cleanup. Neither delivery step
triggers Optimize, compilation or commercial Native loading. No merge,
force push, old-history deletion or stable-default replacement is made.

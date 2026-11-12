# Independent stage-direction review

Reviewer identity: `/root/round163_stage_review`, an independently tasked Codex
agent under `/root`, not a human peer reviewer. Review date: 2026-11-12.
Scope: goal F/H and the stage recommendation. This review read the existing
evidence; it did not run a solver, producer, helper, numerical checker, or new
scientific experiment. It made no production, CSV, or Git changes.

## Recommendation and its basis

Keep **B as the paper's main algorithm and present uniform E+ as a limited,
clearly identified proof enhancement**. This is a choice about the paper's
principal method, not an automatic change to the stable release or a rule
that one proof improvement can never justify an enhancement.

The full denominator is six configurations and eighteen completed arms. The
authoritative inputs to this judgment are `reports/complete_arms.json`,
`reports/comparisons.json`, and `reports/summary.json`. The reports admit all
eighteen positions as qualified complete-method evidence. I rely on the
separate method/input/source/route reviews for their detailed implementation
readbacks; I have not represented this direction review as a second execution
of those audits.

| Predeclared criterion | Actual E+ versus B evidence | Consequence for the choice |
|---|---|---|
| Correctness and evidence completeness | Both have six admitted complete arms, with the original certificate/gap policy and all paid costs retained. | Neither is disqualified on this criterion. Correctness alone does not rank the methods. |
| Certificates | B 3/6, E+ 3/6, P 1/6. E+ adds no certificate and loses none. | The complete certification result favors retaining B as the central method rather than making the extra producer part of the main identity. |
| Paid time when both certify | E+/B ratios are 1.130665945756784, 1.3357446355323432, and 1.0515856109492556 on C20, B20, and X20. | All three observed E+ certificate times are later. This is finite one-Seed evidence, not an estimated runtime distribution. |
| Both endpoints when OPEN | C35 and B35 have the same U and proof L in B and E+. X35 has the same U and a material proof-L gain in E+. | E+ has genuine retained proof value, but the value is concentrated in one of six final endpoints. |
| Actual paid cost | B `T_total=7451.303745185491s`; E+ `7506.416129835416s`, a difference of `55.112384649924934s` (about 0.74%). E+ helper time is `256.7365551s`, already inside its production deadlines. | The total surcharge is small, but it accompanies later observed certificates and no physical-U improvement. The helper cost must not be added to T_total again. |

The joint-CERT times themselves are B/E+ 199.77935039671138/
225.8837081589736s on C20, 5.05829244107008/6.75658699311316s on B20,
and 119.74938786122948/125.92673319485042s on X20. These are production
certificate times; postproduction verification is separately included in
T_total. The three OPEN configurations remain in every denominator and are
not assigned a convergence time from their caps.

The OPEN endpoints below preserve the primal/dual distinction. Displayed
values are rounded; the JSON is authoritative.

| Configuration | P U / proof L | B U / proof L | E+ U / proof L |
|---|---:|---:|---:|
| R163-C35-U | .093319344 / .008286772 | .129566390 / .019837503 | .129566390 / .019837503 |
| R163-B35-S | .249253013 / .113979409 | .194290311 / .120234003 | .194290311 / .120234003 |
| R163-X35-S | .541530680 / .362971432 | .457475317 / .394988256 | .457475317 / .423199550 |

On X35 E+ raises proof L from `0.3949882559151472` to
`0.42319954961578576`, by `0.028211293700638573`, at the same physical
`U=0.45747531701601785`. This is a material positive result and belongs in
the paper's substantive findings, with its paid cost. E+'s qualified raw
search L is slightly lower than B's there, so the improvement should be
attributed to the qualified proof-floor placement, not to stronger raw
Native progress.

Uniform E+ as the paper's principal enhanced method is a serious alternative:
it preserves all six U values and all three certificates, improves one hard
proof endpoint substantially, and increases aggregate paid cost by only about
0.74%. A paper whose explicitly declared primary objective were the strongest
observed final proof endpoint could reasonably prefer that tradeoff. My
recommendation instead gives greater weight to the complete-method certificate
and paid-CERT evidence: no added certificate, three later observed certificates,
no U gain, and five unchanged final proof endpoints. It keeps the simpler B
identity central while retaining the enhancement's actual contribution. This
is not a demand for E+ to win every instance, nor a claim that its small aggregate
cost is prohibitive. Conversely, omitting E+ entirely would lose both the X35
result and the useful conclusion that proof-only placement can transfer beyond
its development inputs without becoming a generally better complete method.

B versus P supplies useful context: B has three certificates against one,
lower U on three configurations, higher U on one, and stronger qualified proof
L on five at the reported endpoint qualification scale. C35 is the important
opposed-endpoint case: P's physical U is strictly better while B/E+ have the
stronger proof L. The one B/P joint-CERT time ratio
`0.0214465738525656` is a single paired observation, not a six-instance
speedup claim. Neither aggregate paid totals nor Native Work/node counts
turn the time-limited OPEN cases into solved-time observations.

## Bottleneck interpretation and historical boundary

The helper explanations matter as much as the endpoint counts. On C20, B20,
and X20, final search L exceeds the returned inventory upper at the inherited
qualification scale. C35's inventory floor is numerically near zero
(`3.99954800422003e-17`), but that is not an exact-zero physical certificate;
all three physical C35 outputs are OPEN. On B35 the returned inventory floor
`0.11803645384434823` is below final search L
`0.12023400258397535`. Its same-domain inventory upper is nevertheless
`0.1324235571810887`, so the unchanged final bound is not evidence that the
inventory problem has been solved. On X35 the returned floor supports the
final proof L directly.

Both new shortage n35 prices reached the frozen 16384-node capacity. Their
reported inventory widths are `0.014387103336740467` for B35 and
`0.02295563610060769` for X35, with price decisions `UNDECIDED`. R156's
near-tight inventory intervals belong to its old matched scopes. They must
not be transported to these two domains, and these data do not allocate all
remaining physical gap to routing/loading. The identity separating incumbent
suboptimality, inventory-to-physics difference, and inventory precision is
useful only with a common objective and a justified common scope.

I read `structural_synthesis.md` and `historical_source_map.json`, R137's
maintained research-priority passages, R154/R156 and R162 final reports, and
the R157--161 final reports in their retained worktrees. The parent supplied
the exact pinned R157 Git bytes as `review/pinned_R157_final_report.md`, SHA256
`0fa5452efb29196b70c8b269962925de85026a6489e8bcc8830c9a77b703f066`;
that pinned version, including the unfinished-Optimize erratum, governs the
R157 interpretation here. The fixed commit/member/SHA source map governs
historical attribution; checkout bytes with line-ending differences are not
substituted for those identities.

Those results constrain the direction as follows:

- R137 already supplies breadth, startup and mechanism comparisons, AM
  sensitivity and limited second-Seed evidence. Its old priorities should not
  be recycled as claims that these foundations are missing.
- R154/R156 establish proof-placement value and scoped inventory-precision
  results; they do not establish a generally superior complete algorithm.
- R157's finite family exclusions give no global increment. R158's completed
  whole-level resource query remains UNKNOWN after substantial capacity and
  exhibits fractional ownership. R159's joint resource improvements do not
  produce a new physical route or global original-J lower. A renamed
  master/oracle or another finite-family exclusion loop is not a justified
  next step.
- R160 demonstrates early physical neighborhood capability but worse or equal
  complete endpoints and a certificate delay. More blocks, nodes or passes
  do not follow from that evidence. R161's integer-preserving RN replacement
  and its sole revision lose to OLD at both endpoints on the tested sources.
- R162's real but small matched continuous-Q increment and retained projection
  do not survive the full method. They neither upper-bound the integer physical
  gap nor justify restarting the same continuous-product chain.

## Exactly one next question and its prerequisites

**On the now-exposed R163-C35-U configuration, can B's saved complete route
skeleton attain the already verified P objective `0.09331934374779818` by
changing its legal integer service quantities, directions and zero-service
deletions alone, or does a qualified lower on that precisely restricted domain
prove that reaching this target requires a change of active stations,
ownership or visit order?**

Here a skeleton fixes the ordered station sequence of each vehicle from B's
saved verified fleet. Stations outside those sequences retain `Y_i=b_i`.
Stations inside retain their original supported integer inventory choices and
may change direction or become zero service; zero-service visits may be
deleted while preserving the order of retained visits. This defines a finite,
parent-containing restricted physical domain, not a relaxation covering every
physical fleet.

The trigger is a new, unambiguous primal witness: B/E+'s C35 incumbent is
`0.03624704590416217` worse than the saved P fleet on the same original
input/objective/T. The near-zero inventory value supplies no route and cannot
explain this physical-U deficit away. The proposed question narrows a specific
primal bottleneck before selecting another search mechanism. It is not a
proposal to enlarge R160's online block neighborhood or to inject P's plan
into B.

The following are prerequisites, not work launched in this round:

1. Bind the two saved fleet witnesses to the same input, loaded objective
   coefficients and original physical horizon. Define the entire restricted
   domain explicitly, including inventories of unvisited stations and every
   allowed zero-service deletion. Retain the full original n-station Gini and
   penalty, including contributions of unchanged stations and the S=0 rule.
2. Prove expansion/contraction between the restricted representation and
   legal physical fleets with empty departure, unique nonzero one-way service,
   every prefix capacity, heterogeneous Q, loaded return and final unloading.
   Evaluate the exact emitted travel costs of retained subsequences; do not
   assume that a floating-point triangle inequality permits a free shortcut.
   Preserve the original T and objective rather than a tour/handling surrogate.
3. Before **any new solve**, reconcile the finite computable object with the
   existing whole-route quantity tools, establish its full-domain completeness
   and physical lifting proof, and give a bounded cost/value basis for the
   target decision. This non-duplication gate is substantive: read-only source
   inspection finds that `scripts/round96_fixed_route.py` already defines a
   full fixed-order one-hot-Gini diagnostic with original owners, both service
   signs, optional DAG deletion, unserved stocks fixed at b, prefix rows and
   full handling/travel. The proposed domain is therefore inherited, not a new
   formulation. R75's single/pair descent is a different, smaller object; its
   exhaustion does not certify this domain. Reconcile R96 with the current
   full original objective, S=0, supported-state and numerical contracts, and
   first determine whether retained evidence already answers the question.
   The only potential new information is the C35 target diagnosis. If its
   incremental value and bounded computation are not justified, stop at this
   prerequisite rather than launch another renamed quantity optimization.
   Parent lifts and meaningful tiny enumeration qualify any representation
   adaptation; any new repeated algorithm core must be C++.
4. Register one bounded original-J target decision at the saved P value and
   the original numerical policy, with paid construction/qualification and an
   independent fleet-or-bound reader. Require a certificate from the complete
   restricted domain, not a local no-improvement result. A feasible restricted
   fleet at the target certifies attainability; a strictly higher qualified
   restricted lower certifies that the saved topology cannot attain it. A
   returned incumbent above the target without such a lower is UNKNOWN,
   regardless of a block or local status. Neither a restricted lower nor a
   local Native status becomes a global physical lower.

This asks for a specific inherited physical value object at a discriminating
new target, not a generic restart, novel formulation, or new production
candidate. R160's early local
improvements do not determine this full saved-skeleton attainability question;
R137's basic ablations and root-to-final inspection do not answer it either.
Any later online mechanism would still need a new, affordable own-state benefit
before a fresh complete comparison could be justified. No such mechanism or
follow-on run is started here.

## Limits and final-paper review closure

This is prospective confirmation of new configurations on archived sources,
not new cities, IID demand, independent observed demand, or a factorial source/
size/geometry experiment. All six configurations are exposed after this round.
There is one Seed, so the observed timing directions do not establish a
stable runtime distribution. Historical panels retain their own denominators,
versions and budgets. No per-instance B/E+ selection is recommended.

Final readback completed at **2026-11-12 01:28:39 UTC**. Disposition: **PASS
for the assigned stage-direction review**, with no unresolved material issue
in the reviewed stage choice or next-question framing. This is not a claim
to have independently rerun the separate execution, mathematical or physical
verifiers, nor a publication/recovery acceptance.

I read the completed `decision.json` and `final_report.md`, the maintained
paper's abstract and sections 6.4--7.1, the structural mathematical insertion,
the completed supplement integration, and current navigation. The final text
retains the full eighteen-arm denominator, weighs uniform E+ seriously,
selects B with limited E+ on the fixed criteria, preserves C35's opposed U/L
and the new unresolved B35/X35 price widths, and distinguishes the paper
recommendation from released defaults. The sole next question now expressly
inherits R96 and requires its complete restricted-domain contract, bounded
cost/information justification, and a stop at the prerequisite if those are
not met. It supplies no global physical bound or complete-method gain.

Two review-driven framing corrections are resolved in these final texts:
R96 is credited rather than claiming a new skeleton value formulation; the
supplement labels its retained R137 research-priority menu as historical and
explicitly superseded by the sole current Round163 question. The latter
label was re-read after the parent's correction. No scientific run was used
to make either correction.

Reviewed final snapshot hashes (SHA256; later delivery-only metadata can have
its own identity):

| File | SHA256 |
|---|---|
| `results/unified_exact_round163/decision.json` | `c73d8931abf4f6f67dc52fcd8bcdce9204ccd17c8b5195d1378ef787cabfb6af` |
| `results/unified_exact_round163/final_report.md` | `c825959a1b100d70b4e575f5a5c867cde861dd6f6301041226bc9effe1aacb84` |
| `results/unified_exact_round137/paper_body.md` | `2ed69247daed09e86c748d85de0c91b41f25f7002b014de022e734af26bf2754` |
| `results/unified_exact_round137/mathematical_analysis.md` | `54e34bb2c009dc04a6aa11e944384b8b71986761182e83d04d419e47f83bd5f4` |
| `results/unified_exact_round137/supplement.md` | `3258fe83528e7786c94c85d86322944d2f568aafe6083e3cc0ef1b4fadfb39b8` |

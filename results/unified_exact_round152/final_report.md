# Round152: resource-feasible integer objective epigraphs

The offline object-level study is complete. It establishes nonduplicate
objective information beyond the declared AP/GD/count/stock reference, two
qualified pricing formulations, and finite consequences on three complete
saved LP domains. Stable R137 GI-TBC remains the paper algorithm. Production
and new complete B/J arms were not entered; no new physical U, terminal
supported L, certificate or complete-method speedup is claimed.

## Structural result

At fixed compatible marginals, Theta(s)=H_AP(s)+Gamma(s). Expected penalty is
already fixed by AP; Gamma is the minimum expected nonminimal Gini completion
over the same hard-resource joint distribution. The independently verified
heterogeneous three-station example has an exact feasible extension through
all 117 rows and 46 variables of the declared old strong inventory block.
Its unique feasible common distribution gives a same-marginal objective gap
**53/1080**. Exhaustive evaluation of 49 feasible inventories also gives a
separate global-integer-floor gap **1/480**. The equal-target R133 control is
closed by the strong reference. See [the full proof](mathematical_analysis.md)
and [independent exact theorem](review/exact_small_theorem.md).

The small theorem is scoped to the complete declared inventory block. It
does not claim a route extension or dominance over every historical RN/source
projection or count disjunction. R55 penalty-cover, R135 AP, R138--142 count
and common-product results, R143--145 normalization and R146--151 local/full
boundaries retain their original positive and negative evidence.

## Same-domain complete free LP evidence

| Role | Reused B | AP | AP+GD/stock/count/CP | + old RN | Eight-row loop before RN | Final after RN and qualified new row/floor |
|---|---:|---:|---:|---:|---:|---:|
| N-B35-S | 0.327833772177 | 0.384359410431 | 0.386698028674 | 0.386737186565 | 0.392978953519 | 0.392978953519 |
| K-35-U | 0.200177661949 | 0.273857681327 | 0.274861988699 | 0.278835642981 | 0.274882441452 | 0.278835642981 |
| N-C20-U | 0.048357676071 | 0.167731433193 | 0.174465267785 | 0.174465267785 | 0.174626598216 | 0.174732884302 |

Every original variable, objective coefficient, cutoff and old row is
retained; no g, selector, product, route or auxiliary is fixed to manufacture
gain. Both N-domain B roots and K35's matching R135 AP result are reused,
with no baseline Optimize. The K35 complete-domain equality and its saved
AP point were checked before reuse. AP, all supported count ranges, CP and
RN references are diagnostic controls, not adopted online components.

N-B35's new integer-objective scalar floor raises the RN reference from
0.386737186565 to 0.392978953519 (1.613956%). Its original
bin oracle LB/UB are 0.392978953519/0.396046548957. Eight lifted residual rows
and a full-support normalized-priced row add no further root objective value.
K35's eight-row microgain is more than covered by old RN; the new full-support
row then separates the saved RN point but gives no distinguishable root gain.
N-C20's full-support row raises the RN reference by 0.000267616518
(0.153392%). These are initial free-LP results, not Native
MIP root-after-cuts or terminal proof bounds.

All three original strong-reference marginals have explicit hard-resource
joint mixtures satisfying the actual Gini upper bound. The later global
comparisons also reconstruct compatible mixtures. Thus the reported positive
point separations concern objective information, not projection infeasibility.
One row can cut a saved optimum and still permit another optimum at the same
value; the repeated loops explicitly observe this limitation.

## Oracle deepening, cost and uncertainty

The reference oracle uses fully covered positive-denominator bins and hard
integer resource MILPs, with an independent exact unary-DP fallback for every
unsolved bin and a separate exact zero-stock component. It records denominator
error, MIP gap, lower bounds and true-stock upper bounds separately. A bounded
residual master proposes potentials; only global qualified pricing LBs are
installed. Negative potentials and negative intercepts are retained.

The first refinement prices sparse active states and covers the whole parent
complement by an exact flagged hard-resource DP. A deterministic coefficient
lift reduces inactive penalties. N-B35's first discovery has 78 active versus 537
full states, but later directions become harder and free LPs keep moving their
marginals. Eight support rounds cost 444.078/82.955/52.914 outer seconds for
N-B35/K35/N-C20, respectively; these costs include their LPs, projections,
masters, pricing and coefficient construction, not just Native Runtime.

The second refinement makes the historical RN formulation integer in its
selectors. On positive stock its common reciprocal t satisfies tS=1 exactly;
there is no denominator approximation. Hard resource, gamma_L's max semantics
and the separate zero state remain. The accompanying continuous RN+scaled-stock
reference prevents old normalization from being presented as new information.
The final full-support discovery/LP stages cost 137.216/6.522/4.614 outer seconds.
The longer N-B35 MIP returns a useful separating lower bound before resolving
its whole MIP gap; this is sufficient for its valid row.

The saved audit counts **274/274 returned new Native calls**, including
masters, projections, small qualifications and all failed-attempt calls.
There are 41 new complete saved-model LP optimizations and one reused AP result.
The pricing classification includes 28 separations, 21 direction-nonseparations,
two resolved prices and one **undecided small qualification price**. The last
has a valid exact bracket but the configured relative MIP gap does not meet
the stricter fixed price-resolution threshold; it is retained as undecided.
No unresolved direction is called a negative family result. See
[the machine audit](reports/audit.json), [pricing records](reports/pricing_results.json)
and [expense ledger](cost_report.json).

Final new experimental outer cost, including independent scientific review, is
**851.596856299 seconds / 86400**. The independent review accepted
the offline scientific stage with no scientific blockers. Nested Work and
Runtime, historical experiments and pure authoring/public I/O are not charged
again. Build cost is zero. All seven failed outer attempts are preserved and
paid: syntax errors, a zero-term sparse readback mismatch, and three verification
fixture issues; none produced an admitted invalid row. The normalized tiny
result was reused after its fixture correction, not reoptimized to force a
preferred label. See [failures](failures.json).

## Stage decision

The object contains new information and has executable, qualified separation.
The tested small row collections yield limited extra free-LP strength after
the relevant old information is present. This stage does not establish a
uniform production composition with convincing complete-cost value. The task
explicitly permits an offline theoretical/object-level delivery, so no new
production entry, profile, PE or complete B/J panel is forced. This decision
does not assert that the entire epigraph is redundant or uncomputable.

The next focused question is whether a full-domain potential chosen against
several marginals on the current optimal face can improve the complete free
LP more consistently than a direction fitted to one sparse optimum. That
question can be addressed without reopening the old inventory-routing master
architecture or automatically promoting all diagnostic AP/GD/count/RN blocks.

## Identity and delivery

The new branch starts at verified R151 c6e930ffcb84f0c3801c651f28b5f7e8e2062f33;
main had not absorbed it. Research source files and per-process snapshots are
bound in source_manifest.json and engineering/source_snapshots. The unchanged
production source is c26382d9bf1d4edde538a01c62e57ba563cf865c; its retained PE SHA
is fbdd7c2ece5c748e086761f2490fd901ccdaeffa29df357d2d98fd8743e1dc39. The Native DLL SHA is 9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88. Existing
production source, entries and profiles are byte-preserved. Seed 0 / Threads 1
is used throughout; own-H seed 20260626 is unchanged but no new H is run.

All new assets are under ExactEBRP-work. The original workspace and historical
user/raw assets are protected. New necessary carriers, fixed old member
references, one bounded public restore, English Draft PR and bounded cleanup
are recorded in [RESUME](RESUME.md). No merge, force push or old-history deletion
is part of this delivery. [Independent reviews](review) and the
[paper section](manuscript.tex) preserve the stage's scope.

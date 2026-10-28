# Independent review of the four resource-value separations

Disposition: **PASS for the four stated finite-pair strict value comparisons**,
under the accepted numerical bound/physical-witness policy. Separate reviewer
`/root/independent_review` while arm059 is active. Only eight already closed
endpoint/qualification JSONs, declared matrix/input metadata, manuscript source
and the existing mathematical note were read. No active result, native solve,
full analysis, raw LP/journal scan, archive, PDF or native asset was used. Only
this review was written; final120-position/PDF acceptance remains separate.

## Fixed physical problem and comparison rule

For each base, the two input records share the exact serialized input SHA and
every recorded physical/objective setting except the configuration ID and T.
In particular lambda, rho=1, weights, fleet/Q, handling, Seed and cap are fixed.
The selected endpoint input identities match those records. All eight selected
endpoints are qualified, performance-eligible, non-source-reduced and have
completed necessary qualification.

For this fixed objective, accepted bounds give
F*(T2)<=U(T2)<L(T1)<=F*(T1). Hence U(T2)<L(T1) establishes a strict value
improvement even when neither run determines its own optimum. All four observed
separations exceed the manuscript's1e-7 margin by a wide amount:

| Base | T1 lower witness | T2 feasible upper witness | L1 | U2 | L1-U2 |
| --- | --- | --- | ---: | ---: | ---: |
| R-B20-S | GI-TBC pos39 | GI-TBC pos41 | .480735422994 | .198473446865 | .282261976129 |
| R-X20-S | GI-TBC pos43 | GI-TBC pos48 | .645325030386 | .434795630821 | .210529399565 |
| R-B35-S | GI-TBC pos50 | GI-TBC pos52 | .455903891252 | .344642625592 | .111261265660 |
| R-X35-S | GI-TBC pos57 | PS pos58 | .463357997248 | .404567227014 | .058790770234 |

The n20 pairs are certified at both horizons. R-B20-S certificate cost decreases
from784.143484s to538.602932s, whereas R-X20-S cost increases from20.506462s
to337.304909s. The source correctly treats those as opposite observed proof-cost
directions rather than a consequence of feasible-set inclusion.

Both R-B35-S GI-TBC runs remain open: the retained intervals are approximately
[.455903891252,.591517634770] and [.218985949603,.344642625592]. Their
separation proves the claimed value direction without closing either interval.
Both own T_cert values remain null.

The R-X35 comparison uses **different methods across horizons**: the T1 GI-TBC
lower bound and T2 PS physical upper bound. Both runs remain open with null
own certificate times. Combining these accepted facts offline answers the
physical resource-value question; it transfers neither a fleet/bound into a
production run nor a certificate/time to either method. No active pos59 result
was used. A later stronger eligible T2 witness could support the same
existential comparison without replacing any registered observation.

## Wording and scope

The source explicitly preserves individual certificate/open status and clocks,
uses the open n35 separation without a certificate-time ranking, and restricts
strictness to these four designed pairs. It does not claim every increase in T
must improve the optimum strictly, or that runtime/finite-budget U/L must be
monotone. The existing mathematical note states only feasible-set inclusion and
weak optimal-value monotonicity in general. These distinctions are correct.

For final-reader clarity, the four-row separation summary should name the
actual lower/upper witness methods (or add a sentence naming R-X35's GI-TBC/PS
combination). The current general “eligible T2 feasible upper endpoint” wording
is mathematically valid, but the method identities matter to distinguish this
offline value statement from an individual algorithm certificate. Preserve
the full endpoint tables and all ordinary open outcomes.

No native rerun, parameter change or expanded experiment is warranted by this
limited review. Whole-B2 totals, eventual n35 T2 GI-TBC results, remaining
studies, manuscript/PDF and final integration still require their later review.

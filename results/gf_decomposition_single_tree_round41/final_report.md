# Round 41 final report: static single-tree segmented Gini feasibility

## Decision

Static K=2 single-tree segmentation is technically feasible and exact when its
strict certificate gates pass. ST-K2-P-Core is the best formulation tested: it
uses one native Gurobi MIP job, has reasonable model growth, and captures
essentially 100% of the external-K2 root-bound improvement on all six panel
instances with a positive K2-minus-K1 denominator. It passes the fragmentation
witness decisively and materially improves over K1 on the opposing witness.

It does **not** pass the complete predeclared Gate C. On the strongest K4
positive control, Core takes 1.313 times external K4's exact-phase time and
1.371 times its Work, above the frozen 1.25 ceilings. ST-K4-P and held-out
validation were consequently not authorized. The validated default remains
**C6-HGA-FULL, K=4, rho=0.01**; all Round 41 mechanisms remain explicit and
default-off.

Final gates: A pass, B pass, C fail, D not justified, E not justified.

## Protocol and evidence

- Branch base: Round 40 commit `3db7a5efbace14dfed7557560e96636f749b84bc`.
- Final executable SHA-256:
  `572834f01bf923ae0026300b4f6a5b88f9ca78db27cc0bb38b39938de836fcdd`.
- Solver contract: one thread, Seed 0, Presolve Auto, MIPGap 0,
  MIPGapAbs 0, verified HGA-FULL start for all C6-derived arms.
- Panel: the unchanged ten-instance Round 40 diagnostic panel, including both
  named witnesses and the numerical fail-closed endpoint.
- Static evidence: 30 root LP rows and 30 MIP rows. Twenty-seven MIP rows have
  strict certificates; three are accepted noncertificates; false certificates
  are zero.
- Default regression: all three pre and post implicit-default/explicit-off
  pairs match in all 25 deterministic fields, and every pre/post trajectory
  hash matches.
- No official cap is 3600 seconds or more; the two selected witnesses use the
  maximum allowed 1800-second external cap.

The three noncertificates are intentionally visible. ST-K2-I times out on the
fragmentation witness. Core on the numerical endpoint and Extended on the K4
positive control receive native OPTIMAL statuses and verified incumbents, but
native-bound residuals of `2.25e-7` and `1.33e-7` fail the stricter Round 41
certificate gate. Neither is promoted to a certificate.

## Root strength and model growth

The direct one-interval helper solves exactly one LP for K1, the left midpoint
interval, or the right midpoint interval. It avoids inferring a missing child
bound from a scheduled external-tree run. On six instances with a positive
external-K2-minus-K1 denominator, I, Core, and Extended all capture the
external-K2 bound to numerical precision; Core's minimum reported capture is
`0.9999999999999679`. The other four instances have a zero denominator, so the
ratio is undefined rather than reported as a success. On the strongest K4
case, Core alone improves the K1/K2-disjunctive bound by about `4.68e-5`.

Across the ten root models, Core averages 1200.9 variables versus 961.3 for I.
Its variable ratio ranges from 1.192 to 1.474 (below the frozen 2.5 limit), and
its nonzero ratio averages 1.071 with a maximum of 1.139. Extended adds eight
variables beyond Core per model and does not improve either named witness's
root bound. Selector fractionality is zero in every recorded root. Mean route,
visit, and inventory-bit fractionality and the ambiguity measures remain of
similar magnitude across arms; no diagnostic supports a runtime dispatch rule.

## Opposing-witness result

| Witness/arm | Strict | Exact phase (s) | Work | Frozen comparison |
|---|---:|---:|---:|---|
| fragmentation external K4 | yes | 1777.865 | 4014.177 | reference |
| fragmentation Core | yes | 760.801 | 1738.405 | 0.428 time, 0.433 Work: pass |
| coarse weakness external K4 | yes | 74.789 | 133.735 | reference |
| coarse weakness external K1 | yes | 406.559 | 739.784 | reference |
| coarse weakness Core | yes | 98.225 | 183.296 | 0.242/0.248 vs K1; 1.313/1.371 vs K4: fail |

The detailed reference, I, Core, Extended, and P-GRB trajectories are in
`representative_trajectory_analysis.md` and its CSV companion.

## Answers to the required questions

### 1. What current C6 decomposition problem is being addressed?

External interval decomposition trades interval-local formulation strength for
multiple independent native MIP trees. K4 can duplicate search and cause a
fragmentation regression; K1 avoids that fragmentation but can be too weak.
Existing LP-bound and child-gain signals do not reliably select between those
regimes. Round 41 tests whether fixed interval strength can be encoded in one
static MIP without an external terminal-tree scheduler.

### 2. Which historical CPLEX operations are not directly available in Gurobi?

The historical code read node-local continuous-G bounds, created two children
with `CPXcallbackmakebranch`, and later attached local rows to a child subtree.
The current Gurobi C callback API supplies callback cuts, lazy rows, and
solution submission, but no counterpart for application-created continuous-G
children or named child-local inherited row packs. Static variables, linear
rows, indicators, and perspective formulations are supported before optimize.
No direct callback migration was attempted.

### 3. Is static single-tree segmentation technically feasible?

Yes. A deterministic, hashed canonical model with two selectors can be loaded
by Gurobi, presolved, solved with one model and one optimize call, decoded in
original space, and checked by the independent verifier. Root-LP mode remains
diagnostic and cannot certify.

### 4. Is ST-K2-I exact and operational?

Yes as an integer formulation. It exactly covers the midpoint partition,
enforces selector exclusivity and G/Y/S/P domain aggregation, activates the
complete interval factory with native indicators, and uses one proof job. It
strictly certifies 9 of 10 panel MIPs; the remaining major-witness row is an
honest time-limit noncertificate. This is operational evidence, not a claim of
LP-relaxation equivalence in general.

### 5. How strong is ST-K2-I relative to K1 and external K2?

On all six positive-denominator panel instances, its root objective matches the
external-K2 disjunctive bound within numerical tolerance, recovering essentially
100% of the K2-over-K1 improvement. On four zero-denominator instances the
capture ratio is undefined. The result is empirical for this frozen panel and
does not establish a general hull-equivalence theorem.

### 6. How much interval strength does ST-K2-P recover?

Core also recovers essentially 100% on every positive-denominator row; its
minimum capture is `0.9999999999999679`. On the strongest K4 case it is slightly
stronger than the external-K2 disjunctive bound by `4.68e-5`, although the K2
denominator there is zero. Extended does not improve the named witness bounds.

### 7. Which interval-local strengthening families are essential?

This experiment establishes that exact G/Y/S/P aggregation plus the complete
existing interval pack is jointly sufficient to retain the observed K2 bound.
Core's disaggregated inventory-bit/G products materially improve search versus
I on both witnesses, even where the root objective is unchanged. The Extended
direct-Gini, objective-estimator, penalty-closure, and selected SP-copy pack is
not essential on the observed evidence: it adds no named-witness root strength
and is slower than Core. Because no family-by-family confirmation ablation was
authorized, the data do not identify one remaining indicator family as uniquely
essential; the encoding matrix records every family without overclaiming.

### 8. Does single-tree segmentation reduce the major fragmentation regression?

Core does. It certifies in 760.801 seconds and 1738.405 Work versus external
K4's 1777.865 seconds and 4014.177 Work, while using one integer proof job.
The frozen ratios are 0.428 and 0.433, both below 0.80. I does not: it reaches
the cap without a certificate. Extended certifies but misses the 0.80 ratios.

### 9. Does it preserve the strongest K4 positive case?

Not within the frozen materiality rule. Core certifies and strongly beats K1,
but it needs 1.313 times K4 exact-phase time and 1.371 times K4 Work. Those
ratios exceed the allowed 1.25. Thus it preserves correctness, not K4's best
performance.

### 10. Does the candidate reduce both fragmentation and coarse-MIP weakness?

It addresses both mechanisms relative to their direct references: Core beats
external K4 on the fragmentation witness and beats K1 by about 76% in time and
75% in Work on the coarse-weakness witness. It nevertheless fails the combined
gate because it is too slow relative to K4 on the positive control. The answer
under the predeclared success criterion is no.

### 11. Is model growth compatible with K4 or larger instances?

K2 Core growth is reasonable (maximum 1.474 times I variables and 1.139 times
I nonzeros), so engineering size alone does not rule out K4. Runtime evidence
does: the K2 candidate already misses the opposing-witness performance gate,
and K4 would add selector/disaggregation objects. Compatibility was therefore
not established sufficiently to justify expansion.

### 12. Was ST-K4-P justified and implemented?

No. Gate D required A, B, and C. Gate C failed, so ST-K4-P was neither justified
nor implemented. Split points, HGA, rho, presolve, and branching rules remain
unchanged.

### 13. Did any candidate pass held-out validation?

No candidate was sent to held-out validation. Gate E required the preceding
gates, and Gate C failed. The predeclared diagnostic panel was completed; no
unfavorable instance was removed or replaced.

### 14. Should a single-tree candidate advance, or should C6 remain unchanged?

C6 should remain unchanged. Core is a useful research prototype and a credible
future basis for more compact disjunctive strengthening, but it is not stable
enough across the two mechanisms for promotion. A separate future round could
study why external K4 remains better on the positive control; it should not add
an instance-specific K1/K4 dispatcher.

### 15. What was learned from every failed variant?

- **ST-K2-I:** exact indicators and one tree are not sufficient for robust
  search; it caps on the fragmentation witness despite full K2 root capture.
- **ST-K2-P-Core:** the inventory-product perspective block is operationally
  valuable and solves the fragmentation problem, but K2 segmentation still
  loses too much to external K4's best case. Root strength is not a complete
  predictor of proof time.
- **ST-K2-P-Extended:** selected S/P/H/WSP copies add no named-witness root
  strength, nearly double Core time on the fragmentation witness, and trigger a
  correct fail-closed certificate rejection on the positive control.
- **ST-K2-H:** not implemented because direct left/right roots plus the static
  formulations already showed full K2-bound capture; a full-hull oracle was not
  needed to diagnose missing root strength.
- **ST-K4-P and held-out expansion:** correctly not attempted after Gate C
  failed. This prevents post-result threshold changes or an unjustified larger
  model.

## Recommendation

Retain C6-HGA-FULL K=4, rho=0.01. Preserve Core as an explicit default-off
research arm and its formulation/audit infrastructure. If continued, focus on
uniform search-strength explanations that can preserve the K4 positive control,
not runtime dispatch, witness-specific packs, or unsupported callback branching.

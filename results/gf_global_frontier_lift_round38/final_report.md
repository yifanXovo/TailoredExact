# ExactEBRP Round 38 final report

## Decision

**Do not promote G2-A. Retain C6-HGA-FULL with K=4 and rho=0.01 as the
validated default mainline.** No stable general improvement was found.

Round 38 implemented an explicit, deterministic, default-off
`pilot-next-frontier-complete` experiment. The protected path remained
structurally equivalent before and after implementation (18/18 comparisons in
each gate). Across 42 official runs
(21 pairs), all coverage, lifecycle,
monotonic-bound, feasibility, artifact, and certificate gates passed; false
certificates and certificate regressions were both zero.

## Mechanism result

Prior Round 37 forensics found 0/10 historical G1 exposures whose midpoint
child bound reached the next strict frontier. Round 38 then obtained
19 complete G2-A child evaluations over smoke,
full-panel diagnostic, and confirmation stages. Again, **0 reached the next
strict frontier and 0 refinements were accepted**. H1 therefore has no
empirical accepted-lift class, and G2-A is too selective to explain the
observed computational effects.

The effects instead arise from the rejected pilot path. G2-A completes all
initial LPs, evaluates and discards the midpoint children, then resumes the
unchanged parent at the next strict frontier. On the stable V20 witness this
changes the native-target path and confirms a gap improvement of
0.112251 with AUC improvement
0.094528. On the original stable V50
adversarial witness the final gap ties, with AUC change
-0.000789.

However, V50 tight-T is adverse at both 480 and 900 seconds. At confirmation,
the common-UB gap change is
-0.009008 and the AUC change is
-0.010889. C6 reaches an intermediate
target, performs an exact child-infeasibility split, and obtains a stronger
lower bound; G2-A's rejected pilot instead sends the unchanged parent directly
toward the higher frontier and remains deadline-open. This is a confirmed
bidirectional path effect, not a global-frontier lift.

## Hypotheses

- H1 is not supported: 19 evaluated midpoints, 0 next-frontier completions.
- H2 is rejected: the original witnesses look favorable, but a second V50
  stratum has a confirmed common-UB gap and AUC regression.
- H3 remains diagnostic: no live refined descendants existed; target/split
  reordering explains the observations but supplies no simple online rule.
- H4/G2-B was not activated: multi-cell speculative enumeration would add
  overhead without evidence of an accepted lift.

## Exactness and mainline status

G2-A never uses elapsed time, Work, nodes, V/M, scenario labels, instance
identity, hardware state, or historical outcomes. Its acceptance test uses
only complete valid LP dispositions, Gini geometry, the unique global
minimum, the next strict frontier, and the existing correctness tolerance.
Speculative children are either atomically incorporated as a complete cover or
discarded before C6 resumes. No accepted G2-A split occurred in the official
experiments, and the unchanged certificate verifier correctly rejected
deadline-open runs.

The experimental code and telemetry remain available behind an explicit
default-off option for reproducibility. They do not change C6, K, rho, HGA
startup, proof cutoff semantics, or certificate semantics.

## Learned mechanism and next step

Initial global-frontier geometry alone did not yield a stable online rule.
Before any future G2-B enumeration, a later round should isolate two distinct
effects: complete-initial-census scheduling and rejected-lookahead target
reordering. Those experiments must remain default-off and must not infer a
policy from instance classes or historical winners.

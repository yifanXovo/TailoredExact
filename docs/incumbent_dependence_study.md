# Incumbent Dependence Study

## Question

The exact certificate is lower-bound driven, but a strong verified upper bound
shrinks the improving Gini range and lets relaxation-only interval proofs
fathom more leaves. This study compares UB sources without allowing any UB
source to contribute lower-bound evidence.

## Compared Sources

Rows are summarized in
`results/primal_heuristic_round/incumbent_dependence_summary.csv`.

- Empty fallback only.
- BPC-owned portfolio probe.
- New paper primal heuristic (`hga-tgbc`).
- Explicit exported heuristic incumbent JSON.
- Diagnostic archive incumbent.

The diagnostic archive row is intentionally not paper-core evidence. It is
kept to quantify the cost of replacing local-history scanning with a
reproducible heuristic input.

## Regenerated V12 M2

The new heuristic found a verifier-passed UB of `0.756165366387`. The previous
diagnostic archive row still has a stronger UB of `0.719065249476`, which
explains why archive-dependent runs can close or bound-fathom more aggressively.
With the heuristic UB, a 300s paper-core row reached LB `0.68873937145` but did
not close; a 120s rerun with the latest guard reached LB `0.59214123903`.

## Regenerated V12 M1

The heuristic found a verifier-passed UB near `0.369699`; paper-core improved
the active incumbent to `0.364375057616` during the frontier run. The 300s row
reached LB `0.354350322125` but remained noncertified.

## Interpretation

Strong UBs materially improve relaxation-fathoming. The archive incumbent is
useful diagnostic evidence, but it is not an acceptable default for the paper
algorithm. The immediate next primal target is to strengthen the seeded
HGA-style heuristic toward the archived V12 M2 UB while keeping route-plan
exports verifier-gated and reproducible.

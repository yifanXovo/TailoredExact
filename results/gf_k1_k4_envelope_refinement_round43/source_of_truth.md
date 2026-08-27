# Round 43 source of truth

- Base: `codex/round42-decomposition-architecture-optimization` at `a188181a3257270eebc6d546b121a168184ae951`; upstream was exactly
  synchronized (ahead 0, behind 0).
- Research branch: `codex/round43-k1-k4-envelope-refinement`.
- Machine: `WIN-3NO58RVQ4VC`; Gurobi 13.0.2; one thread; Seed 0;
  Presolve Auto; zero relative and absolute gaps.
- Dataset: the unchanged Round 39 10/7/7 Round 42 split. No V20 or V50 run is
  permitted. Validation and holdout candidate results are unopened at freeze.
- Validated default: C6-HGA-FULL, K0=4, rho=0.01. All Round 43 behavior is off
  unless explicitly selected.
- Baseline before changes: Release build passed and CTest was 20/20. The Python
  suite was 117/118 because the Round 41 source-name test was not updated after
  the Round 42 shared-function rename; this pre-existing failure is recorded
  and must be repaired without weakening its assertions.
- The raw checkout contained old generated artifacts despite the expected clean
  start. Six tracked artifacts are preserved in a named Git stash and exact
  untracked paths remain on disk behind local excludes. Neither is Round 43
  evidence or part of the PR.
- Existing Round 40 comparator rows are inventory-only until the required
  post-implementation model/contract equivalence audit passes. C6 and P-GRB are
  always rerun contemporaneously on the major regression, strongest control,
  and one easy startup guard.

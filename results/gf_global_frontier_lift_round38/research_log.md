# Round 38 research log

## 2026-08-13: provenance and pre-result freeze

* GitHub CLI authentication was repaired. Direct github.com traffic timed out;
  OAuth succeeded through the existing local proxy on 127.0.0.1:7890. The
  credential is stored in Windows Credential Manager with repo, read:org, and
  gist scopes.
* PR 84 was found merged at 2026-08-13T03:06:02Z. Remote main was fetched and
  Round 38 branched from merge 1459308492a5eceed523dee53b5f9d79141b5242.
* The three protected tracked changes retained their pre-branch SHA-256 values.
* A new GNU 14.2.0 Release/Gurobi 13.0.2 baseline build was configured in
  build_round38_baseline/official/gurobi; 16/16 C++ tests passed.
* The 12-row development panel and hypotheses were frozen before any Round 38
  candidate outcome was generated.
## Protected baseline detail

- Reconciled the latest local topic with merged GitHub `main`; the Round 37
  merge commit is `1459308492a5eceed523dee53b5f9d79141b5242` and is content
  equivalent to the Round 37 topic tip.
- Preserved all pre-existing mixed-worktree files and created the dedicated
  `agent/round38-global-frontier-lift` branch.
- A clean baseline build passed all 16 inherited C++ tests.  The frozen Round
  37 executable and clean Round 38 baseline passed 18/18 structural
  equivalence checks across a small and a real-split case.

## Default-off implementation and revalidation

- Added isolated `off|pilot-next-frontier-complete` policy plumbing.  `off` is
  the default and is the only path eligible for baseline equivalence.
- Added pure deterministic frontier selection/lift functions and six C++ unit
  checks.  The protocol linter passed four checks, including forbidden-input
  isolation.
- The candidate executable with the policy explicitly `off` passed the same
  18/18 structural equivalence gate against the frozen Round 37 executable.

## Prior forensic result

- Ten prior exposed Round 37 G1 runs reduced to six unique initial-frontier
  geometries.  None had `b+ >= t`; strict next-frontier completion was 0/10.
- This falsified the claim that G2-A would reproduce prior G1 splits.  The
  policy remained useful as an explicit test of whether a global frontier
  rule could suppress the known V50 regression without losing the V20 signal.

## Exploratory smoke

- Froze six serial pairs (panel ordinals 1, 4, 8, 9, 10, and 14) at 180
  seconds.  Matrix SHA-256 is
  `39418e71216f4d8029ca5a75ab95d98ffd2878a29e72558094b87c651e2e63a2`;
  executable SHA-256 is
  `701d6cae4bdb9639ddc8a9046618ec97cdb5687ee534c808efb3497948b4077d`.
- One outer orchestration wrapper expired while the third row was running.
  The incomplete row was preserved under `invalidated_attempts/`, was never
  assigned a completion marker, and was excluded from all evidence.  The
  checksum-resumable runner then reran that row from scratch and completed all
  12 official rows.
- All artifact, arm, coverage, lifecycle, monotonic-bound, feasibility, and
  certificate gates passed; false certificates and certificate regressions
  were both zero.
- Five G2-A rows evaluated a child pair.  No pair reached the next strict
  frontier, so actual G2-A refinements were 0/6.  The stable V20 witness
  improved its final common-UB gap by `0.0799122`; the stable V50 regression
  witness tied at final gap.  Other final gaps tied.  This advances the
  unchanged executable to a full-panel diagnostic, but cannot yet support
  promotion because the only possible effect is rejected-lookahead path
  perturbation rather than an accepted global-frontier lift.

## Full-panel diagnostic

- Froze all 12 panel rows as 24 serial runs at a 480-second process cap.
  Matrix SHA-256 is
  `c13473edfa3c24eaf13befbeb65ae4f25d3a02cac59b9ad93d93e2a0342d0590`;
  the executable remained byte-identical to smoke.
- All 24 rows completed atomically. Run/artifact/coverage/lifecycle/bound/
  feasibility gates passed, with zero false certificates and zero certificate
  regressions.
- Eleven G2-A rows evaluated children; no pair reached the next strict
  frontier and no refinement was accepted. Common-UB final gaps had four
  improvements, one regression, and seven ties. The stable V20 witness
  improved, the stable V50 adversarial witness tied, and V50 tight-T was the
  single regression. The predeclared rule selected those three rows for
  confirmation.

## Selected confirmation and decision

- Froze six serial runs at a 900-second process cap. Matrix SHA-256 is
  `0bf37f6c8ef91857799d65c9828e73e9830874ce564191274007d093da9f4598`;
  the executable again remained byte-identical.
- The stable V20 gap/AUC improvements persisted (`0.112251`/`0.094528`), and
  the stable V50 final gap remained tied (AUC `-0.000789`). V50 tight-T
  retained a common-UB gap regression of `-0.009008` and AUC regression of
  `-0.010889`.
- Across smoke, diagnostic, and confirmation there were 42 official runs,
  21 pairs, 19 child evaluations, zero next-frontier completions, zero
  accepted G2-A refinements, zero false certificates, and zero certificate
  regressions.
- The general mechanism is rejected for promotion. Observed gains and losses
  arise from completing the initial census, evaluating/discarding speculative
  children, and reordering parent targets/splits. This is bidirectional path
  behavior, not an accepted global-frontier lift. C6-HGA-FULL, K=4,
  rho=0.01 remains unchanged.

## Final verification

- The full Release/Gurobi build preserved executable SHA-256
  `701d6cae4bdb9639ddc8a9046618ec97cdb5687ee534c808efb3497948b4077d`.
- Compiled suite: 17/17 passed. Python suite: 94/94 passed. Final explicit-off
  equivalence: 18/18 passed. Compact final audit: 40 checks passed.

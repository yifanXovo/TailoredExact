# Round 24 final report

## Outcome

Round 24 delivers the optional plain Gurobi adapter, a shared canonical compact-model source, and solver-neutral external global-Gini-tree architecture with audited retained-leaf and complete warm-start mechanisms. Both release configurations build, and all prescribed source-level, C++, and Python validation passes. The installed Gurobi 13.0.2 runtime has no usable license (error 10009), so the preregistered Stage 0 gate fails closed and all 41 Stage 1/2 rows are excluded without execution. No performance or migration claim is made. Corrected CPLEX S0/F0 remains the stable paper mainline.

## Required questions

1. **Repository provenance.** The Round 24 branch was created from local `a977efe52a79877c057ce8e3421901979d16f1be`; the one inspection fetch observed remote main `f115e9bb600f68e5368df78f06203331a800a33b`. Their source trees were identical although remote history had two merge commits.

2. **Gurobi discovery/license.** The existing installation at `D:/gurobi1302/win64` was found. It is not licensed in this environment: a minimal environment/optimize attempt fails with error 10009.

3. **Exact Gurobi identity.** Command-line/runtime version is 13.0.2, build `v13.0.2rc1`; headers are 13.0.2 and the dynamically loaded native library is `gurobi130.dll`.

4. **Secrets.** No license file content was read. No key, token, user, hostid, WLS access identifier, or secret is committed. Serialized failures are sanitized to `gurobi_error_10009:No Gurobi license found`.

5. **P-GRB mathematical model.** Yes at the canonical-artifact boundary: P-CPX and P-GRB are handed identical LP bytes from one writer. The Gurobi native model could not be created, so native-import equivalence is blocked rather than asserted.

6. **Canonical audits.** Objective, row, column, domain, bound, sense, RHS, and coefficient audits pass by exact byte identity on the toy and V12_M1 artifacts. Toy SHA-256 is `c6bb54...71ff`; V12_M1 is `4f3aa0...22fe`. Native Gurobi counts/Fingerprint remain unavailable, so the overall Stage 0 cross-solver-native gate is not a full pass.

7. **Plain Gurobi certificates.** None. P-GRB stops before model creation/optimize and correctly serializes no status, bound, solution, or strict certificate. The certificate adapter’s positive and negative gates pass unit tests.

8. **Four-instance P-GRB versus P-CPX.** Unavailable. All four pairs are excluded by the Stage 0 license gate; there are no final-LB, common-gap, AUC, time, work, or certificate comparisons.

9. **Scheduler reuse.** Yes. `ExternalGiniTree` uses the existing `ControllingLeafScheduler` as the sole leaf-selection/budget/checkpoint scheduler; tests also scan against instance-dependent selection.

10. **Coverage.** The shared geometry exactly covers the improving root range and every split parent by construction and exhaustive tests. The CPLEX F0 smoke reports valid root and parent-child coverage.

11. **Bound validity/monotonicity.** Parent-copy inheritance is valid by feasible-set containment; only finite validated native bounds can strengthen it. Leaf and minimum-frontier global LBs are monotone in tests and the CPLEX smoke. Incumbents/starts never become LBs.

12. **Optimize calls.** Architecturally S0-SAFE has one `CPXmipopt`; external arms may have one per leaf attempt; retained Gurobi may repeat optimize on an unchanged model. Official counts are unavailable. The CPLEX F0 smoke has one model/read/optimize; Gurobi smokes have zero.

13. **Root/presolve executions.** Official counts are unavailable. The CPLEX F0 smoke has one distinct root/presolve execution; the Gurobi smokes have zero.

14. **Repeated overhead.** Not quantified because official rows were excluded. The CPLEX smoke’s single root took approximately 1.11 seconds, but it is a structural diagnostic, not an architecture estimate.

15. **Safe presolve-off single-tree advantage.** Unavailable; all four Stage 1C rows were excluded.

16. **Presolve-on diagnostic speed advantage.** Unavailable; no performance row was run.

17. **Unsafe evidence exclusion.** Yes. The switch defaults false, requires Round 24 research mode, visibly labels the arm known unsafe, forces native model configuration invalid, and forces strict original-problem certification false even at native status 101.

18. **Moderate4301 fail-closed behavior.** Yes as a preserved correctness policy and immutable Round 23 result. Round 23 proved both witnesses feasible and identified presolve-induced feasible-child loss; corrected S0 reached time limit without the invalid status-103 certificate. Round 24’s unsafe arm cannot certify. New Stage 1A rows were excluded, so no new runtime claim is substituted.

19. **Static witness retention.** The static model removes the continuous-callback child-loss mechanism by construction, and mapping/interval tests retain valid witnesses. The CPLEX V12 F0 model passes runtime structural audit. Moderate4301 CPLEX/Gurobi runtime witness rows were not run; Gurobi presolve witness retention is unavailable.

20. **Unchanged Gurobi leaf resume.** Implemented and unit-tested: the same model object is retained, only TimeLimit may change, reset is forbidden, and continuation requires cumulative native evidence. Runtime observation is unavailable because no licensed model exists.

21. **Fresh versus retained waste.** Not measured; Stage 1B is excluded.

22. **State lost at a split.** All native parent-tree state is lost: presolve products, basis, cuts, pseudocosts, node queue, pools, and internal heuristics. Children inherit only the proved parent LB and may receive separately verified primal starts.

23. **External Gurobi versus CPLEX.** Unavailable. CPLEX’s structural smoke passes; Gurobi never reaches optimize, which is a capability blockage rather than solver-strength evidence.

24. **Does Gurobi strength offset restart cost?** Unknown; no licensed performance data exist.

25. **Warm-start counts.** Official available/submitted counts are unavailable because no warm run began. Runtime submitted count is zero.

26. **Start disposition.** No native starts were submitted, accepted, rejected, or ignored. Complete mapping and rejection cases pass unit tests only.

27. **First-incumbent effect.** Unavailable.

28. **LB/gap/AUC/closure effect.** Unavailable.

29. **Warm-start overhead/regression.** Unavailable.

30. **Warm Gurobi versus S0-SAFE.** Unavailable on every tested case; no approach/exceed claim is permitted.

31. **Warm Gurobi versus unsafe speed ceiling.** Unavailable; the unsafe diagnostic is also excluded from authoritative exact evidence.

32. **Longer migration round.** Not yet justified. The implementation warrants a short licensed qualification, not a long matrix.

33. **Stable mainline.** Corrected CPLEX S0/F0 remains unchanged and is the sole stable paper mainline. P1, P2, F3, native starts, and instance dispatch remain off.

34. **Single next experiment.** Make a valid local Gurobi license available, rerun Stage 0 unchanged, and—only if every gate passes—run the preregistered 120-second V12_M2 fresh/cold/warm Stage 1B gate.

## Validation and run accounting

Prechange validation passed 8 C++ executables/111 groups and 6 Python suites/107 checks. Postchange, each clean release configuration passes 9 C++ executables and 191 groups/checks (382 total); 5 Python suite runs pass 106 checks. Failures: zero in the prescribed sequential suites. Two transient cross-configuration temp-file collisions from an excluded parallel orchestration attempt are disclosed; both sequential reruns passed.

Stage 0 completed the two builds, canonical exports, CPLEX exact toy, CPLEX external F0 smoke, Gurobi license smokes, static scans, and certificate tests. The blocking Gurobi license gate failed once. Official Stage 1 planned 13 rows and Stage 2 planned 28: completed 0, failed runs 0, interrupted 0, excluded without execution 41. Counting the blocking gate itself yields completed 0 / failed 1 / interrupted 0 / excluded 41.

The Stage 0 CPLEX F0 smoke used one model/read/optimize/root-presolve execution and ended with valid global LB `0.26111604306990788`, verified UB `0.493696053862549`, and an open-leaf certificate rejection. These values are diagnostic only. All official final-LB/common-gap/AUC and paired optimize/restart metrics are unavailable. Certificate gains/losses across official pairs are 0/0 because no pair executed.

## Separate conclusions

- **Plain Gurobi benchmark:** implemented; runtime/performance unavailable due license.
- **Canonical model correctness:** exact cross-adapter bytes pass on toy and V12_M1; native Gurobi import is blocked.
- **Gurobi certificate correctness:** fail-closed policy and tests pass; no runtime certificate exists.
- **Persistent single-tree value:** not quantified.
- **External restart cost:** not quantified.
- **Same-leaf native resume:** implemented/tested, not runtime-observed.
- **Gurobi backend strength:** unknown.
- **Explicit warm-start effect:** unknown; zero runtime submissions.
- **Moderate4301 safety:** corrected S0 remains fail-closed; unsafe presolve-on results remain non-authoritative.
- **Migration feasibility:** source/build feasibility established, runtime feasibility not established.
- **Stable status:** corrected CPLEX S0/F0 remains the stable paper mainline.

# Round 37 source of truth

Round 37 starts from `origin/main` merge commit
`414c01216bb3aa30eb1f27f390b6f23bf06cb2eb`. That merge and the Round 36
research head `4eb8e36515bbb2dd36ba49c5605c7c1b12a7ae32` have identical trees
(`6d0b1e2727c7729d9013d33fb341145d4ebab135`). The working branch is
`agent/round37-gini-geometry-mechanism`.

The solver mainline entering this round is **C6-HGA-FULL** with K=4 and
rho=0.01. Round 36 did not promote its BW-P candidate.

Round 36's `final_report.md` and `final_audit_decision.json` are frozen Stage B
decision artifacts. Their hashes are inputs to the separately frozen Stage C
manifest, so they remain immutable historical evidence. The terminal Round 36
scientific decision is recorded by `stage_c_final_report.md` and
`stage_c_final_audit.json`: BW-P failed its predeclared broad performance gate,
C6-HGA-FULL stayed unchanged, and no automatic promotion occurred. The
consolidated interpretation is in `round36_reporting_consolidation.md`.

Pull request 83 was subsequently merged into `main` at
`2026-08-12T14:37:45Z`. Therefore the committed PR record and completion audit
correctly describe the pre-merge completion checkpoint but are not current PR
status records. They are preserved rather than rewritten.

All pre-existing modified or untracked files outside the explicitly scoped
Round 36 cleanup are user work. In particular, the three protected tracked
files listed in `round36_cleanup_manifest.json` are hash-guarded and excluded
from Round 37 staging.

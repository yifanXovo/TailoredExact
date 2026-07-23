# Stage 0 incident: C4 lifecycle parser normalization

The first post-commit deadline suite exposed a general configuration bug before
any official performance run. The command correctly requested
`round29-same-leaf-in-memory-model`, but CLI normalization accepted only the
two legacy lifecycle spellings and replaced every other value with
`retained-per-leaf`. The result object labeled the arm from the C4 scheduling
selector, so the requested lifecycle remained visible even though the
effective option differed.

The frozen C4 option guard failed closed with
`c4_requires_round29_same_leaf_in_memory_model_lifecycle`. No invalid row
entered an official matrix. The affected clean builds, build/test record, and
five deadline runs are retained under paths named
`invalidated_pre_lifecycle_parser_fix`.

The general fix adds explicit parser acceptance for the paper-event,
replica-event, and Round 29 lifecycle spellings. A permanent protocol test
checks that the C4 spelling occurs in the normalization block. After the fix,
both clean builds and all Stage 0 suites are rerun from fresh directories; no
C4 mathematical rule, threshold, geometry, or experiment parameter changes.

# Round128 methods and finite differences

| ID | Complete independently paid method | Difference from ordinary E2 MB |
| --- | --- | --- |
| P | Original cold compact P-GRB, native default parameters, no H or Start | Original compact benchmark representation and solver path |
| MB | Frozen full M-B / GI-TBC in the one E2 research build | None |
| MD-R | Inclusive-root control v1; same full H/R/C_R/C_G, fixed own-U0 root, one complete LP then one complete MIP with own Start | Removes the external probing/target/split/scheduling package; omits only the named pseudo-infeasibility shortcut if it would be emitted; adds mandatory own-Start pre-LP validation and explicit complete-root-return gates |
| MS2 | Original M-B controller, H/R/C_G and ordered supply plus pair support | Deletes only triple support cover/conditional-handling rows |

The new `--round128-mode md-r` entry is off by default. It reuses the existing single-root control and shared backend. The `round128EmitIntervalNoImproverDomainClosure` predicate guards the named proof shortcut in both `IntervalRowFactory.cpp` and the direct fallback in `CplexBaseline.cpp`. The valid weighted penalty lower-bound row remains outside that guard. No model row index, global penalty option or constant-row filter controls the omission. Ordinary MB, MS2 and P do not enter the new validation, scheduling or return gates. They retain their original generated matrices and parameter paths; E2 has its own PE identity and is never described as byte-identical to E1.

Model equality checks use duplicate-preserving complete rows, every column's actual VType/bounds/objective, and the complete H action/fleet trace. Fingerprints are descriptive identities rather than semantic proofs. Preformal role exports use archived same-H root scopes only as qualification fixtures; formal methods independently obtain their own U0. Actual formal roots are compared again after execution. A preprocessing difference or unmatched H/scope restricts attribution to complete-method results.

MS2 retains the original per-vehicle order, pair-before-triple enumeration, ordered supply compatibility, and shared per-model 50000 candidate cap. The three roles have 1120, 2660 and 21420 pair-plus-triple candidates; none binds that cap. Triple row deletions are respectively 910, 2280 and 19635, while all 210, 380 and 1785 pair rows remain. No four-station family or cap reallocation is added.

All formal arms use lambda=.15, pickup=drop=60 seconds, H_seed=20260626, Threads=MIPThreads=1, affinity mask 4, Presolve Auto, MIPFocus=0, native Cuts=-1, MIPGap=MIPGapAbs=0 and the inherited feasibility/integer/optimality tolerances. The original 30-second shutdown reserve, 6-second native offset and 2-second hard-stop offset remain. P receives no free H, Start or linear cutoff. Each MB-type method independently pays complete H and its own native work; no fleet, bound, basis, tree or cache crosses arms or Seeds.

Only the predeclared 16 arms and 17 typed comparisons are formal. The three known inputs are not unseen confirmation samples. Seed repeats add matched observations rather than new problems; shared arms are not independent replications. R127 E1 Seed1 appears only as historical context, including all unfavorable tiny, C_R and PT results. No R127 P time is used to evaluate a Round128 Seed1 MS2.

Evidence-field note: the inherited `formal_performance` field refers to the older Round108 whole-arm clock that included post-exit audit. Round128 retains that historical reader field without relabelling it. Current qualification uses `formal_protocol_qualified`, `numbers_qualified`, `certificate_qualified` and the independently sealed production/verification/total clocks; only a qualified certificate receives `T_cert=T_produce`.

The full mapped own fleet, actual returned model, Start readback, call-scoped return/coverage and raw signed-gap gates remain mandatory. The inherited startup-zero policy remains explicit and records D as unexposed. MD-R requires a complete native optimal root return for a nonzero certificate; a TIME_LIMIT/INTERRUPTED return may supply qualified scoped bounds and a valid open result, never native optimality. These finite checks do not claim a rational proof of every generated matrix or a global floating-point error bound.

Publication and recovery retain original raw outputs and failed qualification records. R127's three MD entries remain unstarted; this revised control does not rewrite their status or select another main algorithm.

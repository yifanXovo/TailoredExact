## Summary

- publish verifier-approved HGA improvements at strict-best events without changing the HGA RNG or logical prefix
- add a bounded BRP candidate builder plus complete Gurobi variable mapping, current-row residual checks, `GRBcbsolution` submission, and conservative post-solve acceptance labels
- unify the canonical F0 configuration, correct root cut-pass sampling, add Single-H and fixed-inventory diagnostics, and keep every Round 60 feature default-off
- add frozen Round 60 experiment/analysis drivers and a complete evidence bundle under `results/gf_verified_candidate_native_round60`

## Decision

HGA event publication materially improves the D6/D7 deadline solutions and remains an explicit research switch. Native injection is not promoted: its 120-second D3 gap improvement reverses to a 154.29-second certificate slowdown in the matched 600-second run. Stable `paper-k1-am-sf` and official P-GRB behavior remain unchanged.

## Verification

- Release build completed successfully
- 37/37 CTest tests passed
- canonical D2/D3/D4 F0 LP files are byte-identical to the Round 59 artifacts
- 52/72 charged optimization attempts; 6/6 native micros; maximum observed optimizer concurrency 1
- matched fixed-window, long-window, HGA publication, split attribution, and full-integration experiments recorded in the result bundle

## Key evidence

- D6/D7 HGA publication reduces deadline UB by 85.40%/86.01% with identical common generation prefixes
- D3 600-second INJECT and OFF reach the same incumbent, but INJECT certifies 154.29 seconds later
- final native micro validates all 214 current linear rows with zero violation and confirms the submitted integer vector as the final native solution
- fixed rounded-root inventory closes product equations to machine precision; D3/D4 become route-feasible only after relaxing the route-duration horizon, while D6 is feasible under the original horizon

The two failed attempts remain in the process ledger and count against the frozen budget. Raw local solver outputs remain ignored; compact auditable artifacts and final logs are committed.

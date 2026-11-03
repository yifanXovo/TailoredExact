# Matched pure-B root LP bridge

The fixed R150 pure-B N-B35 root is the sole newly optimized domain. Both new models retain the original objective, constant, cutoff, physical/resource rows, supports and variable bounds; every integer column is relaxed and every variable remains free. Removing the added cap rows recovers the same relaxed B model. B itself is not reoptimized. The saved old complete point is checked against all original rows and bounds before separation is measured. Source archives and member hashes are recorded in reuse_index.json.

| Model | Qualified numerical LP value | Increment over previous layer | New cap rows / NZ |
|---|---:|---:|---:|
| Saved B | .3278337721771161 | inherited | 0 / 0 |
| P | .33216166600112773 | .00432789382401161 | 537 / 1074 |
| C | .337310427549131 | .00514876154800326 | 537 / 1074 |

C-B=.009476655372014864. C was solved first, then P was admitted because C provided new distinguishable information. Both returned OPTIMAL with Seed0/Threads1, one Optimize per matrix and a 120-second Native cap. Actual Optimize walls were approximately 1.47651 seconds for C and 1.26605 seconds for P; exact costs, Runtime and Work are in the raw receipts/results and outer fees. No extra quality Optimize was needed. New numerical primal-dual differences are approximately -5.0e-16 (C) and -2.2e-16 (P), attributable to floating evaluation. These are numerical qualifications rather than rational optimality proofs.

The old B point violates P in 24 states and C in 26 states at 1e-8; the respective maxima are approximately .0305402 and .0614552. Those are saved-point separation observations. The LP values above come from complete free reoptimization, not from adding the largest violation to an old bound. Both actual models contain one row per applicable state; C does not omit the 65 uniform-only states at the 1e-12 substantive-resolution definition. Actual outward arithmetic yields 502 strict binary64 beta<beta0 comparisons, of which 30 have no distinguishable extra information at that resolution.

N-C20 has 490 supported states and 470 effective cap rows. Its old qualified optimal point remains feasible for all of them and the objective is unchanged at .048357676070725. At the accepted floating qualification this establishes that no new LP is needed to seek an increase at that saved root. It does not establish that the added rows have no Native/search effect, and no exact rational optimum is claimed.

LP_frozen.json binds the executed LP matrices, cap rows and helper version. The later scope-reader revision removes an inherited GD positive-service prerequisite so zero-service descendants can be parsed. The arithmetic/cap construction is unchanged, and independent review compares the two inherited root scopes with the frozen scopes without rerunning either LP. The executed helper bytes are preserved in engineering. The K35 old PF numerical gap of about .000619046 belongs to the inherited R149/R150 GD carrier and remains a historical limitation; it is not used as an exact bound or a matched B control here.

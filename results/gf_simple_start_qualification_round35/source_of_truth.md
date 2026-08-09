# Round 35 source of truth

Round 35 starts at `b1225b9e723516f736df69b5d79f367551ad78ff` on
`codex/round35-simple-start-full-qualification`. Live remote `main` was
observed as `722b9b50cbd2155c43af1b2b511f55d579efb59d` before preparation and is not modified.

The current source tree is authoritative for SIMPLE-START and the validated
C6 exact phase. The detailed algorithm basis is the read-only Round 34
`current_exact_algorithm.md`; Round 32 is authoritative for the 35-row
1,800-second and 12-row independent V50 3,600-second comparator matrices.
Round 34 is authoritative for the already qualified V10 SIMPLE evidence.

Historical raw evidence remains read-only. Every comparator enters derived
Round 35 tables only through `historical_comparator_compatibility.csv`.
No P-GRB or C6-HGA-FULL process is launched in Round 35.

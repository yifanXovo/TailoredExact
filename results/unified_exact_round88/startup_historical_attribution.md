# Historical startup-path attribution before A1 performance runs

Read-only extraction on 2026-09-26 from the preserved Round87 runtime `campaign/local_raw/*ENS-C/hga.csv.descent.csv`. For each run, retain the exhausted terminal row per seed and take the maximum reported fitness among seeds 1–24; seed 25 is the constructive path. Every listed run completed 25 paths. These are logged decoded fitness values, not independently replayed A1 physical UBs or full-method performance results.

| Historical run | Best fitness, seeds 1–24 | Constructive-path fitness | Final logged descent elapsed seconds |
|---|---:|---:|---:|
| 02 D6 | -0.16002728060440294 | -0.2612388786428372 | 5.7418129 |
| 03 D7 | -0.5445105902163794 | -0.380773687462457 | 10.071735 |
| 06 U6 | -0.2433855505932638 | -0.2485589260232104 | 13.0835513 |
| 07 F2 | -0.9606845040541139 | -0.9139186744864067 | 0.0516746 |
| 10 F5 | -0.7754952754207787 | -0.4485843474105377 | 2.318038 |
| 11 F6, excluded from R87 formal comparison | -0.4166806292696964 | -0.44894532269130416 | 16.7683136 |

D6's original ENS-C physical-closure result reports F=0.15750980361456174, exhausted=true, verification_failed=false. That closure started from the original retained witness; it cannot predict A1 closure from the constructive path. Existing constructor retention and physical verification also prevent simply negating the above fitness and reporting it as A1's final UB.

Research decision before any A1 performance result: add the already allowed G2 startup-only diagnostic for D6, with fresh matched default ENS-C and A1 runs on the same qualified executable. Each diagnostic runs the complete declared startup/closure, with its own common 120-second whole-diagnostic cap and independent physical replay; it performs zero Optimize and is not a complete exact-method comparison. Report unknown/incomplete if it hits the external deadline. Use the frozen D6 input and scenario from the main panel. Register exact commands before launch.

The evidence can reject a uniform candidate or motivate a new uniformly defined startup mechanism. It cannot authorize per-instance seed counts or dispatch. No G3 observation has been used to amend the screening panel or thresholds.

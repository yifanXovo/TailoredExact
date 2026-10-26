This stage tests whether the frozen VD-S integration repairs the long-window P-GRB deficit while preserving an important K1 advantage. No solver source, executable, default, or algorithm parameter changes are included. The PR is stacked on Round68/PR #129, base 07c6e899d56230920c162c14bd8b7c07a960c79f.

The bounded 16-run panel confirms useful gains and a remaining defect:

- D3 repeats its certificate in 84.687s; N12 materially improves over K1-R while staying close to P-GRB.
- D6 at a 3600s whole-run limit reduces the final gap by 37.9% versus P-GRB and 54.6% versus K1-R. Both UB and LB improve over P.
- D7 at 1200s retains and strengthens K1 protection: gap falls 85.3% versus P and 34.3% versus K1-R, at the same candidate UB.
- E7 and S12 retain material/severe startup regressions. All six long runs remain uncertified. The overall research goal is unmet.

D6/VD-S has a disclosed HGA timing anomaly: about 550.6s versus K1-R's 323.7s despite matching generations, decoder counts, best-fitness history and retained routes. Its within-run 600s checkpoint is worse than P. All time remains paid; no discarded run, counterfactual correction, extra repeat, or claim of clean timing stability is introduced. The cause is not established.

Validation: 16 performance runs, 63 experiment Optimize calls, 14580.595s paid process wall, zero failures; six no-opt P exports separately cost 0.641s. All arms use Gurobi 13.0.2, Threads=1, Seed=0, Presolve=Auto and unchanged numerical standards. P is the original compact/default benchmark. The identical binary inherits the prior 45-test qualification; no new CTest batch or native qualification is claimed.

All eight actual Starts are eligible, accepted and fully observed. Independent audits check physical routes, full submitted/readback vectors, actual model rows/types/bounds/objectives, native settings, and complete proof-domain coverage. MIPSOL equality comes from the qualified C++ observer, not separately retained native event vectors. There are 43 initial-witness model checks with zero failures, 236 compact artifacts, 27 conservative within-run checkpoints, and full-content provenance for all 11 HGA initial routes. Zero requested gaps do not imply rational certificates.

The final report, long-window interpretation, machine-readable comparisons, identities and fresh-output reproduction helper are under results/unified_exact_round69 and scripts/round69_reproduce.py. Large raw models/logs and binaries stay local. Next work is a separately bounded admissible startup revision with newly matched measurement controls; no draft startup code is part of this measured stage. No main merge is requested.

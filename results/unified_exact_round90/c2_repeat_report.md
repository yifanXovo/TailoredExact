# Round90 C2 finite seed repeat

The signed, frozen C2 repeat ran **exactly four** new full solves: seed 1 ENS-C then LP-G, seed 2 LP-G then ENS-C. All four completed inside their 600 s whole-process limits with exit 0, passed physical/proof audit and within-seed cross-arm contradiction checks, and returned certified original-problem endpoints. Native parameter readback confirmed effective Gurobi seed 1 or 2 for both arms of its pair, one thread, and presolve −1; the control reported the Round83 ENS-C preset and the flagged candidate reported the Round90 LP-G identity. Seed 0 below is the already audited original Round90 G3 C2 pair, not a new solve in this batch.

| Seed | ENS-C proof time (s) | LP-G proof time (s) | LP-G / ENS-C | Direction |
|---:|---:|---:|---:|---|
| 0 (original G3) | 123.813 | 112.141 | 0.9057288006893817 | LP-G faster |
| 1 | 141.610 | 99.859 | 0.7051691264726901 | LP-G faster |
| 2 | 136.469 | 151.703 | 1.111629747416386 | ENS-C faster |

The **median certified ratio is 0.9057288006893817**. The direction changes across the preselected seeds: LP-G is faster in two pairs and slower in one. No seed is censored. The exact paired U/L/gap, certificates, process times, and seed readbacks are in `c2_repeat_table.csv`.

| Seed | Arm | Physical U | Global L | Final certificate |
|---:|---|---:|---:|---|
| 0 | ENS-C | 0.8299634131717752 | 0.8299634131717741 | yes |
| 0 | LP-G | 0.8299634131717752 | 0.8299634131717752 | yes |
| 1 | ENS-C | 0.8299634131717752 | 0.8299634131717744 | yes |
| 1 | LP-G | 0.8299634131717752 | 0.8299634131717748 | yes |
| 2 | ENS-C | 0.8299634131717752 | 0.8299634125771549 | yes |
| 2 | LP-G | 0.8299634131717752 | 0.8299634111736707 | yes |

The new LP-G runs each recorded three eligible split proposals and two realized atomic child splits; the corresponding ENS-C controls left the LP-G flag off. Both new seed pairs passed physical witness and original-problem cross-arm checks. There were no execution, identity, audit, resource, or severe-signal failures; no retry or extra seed was attempted. The wrapper/preregistration/binary and seven source identities match the signed prepared identity after execution, and no runner lock or heavy process remains.

The sole new `run` command cost **531.7086207 s** from outer launch to exit. Its four nested native process walls total **529.641 s**; prelaunch totals **1.312 s**, so fully observed per-arm end-to-end totals **530.953 s**. Remaining outer work is **0.7556207 s**, including nested offline audits of **0.1428904 s**; none of these components is added twice. The wrapper's own inner full wall was 531.2708921 s. The separately completed one-time preparation cost was 0.6492336 s (0 Optimize); it is not hidden inside or added to the `run` wall. The post-run evidence inspection and report writing are additional research work: the outer receipt finished at 02:34:40.309 UTC and postflight was observed at 02:36:19.188 UTC, about **98.88 s** later. That interval lacks a complete separate work timer, so its duration is disclosed rather than called zero or folded into the run wall. Raw stdout/stderr, launch, completion, audit, native parameter, and witness receipts remain in `runner_lp_g_c2_repeat/`.

Acceptance recommendation: accept these three C2 pairs as a bounded development fluctuation check and retain the mixed sign in the evidence record. The median favorable ratio does **not** establish robust speedup, statistical significance, or promotion of LP-G. No further seed or experiment is implied by this report.

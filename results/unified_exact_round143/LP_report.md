# Round143 matched LP evidence

All four new LPs are numerical optima under unchanged 1e-6 feasibility/optimality qualification, explicit Gurobi Seed 0, Threads 1 and affinity mask 4, run serially. The original complete objective, cutoff, support, g interval and old matrix are retained. BASE gains include physical inventory information used for t bounds; TC+stock controls still show information beyond that older resource/count combination.

| Role | Old expression | Old L | RN L | Gain |
| --- | --- | --- | --- | --- |
| K35 | base | 0.200177662 | 0.228090497 | 0.027912835 |
| K35 | tc_stock | 0.218088779 | 0.228090497 | 0.0100017179 |
| RX20-T1 | base | 0.331594316 | 0.389761616 | 0.0581672999 |
| RX20-T1 | tc_stock | 0.37755753 | 0.394121979 | 0.0165644487 |

| Role / expression | Old g | RN g | Old weighted P | RN weighted P |
| --- | --- | --- | --- | --- |
| K35/base | 0.0386391834 | 0.0665520184 | 0.161538479 | 0.161538479 |
| K35/tc_stock | 0.0565503004 | 0.0665520184 | 0.161538479 | 0.161538479 |
| RX20-T1/base | 0.100712705 | 0.17210734 | 0.230881611 | 0.217654276 |
| RX20-T1/tc_stock | 0.14667592 | 0.173850507 | 0.230881611 | 0.220271472 |

| Role / expression | Added rows | Added columns | Added nonzeros | Build / solve s |
| --- | --- | --- | --- | --- |
| K35/base | 2340 | 1170 | 7474 | 1.7644687 / 0.5281877 |
| K35/tc_stock | 2340 | 1170 | 7474 | 1.8504794 / 1.6446136 |
| RX20-T1/base | 708 | 354 | 2232 | 0.4122916 / 0.0574667999 |
| RX20-T1/tc_stock | 708 | 354 | 2232 | 0.4220257 / 0.0796056001 |

Actual denominator bounds, reciprocal endpoints, complete row/column/nonzero counts, Runtime/Work, all quality measures and actual source/solution hashes are in reports/LP.json and LP.csv. These reoptimized full-objective gains are separate from saved-point exclusions. Four diagnostic Optimize calls were sufficient; no RN x TC2 x CP grid was opened.

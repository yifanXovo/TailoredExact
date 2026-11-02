# Finite matched LP decision

Five new continuous optimizations, with sealed baseline values and actual solutions reused. All use the complete original objective, penalty and constant, matrix, support, g domain and cutoff; Seed=0, Threads=1, affinity=4, serial. Actual compiled GD coefficients are independently checked as rational lower bounds and read back from Native. These are numerical LP optima, distinct from Native root-after-cuts bounds and complete certificates.

| Role | Carrier + GD-state | Old L | New L | Gain | G | Weighted penalty | GD NZ | Generation ms | Runtime s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K-20-S | base | 0.195149152441 | 0.236010302342 | 0.0408611499012 | 0.0650677958908 | 0.170942506452 | 330 | 1.189 | 0.171 |
| K-20-S | joint | 0.222808939661 | 0.239052184675 | 0.0162432450143 | 0.0655189982186 | 0.173533186457 | 330 | 1.218 | 0.29 |
| K-20-S | stock | 0.204590439178 | 0.251016109922 | 0.0464256707442 | 0.0703499227555 | 0.180666187167 | 330 | 1.194 | 0.152 |
| K-35-U | base | 0.200177661949 | 0.204187028164 | 0.00400936621457 | 0.0426485495924 | 0.161538478571 | 405 | 1.945 | 1.096 |
| R-X20-S-T1 | base | 0.331594316287 | 0.365004645621 | 0.033410329335 | 0.15 | 0.215004645621 | 97 | 0.3848 | 0.096 |

K20 gains beyond both BASE and the stronger R145 joint carrier. Its matched STOCK+GD value is higher than standalone GD and STOCK, supporting one uniform STOCK+GD candidate with STOCK as the same-PE reference. K35 and RX20 also gain on BASE. The existing joint optima of K35/RX20 satisfy both GD rows and therefore witness no additional numerical optimum value on those particular stronger models; they were not reoptimized.

Each actual production block uses two rows, no columns and no paid source LP. Measured coefficient generation is approximately 0.38–1.95 ms on these domains. Point separation alone was not used to claim any optimized increment. The more elaborate state-level Hoover extension was not opened because the direct original-variable question already has useful optimization information. No global/state parameter grid or full formulation factorial was run.

# Low-Gini Plateau Diagnosis

Target: `moderate_seed3301` low-Gini leaf `[0.0122881381662, 0.0245762763324]`, with secondary confirmation on `[0.0245762763324, 0.0368644144986]`, `high_imbalance_seed3201_hard`, `tight_T_seed3102_hard`, and `moderate_seed3302_hard`.

The forensic record compares plain fixed-interval MIP, static tailored Compact-BC, callback cut profiles, subset cross-H centering, local q-centering, transfer cutsets, required external-source rows, diagnostic S-buckets, and the best combined paper-safe variant. Root LP tableau details are not fully exposed by the current CPLEX callback API, so the durable evidence is exported LP hashes, family row counts, native CPLEX best-bound checkpoints, and matched-budget deltas.

Best plain low_gini_1 LB: 0.048296011756; best paper-safe low_gini_1 LB: 0.0487233640003; best diagnostic S-bucket LB: 0.0491525526647.

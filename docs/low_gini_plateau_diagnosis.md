# Low-Gini Plateau Diagnosis

Target: `moderate_seed3301` low-Gini leaves `[0.0122881381662, 0.0245762763324]` and `[0.0245762763324, 0.0368644144986]`.

The round compares plain fixed-interval MIP, callback infrastructure with profiled cut families, static tailored Compact-BC, local centering, and diagnostic S-bucket rows under one-thread CPLEX. Root LP snapshots are limited by the current CPLEX callback API exposure, so the report uses exported LP hashes, family row counts, node counts, and native CPLEX best bound trajectories as the forensic record.

Best plain low_gini_1 LB: 0.048296011756; best local/full paced low_gini_1 LB: 0.0487233640003.

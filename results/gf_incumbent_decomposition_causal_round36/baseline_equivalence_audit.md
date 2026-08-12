# Round 36 baseline-equivalence audit

Gate passed: **True**.

A contemporaneous frozen Round 35 C6 executable, the new executable with every Round 36 control off, and explicit HH were run on V12_M1. Hashes exclude wall time and solver effort but include every mathematical decision field listed below.

| component | default off | HH |
|---|---|---|
| initial_intervals | True | True |
| lp_bounds | True | True |
| controlling_leaf_sequence | True | True |
| native_target_sequence | True | True |
| split_sequence | True | True |
| closure_sequence | True | True |
| final_objective_certificate | True | True |

A false result is a blocking Stage A error.

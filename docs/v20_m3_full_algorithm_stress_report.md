# V20/M3 Full-Algorithm Stress Report

Six generated V20/M3 instances were run with paper-core native HGA-TGBC
incumbents and 300-second limits. All heuristic incumbents passed the
independent verifier.

Outcome:

- Certified cases: 0/6.
- UB improvements after the initial native HGA-TGBC incumbent: 0/6.
- Main plateau: relaxation lower bounds remained below the verified incumbent
  cutoffs; BPC/pricing did not dominate runtime in these rows.
- Route-pool incumbent master was called but found no improving verified route
  plan.

Representative gaps:

- `tight_T_seed3101`: UB `0.617830412041`, LB `0.284602061219`, gap `0.539352457127`.
- `tight_T_seed3102`: UB `1.57552584458`, LB `1.39118663149`, gap `0.117001706903`.
- `high_imbalance_seed3201`: UB `2.44340319194`, LB `2.11629979572`, gap `0.133872050793`.
- `moderate_seed3301`: UB `0.0491525526647`, LB `0.0427477151184`, gap `0.130305288314`.

Two selected rows were rerun after adding local re-decode repair. Neither
improved UB, so the next V20 round should target relaxation closure rather than
additional short primal repair.

# high_imbalance_seed3202 Full Certificate Report

`high_imbalance_seed3202` is certified by the reproduced full-frontier run:

- raw JSON: `results/v20_exact_certificate_round/raw/high_imbalance_seed3202_reproduced_baseline.json`
- interval ledger: `results/v20_exact_certificate_round/raw/high_imbalance_seed3202_reproduced_baseline.intervals.csv`
- certificate copy: `results/v20_exact_certificate_round/high_imbalance_seed3202_full_certificate.json`

Every final interval is either replaced by children or bound-fathomed by a valid
inventory/route/Gini relaxation reaching the verified incumbent cutoff.  No
BPC tree interval was used, so exact pricing closure is not required for this
certificate.  The result has `unresolved_intervals=0`,
`invalid_bound_intervals=0`, `open_nodes=0`,
`frontier_covers_all_improving_gini_values=true`, and
`frontier_range_certificate_scope=original_full_improving_range`.


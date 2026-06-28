# high_imbalance_seed3202 Interval Oracle Closure

The reproduced full-frontier run closed all final leaves, so exact interval
oracle closure was not needed for the final certificate.  To validate the new
oracle path, the previous round's unresolved leaves `13,18,19,20` were run with
short compact cutoff-MIP budgets.

Those diagnostic oracle rows timed out and were not merged.  The merge audit in
`results/v20_exact_certificate_round/ledger_merge_audit.csv` keeps the old
ledger incomplete, which confirms that focused timeout evidence is not promoted
to a certificate.


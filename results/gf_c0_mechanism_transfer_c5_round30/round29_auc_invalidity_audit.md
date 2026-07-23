# Round 29 AUC invalidity audit

Round 29 C4 did not emit the compatible
`external/global_bound_trace.csv` consumed by its analyzer. Its paper-tree
event ledgers omit active native-MIP bound observations. The analyzer therefore
reported zero C4 observations while still constructing an endpoint-based
pseudo-trajectory.

Those C4 AUC values are invalid as observed anytime evidence. Round 30 marks
every such row `auc_unavailable`; it does not overwrite Round 29. C3 rows are
retained only when their compatible external trace has observations, and
P-GRB rows are retained only from native progress callbacks.

Round 30 C4 and C5 runs must use the new complete trace schema. No C5
performance conclusion is permitted for a row whose trace-completeness audit
fails.

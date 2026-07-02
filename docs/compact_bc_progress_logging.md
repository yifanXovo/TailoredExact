# Compact-BC Progress Logging

`--compact-bc-progress-interval <seconds>` is an alias for the established
frontier progress checkpoint interval. The progress CSV records global ledger
state:

- elapsed time and event;
- incumbent UB, global LB, and global gap;
- unresolved interval count;
- controlling interval id/range/source;
- open nodes and cumulative timing fields.

The final JSON records `progress_log`, `progress_checkpoints_written`,
`gap_trajectory_available`, `time_budget_seconds`, and
`actual_runtime_seconds`. Wrapper-finalized noncertified rows refresh LB/UB/gap
from the latest progress checkpoint but never synthesize optimality.

# Global-bound trace schema

Every Round 30 external arm writes `external/global_bound_trace.csv` with one
row per observed validity-changing event. Required columns are:

- `process_elapsed_seconds`
- `exact_phase_elapsed_seconds`
- `event_type`
- `active_leaf`
- `active_leaf_valid_lower_bound`
- `other_open_leaf_min_valid_lower_bound`
- `valid_global_lower_bound`
- `verified_global_upper_bound`
- `open_relevant_leaf_count`
- `closed_relevant_leaf_count`
- `event_source`

The active native-MIP global bound is exactly the minimum of its
backend-certified active-leaf bound and every other relevant open leaf's valid
bound. No incumbent is a lower bound. No bound is interpolated, and no
post-last-event progress is synthesized.

Initialization, parent/child LP completion, native bound improvement, split,
declined split, infeasible/fathomed closure, terminal closure, interruption,
incumbent improvement, and finalization are explicit events. A completed row
is AUC-eligible only if initialization and finalization exist, timestamps and
bounds are monotone, every active native event is validity-gated, and its final
trace bound equals the serialized valid lower bound.

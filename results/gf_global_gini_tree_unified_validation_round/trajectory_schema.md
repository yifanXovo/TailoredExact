# Round 22 trajectory schema

Schema version: `round22-dense-progress-v1`.

Each raw CSV row identifies the run, arm, flow, retained and callback sequences, monotonic observation time, associated scheduled heartbeat, age, freshness, native callback source/context, and phase. Optional callback-safe fields are empty rather than synthesized. Numeric values use C++ `max_digits10` precision.

Core state fields are native deterministic time, native best bound, native incumbent, independently verified same-run UB availability/value, project gap, native CPLEX-style gap, processed/open nodes, native solution count, simplex iterations, tree memory, Gini/ordinary branch counts, open Gini siblings, sibling delays, bound/incumbent/branch/root milestones, model rows/columns/nonzeros, executable hash, and retention trigger.

Canonical rows use checkpoints `1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 300, 450, 600, 750, 900, 1200, 1500, 1800, 2400, 3000, 3600`, truncated to the nominal horizon. The source is the latest raw observation at or before the checkpoint. `observation_age_seconds` is checkpoint minus source time; freshness uses the checkpoint cadence. A separate solver-final endpoint is always included. A later observation can never populate an earlier checkpoint.

For cross-method analysis, the final independently verified UB from that same run may be attached in explicitly named retrospective analysis columns. It does not rewrite native incumbent/UB availability in historical callback rows. Gap crossings report the preceding observation, first observed crossing, and interval; they never interpolate an exact time. Normalized bound progress is `clamp(1 - max(0, (UB-LB)/abs(UB)), 0, 1)` using the same run's independently verified UB, and AUC is the time-weighted trapezoidal integral divided by observed horizon.

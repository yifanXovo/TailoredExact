# Round 56 time-unit audit

The repository parses the supplied point coordinates and computes symmetric
metric travel times as Euclidean point distance divided by the frozen factor
1.5. The original physical coordinate and speed units are not independently
verified, so Round 56 makes no physical-speed claim. All reported quantities
are **seconds under the repository's frozen travel/service-time convention**.
Pickup and drop times are each 60 seconds per bicycle. T=1800, 3600, 10800,
and 18000 are respectively the 0.5-hour, 1-hour, 3-hour, and 5-hour operational
per-vehicle route horizons. The solver process cap is a separate wall-clock
quantity. The corrected generator computes its stored distance matrix from the
exact serialized three-decimal coordinates; the consistency CSV records only
sub-1e-9 decimal-format residuals.

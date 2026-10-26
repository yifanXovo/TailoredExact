# Operational route-time horizon protocol

Round 56 uses two distinct time concepts:

- `route_time_limit_seconds` is T, the operational per-vehicle route-duration constraint in the mathematical instance;
- `solver_process_cap_seconds` is the wall-clock cap for one execution of the exact algorithm.

T affects route-duration rows, movement-domain propagation, T-dependent valid inequalities, original-solution verification, canonical model bytes, cache/artifact identity, and the mathematical-instance SHA-256. Changing T creates a different mathematical scenario. Changing only the solver process cap does not change the model; it changes the run identity.

The frozen operational values are 1800, 3600, 10800, and 18000 seconds, corresponding to 0.5-hour, 1-hour, 3-hour, and 5-hour route horizons. Distances and pickup/drop service durations are interpreted as seconds under the repository's frozen travel/service-time convention. The repository uses parser-rebuilt point distances with speed factor 1.5 and 60 seconds per pickup or drop unit; this statement does not infer an independently verified physical coordinate or speed unit.

Every official scenario records checkpoint evidence at 300, 1200, and 3600 process seconds unless strict optimality ends the run earlier, in which case the certified final state is carried forward. Nine predeclared V>=20, T=18000 rows may continue to 7200 seconds. Cross-scenario computational comparisons use the common 3600-second checkpoint even when the final cap is 7200 seconds.

No submodel may fall back to T=3600. Round 56 audits parent LPs, midpoint-child LPs, native-target MIPs, exact-parent and exact-child MIPs, propagation, verifier calls, model identities, cache identities, and result serialization against the requested T.

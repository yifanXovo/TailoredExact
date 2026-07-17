# Historical Round-20 V12 certificate audit

This is a no-rerun audit of the official Round-20 Stage-2 global-Gini-tree artifacts. It treats native numeric CPLEX status as authoritative and applies a fail-closed historical classification: status 101 is only a historical strict candidate; status 102 is tolerance-only.

## Conclusion

Of the four selected records, **1 is a historical strict candidate** and **3 are tolerance-only**. In **3 tolerance-only records**, the Round-20 public serializer reported `lower_bound == upper_bound` and `gap == 0` even though the final native trajectory retained a positive best-bound gap.

None of the four is promoted to a hardened Round-21 strict certificate. The historical schema does not record both zero-gap parameter set/readback results or the native objective/bound/gap API return codes required by the new policy.

## Per-run evidence

| Instance | Arm | Status | Native status text | Final native incumbent | Final native best bound | Absolute gap | Round-20 serialized LB / UB / gap | Historical class |
|---|---|---:|---|---:|---:|---:|---|---|
| V12_M1 | baseline | 102 | integer optimal, tolerance | 0.35720058320768794 | 0.35719986149047245 | 7.2171721549E-7 | 0.357200583208 / 0.357200583208 / 0 | tolerance_only |
| V12_M1 | root_flow_only | 102 | integer optimal, tolerance | 0.35720058320768378 | 0.35720026683430645 | 3.1637337733E-7 | 0.357200583208 / 0.357200583208 / 0 | tolerance_only |
| V12_M2 | baseline | 101 | integer optimal solution | 0.71850407075533274 | 0.71850407075533274 | 0E-17 | 0.718504070755 / 0.718504070755 / 0 | historical_strict_candidate |
| V12_M2 | root_flow_only | 102 | integer optimal, tolerance | 0.71850407075532763 | 0.71850361622922809 | 4.5452609954E-7 | 0.718504070755 / 0.718504070755 / 0 | tolerance_only |

## Interpretation rules

- `CPXMIP_OPTIMAL` (101) is a strict-status candidate. Historical evidence still cannot satisfy the full Round-21 evidence contract.
- `CPXMIP_OPTIMAL_TOL` (102) is tolerance-only regardless of how small the remaining best-bound gap is or whether rounded public fields coincide.
- The final `solver_final` row of `global_bound_trajectory.csv` supplies higher-precision native incumbent, best bound, and the project-recorded gap. JSON values are retained separately because its 12-digit rendering rounds those quantities.
- `computed_project_relative_gap_max1` uses `abs(incumbent-bound)/max(1,abs(incumbent))`. `computed_cplex_denominator_relative_gap` is an audit-derived diagnostic using `abs(incumbent-bound)/(1e-10+abs(incumbent))`; it is not a historical `CPXgetmiprelgap` observation.

## Reproduction and provenance

Run from the repository root:

```text
D:\msys64\ucrt64\bin\python.exe scripts/round21_historical_certificate_audit.py
```

The script is standard-library-only and may also be run with any Python 3 interpreter available on another host.

The machine-readable records are in `v12_round20_certificate_audit.csv` and `historical_certificate_audit.json`. Exact paths, byte sizes, and SHA-256 digests for every input used by the audit are in `source_artifact_hashes.csv`.

# tight_T_seed3102 Sealed Certificate Attempt

`tight_T_seed3102` was retested because an earlier sealed run exited
abnormally and left only checkpoint evidence.

## Result

The new sealed run exits normally and produces solver-side final JSON:

- `process_return_code=0`;
- `solver_finalization_reached=true`;
- `abnormal_exit_detected=false`.

The row remains noncertified:

- UB: `0.600704436685`;
- LB: `0.450176109171`;
- gap: `0.250586342169`;
- final unresolved leaves: `3`;
- oracle calls: `9`;
- oracle-closed leaves: `0`;
- timed-out oracle leaves: `9`;
- split leaves: `3`;
- remaining open leaves: `3`.

The exact blocker is interval oracle timeout on every parent/child attempt.
BPC fallback was called only as a diagnostic final stage and did not close a
leaf with exact pricing.

Detailed rows are in:

- `results/sealed_closure_round/tight_T_seed3102_certificate_attempt.csv`;
- `results/sealed_closure_round/tight_T_seed3102_certificate_attempt_oracle_detail.csv`.

# high_imbalance_seed3201 Sealed Diagnosis

`high_imbalance_seed3201` was rerun with the all-leaf oracle and automatic BPC
fallback enabled under the sealed unified command template.

## Result

The row is noncertified but solver-finalized:

- UB: `2.44340319194`;
- LB: `1.74210803`;
- gap: `0.287015734552`;
- final unresolved leaves: `2`;
- oracle calls: `6`;
- oracle-closed leaves: `0`;
- timed-out oracle leaves: `6`;
- split leaves: `2`;
- remaining open leaves: `2`;
- `process_return_code=0`;
- `abnormal_exit_detected=false`.

The gap is materially better than the previous sealed completion row
(`0.384...`), but no certificate was obtained. The current blocker is exact
cutoff MIP timeout on both controlling leaves and their child partitions.
BPC fallback did not supply exact-pricing closure.

Detailed rows are in:

- `results/sealed_closure_round/high_imbalance_seed3201_attempt.csv`;
- `results/sealed_closure_round/high_imbalance_seed3201_attempt_oracle_detail.csv`.

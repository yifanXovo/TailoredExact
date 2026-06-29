# moderate_seed3301 Sealed Certificate Attempt

`moderate_seed3301` was the priority new V20/M3 target because previous
diagnostic oracle rows showed that several leaves can be closed by the exact
cutoff MIP.

## Command Policy

The row used the same sealed command template as the other rows:

```text
--method gcap-frontier
--algorithm-preset paper-exact-v20-certificate
--paper-run-sealed true
--auto-interval-oracle true
--auto-interval-oracle-order all
--auto-interval-oracle-max-leaves all
--auto-interval-oracle-split-on-timeout true
--auto-interval-bpc-fallback true
```

No archive scan, known UB, external incumbent, manual gamma range, or
instance-specific flag was used.

## Result

The row is noncertified:

- UB: `0.0491525526647`;
- LB: `0.00921610362464`;
- gap: `0.8125`;
- final unresolved leaves: `6`;
- oracle calls: `10`;
- leaves closed by oracle: `4`;
- leaves timed out: `4`;
- leaves split: `2`;
- remaining open leaves: `2`.

The solver produced a final JSON with return code 0. The blocker is not missing
finalization; it is exact interval cutoff MIP timeout on the remaining child
leaves. BPC fallback did not provide exact pricing closure for those leaves, so
the row remains noncertified.

Detailed rows are in:

- `results/sealed_closure_round/moderate_seed3301_certificate_attempt.csv`;
- `results/sealed_closure_round/moderate_seed3301_certificate_attempt_oracle_detail.csv`.

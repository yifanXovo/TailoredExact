# Round 58 staged runtime protocol

The protocol was frozen before timed runs. A run stops only when it obtains a
strict original-problem certificate or reaches its process cap. Every attempt
is a fresh process, and only one optimizer process runs at a time.

## Mandatory screen

Both K1-AM-SF and P-GRB run on all 50 scenarios with a 3600-second process
cap. Checkpoints are interpreted at 300, 1200, and 3600 seconds. Method order
within a pair is determined by the first hexadecimal digit of the frozen
scenario SHA-256: even selects K1 first, odd selects P-GRB first.

After both screen arms finish:

- if both certify, neither extends;
- if exactly one certifies, the other receives a fresh 10800-second run when
  its qualified relative gap is at most 0.10 or the certified arm took at
  least 2700 seconds;
- if neither certifies, both receive fresh 10800-second runs.

The 10800-second checkpoints are 3600, 7200, and 10800 seconds. Its 3600
trajectory is compared with the original screen for material repeatability
differences.

## Near-convergence stages

A noncertified 10800-second result with qualified relative gap at most 0.05
receives a fresh 21600-second final attempt. A relative gap above 0.05 and at
most 0.10 receives a fresh 16200-second attempt; it proceeds to a fresh
21600-second attempt only if its 16200-second gap is at most 0.05. Missing
qualified endpoints or a gap above the applicable threshold stops the arm.
No process can exceed 21600 seconds, and a completed 21600-second row is never
attempted again.

The qualified gaps for minimization are:

```
absolute_gap = max(0, verified_upper_bound - valid_lower_bound)
relative_gap = absolute_gap / max(abs(verified_upper_bound), 1e-6)
scaled_gap   = absolute_gap / max(1, abs(verified_upper_bound))
```

The upper bound must be an independently verified original-problem incumbent.
The lower bound must pass method-specific scope and lifecycle checks. If an
endpoint is missing, all three gaps are unavailable. New Round 58 summaries
never use an unqualified field named `gap`.

Comparisons of capped methods use the largest common authorized horizon.
Unequal final horizons are labeled and are not treated as direct bound
comparisons. Capped rows receive no invented time-to-solution.

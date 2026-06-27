# V12 M1 Fast Closure Strategy

Date: 2026-06-28

V12 M1 is not a primal-UB problem: native HGA-TGBC already gives the verified
incumbent `0.357200583208`.  The remaining work is relaxation scheduling over
the final Gini frontier.

## Evidence

| row | status | LB | UB | gap | runtime |
|---|---:|---:|---:|---:|---:|
| current 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 301.673s |
| adaptive 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 310.083s |
| adaptive 600s | certified | 0.357200583208 | 0.357200583208 | 0 | 473.765s |

The 600s row closes slightly faster than the previous 481s certified row, but
the 300s lower bound does not materially improve.  The best conclusion is that
V12 M1 closure is still bound-time and split-depth sensitive.  BPC fallback
should not start before the relaxation split sequence has exhausted its useful
budget.

## Implemented Controls

```text
--frontier-scheduling-mode default|v12-fast-close|adaptive-best-bound
--frontier-critical-band-auto true|false
--frontier-critical-band-max-depth <N>
--frontier-critical-band-min-width <width>
```

These controls are deterministic and preserve inherited lower-bound validity.
They are not hard-coded to a V12 M1 gamma range.


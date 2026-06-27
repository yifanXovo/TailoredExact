# BPC Fallback On Unresolved Intervals

This round adds explicit options for controlled BPC fallback:

- `--frontier-bpc-fallback-mode off|controlling-intervals|best-bound`
- `--frontier-bpc-fallback-reserve-fraction <value>`
- `--frontier-bpc-fallback-min-seconds <seconds>`
- `--frontier-bpc-fallback-max-intervals <N>`

When enabled, the parser converts the fallback request into a reserved final
closure phase. The existing exact branch-price tree routine is reused. Tree
evidence can support a lower-bound certificate only when exact pricing closure
conditions are satisfied by the existing guard. Incomplete BPC output leaves the
interval unresolved.

Observed rows:

- V12 M1 300s with fallback started one BPC node and one pricing call. It did not
  close the controlling interval and reduced available relaxation time, giving a
  weaker final LB than the relaxation-only 300s row.
- Three V20/M3 fallback rows were run. They did not start useful closed BPC
  work before relaxation consumed the available time, so the remaining bottleneck
  is still relaxation-bound closure and time allocation, not route pricing.

The fallback is therefore useful as a diagnostic trigger but is not yet a
productive default for these instances.

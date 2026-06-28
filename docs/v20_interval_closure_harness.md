# V20 Interval Closure Harness

Date: 2026-06-28

The V20 certificate round adds a conservative focused-interval harness:

```text
scripts/v20_interval_closure_harness.py
```

It reads a previous full-frontier interval CSV, selects unresolved interval IDs
or an exact gamma range, and launches `gcap-frontier` in focus-only mode with
the requested relaxation portfolio.

Important certificate rule: focus-only rows are diagnostic by default.  A focus
row can only be merged into a full-frontier certificate if its range exactly
covers a final unresolved full-ledger leaf and the merge audit proves that no
coverage gap remains.  This round does not perform a safe full-ledger merge for
V20.

Outputs:

- `results/v20_certificate_round/interval_closure_trace.csv`;
- `results/v20_certificate_round/interval_ledger_merged.csv`;
- `results/v20_certificate_round/interval_closure_commands.md`.

On `high_imbalance_seed3202`, intervals 13 and 18 from the previous 1200s
mip-light trace were targeted.  Neither focused solve closed the interval, and
both remain diagnostic-only.


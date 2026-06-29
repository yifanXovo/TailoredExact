# Sealed Noncertified Audit Policy

Certificate audit now covers all sealed final JSONs, not only optimal rows.

## Passing Noncertified Rows

A noncertified sealed row passes audit when it honestly reports:

- `certified_original_problem=false`;
- no original-problem optimality claim;
- strict sealed provenance;
- a `finalization_source`;
- no archive scanning;
- no external known UB;
- no focus-only final certificate.

The row may have a positive gap, unresolved intervals, open nodes, oracle
timeouts, or BPC timeouts. These are valid noncertified outcomes when reported.

## Failing Conditions

Audit fails if a sealed row:

- lacks final JSON while matching progress logs exist;
- claims certification with unresolved intervals, invalid intervals, or open
  nodes;
- uses diagnostic archive evidence or external incumbents as a paper source;
- has `no_archive_scanning=false`, `no_external_known_ub=false`, or
  `no_focus_only_certificate=false`;
- lacks `finalization_source`;
- certifies using incomplete route-mask enumeration;
- certifies a BPC tree without exact pricing closure;
- certifies an interval oracle result without proven infeasibility or a
  verified improving original solution and safe full-ledger merge.

## Current Audit

The sealed completion round was audited with:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py `
  results\sealed_pipeline_completion_round\raw `
  --csv-out results\sealed_pipeline_completion_round\certificate_audit.csv `
  --fail-on-error `
  --require-progress-finals results\sealed_pipeline_completion_round\raw
```

Result:

```text
audited_rows=15 failures=0
```

# Sealed Closure Round Final Report

Branch: `codex/longrun-round17-local-results`
Source head at round start: `a8748ed81e5cbdde83270e510466935adea3a6da`
Final commit SHA: recorded in the final response after commit creation.

## Algorithm Changes

- Added all-leaf automatic interval oracle support:
  `--auto-interval-oracle-order all` and
  `--auto-interval-oracle-max-leaves all`.
- Added oracle timeout continuation and child partitioning:
  `--auto-interval-oracle-continue-after-timeout`,
  `--auto-interval-oracle-split-on-timeout`,
  `--auto-interval-oracle-child-split-count`, and
  `--auto-interval-oracle-max-depth`.
- Added solver finalization fields for normal, noncertified, and wrapper
  fallback rows.
- Updated the sealed wrapper so it can pass all-leaf oracle options and record
  finalization status.

## Unified Sealed Command

All rows used the same sealed pipeline policy:

```text
build\ExactEBRP.exe --method gcap-frontier
  --algorithm-preset paper-exact-v20-certificate
  --paper-run-sealed true
  --auto-interval-oracle true
  --auto-interval-oracle-order all
  --auto-interval-oracle-max-leaves all
  --auto-interval-oracle-split-on-timeout true
  --auto-interval-bpc-fallback true
  --input <instance> --lambda 0.15 --T 3600
  --time-limit <budget> --out <raw.json>
```

Only input path, output path, and time budget differed. No row used archive
scanning, known UB injection, external incumbent JSON, manual focus intervals,
or instance-specific gamma ranges.

## Results

Every row produced final JSON. All priority rows exited with return code 0 and
`solver_finalization_reached=true`.

| row | status | LB | UB | gap | certificate |
|---|---|---:|---:|---:|---|
| V4 smoke | optimal | 0 | 0 | 0 | smoke certificate |
| V12 M2 | optimal | 0.718504070755 | 0.718504070755 | 0 | relaxation-only full frontier |
| V12 M1 | optimal | 0.357200583208 | 0.357200583208 | 0 | relaxation-only full frontier |
| high_imbalance_seed3202 | optimal | 1.74931345205 | 1.74931345205 | 0 | relaxation-only full frontier |
| tight_T_seed3101 | optimal | 0.107252734134 | 0.107252734134 | 0 | relaxation-only full frontier |
| high_imbalance_seed3201 | not closed | 1.74210803 | 2.44340319194 | 0.287015734552 | oracle timeouts |
| tight_T_seed3102 | not closed | 0.450176109171 | 0.600704436685 | 0.250586342169 | oracle timeouts |
| moderate_seed3301 | not closed | 0.00921610362464 | 0.0491525526647 | 0.8125 | two leaves remain open |
| moderate_seed3302 | not closed | 0 | 0.195636206549 | 1 | oracle timeouts |

## Oracle And BPC Outcome

The all-leaf oracle improved diagnosis and closed several leaves, but it did
not add a third V20 certificate.

- `moderate_seed3301`: 6 final leaves, 10 oracle attempts, 4 leaves closed, 2
  leaves remain open after child timeouts.
- `tight_T_seed3102`: 3 final leaves, 9 oracle attempts, 0 closed.
- `high_imbalance_seed3201`: 2 final leaves, 6 oracle attempts, 0 closed.
- `moderate_seed3302`: 4 final leaves, 10 oracle attempts, 1 closed.

BPC fallback was attempted as a diagnostic final stage where enabled. It did
not close any remaining leaf with exact pricing closure, so it contributed no
lower-bound certificate evidence.

## Audit

Commands run:

```text
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\sealed_closure_round\raw --csv-out results\sealed_closure_round\certificate_audit.csv --fail-on-error --require-progress-finals results\sealed_closure_round\raw
build\ExactEBRP.exe --method certificate-basis-test
build\ExactEBRP.exe --method option-consistency-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_no_instance_special_cases.py --out results\sealed_closure_round\no_instance_special_case_audit.txt
```

The certificate audit passed with all optimal claims valid. Noncertified rows
remain noncertified and are included in the audit.

## Readiness Decision

The project is not ready for broad paper benchmark testing. V12 remains stable
and two V20/M3 stress rows certify, but the target of at least three certified
V20/M3 rows was not reached. The next targeted round should strengthen the exact
interval cutoff MIP for remaining low-Gini/tight-T leaves or add a more useful
exact BPC interval closure path.

# paper_core_round_next Notes

Git SHA at start of the round: `e4bb0cb748f96dc0879b94467a165430b946eef9`

CMake was unavailable on this machine, so the fallback g++ build in
`commands.md` was used.

## Key Results

| row | status | objective | LB | UB | gap | runtime | certificate |
|---|---|---:|---:|---:|---:|---:|---|
| V4 paper-core smoke 30s | optimal | 0 | 0 | 0 | 0 | 11.3841401 | original BPC |
| V12 M1 paper-core 300s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 0 | 265.220702 | relaxation-only frontier |
| V12 M1 paper-core 1200s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 0 | 257.5489498 | relaxation-only frontier |
| V12 M2 paper-core 300s | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 0 | 217.7839095 | relaxation-only frontier |
| V12 M2 paper-core 1200s | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 0 | 215.7528562 | relaxation-only frontier |
| V12 M1 plain CPLEX 300s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 0 | 186.6176559 | benchmark only |
| V12 M2 plain CPLEX 300s | not_certified | 0.72439493548 | 0.62335837374 | 0.72439493548 | 0.139477178527 | 300.0680098 | benchmark only |

The V12 M1/M2 paper-core certificates do not use compact/CPLEX lower-bound
evidence, focus-only imports, ng-DSSR, two-track relaxed RMP, or diagnostic
large-instance modules. They are full-frontier relaxation certificates: every
final active interval is bound-fathomed by a valid inventory/route/Gini
relaxation lower bound at the verified incumbent cutoff.

## Audit

Command:

`D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_core_round_next\raw --csv-out results\paper_core_round_next\audit\certificate_audit.csv --fail-on-error`

Result: `audited_rows=11 failures=0`.

## Files

- Raw JSON: `results/paper_core_round_next/raw/`
- Logs: `results/paper_core_round_next/logs/`
- Progress: `results/paper_core_round_next/progress/`
- Audit CSV: `results/paper_core_round_next/audit/certificate_audit.csv`
- Summary: `results/paper_core_round_next/summary.csv`
- Convergence: `results/paper_core_round_next/convergence_summary.csv`
- Interval ledger: `results/paper_core_round_next/interval_ledger_summary.csv`


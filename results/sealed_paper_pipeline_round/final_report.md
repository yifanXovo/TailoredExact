# Sealed Paper Pipeline Round Final Report

## Status

- Branch: `codex/longrun-round17-local-results`
- Final commit SHA: recorded in the final response after push.
- Build command: documented fallback `D:\msys64\ucrt64\bin\g++.exe ... -o build\ExactEBRP.exe`
- Sealed preset: `--method gcap-frontier --algorithm-preset paper-exact-v20-certificate --paper-run-sealed true`
- Archive scanning: disabled for all sealed paper-candidate rows.
- External incumbent / known UB injection: not used.
- Instance-specific solver settings: not used.

## Mini-Suite Outcome

| row | status | objective | LB | UB | gap | certified |
|---|---|---:|---:|---:|---:|---|
| V4 smoke | optimal | 0 | 0 | 0 | 0 | yes |
| V12 M2 regenerated | optimal | 0.718504070755 | 0.718504070755 | 0.718504070755 | 0 | yes |
| V12 M1 regenerated | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 0 | yes |
| high_imbalance_seed3202 | optimal | 1.74931345205 | 1.74931345205 | 1.74931345205 | 0 | yes |
| tight_T_seed3101 | optimal | 0.107252734134 | 0.107252734134 | 0.107252734134 | 0 | yes |
| high_imbalance_seed3201 | run_exit_no_final_json |  | 1.74210803 | 2.44340319194 | 0.287015734552 | no |
| tight_T_seed3102 | run_exit_no_final_json |  | 0.450176109171 | 0.600704436685 | 0.250586342169 | no |
| moderate_seed3301 | run_exit_no_final_json |  | 0.00921610362464 | 0.0491525526647 | 0.8125 | no |
| moderate_seed3302 | run_exit_no_final_json |  | 0.027511341546 | 0.195636206549 | 0.859375 | no |

Machine-readable tables:

- `sealed_minisuite_summary.csv`
- `sealed_minisuite_interval_status.csv`
- `sealed_minisuite_oracle_summary.csv`
- `sealed_minisuite_bpc_summary.csv`
- `run_exit_summary.csv`

## Certificate Bases

The certified V12/V20 rows are full-frontier certificates with
`unresolved_intervals=0`, `invalid_bound_intervals=0`, `open_nodes=0`, verified
incumbents, and `certified_original_problem=true`. Automatic interval-oracle
closure was not needed for the certified rows in this round.

The noncertified V20 rows did not produce final JSON under the final sealed
preset. Their progress and UB logs are preserved and summarized as run-exit
failures rather than converted into certificates.

## Audit

Commands run:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\sealed_paper_pipeline_round\raw --csv-out results\sealed_paper_pipeline_round\certificate_audit.csv --fail-on-error
build\ExactEBRP.exe --method certificate-basis-test ...
build\ExactEBRP.exe --method option-consistency-test ...
D:\msys64\ucrt64\bin\python.exe scripts\audit_no_instance_special_cases.py --out results\sealed_paper_pipeline_round\no_instance_special_case_audit.txt
```

Audit result:

- certificate audit rows: 7;
- certificate audit failures: 0;
- no-instance-special-case audit: pass.

## Answers

1. Did every row use the same sealed unified algorithm?
   Yes for the final sealed commands. Only input, output, and time budget differed.

2. Did any row use archive scanning, external UB, or instance-specific settings?
   No. Sealed provenance fields and the no-instance-special-case audit confirm this for final JSON rows.

3. How many V20/M3 rows certified?
   Two of six: `high_imbalance_seed3202` and `tight_T_seed3101`.

4. Which rows remain noncertified and why?
   `high_imbalance_seed3201`, `tight_T_seed3102`, `moderate_seed3301`, and
   `moderate_seed3302` did not produce final JSON under the final sealed pass.
   Their last progress checkpoints show unresolved frontier intervals and
   positive gaps. These rows are run-exit/finalization blockers, not certificates.

5. Did automatic interval oracle closure help?
   No certified row required it. The earlier diagnostic `moderate_seed3301`
   oracle attempt timed out on a low-Gini leaf and was moved outside `raw/` to
   avoid confusing it with final sealed evidence.

6. Did automatic BPC fallback help?
   No. It remains diagnostic/off by default.

7. Is the algorithm ready for broad benchmark testing?
   Not yet. V12 is stable and two V20/M3 certificates are reproducible under
   sealed provenance, but four V20 rows still need robust run finalization and
   exact interval-closure diagnosis. The next round should fix the long focused
   retry/finalization behavior so every sealed run emits a final noncertified
   JSON with its open intervals, then target `moderate_seed3301` and
   `tight_T_seed3102` again.

## Evidence Package

The paper-candidate evidence package is:

```text
results/paper_evidence_candidate/
```

It contains command manifests, instance hashes, sealed provenance audit,
certificate audit, no-instance-special-case audit, raw JSONs, interval ledgers,
progress logs, UB event logs, and summary tables.

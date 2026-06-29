# Paper Evidence Candidate Report

The candidate evidence package is stored under:

```text
results/paper_evidence_candidate/
```

It collects the sealed command manifest, instance hashes, raw JSONs, interval
ledgers, UB event logs, certificate audit CSV, no-instance-special-case audit,
and summary tables produced by the latest sealed evidence round.  The current
package mirrors `results/sealed_closure_round/`.

Rows are classified as:

- `certified exact`: full original-problem certificate with audit pass;
- `noncertified with gap`: full run completed but at least one interval remains
  unresolved;
- `diagnostic only`: interval-local oracle or BPC evidence that was not safely
  merged into a full frontier certificate.

The evidence package is generated from sealed rows only. Archive scanning,
external incumbents, known UB injection, focus-only certificates, and
instance-specific algorithm settings are excluded from paper-candidate rows.

## Current Sealed Closure Classification

Certified exact rows:

- V4 smoke;
- V12 M2 regenerated;
- V12 M1 regenerated;
- `high_imbalance_seed3202`;
- `tight_T_seed3101`.

Noncertified rows with final JSON:

- `high_imbalance_seed3201`;
- `tight_T_seed3102`;
- `moderate_seed3301`;
- `moderate_seed3302`.

The noncertified rows are represented by solver-final raw JSONs in the sealed
closure round. They are included in
`results/sealed_closure_round/certificate_audit.csv` and pass audit because
they honestly report `certified_original_problem=false`, positive gaps,
unresolved intervals, and oracle/BPC plateau reasons.

The project is not yet ready for broad paper benchmark testing: V12 behavior is
stable and two V20/M3 stress rows certify, but the requested third V20
certificate was not obtained in the sealed closure round.

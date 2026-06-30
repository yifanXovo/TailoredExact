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

## Oracle Closure Round Update

The paper evidence package now mirrors `results/oracle_closure_round/`.  It
includes the corrected oracle budget semantics, recursive partition traces,
BPC fallback summaries, raw JSONs, interval ledgers, progress logs, UB logs,
certificate audit, and no-instance-special-case audit.

Certified exact rows remain:

- V4 smoke;
- V12 M2 regenerated;
- V12 M1 regenerated;
- `high_imbalance_seed3202`;
- `tight_T_seed3101`.

Noncertified with audited gap:

- `moderate_seed3301`;
- `tight_T_seed3102`;
- `high_imbalance_seed3201`.

`moderate_seed3302` was not rerun in this round after priority time was spent
on the moderate/tight/high-imbalance closure attempts.  The evidence package
therefore supports continued targeted interval-oracle work, not a broad paper
benchmark matrix.

## Oracle Bound Merge Round Update

The paper evidence package now includes the oracle-bound merge evidence from
`results/oracle_bound_merge_round/`.

Certified exact rows remain:

- V12 M2 regenerated;
- V12 M1 regenerated;
- `high_imbalance_seed3202`;
- `tight_T_seed3101`.

Noncertified rows with audited gaps:

- `moderate_seed3301`: `LB=0.047773`, `UB=0.0491525526647`,
  `gap=0.0280667552335`;
- `tight_T_seed3102`: `gap=0.250586342169`;
- `high_imbalance_seed3201`: `gap=0.123531471571`.

The evidence package classifies `moderate_seed3301` as an improved
noncertified exact row, not as a certificate. The project still needs at least
one additional V20/M3 certificate before broad paper benchmark testing.

## Strengthened Oracle Round Update

The paper evidence package now mirrors `results/strengthened_oracle_round/`.

Certified exact rows include:

- V12 M2 regenerated;
- V12 M1 regenerated;
- `high_imbalance_seed3202`;
- `tight_T_seed3101`;
- `moderate_seed3301`.

`moderate_seed3301` is now certified with
`objective = LB = UB = 0.0491525526647` through automatic exact interval oracle
closure of the final frontier leaves.  Plain CPLEX comparison rows are included
only as benchmark evidence and do not contribute to paper-core lower bounds.

The current readiness decision is paper-candidate ready for a controlled
benchmark matrix: V12 remains stable, V20/M3 hard-stress certification is
`3/6`, and all optimal claims pass audit.

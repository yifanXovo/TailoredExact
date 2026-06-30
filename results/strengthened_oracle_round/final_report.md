# Strengthened Oracle Round Final Report

Branch: `codex/longrun-round17-local-results`

Final pushed HEAD is recorded in the assistant final response.

## Implemented Changes

- Added original compact interval oracle strengthening fields and CLI flags:
  `--gini-spread-cuts`, `--required-movement-cuts`,
  `--global-handling-capacity-cuts`, and
  `--low-gini-ratio-band-tightening`.
- Added Gini max-spread rows, penalty-domain final-inventory tightening,
  required net movement rows, aggregate handling capacity rows, and singleton
  transfer/duration compatibility rows to the compact interval oracle.
- Extended oracle JSON and auto-oracle CSV logging with cut counts, domain
  tightening counts, movement lower bounds, and enabled strengthening families.
- Fixed full-ledger merge finalization so `open_nodes` is cleared when automatic
  interval oracle closes all remaining leaves.

Proof sketches: `docs/v20_interval_strengthening_lemmas.md`.

## V20 Status

V20/M3 certified rows now: `3/6`.

Certified:

- `high_imbalance_seed3202`, objective `1.74931345205`;
- `tight_T_seed3101`, objective `0.107252734134`;
- `moderate_seed3301`, objective `0.0491525526647`.

`moderate_seed3301` is the new certificate in this round.  The sealed run closed
all `9` unresolved leaves with automatic interval oracle evidence and wrote a
merged full-frontier ledger.  Final status is `optimal`,
`certified_original_problem=true`, `unresolved_intervals=0`, `open_nodes=0`.

Noncertified:

- `high_imbalance_seed3201`: strengthened run improved the gap to
  `0.0724502581182` with two oracle-bound merged leaves still open.
- `tight_T_seed3102`: the strengthened full row exited abnormally before final
  solver JSON; an honest noncertified `error_json` artifact is included and
  audited.
- `moderate_seed3302`: skipped in this targeted round after the primary V20
  certificate target was reached.

## V12 Stability

- V12 M2 remains certified: objective `0.718504070755`, runtime about `66.97s`.
- V12 M1 remains certified: objective `0.357200583208`, runtime about `216.97s`.

V4 smoke was skipped because the expected input file is not present in this
checkout.

## CPLEX Comparison

Plain compact CPLEX 300s comparison rows are in
`results/strengthened_oracle_round/cplex_comparison_summary.csv`.

CPLEX is benchmark-only evidence.  It is not used as an incumbent source or
lower-bound source for the sealed exact pipeline.  On `moderate_seed3301`, CPLEX
remained noncertified with gap about `0.41148`, while the sealed exact pipeline
certified the row with the strengthened interval oracle.

## BPC Fallback

BPC fallback closed zero leaves.  It remains diagnostic and is not promoted to a
paper-default certificate path.

## Audit

Commands run:

- `audit_bpc_certificate.py --self-test`;
- `audit_bpc_certificate.py results\\strengthened_oracle_round\\raw --fail-on-error --require-progress-finals ...`;
- `certificate-basis-test`;
- `option-consistency-test`;
- `audit_no_instance_special_cases.py`.

Audit result: `audited_rows=36 failures=0`.

## Paper-Readiness Decision

The project reaches paper-candidate readiness for a controlled benchmark matrix:
V12 remains stable, V20/M3 certification improves from `2/6` to `3/6`, every
optimal claim passes audit, and the successful V20 rows use sealed,
no-archive, no-known-UB, no-external-incumbent evidence.

The next round should run a controlled paper benchmark matrix, while keeping a
targeted closure track for `tight_T_seed3102` abnormal exit and
`high_imbalance_seed3201` remaining open leaves.

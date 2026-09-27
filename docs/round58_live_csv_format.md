# Round 58 live evidence format

Round 58 maintains three interruption-safe local files while the sequential
benchmark runs:

- `tmp/round58_live_runs.csv` appends and flushes one hash-bound row after
  every completed arm;
- `tmp/round58_live_pairs.csv` is atomically rewritten after arm and pair
  state changes;
- `tmp/round58_live_status.json` is atomically refreshed every 15 seconds
  while a process is active.

The run ledger includes scenario structure, method and stage, cap and actual
wall time, Work, native status, strict certificate, independently verified
incumbent values, qualified LB/UB and three explicit gaps, node/iteration and
interval counters, route status, P-GRB expected/actual fingerprints, and
result/completion-marker identities. Blank values mean unavailable, not zero.

The pair ledger contains screen and current final status for both methods,
certificate/time/Work/bound fields, current common-horizon classification,
extension state, completion state, and update time. A pair remains incomplete
until both mandatory screen arms and every extension authorized by the frozen
policy have valid completion markers.

On restart, the runner rereads completion markers and verifies the command,
result, verification, executable, scenario, and run-identity hashes. A valid
completed arm is never rerun or appended twice. A retained incomplete run
directory is stopped for manual audit rather than silently overwritten.

The live files are intentionally not committed. Compact committed equivalents
are regenerated under `results/gf_citibike443_k1_vs_pgrb_round58/` after each
completed pair and at finalization.

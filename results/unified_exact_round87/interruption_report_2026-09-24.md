# Round 87 campaign interruption (2026-09-24)

The frozen serial campaign stopped without a `driver_completion.json`. This is an incomplete campaign, not an 18-run result or an optimality certificate for the active arm. No arm was restarted.

## Last committed campaign state

- Source: `campaign/runtime_status.json`, last written 2026-09-24 07:30:57.564 UTC.
- Active run: 8/18, F2 / P-GRB, process time 70,639.953 seconds.
- Latest legally observed verified UB: 0.8659435203229894.
- Latest legally observed global LB: 0.8386268851956563.
- Last committed gap: 0.027316635127333067; committed events: 719,869.
- Completed before this arm: 7/18 runs and 3/9 pairs, according to `campaign/summary.json`. The seventh completed run, F2 / ENS-C, passed its audit. F2 / P-GRB has no completed record.
- Last sampled available memory: 8,048,271,360 bytes; runtime disk free: 109,557,035,008 bytes. These samples were above the frozen resource stop thresholds (2 GiB memory, 5 GiB disk) and do not establish the cause of termination.

## Independent liveness check

The prior terminal session handle (50263) was unavailable on the first check at approximately 07:32 UTC. At 2026-09-24 07:33:46 UTC, driver PID 4400 was absent, no `ExactEBRP` solver process or matching `round87_research` Python process was present, and `campaign/driver_completion.json` did not exist. The status file had not changed for 168.8 seconds. Windows reported its last boot as 2026-08-13 06:38:49 UTC, so this observation was not explained by a system reboot. The user subsequently identified insufficient agent quota as the cause of interruption.

## Evidence handling

The raw destination recorded for the active arm is `E:\codes\ExactEBRP-round87-runtime\campaign\local_raw\08_F2_P-GRB`. Its journal has 719,974 contiguous committed events, ending at process time 70,647.7970615 seconds; the last event is a global-bound update. No normal result or optimality certificate exists. The user explicitly authorized trusting completed runs and the interrupted arm's terminal data, and continuing only remaining arms. The recovery treats arm 8 as a right-censored interruption, independently replays its journal, preserves an original seven-run summary snapshot, and launches only arms 9–18 with `scripts/round87_resume.py`. Because the original driver-observation timestamps were lost, all recovered events use the final receipt-close time as a conservative availability upper bound. The reconstructed `wall_seconds` is a lower bound on actual process exit time, not an exact exit time; downstream tables require this caveat. No arm is restarted.

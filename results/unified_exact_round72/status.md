# Round72 active: same-byte DS-X validation

Base Round71 final73ce04d9a3c5031c2b5a1021523502f0a9a85168 / draft PR132.
Branch codex/round72-vdsx-validation. The six startup-only diagnostics passed
independent physical and strict terminal-trace checks: 0.390s, zero Optimize
calls, zero new qualification. 48 compact artifacts are archived. One observed
offline packaging failure was repaired without changing raw solver evidence.

DS-X improves startup U from0.166376 to0.129719 onD3, from0.854344 to0.837091
onC2, and from0.723143 to0.592081 onD4. Actual cross-route checks/moves are
47/28,94/22,131/46. This is UB-only evidence, not proof performance.

The service subsequently reported100% remaining with ordinary use allowed.
The agent did not consume a reset credit. The earlier authorization question
has no explicit answer and confers no authority to redeem a credit. The reason
for restoration is unknown; no reset is needed for current work.

The nine fullD3/C2/D4 runs are complete and fully audited:1817.642s,36 native
Optimize calls, zero solver failures. DS-X certifiesD3/C2/D4 in255.360/111.234/
54.703s; all three P arms remain open. DS is open onD3 and certifiesC2/D4 in
154.219/53.860s. Read short_validation.md and campaign/result_tables.md.
22 model checks,11 accepted/fully observed Starts,159 full-run compact artifacts
pass. All six formal startups independently reproduce diagnostic route hashes
and logical traces. Combined15 experiments cost1818.032s; no new qualification.

campaign/long_gate.json now admits the predeclared D7 three-arm3600s reserve.
Latest resource check: ordinary use allowed,97% remaining, no agent reset.
Next preserve the audited checkpoint, then execute
python scripts/round72_campaign.py run --ids D7 .
Do not repackage before dispatch: the gate binds the exact audited nine-row
runs.csv. Later full packaging retains short_runs.csv/short_pairs.csv and the
checkpoint commit preserves all gate audits. Inspect processes.jsonl and the
active_run.lock before resuming; no long run has launched at this checkpoint.
The overall goal remains unmet; no independent confirmation is claimed.

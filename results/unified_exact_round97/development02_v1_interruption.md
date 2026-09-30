# V1 feedback interruption and independent endpoint recovery

Registered arm9 ran once for 1798.078 process seconds within its common 1800-second cap. The supervisor imposed `whole_run_hard_stop`; it did not reach normal finalization. The original audit failed because `paper_optimize_ledger.csv` contains only its header. The original failed `audit.json`, null endpoint in `summary.jsonl`, queue failure and absence of `result.json` remain unchanged. Arm10 P-GRB had not started when the queue stopped.

`development02/hard_stop09_recovery.json` is a separate, narrowly scoped observational recovery. It verifies all 108 committed payloads, including their hashes, close times and original observation times. Independent original-physics verification covers nine journal witnesses. The R97 event audit also passes, and ten retained input/mapped vectors pass the actual model row, type, bound and objective checker without Optimize.

The corresponding OFF arm uses exactly the same three canonical model hashes and scope metadata. This supports model identity only; no OFF time, witness, bound or result is reused. The canonical files are MILP templates: the first three LP calls relax types in memory. Their logs and fingerprints must not be interpreted as exported integer optimization models. Journal calls4/5 are MIPs; they correspond to R97 setup calls1/2 by native log path and model hash, because the counters have different scopes.

Both MIPs cover the complete root interval `[0,U0]`, where the same-run independently verified startup gives `U0=0.28404156412463055`. Their committed parameter readbacks and frozen source establish the unmodified native scope. The recovery deliberately excludes inherited LP and cover lower bounds. For each of the 89 committed native bound events it independently uses `min(U0,max(0,native_bound))`; outside the root interval, `F>=G>=U0`. The maximum of these valid global lower bounds agrees with the R86 replay endpoint. Early recovered trajectories must use this conservative formula too, not retroactively restore inherited LP bounds.

| Outcome | U | L | Absolute gap | Finalization |
|---|---:|---:|---:|---|
| V1 OFF arm8 | 0.17155123467659872 | 0.1534048797180084 | 0.01814635495859032 | Normal, uncertified |
| V1 FEEDBACK arm9 | 0.16951364260212742 | 0.15346582763163313 | 0.01604781497049429 | Independently recovered interruption |

These are observed quality endpoints, not certification-time evidence. The recovered arm has five observed call scopes and four returned calls; complete Optimize accounting and a normal-return certificate remain unknown. The R97 stream has 13 solution events, ten eligible positive-node events, three strict closures/submissions, three vector observations, two fresh combined-operator incremental events, and zero archive handoffs. Three `native_incumbent_change` records mean per-submission threshold satisfaction, not proof of unique source or a complete count of native updates. Terminal callback-return telemetry is missing; summed complete callback-return time cannot be reported as total callback overhead.

The first recovery check failed because it incorrectly required the child LPs to share root dimensions; that zero-Optimize failed receipt is retained. The corrected check matches each observed LP shape to its corresponding frozen OFF model and requires root dimensions only for the two root MIPs. Successful recovery wrapper cost is 1.0902325s; actual-vector wrapper cost is 1.5708301s. Additional direct exploratory read/replay work was not comprehensively wall-timed and is not presented as complete host-wall accounting.

Independent read-only review confirmed the restricted root-bound argument, source distinction between LP/MIP, setup counter mapping and required limitations. The continuation script admits only this exact hashed recovery plus the existing arm5 acknowledgement. It preserves all original records, launches only original unstarted arms, uses the unchanged frozen supervisor/auditor/commands, and stops on any further abnormality.

Recovery and continuation commands (recovery outputs already exist; do not rerun over them):

```powershell
D:/msys64/ucrt64/bin/python.exe scripts/round97_recover_v1_interruption.py
D:/msys64/ucrt64/bin/python.exe scripts/round97_continue_after_v1_recovery.py --completed 9 --through 10
```

After arm10 and V1 interpretation, the separately admitted original F2 block is `--completed 10 --through 13`. No candidate has yet been frozen for confirmation. ENS-C remains the protected default.

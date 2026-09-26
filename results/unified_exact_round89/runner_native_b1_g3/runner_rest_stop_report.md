# Round89 native-B1 G3 rest — preregistered D3 stop

The admitted `D:/msys64/ucrt64/bin/python.exe scripts/round89_native_b1_g3.py run-rest` was invoked **once**. It returned exit 1 after 456.1180496 s outer wall because the runner's preregistered `severe_certification_time_signal` stopped progression after the D3 pair. `runner_rest_completion.json` records 2/12 rest arms completed, 455.219 s combined solver-process wall and the explicit pause-for-root-review reason. All raw output and the full outer stdout are retained. The next C2 arm and all remaining ten rest arms were not launched.

| D3 contemporary arm, same Round89 binary | Process wall | End to end | Verified U | Valid L | Certificate / audit |
|---|---:|---:|---:|---:|---|
| ENS-C | 155.391 s | 155.660 s | 0.04500155005562836 | 0.04500155005562838 | yes / pass |
| native-B1 | 299.828 s | 300.108 s | 0.04500155005562836 | 0.045001550055627795 | yes / pass |

The B1 D3 call has 2/2 MIP summaries, each uniquely joined to its Optimize ledger row and matching the current canonical LP SHA. It records 29,287 MIPNODE calls, 1,168,398 checked pairs, 21,772 reliable rows and 21,772 `GRBcbcut` API-success submissions; setup and callback accounting are 0.0100371 s and 15.8609288 s respectively. API success does not prove solver retention or causal bound gain. The D3 cross-arm original-problem audit passed. The observed D3 certification walls triggered the fixed severe signal; this is a role-specific finding and no broad speed conclusion. Both D3 arms were fully certified, so there is no censored D3 gap. The ten unlaunched roles have no Round89 performance observation.

Round88 P-GRB timings are separately identified historical, unpaired development evidence. They are neither a third contemporary D3 arm nor pooled with these Round89 process walls. The exact `source_round` 83/85/87 P metadata in the preregistration describes canonical model ancestry rather than timing run dates.

The outer receipt contains UTC start/end, command, exit and wall; `runner_rest_risk_stop.json` records the triggering signal and the immutable summary SHA. A post-stop OS query found no matching ExactEBRP, Gurobi, build or Round89 runner process. The computation slot was released. No retry, parameter change, continuation, or rest expansion was attempted.

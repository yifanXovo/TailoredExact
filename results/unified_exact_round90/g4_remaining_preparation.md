# Conditional nine-role Round90 G4 continuation

This is source-only preparation while the F2/D6 priority pair is still under separate computation. It does **not** assume that pair passes, authorize Optimize, add four larger roles, or promote LP-G. The nine roles are exactly N12, D4, E7, C6, C8, F1, C20, B50, S50 from `research_plans/ensc_optimization_instances_2026-09-26.json`. Each role has contemporary ENS-C and LP-G runs on the **same** frozen Round90 binary and its original 24+1 startup. The order alternates ENS-C/LP-G then LP-G/ENS-C by role, beginning with N12 ENS-C. Gurobi Seed 0, one thread, affinity mask 4 and Presolve Auto stay fixed.

| Role order | Pair order | Complete cap per arm |
|---|---|---:|
| N12 | ENS-C, LP-G | 120 s |
| D4 | LP-G, ENS-C | 600 s |
| E7 | ENS-C, LP-G | 120 s |
| C6 | LP-G, ENS-C | 1,200 s |
| C8 | ENS-C, LP-G | 1,200 s |
| F1 | LP-G, ENS-C | 120 s |
| C20 | ENS-C, LP-G | 1,200 s |
| B50 | LP-G, ENS-C | 3,600 s |
| S50 | ENS-C, LP-G | 3,600 s |

The 18 complete-process caps sum to **23,520 seconds**. Each CLI process has the same six-second native-limit, two-second hard-stop and three-second shutdown offsets as the audited Round90 G3 and F2/D6 G4 priority wrappers. The [preregistration](preregistration_g4_remaining.json) pins every scenario, input SHA, handling time, T, lambda, arm order and cap. At eventual preparation, the [new wrapper](../../scripts/round90_lp_g_g4_remaining.py) checks these against the fixed 19-role plan and independent Round88 input-identity audit, hashes each actual canonical-root input, and requires the frozen seven Round90 source hashes, candidate binary and complete G3 harness hashes through `round90_lp_g_g4_priority.py::validate`. It loads its own copies of the frozen priority and G3 modules; it does not edit or relabel those historical files.

The wrapper builds all 18 commands with frozen G3 `command_for`, compares their invariant CLI shape with an audited G3 exemplar, and checks the research LP-G flag, ENS-C flag-off, Seed 0 and each whole-run cap. Prepared identity uses the exact `runner_sha256` key read by frozen G3 `run_one`, and the run gate rechecks it. Frozen G3 `run_one` owns process supervision, physical/evidence/coverage/LP-G point audits and full completion receipts. The frozen priority helper verifies normal-result native parameter read-back. After each complete pair, G3 cross-arm contradiction and severe-signal rules apply. Identity, physical, proof, process, resource or severe paired failure stops before the next arm; deadline-censored observations remain explicitly unknown. Already started raw directories and cost receipts remain in place; no retry, resume, overwrite, internal component time slice or extra seed is possible. A shell launch-to-exit receipt is still required because wrapper `full_outer_wall_seconds` begins after preflight validation.

One **root prepare gate** is enough after F2/D6 priority results and independent review have been accepted. It must have `schema=round90-lp-g-g4-remaining-prepare-gate-v1`, `authorized_by=root`, `allow_prepare=true`, `allow_optimize=false`, `priority_stage_accepted=true`, current new prereg/wrapper/frozen-priority-wrapper SHA fields, current priority `run_completion.json`/`summary.jsonl` SHAs, and an accepted independent-review path/SHA under Round90 results. The wrapper additionally requires priority `completed=planned=4`, no error/not-run arms and the exact F2/D6 order. There is no guessed future review hash in this source-only handoff. `prepare` creates one campaign identity and preflight receipt with **zero Optimize** calls.

After root inspects that preparation, one batch lease at `runner_lp_g_g4_remaining/runner_remaining_lease.json` is sufficient: exact object `schema=round90-lp-g-g4-remaining-run-lease-v1`, `authorized_by=root`, `allow_optimize=true`, `identity_sha256=<prepared identity SHA>`, `planned_runs=18`, and the predeclared `execution_order` array. There is no per-arm human approval. The conditional commands, **not to run now**, are:

```
D:/msys64/ucrt64/bin/python.exe scripts/round90_lp_g_g4_remaining.py prepare
D:/msys64/ucrt64/bin/python.exe scripts/round90_lp_g_g4_remaining.py run
```

The final report must retain all 18 planned positions, paid attempted prefix, unstarted suffix, original UB/LB/gap or censoring, physical/coverage/point/cross-arm findings, native parameter evidence, severe signals and full native/wrapper/outer costs. F2/D6 and the eight G3 roles remain historical stages of this development screen; the new 18 arms do not change their raw results or establish a formal speed claim by themselves. No command was imported or executed in this preparation.

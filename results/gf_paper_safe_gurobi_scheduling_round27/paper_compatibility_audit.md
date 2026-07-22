# Round 27 paper-compatibility audit

Status: **PASS**

The dedicated `C2-PAPER` source path contains no per-leaf wall-clock quantum,
WorkLimit, NodeLimit, SolutionLimit, attempt threshold, retry threshold, legacy
launch planner, or split-after-attempt control. Its only native `TimeLimit` is
the remaining overall benchmark deadline, which can stop the complete tree but
cannot select, retry, switch, or split a leaf.

The production HGA loop reads only the completed-generation stagnation counter
and its fixed limit. It stops after 2,000 consecutive completed generations
without strict global-best fitness improvement. Wall time is collected after
the run as telemetry; the legacy wall-time loop remains separately labeled for
historical C0/diagnostic compatibility.

The frozen C2 command contains the generation-stagnation and paper-LP-event
selectors and omits both `--primal-heuristic-seconds` and
`--external-gini-split-after-attempts`. The production source contains none of
the named study instances, so there is no instance/family/size/path dispatch.

See `forbidden_internal_budget_scan.csv`, `leaf_scheduling_audit.csv`, and
`hga_generation_termination_audit.csv` for machine-readable checks.

# Reproduce the unchanged candidate and new observations

The compiler source and binary are inherited from Round71; see its algorithm.md,
mathematics.md, build_v1.json and qualification.json. This stage changes neither
C++ nor preset behavior. Full definitions are also bound by campaign/plan.md
and campaign/mathematics.md. Numerical certificates are not rational proofs.

Use Python with the repository scripts on its normal path, the qualified
build/round71/ExactEBRP.exe and Round65ReferenceBuild.exe, and Gurobi13.0.2.
The driver checks all199 source hashes, both executable hashes and tests.log.
The shared49 tests/39 native qualification calls are inherited; no new batch
is represented as executed. Rebuilding requires a separate qualification and
new identity; do not substitute a rebuilt executable into this campaign.

Original dispatch was:

```powershell
python scripts/round72_campaign.py freeze
python scripts/round72_campaign.py run --ids D3 C2 D4
python scripts/round72_campaign.py package
python scripts/round72_campaign.py verify
python scripts/round72_analysis.py summary
python scripts/round72_analysis.py gate
```

The freeze/run commands refuse existing identities or destinations. Resume
using the write-ahead processes.jsonl and completion.json, without repeating
completed roles. The conditional D7 command is legal only after long_gate.json
records admission and remains bound to the audited nine-run table:

```powershell
python scripts/round72_campaign.py run --ids D7
```

After the complete serial long queue has stopped, run package, verify and
summary again, then `python scripts/round72_checkpoints.py`. The last command
extracts conservative300/600/1200/1800/2400/3600s points from these fresh runs
and refuses an active queue. It adds zero optimizer calls and never joins
historical short runs to a new long run. The gate and short-table snapshots
remain immutable; do not rerun the gate action after the long results arrive.

For a separately budgeted replay, use a new nonexistent repository-relative
output directory. Each selected role runs all three declared arms; the exact
caps, uniform mask4 and paid startup are unchanged. The script is provided but
was not invoked as an additional experiment in the original stage:

```powershell
python scripts/round72_reproduce.py --output results/round72_replay_example --ids D3 C2 D4
```

The six startup-only diagnoses are separately preserved under local_raw and
diagnostic_processes.jsonl. Their entry point uses method primal-heuristic,
whose compiled dispatch performs only the same fully decoded construction.
They supply verified UB-only evidence, zero Optimize calls and no proof claim.
Do not rerun them into existing paths or import their witnesses into formal
runs. Offline packaging uses round72_package_diagnostics.py; it launches no
optimizer. The raw result schema is retained in postprocess_failures.json.

Large raw models, native logs and binaries remain local. Compact evidence
includes lossless traces, exact result fields, physical routes, Start vectors,
coverage and native-call records with source hashes. Original dirty checkout,
closed-stage evidence, official defaults and main remain untouched.

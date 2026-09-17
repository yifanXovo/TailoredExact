# R85 reproduction and producer guards

Use the owned Windows checkout, D:/msys64/ucrt64/bin/python.exe with
PYTHONUTF8=1, Gurobi13.0.2 and the unchanged qualified build/round83/v1 binaries.
The plan and protocol are frozen before the first full launch. Do not rerun
round85_prepare.py over an existing protocol or a campaign producer over a
completed/partial campaign. A fresh reproduction needs a separately identified
output root and run allocation; it must not replace these original observations.

Original sequence: round85_prepare.py (already executed, zero Optimize),
freeze the plan/driver/auditors, then round85_research.py once. It exports seven
original compact references and launches the21 paid arms serially. The campaign
identity binds source/input/binary/driver/settings and the exact commands.
Summary, per-run completion/audit and driver_completion distinguish active,
normal, valid whole-run interruption and invalid runs. active_experiment.json
alone is a retained last-launch record, not proof of a live process.

After all originals close, run round85_analyze.py, round85_mechanism.py and
round85_replication.py once in that order. Their no-overwrite guards preserve
audits. round85_package.py packages all original run/reference files and
verifies every member; --verify-only separately verifies without extraction
or optimization. Source/qualification/startup bytes are inherited from the
hash-bound R83 delivery. Never rerun its qualification to count it as new work.

round85_monitor.py reads compact unreviewed live status. Its log excerpt is
not a physical witness, formal checkpoint, certificate or algorithm gate.
Final plotting and publication receipts will be documented at closure.

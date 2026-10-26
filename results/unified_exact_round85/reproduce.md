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

Closure: round85_summarize.py reads closed audits and writes findings/result
 tables once. round85_plot.py uses the existing build/round81/plot_env Python,
Matplotlib3.11.2, and writes five PNG/SVG figures plus exact checkpoints.
All five PNGs were visually reviewed; receipt and visual_review bind bytes.
Every campaign/audit/package/plot producer is now CLOSED. --verify-only was
executed separately and its original stdout is saved as delivery_verify_only.json.

Publication uses exact existing Git trees/commits, non-force branch updates,
and independent connector ref reads. round85_publish_binary.py checks every
new binary's locally recomputed Git SHA against the base64 creation response;
it does not claim a full remote binary-body readback. Bundle members were
locally verified twice. UTF8-only metadata commits use round85_publish_api.py.
No publication action merges the draft or changes main/defaults.

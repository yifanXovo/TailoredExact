# Stage 0 incident: plain-Gurobi optimize deadline rebase

The first Moderate4301 P-GRB sentinel returned normally but used about 120.1
seconds under a 120-second nominal process cap. The plain backend set its
native `TimeLimit` from the work allowance before canonical model export,
environment startup, model import, and domain audit. It then passed that
unchanged solver-only duration to `Optimize`, effectively rebasing the
absolute deadline and consuming the five-second shutdown reserve.

No official performance run had begun. The affected sentinel evidence and
binary are retained under `invalidated_pre_plain_deadline_fix`.

The general fix recomputes `processWorkRemainingSeconds(options)` immediately
before the native optimize launch and resets the model-environment
`TimeLimit`. A permanent protocol test checks this launch-time dependency.
Fresh clean builds and every Stage 0 suite are rerun at the corrected source
commit. This changes no mathematical model, split rule, Gurobi seed, presolve
setting, gap target, or benchmark parameter.

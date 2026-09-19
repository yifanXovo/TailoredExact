# Round 87 frozen long-certification plan

This is a test-only comparison of the unchanged R83 ENS-C preset against the
official original compact P-GRB model. The research base is R86 head
`95f15acf33b8522870cc5e64baf03a33b131f813`; the measured algorithm source is
still `4496078f25c0cdad1cf7a5c39835fd23121e8978`. No algorithm, mathematical
model, neighborhood, cut, branching rule, split rule, tolerance, default, or
per-instance dispatch is changed.

`protocol.json` freezes nine pairs and their exact input identities before any
R87 solver result is opened. The six requested D6/D7/U6/F2/F5/F6 roles and the
three named R58 CitiBike roles are all retained. No optional role is admitted.
Pair order is fixed and alternates the first arm where possible. K1 is historical
context only and is not run.

Every arm starts from scratch and pays the complete process time. P-GRB uses
`--method gurobi --plain-baseline`, its independently exported original compact
model fingerprint, and no Start, ENS component, added inequality, or imported
bound. ENS-C uses `--method gcap-frontier --algorithm-preset
research-round83-vds-equal-net-exchange` with the inherited witness checks. It
keeps VD-P, F0, AM, 25 decoded starts, strict physical closure, balanced
relocation, equal-net exchange, full Start mapping, full-domain coverage, and
the original numerical certificate contract.

All runs use Gurobi 13.0.2, Threads=1, Seed=0, Presolve=Auto, requested
MIPGap=MIPGapAbs=0, logical processor 2 / mask 4, and the original feasibility,
integer, optimality, physical, and certificate tolerances. A zero requested gap
is a numerical solver contract, not a strict rational proof.

The primary stop is each arm's own original-problem certificate. The uniform
safety cap is 86,400 process seconds per arm. Native time is 86,394 seconds,
the inherited shutdown margin is 3 seconds, and the external guard is 86,398
seconds. The maximum admitted solver cost is 18 runs / 1,555,200 process seconds
(432 hours) executed serially. No shorter historical cap is substituted.

The host snapshot before preparation has 31.82 GiB RAM (17.64 GiB free), a
12-core/20-thread i7-12700KF, about 104.5 GiB free on E, and no ExactEBRP or
gurobi_cl process. Raw models/logs/journals remain under the separate E-drive
runtime root. Before each launch at least 10 GiB must remain. A live arm is
stopped and explicitly censored only if free disk drops below 5 GiB or available
host memory below 2 GiB at two consecutive 30-second checks. Those are host
safety stops, never certificates. Heavy hashing, packaging, plotting, builds,
and offline analysis do not overlap solver processes.

The existing native evidence journal is reused without a new callback. It
records committed call identities, global bounds and physical witnesses. The
driver observes committed receipts without pausing the solver, records process
time, and refreshes a compact heartbeat. Checkpoints are 300, 600, 1200, 1800,
3600, 7200 seconds, every 3600 seconds thereafter through the cap, and the final
endpoint. Missing verified UB gives a null gap; scoped leaf bounds never become
global bounds.

Certification time is the full process completion time for a verified
original-problem certificate. Discovery time is obtained only from that run's
own verified witness history; a final-only witness gives an upper bound on its
discovery time. If no arm certifies a role, analysis uses “first reached this
run's final UB” rather than `t_find*`. A capped or host-stopped arm is censored,
never assigned the cap as a solve time.

The frozen R83 qualification (62 tests, 165 native calls) is inherited by hash
and is not rerun or recharged. Preparation performs only hashes, source/history
checks, input checks, and nine zero-Optimize compact reference exports. Any
correctness failure stops later launches without replacement or automatic rerun.
Raw evidence is preserved even on failure.

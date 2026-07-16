# Current state and forensic plan

Round 19 uses one persistent compact CPLEX model and exact recursive Gini
coverage, but its child estimates copy the parent relaxation and its deferred
row callback did not distinguish the relaxation that existed before adding
local rows from the first relaxation in which those rows were active. It also
resubmitted the full child pack even when most canonical rows and bounds were
already inherited.

Round 20 first instruments those mechanisms without changing their
mathematics. The baseline is `parent-copy + full-inherited-pack + deferred`,
with no native MIP start. Separate switches expose the proved factory-domain
estimate, exact canonical incremental delta, eager branch-row attachment, and
a complete verified native MIP start. None depends on an instance name, seed,
path, known objective, `V`, or scale tier.

The evidence order is fixed:

1. mathematical/unit/source/lifecycle gates;
2. six fresh baseline forensic runs and standalone interval/model diffs;
3. four-way 300-second estimate-by-row-delta ablation;
4. narrowly isolated eager and native-start arms only if the forensic traces
   justify them;
5. fresh eight-instance 900-second baseline/selected comparison;
6. continuous 1800-second selected/plain trajectories on four cases.

Any callback-state ambiguity, signature collision, unsupported factory family,
invalid estimate, missed post-row observation, lifecycle violation, or false
optimality aborts or invalidates the corresponding arm.

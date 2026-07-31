# Long-run callback timestamp root cause

The first frozen official matrix exposed one trace gate failure in
`stage1__round31_sealed_tight_T_V20_seed2113109204__c6_frozen__1800s`.
At CSV row 7619 the callback-reported solver runtime moved backward by
1.318000078 seconds. The serialized native bound and formal global lower
bound continued to improve, the callback event sequence was intact, and
there was no scheduler-bound or mathematical-decision regression.

The trace reconstructed process time by adding Gurobi `GRB_CB_RUNTIME` to a
monotonic process launch timestamp. Gurobi defines that value as elapsed
wall-clock time, so a host wall-clock correction can make it decrease during
a long solve. The general repair timestamps callback telemetry from a local
`std::chrono::steady_clock` epoch. Native Gurobi runtime remains retained in
the final Runtime attribute and native log. No target, requeue, child,
split, closure, deadline, certificate, or solver decision reads the repaired
event timestamp.

The initially completed matrix and derived incomplete classification are
preserved as invalidated evidence. Round 32 is rebuilt, rehashed, refrozen,
and rerun uniformly; the failed CSV row is not deleted, reordered, or
silently edited.

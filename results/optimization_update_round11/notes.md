# Round 11 notes

Implemented certificate-basis reporting for frontier intervals and final BPC results. The V4 smoke frontier remains certified with objective 0 because each relevant interval is skipped by the gamma-floor/nonnegative objective basis; pricing closure is not required for those intervals.

Implemented an automatic iterative frontier-closure loop over the current controlling unresolved leaf interval. The loop refreshes the inventory/route/Gini relaxation, optionally runs exact-CG/tree continuation, checkpoints the pricing verifier, exports per-round interval state, and updates the active frontier ledger. It is certificate-neutral and does not mark any incomplete run optimal.

Implemented partial open-node state export/resume metadata. The current implementation saves selected interval bounds, scalar open-node counts, column counts, and compatibility metadata. It is explicitly reported as partial warm restart (`open_node_state_resume_exact=false`) because live RMP/open-node queues are not fully serialized yet.

Implemented final pricing-verifier checkpoint/resume plumbing. It writes progress/checkpoint files and can report completion only when existing true-dual exact pricing closure is already available. It does not certify closure after time-limited pricing.

V12 M2 iterative closure 300s targeted intervals `[0.465922,0.489218]` and `[0.489218,0.512514]`. The lower bounds did not improve; final gap remained about 0.04090 in the reserved diagnostic row.

V12 M1 multi-focus import accepted one historical focus bound. The full import run improved the active LB to 0.34466673345 but remained open. A lite iterative V12 M1 row executed two iterative rounds and remained open with gap about 0.10566.

No memory/address/fatal error pattern was found in round-eleven logs. CPLEX plain benchmark was skipped in this implementation pass; no speedup claims are made.

Remaining TODOs:
- Serialize true live BPC open-node queues, including node-local RMP state and active cuts, then mark `open_node_state_resume_exact=true` only when this is actually restored.
- Implement a full true-dual route-load pricing verifier with resumable label-DP state; current checkpointing is conservative and does not certify when pricing is incomplete.
- Add reserve scheduling earlier in the initial frontier pass more systematically, rather than through budget capping only.
- Run 1200s/3600s iterative closure rows once local wall-clock budget is available.

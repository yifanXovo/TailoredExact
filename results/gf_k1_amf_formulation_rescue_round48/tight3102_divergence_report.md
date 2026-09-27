# tight3102 divergence reconstruction

The exact historical alignment contains 2 common parent state(s) and 1 action divergence(s). The first divergence is `L0.0`: identical input, interval, incumbent, parent/child bounds, and byte-identical canonical parent model; K1-r015 splits while K1-AM retains. No later exact common parent exists after that action divergence.

The matched one-step RETAIN arm capped at 1180.031 seconds with Work 2444.852437 and gap 0.0742779706. The MIDPOINT arm, with both descendant split opportunities suppressed, completed exact in 789.315 seconds with Work 1500.197653 and zero gap. Thus the historical divergence is confirmed beneficial under a matched replay. AMF predicts retain at this state (`S_AMF < tau`), so the frozen formula does not recover the confirmed divergence. Both arms are restricted diagnostics and neither is an original-problem certificate.

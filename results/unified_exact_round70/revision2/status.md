Revision2 qualified: first configure/build/test attempts passed,47/47 tests,
including an18-Optimize real-CLI nonzero certificate regression. Binary
2e841e23cdbc81f71b9373f35b7c82494223a7ecfbb670bcdc33f7ec2b66e6f3.
Frozen source commit86c35aa7f; no solver changes after freeze. Ten no-opt
original P exports and all six micro runs passed. Full audit after the nine
small performance runs passed; see ../small_screen.md. E7/S12 startup losses
are repaired in these development runs; N12 also improves.
D3's four runs and full audit are complete. DS gap0.001781355 improves over
P0.003475853; versus K1-R0.001160313 it has better UB but weaker LB. VD-S
alone certifies in84.187s; DS loses that gain. No per-point veto is imposed.
Latest full audit19 runs/82 native calls/1039.687s,63 initial-witness model
checks,11 actual Starts accepted/full-vector observed,303 compact artifacts.
C2 then D4, each P-GRB/VD-S/DS at300, is the current serial queue. D6/D7's
eight600-second runs remain unopened. No repeat/extension/confirmation.
Overall goal remains unmet.
Root revision1_failure.json preserves all six earlier micros, including two
DS backend-configuration failures. Never rerun old frozen-stage packagers.

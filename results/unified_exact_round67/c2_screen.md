# C2: short-T protection and full certification

All four300-second whole runs completed and passed the final original-route,
native-parameter and interval-coverage audits. All three K1 variants have the
same paid initial witness; HGA costs2.652/2.706/2.691s.

| Arm | Process wall | Certified | UB | LB | Absolute gap | Relative gap |
|---|---:|---|---:|---:|---:|---:|
| P-GRB |297.062|No|0.8299634131717752|0.7714011871263801|0.05856222604539518|7.056001%|
| K1-R |297.063|No|0.8299634131717752|0.7976971915979978|0.03226622157377745|3.887668%|
| VD-P |132.656|Yes|0.8299634131717752|0.8299634128939517|2.77824e-10|3.34742e-8%|
| LOG |297.078|No|0.8299634131717752|0.8266556524305856|0.00330776074118966|0.398543%|

VD-P gains a numerical certificate against both controls. LOG reduces the
open gap by94.35% against P and89.75% against K1, meeting the frozen severe
improvement criterion, but does not preserve VD-P's certificate. This is a
positive protection result for both formulations, not evidence of a universal
speed advantage or sufficient confirmation for the final unified algorithm.

Each K1 variant makes5 LP calls, one child-bound target MIP and one terminal
MIP, with one split and an infeasible upper half. The second-level LP probes
do not replace the lower parent's remaining complete proof obligation.
Terminal times are292.876/128.273/292.688s, with17051/7001/28956 nodes.
Target MIPs cost0.279/0.282/0.293s. Thus the VD-P gain is predominantly native
terminal search/proof, not saved HGA or one fewer required call.

Root model rows/columns: K1-R8663/2402, VD-P8575/2794, LOG8660/2879. LOG adds85
code rows/variables to VD-P's state relaxation. The first LP objective is
0.6026783958 for both encodings; LP projection equality does not imply equal
native MIP behavior. These statistics explain the result but never govern an
internal time/Work switch. Further VD-P development must preserve this gain
while addressing the D3 loss and the still-unrepaired D6/startup objectives.

# Frozen GI-TBC on six positive n50 configurations

B returned a qualified fleet on 6/6 configurations and P on 6/6. At the prespecified descriptive scale, B had a lower U in 5/6 pairs, a higher global L in 6/6 and a smaller absolute gap in 6/6. The corresponding counts for P were 1/6, 0/6 and 0/6. B certified 0/6 and P 0/6, with 6/6 joint OPEN and 0/6 joint CERT pairs. B reduced relative gap in 6/6 pairs and jointly improved U, L
and absolute gap at the descriptive scale in 5/6. Certificate-time comparisons had an empty joint-CERT subset. Both objective comparisons and the cost ledger use each arm's own evidence.

| Configuration | B / P state | B / P U | B / P L | B / P absolute gap | B / P gap % | B / P process s | B / P audit s | Cert. ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R171-C50-S-C | OPEN / OPEN | 0.536923 / 0.523772 | 0.356919 / 0.291331 | 0.180003 / 0.232440 | 33.53 / 44.38 | 1194.641 / 1194.088 | 6.337 / 0.727 | — |
| R171-C50-S-R | OPEN / OPEN | 0.541165 / 0.574631 | 0.355390 / 0.312450 | 0.185775 / 0.262181 | 34.33 / 45.63 | 1194.076 / 1194.091 | 13.491 / 0.642 | — |
| R171-B50-S-C | OPEN / OPEN | 0.653336 / 0.705181 | 0.416792 / 0.343940 | 0.236544 / 0.361241 | 36.21 / 51.23 | 1194.112 / 1194.086 | 5.575 / 0.583 | — |
| R171-B50-S-R | OPEN / OPEN | 0.572824 / 0.608779 | 0.378424 / 0.186291 | 0.194400 / 0.422488 | 33.94 / 69.40 | 1194.098 / 1194.107 | 5.570 / 0.618 | — |
| R171-X50-S-C | OPEN / OPEN | 0.660495 / 0.729345 | 0.436240 / 0.284463 | 0.224255 / 0.444882 | 33.95 / 61.00 | 1194.101 / 1194.086 | 12.169 / 0.619 | — |
| R171-X50-S-R | OPEN / OPEN | 0.843694 / 0.920095 | 0.551354 / 0.445402 | 0.292340 / 0.474693 | 34.65 / 51.59 | 1194.086 / 1194.098 | 5.544 / 0.549 | — |

The gap percentage is 100 times the nonnegative display gap divided by
the arm's own U. The signed gap and full-precision values are in the
arm table. A dash means the reported quantity was unavailable or
inapplicable. OPEN durations are budget outcomes and certificate times
are reserved for qualified certificates.
Cold P on R171-B50-S-C has Native ObjVal 0.705246149 and a separately verified physical U of 0.705180552 (Native minus physical 6.56e-05). Its incumbent consistency flag is false. The OPEN comparison uses the physical U and the same run's qualified global L of 0.343939898.
[Complete arms](complete_arms.csv) · [Matched differences and costs](comparison_BP.csv)

## Paid work and observable bottlenecks

The producer clocks sum to 14329.67 s. The 6 own H calls took 3.09 s, and 40 Optimize calls (24 LP and 16 MIP) recorded 14298.72 Native s. The six zero-Optimize references took 9.19 s including static checks. Successful independent post-return readers cost 52.42 s (52.42 s across all reader attempts). Native LP and MIP work consumed
140.11 s and 14158.62 s, respectively.
Native MIP accounts for 98.81% of the total
producer clock. The unresolved gaps persist after this paid search.
B's recorded strengthened-model construction used 19.90 s and
its imports used 2.98 s. P's
combined pre-Optimize phase used 1.58 s
across the six arms. The frozen P trace has a combined pre-Native timer.
The final raw Optimize-return marker precedes the qualified journal tail.
The total return-marker-to-tail interval is 0.070 s.
The remaining tail-to-exit interval is 0.442 s.
These timers include evidence handling and finalization. Gross elapsed, occupied scientific time and ordinary publication I/O are recorded in the closeout receipts.

B improved its own H incumbent during the paid exact phase on
6/6 arms (difference greater than the inherited numerical tolerance).
The root LP yielded a qualified original global L on
6/6. Subsequent proof raised it on 6/6.
The B controller accepted 0 splits and declined 6. Its 4 child-bound-target MIP phases requeued the parent 4 times. The unchanged full/root controls leave the controller's independent net benefit unresolved. Endpoint movement and time attribution are
descriptions of this lifecycle. The different model, cutoff and startup
can all change Native search.
[Initial proof scope and actual controller activity](activity.json) · [Costs](cost_report.json)

## Scope

All six generated inputs were included with Seed 0, one thread, three
heterogeneous capacities and the 1,200-s complete-process budget.
Each arm used the same frozen PE and DLL. Each B independently paid for
one full H. P was built separately in its original compact domain with
zero submitted starts. The calibrated T1 route horizon is an input
property. History and archived source-row overlap remain linked.
[Research design](research_design.md) · [Input manifest](input_manifest.json)

The observations extend direct complete-method evidence to six
positive-target configurations at n=50. Their archive-based, synthetic
operational data and single solver Seed delimit the claim. The retained
n15/20/35 evidence answers separate questions. B remains the uniform
main method and C166, D167 and fixed C169 remain off.
[Finite research decision](research_decision.md)

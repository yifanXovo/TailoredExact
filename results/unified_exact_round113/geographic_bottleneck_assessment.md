# Geographic observations

G50-C1 uses the original integer inventory input, V50/M4/Q30 each/T7200. Positive lambda and weights imply F=0 exactly when Y=D. The current full physical fleet, quantities, vehicle assignments and every load prefix are in physical_completion.json. ENS-C has exact Y=D at all 50 stations, G=P=F=0, maximum route duration7197.188309052213<=7200, and zero return loads. Its earliest verified committed zero witness is sequence13; conservative complete-wrapper availability upper322.2456690000836 seconds, complete certification322.5586690000491 seconds. The native true first discovery is unknown.

M-B and P-S both retain one bike of deficit at station20 (Y20=8,D20=9); all other inventories match. G=.0021826280623608025, P=.040000000000000015, F=.008182628062360805. Both have own positive complete H and actual backend exposure, no own zero witness. M-B maximum duration7149.075539656113; P-S7180.990933955269, both legal. Loads start empty, remain in assigned Q30, and one vehicle legally returns carrying one bike and pays unloading time. Cumulative pickups are not Q. Inventory is constrained to[0,C], with no min_ratio floor.

The 25-seed H semantic traces, accepted actions, complete capacity-assigned fleets and inventory agree for P-S/ENS-C/M-B, with initial F=.0325201793721973. Both M-B and P-S improve their own positive H to .008182628062360805 through actual search; they do not merely retain the initial H. ENS-C therefore shows an integer-completion increment over P-S in this window: WIN by sole complete certificate. M-B/P-S is TIE; M-B/ENS-C is severe LOSS by only the control certified. Whole times are1777.2817804088118,322.5586690000491,1771.3991304999217 seconds respectively. This directly exposes a real M-B completion cost without making P-S an adoption gate.

A single deterministic check of the final M-B fleet reduces vehicle1's pickup at station20 from4 to3. It fixes that inventory but makes the following load at station47 equal-1. This proves only that specified change infeasible; it neither searches quantities nor explains the hidden MIP failure. The equal initial H, actual call domains and final quantities support the observed completion difference, not a unique AM or solver-tree cause.

Both tree arms executed3 LP+1 MIP, all returned; P-S executed1 full-original MIP after a complete13326-column Start and API readback. Recorded H/LP/MIP/residual seconds are in time_partitions.csv. Start, native adoption messages, root/end bounds, nodes/Work/cuts, original numeric model and true-G/cutoff scopes/cover are preserved in the corresponding CSVs and raw. These inclusive accounting differences cannot be subtracted as causal gains. Only committed atomic parent replacement events count as splits; hidden branching causes remain unknown. Checkpoints contain observed committed evidence plus conservative wrapper residual, actual endpoints and certificate continuation only.

Cold P's physical incumbent remains diagnostic raw, but its positive LB conflicts with the independently legal zero, so no new primary cold-P comparison is qualified. This is an authority barrier, not an algorithmic LOSS. See blocking_incident.md.

|Actual G50 MIP|Rows/columns|Nodes|Work|Native MIP seconds|Root bound|Atomic splits|
|---|---|---:|---:|---:|---:|---:|
|M-B|102843/23953|2030|3911.76|1735.77|0|0|
|ENS-C|102743/23953|190|663.81|284.57|0|0|
|P-S|35567/13326|12345|2993.88|1758.35|0|0|

All three logs report loading their own initial Start with objective.0325202. Final verified own witnesses improve it; native log loading is not a new-incumbent timestamp. Full cut counts are in native_calls.csv. None of these node/Work/model-row differences identifies a single hidden causal mechanism.

G100-R2 uses V100/M8/Q30 each/T18000 and the original input SHA. All four fixed arms remained unstarted after the G50 authority barrier. Its zero optimum is unknown in this round. No new feasible fleet, certified positive target, LB or whole time exists. All six G100 pairs and all dU/dL/dGap are null/UNEVALUABLE; no UB/LB contribution or completion mechanism can be attributed.

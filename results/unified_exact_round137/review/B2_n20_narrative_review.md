# Independent interim B2 n20 narrative review

Disposition: **PASS for the inspected input-design and four closed n20
configuration narratives**. Separate reviewer `/root/independent_review` during
active B2 arm049. This is not whole-B2,120-position, assembled-paper or PDF
acceptance.

Read only the small manuscript/analyzer source, source_recipe/input_manifest
and twelve sealed endpoint/qualification JSONs for positions37-48. No heavy
reader imports, raw LP/journal parsing or enumeration, aggregation, solver,
build, archive, PDF or native-asset load occurred. Only this review was written.

## Input design and positivity

The Section4 formula matches the preregistered recipe exactly:
T_base=2*d_max/1.5+120*sum(max(b-D,0))/M;
T1=300*ceil(max(1800,.75*T_base)/300);
T2=300*ceil(1.5*T1/300). Recomputing the rounding from each recorded
T_design_base reproduces all eight declared T values. The rule uses input
geometry/stock/fleet, with no solver-outcome term or binding-horizon guarantee.

Each of the four base pairs has identical metadata/input SHA except its
configuration ID and physical T. In particular objective weight, fleet/Q,
handling, cap and Seed remain fixed. All eight lambda*Omega values equal1
within floating-point precision. The metadata table agrees with the manifests:

| Base | n | T1/T2 seconds | Shortage | Omega | Positive floor |
| --- | ---: | ---: | ---: | ---: | ---: |
| R-B20-S / CABI | 20 | 3300/5100 | 20 | 13.47 | .103934669636 |
| R-X20-S / Divvy | 20 | 4800/7200 | 20 | 7.888886 | .126760609800 |
| R-B35-S / CABI | 35 | 4800/7200 | 35 | 18.140499 | .079726803546 |
| R-X35-S / Divvy | 35 | 4200/6300 | 35 | 13.261724 | .097747095325 |

These are the previously audited serialized shortage/positive-weight floors,
not new solver L values or evidence that n35 production is complete. The new
source includes the required lambda>0/rho>0 premise and correctly distinguishes
the analytic floor from the reported native bound.

## Closed n20 evidence

All twelve inspected positions have completed necessary qualification and
performance eligibility. GI-TBC certifies all four n20 configurations; both
compact controls remain open on all four, with null own T_cert.

| Configuration | GI-TBC U | GI-TBC L | Own certificate seconds |
| --- | ---: | ---: | ---: |
| R-B20-S-T1 | .480735435974 | .480735422994 | 784.143484051 |
| R-B20-S-T2 | .198473446865 | .198473446865 | 538.602931936 |
| R-X20-S-T1 | .645325030386 | .645325030386 | 20.506461604 |
| R-X20-S-T2 | .434795630821 | .434795628383 | 337.304909019 |

In both pairs, the larger-T feasible U is strictly below the smaller-T
qualified L by far more than1e-7. Thus the claimed strict value improvement is
supported under the accepted numerical qualification policy. R-B20-S has
lower observed certificate cost at larger T; R-X20-S has higher cost. These
are the stated opposite observed proof-cost directions, not a runtime theorem.

At R-X20-S-T1, all three own verified U values are exactly
.6453250303858205. P/PS retain L=.589196857510/.590359222619 and no own
certificate, while GI-TBC closes its own gap. The prose correctly discusses
this as a complete-method proof-gap difference. It neither transfers the
GI-TBC proof/time to the controls nor assigns the result to an isolated
component. Open controls are not assigned cap-based speed ratios.

## Operation-table source contract

The table reads G/P_avg/S and physical T from the current arm records, and
joins `returns` and `maximum_duration` by position from operation records.
Those operation keys are emitted by inherited `round134_analyze.gather`;
its per-vehicle records include travel, complete handling, pickups/drops,
returned load and peak prefix load. The table's source keys are consistent.
Route utilization is explicitly descriptive of each own verified incumbent,
including open positions, and is not called proof of a binding optimum.

No concrete defect was found in this narrow source/n20 endpoint scope. Keep
the completion guard and defer n35/resource-panel totals, full operation-data
validation and final integrated/PDF acceptance until actual completion.

# Residual insertion exists after the decoded handoff

Both fixed-witness diagnoses finish normally and pass independent physical
replay. The harness links the unchanged qualified R75 v2 library; no Optimize
is called and no saved witness enters a formal algorithm.

|Role|Initial F|Closed-insertion F|Accepted motifs|Served before/after|
|---|---:|---:|---:|---:|
|D6|0.160027280604|0.160027280604|0|30/30|
|D7|0.380773687462|0.336367943448|2|46/50|

D7 first inserts pickup40/drop18, q6, into vehicle2, adding848.032278s of
mathematical route duration. It then inserts pickup3/drop33, q3, into the same
vehicle, adding750.670491s. The second move increases deviation P slightly
but decreases the complete F through Gini; a stationwise penalty rule would
miss that distinction. The final physical witness has G0.112576917438,
P1.491940173402,192 pickups/drops, and maximum duration17985.801547.
The fourth vehicle remains unused. No claim about the unique cause of the
remaining deficit follows from that fact.

The constructor proposes7642 placements and evaluates120 feasible quantities
over3 passes. No new insertion is available afterward because all50 stations
are served. D6 proposes0 placements/quantities because its30 stations were
already served. These are properties of the declared unvisited-insertion
neighborhood, not global local-optimality certificates for arbitrary moves.

One harness compile costs1.4171765s; two full process runs cost0.093s;
independent replay costs0.0145785s. The entire measured driver costs1.640808s,
including preparation and all those nested components. Do not add that total
again to its components. All source/input/library/compiler identities and
failure/deadline fields are in diagnostic/identity.json and summary.json.

The11.66% D7 F improvement motivates an actual uniform closure implementation.
It does not demonstrate a speed benefit, preserve K1 protection, or establish
independent generalization. D7 remains far above the historical K1 physical UB.
Read implementation_plan.md for the next separately admitted work.

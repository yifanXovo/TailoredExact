# Confirmation scope and analytic nonzero checks

The candidate, parameters and execution rules were already frozen in R78.
R79--81 supplied development evidence and limited replication without changing
that candidate. R82 fixes six roles, their generation recipe and seed rule in
commit d7e5d5fd64ffffc1694d22cba8f1490cc19de1a6, before the only generation pass.
Generation takes0.288694s and makes zero optimizer calls. All six draws remain.
The protocol binds their serialized input hashes; fresh compact exports bind
their P fingerprints. Familiar recipes and shared sources limit the scope of
confirmation even though these exact draws were not used to design BDS-C.

With empty vehicle departure, flow balance gives

    sum_i Y_i = sum_i b_i - sum_k return_load_k <= sum_i b_i.

All six instances have positive lambda, positive service weights and positive
targets. Therefore F=0 implies Y_i=D_i for every station. A total initial stock
below the total target excludes zero, independent of route or proof strategy.
This applies to U1, U3, U5 and U6. Loaded return cannot fill a stock shortage;
it is allowed throughout, and station inventory is not incorrectly conserved.

Under single-visit, nonzero one-way service, achieving Y=D requires total pickup
P0=sum_i max(b_i-D_i,0). Each route satisfies travel+120*pickup<=T here, so
P0<=M*T/120 is necessary even before travel. U4 has equal total initial and
target stock but needs92 pickups; its handling-only capacity is90. Thus U4
also has a strictly positive optimal objective. This check is a necessary
condition, not a route feasibility oracle or a proof that a run will be hard.
U2 passes these necessary zero checks; the generation record correctly leaves
its zero status unknown. Later solver findings do not rewrite that record.

|Role|Initial total|Target total|Pickup needed for zero|Handling-only capacity|Pre-solve zero exclusion|
|---|---:|---:|---:|---:|---|
|U1|235|240|91|20|Stock shortage|
|U2|132|118|43|60|Not established|
|U3|288|454|164|60|Stock shortage|
|U4|516|516|92|90|Necessary handling|
|U5|795|821|185|90|Stock shortage|
|U6|569|647|157|600|Stock shortage|

These facts classify the preselected roles. They neither filter inputs nor add
cuts, starts, lower bounds or selectors to any measured arm. In particular, a
structural nonzero argument is not a measured full-domain MIP proof gain.

The new Citi selections share the original443-station universe. U2 shares all12
stations with the old V50 compact r2 selection (Jaccard.24); its largest Jaccard
is7/13 with the old V8 compact r2 selection. U4's largest Jaccard is15/65 with
the old V50 regional r1 selection. U6's is14/66 with the old V30 regional r1.
The complete old/new and new/new overlap counts are in generation.json. No
station overlap was rejected. Coordinates and capacities are source-derived;
inventories, targets, weights, centroid depot and operating parameters are
synthetic, and travel is straight-line distance/1.5, not a street network.

The three synthetic roles use the existing three-cluster geometry with fresh
deterministic seeds, different inventory recipes and fleet conditions. These
are not independent geography families simply because their seeds differ.
The panel supports a limited statement across the represented input types;
it cannot estimate population-wide dominance or statistical significance.

Any later use of these outcomes to revise the candidate changes these roles
to development data for that revision. Original confirmation results, including
negative results, remain available. A revised candidate needs other unadapted
evidence, not relabeling or replacement of an adverse draw.

# Initial JI tranche: fast construction with a material quality tradeoff

This is a component checkpoint, not stage closure or an exact-performance claim.
Sourcec825be043cb1ebb5d8b1f4f0a21ff71747c7d2a4, executable
05483b078d1d50ea09f169d9e2b5e4b76b2c4452ff5bbfb94f42d0f5ed5a7283,
build/round73/v3. All51 CTests pass, including actual JI native certification
of5/24 and18 Optimize calls.37 exhaustive structural comparisons cover2741
physically feasible motifs. Two previous qualification revisions each pass
50/51 tests and reject the JI native path before any Optimize because separate
historical AM/coarse startup guards lacked the new preset. Both failures,
logs, result and source identities are retained. Total qualification135 native
calls includes39+39+57 across the three actual batches; none is hidden.

All10 declared startup diagnoses complete,15.438s and zero Optimize calls.
No full-problem certificate is inferred from these UB-only results.

|Role|DS-X initial F|JI initial F|DS-X wall(s)|JI wall(s)|
|---|---:|---:|---:|---:|
|D3|0.129719447430|0.101615105724|0.062|0.032|
|C2|0.837091467555|0.847762090530|0.063|0.031|
|D4|0.592081017430|0.540094099931|0.078|0.031|
|D6|0.160027280604|0.301950469274|5.578|0.047|
|D7|0.544510590216|0.442597489124|9.438|0.078|

All JI accepted prefixes are replayed independently from the CSV insertions;
final route hashes, inventories, load prefixes, handling/travel and original F
match retained results. All constructions exhaust their specified motif set;
no diagnostic terminates by deadline. DS-X completes all24 finite seeds.
155 lossless startup/qualification artifacts,302741bytes, are checked against
1522740 original bytes. Source/input/driver hashes also pass. Complete raw
result JSON is preserved losslessly, not replaced by selected successful fields.

The quality regression on D6 is structurally informative. JI assigns all30
visited stations to vehicle0, picking/dropping92 bikes within its17914.500s
duration; the other two vehicles remain unused. DS-X distributes2/10/18
stations and9/40/70 pickups across three vehicles,119 total pickups, with
lower original F. JI's local duration-density score can favor early low-quantity
visits; once all stations have been visited, its unvisited-only motif space
cannot revise quantities or move existing visits to exploit the unused fleet.
This is a neighborhood limitation, not evidence of infeasibility or a full
exact-runtime ranking. C2 also has a worse initial F. D7 improves but remains
far above the earlier fully verified K1 startup0.2156440753, so protection is
not repaired merely by this constructor's speed.

No formal performance/long/confirmation campaign is opened. Durable native
deadline evidence is still unimplemented and its six-diagnosis reserve unused.
A general mechanism revision, using the constructive route as an additional
seed in the existing finite decoded descent, is considered in seed_extension.md.
The initial constructor/diagnostic files and their identities remain frozen.

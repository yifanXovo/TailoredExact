# Round77: JDS-C does not repair the complete D7 regression

The better physical starter established in R76 does not deliver a better
complete method on the exposed D7 protection role. At the same 1200-second
whole-run cap, JDS-C has a stronger global lower bound than fresh P-GRB but a
worse upper bound and a 44.35% larger absolute gap. This is a material primary
regression under the frozen rule, not a severe primary regression (which
requires more than 50%). The important K1 advantage is still lost.

Base: R76 final cc3bced895bc0f17c25c5bc23b3466e470d9633e / draft PR137.
Branch: codex/round77-jdsc-protection. This negative full-method screen changes
no C++, default or main. publication.json records the independent draft PR.
The overall goal remains unmet.

## Matched complete runs and observed trajectory

All three fresh serial runs return normally and remain uncertified. D7 retains
V50/M4/Q30, regional shortage input, mathematical T18000, handling 60/60 and
lambda .15. Input SHA256 is
d7dbd018331b9d5f3d84c0fd6c907560ef1fa92a2f8c153ac7d81e46a6cd4e9c.
Gurobi 13.0.2, Threads 1, Seed 0, Presolve Auto, zero requested gaps and original
numerical tolerances are common. Owned logical processor 2/mask 4 and restoration
are recorded. Whole wall includes startup, models/calls, persistence and exit.

|Arm|Paid wall s|Physical U|Global L|Absolute gap|Relative gap|
|---|---:|---:|---:|---:|---:|
|P-GRB|1197.093|.277320865934|.197286478715|.080034387219|.288598505|
|JDS-C|1197.094|.318870665861|.203338383594|.115532282266|.362317060|
|K1-R|1197.125|.215644075316|.197357479228|.018286596087|.084799900|

Relative gap is (U-L)/abs(U), with unavailable or zero U handled separately.
JDS-C's U is worse by .041549800 and L better by .006051905, yielding gap
deterioration .035497895. K1 improves P's gap by .061747791 (77.15%). The
unclipped fraction of that advantage retained by JDS-C is -.574885261. This is
an important protection failure without a historical-fastest-point veto.

|Observed time s|P gap|JDS-C gap|K1-R gap|
|---|---:|---:|---:|
|300|.139455121|.128315522|No recorded physical U|
|600|.093231319|.128283178|No recorded physical U|
|900|.081833725|.116872649|.019312551|
|1200|.080034387|.115532282|.018286596|

The 300s JDS-C improvement is below the material 10% threshold. Availability
is the later of payload closure and complete receipt observation. K1's startup
U is first observed at 613.984s and is not backdated. Its native MIP finds no
feasible vector; the current-run verified HGA witness and complete-cover LB
still form a legitimate endpoint. No recorded earlier U does not imply that
no physical solution existed then. No certificate is gained or lost here.

## Mechanism and validity

The exact R76 qualified executable is reused: source
4f6254c2639972ce3ac2b80906ce6d4ebd701f3e, binary SHA256
df1de39a0c74a42633f80a939dcbed4218192ad1466760061b45d73f948451fc.
All source/CMake hashes and inherited 58/58 qualification are checked, without
retesting or charging inherited calls again. P has no new Start, cut or bound.
Its original 35618-row/13360-column canonical compact SHA256 remains
4cd7967ea4d65804e6ab7ae8913033454ba495766ff9eb03529bd935f6e0bace
(fingerprint -373258443). Candidate preset is
research-round76-vds-physical-closure; K1-R is research-round65-k1-h with only
the defined same-run witness/zero-stop reliability repairs.

JDS-C completes the same 25 logical descent paths and two insertions plus five
within-vehicle quantity changes as R76. Its startup F .331621561270 is observed
at 10.407s; all 50 stations are served with 189 pickup/drop units. The closure
trace interval .005081s excludes initial/final snapshots; full startup pays
that overhead. Its one actual native Start passes full-vector, actual-row and
readback checks and is accepted in the native log. All nine closure states
are independently physically replayed. Start acceptance is not a speed claim.

All 11 actual Optimize calls return: P 1, JDS-C 4, K1-R 6. JDS-C performs three
LP calls and one parent MIP, without an extra MIP restart. That MIP has 104726
rows/25943 columns and records 72 nodes, 1201141 simplex iterations and 1168.54
native seconds. P records 2238 nodes, 2030660 iterations and 1196.68 native
seconds. K1 uses five LP calls and one target MIP, recording 239 nodes and
560.12 native MIP seconds after its paid HGA. These rounded per-call diagnostics
do not replace whole wall or original endpoints. Stronger relaxation and
node/model counts alone do not establish a causal efficiency gain; startup
seconds cannot be subtracted to invent an alternative algorithm's performance.

Independent audits pass for 223 physical journal witnesses (221 native and
two startup), 122 global-bound events and all 370 committed events, including
scopes, coverage, settings and normal endpoint gates. K1's startup G .038722674
lies inside its active interval [0,.053911019]. Numerical certificates are
distinct from strict rational proofs; this panel has no certificates.

## Preserved failure, correction, cost and delivery

After JDS-C returned normally, the original Python supervisor supplied a
snapshot with array operations to a CLI-result hash expecting dictionaries.
The TypeError stopped the driver after two solves. Original summary, failed
audit, exit and identities remain unchanged. A separately admitted zero-Optimize
correction reproduces the error, normalizes only the wrapper input, and repeats
physical, scope, coverage, closure and actual Start checks in 2.136539s. No
criterion is weakened. Only the originally allocated, previously unlaunched
K1 command is continued through a separate frozen driver/ledger. No solve reruns.

Full-run wall totals 3591.312s/11 Optimize. Reference export .359s is included
in .558712s preflight. Offline replay totals 2.492311s including the .082978s
failed adapter audit and correction, not counted twice. Joint analysis costs
.487809s, mechanism audit 2.025174s, packaging/verification 9.539400s and a
separate delivery-only check .370994s. Resource records retain one supervisor
exception. No solver failure, new build/test, extra seed or reset credit.
Interactive work is not represented as a complete machine-time census.

Four lossless bundles deliver 834 files: 143719501 raw and 21262717 compressed
bytes. Every member length and SHA256 verifies. Raw logs/models, receipts and
witnesses, closure/Start artifacts and original failed audit are included.
Executable remains local with its hash. reproduce.md records limitations.

## Stage decision and next question

Evidence is credible and the inherited architecture admissible, but JDS-C fails
this protection screen. R74 JDS-X gap .121030952 is historical context, not a
fresh same-build causal comparison against this stage's .115532282. No unchanged
candidate 3600/7200s extension or independent confirmation follows from this.

The prospective design review keeps both representation/organization and
physical assignment open. On observed empty-return routes, a nonzero cross-
vehicle quantity pair would create return loads t and -t, making one negative.
A bounded inventory-preserving balanced-block relocation diagnostic with finite
duration descent is a distinct question. Original compact plus the same paid
cheap starter is also available as a core comparison. Neither is admitted by
this report. Declare a new bounded stage, avoid indefinite local tuning, and
continue toward the original P/K1 goals.

# Round73: one constructive seed improves complete D3 proof and retains D4

The revised JDS-X candidate completes D3's original-problem certification in
138.578s versus259.968s for fresh DS-X, a121.390s/46.69% reduction. Both
candidates also certify D4;52.937s versus57.484s is below the frozen material
threshold. Official P-GRB remains open at the common300s process allowance
on both roles. This closes the stage with a useful full-method result; it
does **not** establish medium/large stability or repair D7's K1 protection
deficit. Continue with the latter question in the next stage.

## Candidate and rationale

`research-round73-vds-joint-seeded-descent` keeps the same VD-S/AM exact proof
and the original24 DS-X random starts, adding one order from a finite joint
route-position/integer-quantity insertion constructor. The constructor
scores improving physical pickup/drop motifs by original objective gain per
added route duration. Its explicit insertion positions and quantities use
actual stock, prefix capacity, depot return handling and original T. The
additional order goes through the same decoder and finite descent; the best
independently verified physical witness remains available even if decoding
is worse. No internal seconds/Work slices, evolution, timed restart, instance
dispatch or historical witness enters this candidate.

Correctness and efficiency are separate. The constructor and descent supply
only physical UB witnesses; they do not certify optimality or remove proof
domains. The unchanged complete MIP/interval-cover proof remains responsible
for lower bounds and certification. Each accepted constructor step adds an
unvisited station, giving a finite step bound, and all retained routes pass
the original verifier. Exhaustive tiny oracles cover integer quantities,
placements, heterogeneous capacity, cumulative pickup>Q, loaded returns,
zero handling/travel, S=0 and deadline behavior. Parameters define a finite
neighborhood and one extra seed, not a renamed runtime allowance.

The design uses BRP's coupling between inventory change, pickup/drop order
and feasible physical route time. It is not a claim that generic insertion,
multistart, relocation, greedy loading, one-hot inventory or MIP Starts are
new theory. Prior BRP routing/loading work is recorded in Round72 literature
notes; its different objectives and route semantics do not justify importing
a fixed-route loading optimality theorem for this normalized-Gini objective.

## Retained revision evidence

The initial standalone JI constructor improved D3/D4/D7 startup values but
lost C2 and especially D6: D6 worsened from0.160027 to0.301950, placing all30
stations on one vehicle. This negative result is retained, not hidden by the
later seed integration. The second fresh five-role tranche keeps the original
24 logical descent trajectories exactly on every pair and searches a25th
seed. It improves initial F on D3/D4/D7 and retains C2/D6 physical witnesses.
D7 improves0.544511 to0.380774 for0.750s additional startup. It still trails
the historical verified K1 startup0.215644 substantially. Read
startup_checkpoint.md, seed_checkpoint.md and seed_revision/pairs.json.

Read-only inspection of the archived D7 JDS-X witness finds17/23/6/0 served
stations on its four vehicles. Two physical horizons are nearly full while
the third has spare time and the fourth is unused. This is a concrete clue,
not proof that a profitable redistribution exists. No subsequent relocation
or quantity mechanism was implemented or tested in this stage.

## Frozen full-method screen

All six fresh runs use v6 source
`4ba09609cf3fb92ef29598dce8201231668324f9`, executable SHA256
`90d7bd2f84744b87958ff19a6e35bed76722cf680964a04ad6331135f5ff9029`.
D3 is the Round39 small-medium V12/M3/Q30 role with T2850; D4 is the
Round39 small-hard V12/M3/Q30 role with T2400. Their full input hashes,
commands and parameters are in formal_small/identity.json. Both are exposed
development instances; this is not independent confirmation.

| Role | Arm | Paid wall s | Original U | Original L | Certificate |
|---|---|---:|---:|---:|---|
| D3 | P-GRB |297.062|0.045054161581|0.041541474117|open|
| D3 | DS-X |259.968|0.045001550056|0.045001550056|yes|
| D3 | JDS-X |138.578|0.045001550056|0.045001550056|yes|
| D4 | P-GRB |297.079|0.506343307565|0.194519315931|open|
| D4 | DS-X |57.484|0.506343307565|0.506343307565|yes|
| D4 | JDS-X |52.937|0.506343307565|0.506343307565|yes|

Gurobi13.0.2, Threads1, Seed0, PresolveAuto, requested relative/absolute
gaps0 and original feasibility/integrality tolerances were read back. The
same owned launcher/child affinity logical2/mask4 was restored after every
run. P remains the original compact model, with fresh v6 canonical/native
fingerprint binding and no external Start, cut or imported bound. All arms
use the same optional observational journal, whose callback, verification,
writing and supervisor-read costs are included. No frequency lock or causal
correction for machine variation is claimed. This is a single paired screen,
not a significance estimate or a timing comparison against historical builds.

The300s allowance covers the entire process, with3s for shutdown and an
owned-child hard-stop guard at298s; every formal run returned normally.
All normal endpoint witnesses, scope/parameter gates and complete cover
checks passed. Very small signed floating-point endpoint differences are
retained in raw JSON (including D3 JDS-X gap about-2.08e-17); none were clipped.
Certificates use the original numerical contract, not strict rational proof.
C2's unchanged startup and D6's retained starter do not prove a new-build
full-method tie; those complete comparisons remain unrun here.

## Native non-return reliability prerequisite

The Round72 baseline non-return motivated a default-off observer that saves
original-model MIPSOL routes and scoped MIP bounds before Optimize returns.
The first native physical witness per call is retained even when it equals
the startup witness; later improvements and any contradictory new witness
are persisted. A bound can strengthen only a matching frozen live leaf;
excluded halves and cutoff complements explicitly cover omitted regions.
Local conflicts are checked before cutoff aggregation. Complete content,
hash receipts and completed observation time govern checkpoint availability.
The observer changes no solver choice or controller state.

Six predeclared <=30s native diagnoses pass, including two actual owned-child
kills after committed native witnesses and bounds. They total65.484s and32
Optimize calls, with32 physical witnesses and215 full-domain bound events.
D6 JDS-X recovery yields U0.160027280604/L0.131389465040 after the forced kill;
it is explicitly interrupted and uncertified. Different forced-stop times
are not performance pairs. The tiny candidate's normal result certifies5/24
although its last MIP produces no usable bound callback; the current recovery
reader conservatively reports analytical0. It does not infer a final native
certificate. See runtime_checkpoint.md for scope and limitations.

## Cost, verification and delivery

All six configure/build/test revisions cost583.930s and360 actual native
fixture calls. v6 passes54/54 tests, including28 new journal checks. Three
failed batches are retained: two initial JI configuration guards and the v5
Windows corrupt-fixture setup. Their costs and logs remain in evidence.

Twenty startup diagnoses cost46.686s/zero Optimize. Six native reliability
diagnoses cost65.484s/32 Optimize. Six full runs cost1103.108s/22 Optimize.
Thus all32 research runs cost1215.278s, and all stages of this round total414
native Optimize calls including qualification. Four build-only references
cost0.327s/zero Optimize. Separate offline replay and archival costs are in
formal_resource_summary.json; the120.075s initial per-file archive and5.387s
bundle conversion are both charged and retained.

The full screen independently checks126 physical witnesses and14533
full-domain bound events, plus16 negative replay cases. Its29614 raw files
are delivered byte-exact in7 deterministic tar.gz bundles,3753642 bytes;
every member has a source-path/length/SHA256 mapping in
formal_small/bundle_manifest.json. The local per-file gzip duplicates are
retained but need not be published. Run
`python scripts/round73_verify_bundles.py` for a no-extraction, zero-Optimize
verification of all submitted members. Earlier startup and reliability
archives and their failed revisions remain separately available.

Stage decision: retain JDS-X as the next candidate because it has a material
complete-proof gain on D3 and retains D4's primary-benchmark advantage.
Keep stable defaults unchanged. Next perform a bounded fresh D7 comparison
against P-GRB, DS-X and K1-R on this qualified build, then use its actual
primal/proof tradeoff to choose further work. Do not claim D7 protection,
medium/large generalization or the overall unified-algorithm goal is achieved.
Draft PR134 is this stage's review artifact; no main merge is authorized.

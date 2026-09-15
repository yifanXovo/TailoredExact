# Round70: finite decoded descent repairs startup, but loses D7 primal quality

The bounded stage is complete. DS is a valid default-off exact candidate,
with useful small-instance and D6 improvements and a material D7 regression
against official P-GRB. The overall research goal is unmet. No independent
confirmation, extra repeat or long extension was opened; all eight roles are
exposed development data. The proposed long/confirmation campaign is deferred.

Baseline is Round69 final b87850c474c8cb9ac45b65f881ebc629bb137f24 / draft
PR130. The accepted revision2 source freeze is86c35aa7fc055e784fecf7eb1a623483c6206dc8;
executable SHA256 is2e841e23cdbc81f71b9373f35b7c82494223a7ecfbb670bcdc33f7ec2b66e6f3.
All measurements used those bytes, Gurobi13.0.2, Threads1, Seed0, PresolveAuto,
requested gaps0 and original numerical standards. Every fresh arm inherited
logical processor2/mask4, with readback and launcher restoration. Historical
default-affinity times are not strictly pooled with these measurements.

## Method and correctness

Preset research-round70-vds-descent replaces full evolutionary startup with
24 uniformly sampled route-separator seeds, seed20260626, followed by finite
first-improvement decoded descent on the existing guided intra-route
neighborhood. The proxy only orders candidates; each unsuccessful pass fully
checks every generated neighbor. A decoded gain greater than1e-12 accepts a
move. No cross-route moves, evolution, constructive initializer, local timer,
Work allocation, iteration fallback or instance switch is enabled.

The best independently verified physical witness feeds the unchanged VD-S
one-hot Gini-product model, AM controller and complete native Start map.
Gurobi remains the full MIP engine. The only time cutoff ends the entire
algorithm; inherited mathematical bound targets retain all proof obligations.
Finite strict descent establishes termination for the declared decode map
and generated neighborhood, not global routing optimality. Original route,
inventory, handling, prefix load and allowed loaded-return semantics are
unchanged. Legal UB and full-domain LB determine numerical certification;
there is no rational certificate or new-theory claim. See algorithm.md and
mathematics.md for the actual rules and parameter meanings.

## Full outcomes and tradeoffs

All UB/LB/gap values, certificates, paid times and frozen practical labels
are in result_tables.md and revision2/runs.csv / pairs.csv. Micros are excluded
from performance pairs. Representative results are:

|Role|DS outcome|P-GRB reference|Other evidence|
|---|---|---|---|
|E7|Certified1.156s|Certified1.282s|VD-S5.610s; startup regression repaired, DS/P below practical threshold|
|S12|Certified2.094s|Certified5.187s|VD-S39.187s; material P improvement and severe startup repair|
|N12|Certified1.453s|Certified3.891s|VD-S3.640s; material improvement on the non-startup recovery role|
|D3,300|Open gap0.001781355|Open0.003475853|VD-S certifies84.187s; DS loses that certificate. K1-R gap0.001160313|
|C2,300|Certified154.297s|Open gap0.058466271|VD-S124.078s; DS retains P protection but is materially slower than VD-S|
|D4,300|Certified53.968s|Open gap0.310143296|VD-S54.219s; difference below practical threshold|
|D6,600|Open gap0.006996067|Open0.012255293|VD-S0.011402924; K1-R0.013742165; material improvement over each|
|D7,600|Open gap0.127888629|Open0.093231319|Material P regression; both full-HGA controls end before exact proof|

D3 versus K1-R is mixed: DS improves UB by0.000052612 but weakens LB by
0.000673654; its gap is larger by0.000621042, below the frozen absolute
material-gap threshold. This tradeoff and the VD-S certificate loss remain
visible without imposing a best-historical-variant veto.

D6 DS ends at U0.15708313110317415/L0.15008706391847396:42.9% less gap
than P and38.6% less than VD-S, primarily from the stronger LB. Its5.511s
startup is paid, compared with319.129s for VD-S and318.508s for K1-R. These
two completed HGA searches have identical best histories, decode counts and
full routes. Their close times do not establish future stability or explain
Round69's earlier timing anomaly. See d6_screen.md for the physical evidence.

D7 is the critical new limitation. DS initially supplies U0.6945633798694341
after2.799s:33 served stations,144 pickups,127 drops and legal return load17.
HGA's retained route serves50 stations with228 pickups/drops and U0.215644075.
DS's full MIP improves to U0.33196578761179407/L0.20407715858329653. Against
P U0.29018624629581247/L0.19695492691463842, the better LB is outweighed by
the worse UB: gap grows0.034657310, or37.2%. Shorter startup alone is insufficient.

Both D7 HGA controls reach the whole-run deadline before proof: VD-S2673
generations/40512 uncached decodes; K1-R2463/37533. Each retains the same
verified U0.21564407531579505 and analytic global LB0. Neither completed
its2000-stagnation search, so their approximately597s costs are censored
searches, not equal-work timing comparisons. DS's smaller gap than these
startup-only results does not demonstrate retention of historical K1 long-run
protection. Every cost and negative endpoint is retained without correction.

## Qualification, failures and cost

Revision1 passed46 CTests but its six CLI micros exposed two DS invalid-
configuration results: the backend startup guard omitted the new mode.
No performance run used that revision. All six micros,21 native calls and
0.766s remain in revision1_failure.json. The backend guard was fixed under
a new freeze, and an actual CLI certificate/Start regression was added.
Revision2 passed47/47 CTests and six fresh original-problem micros. Both tiny
settings have nonzero optimum5/24; micro-zero means zero handling, not zero F.

Revision2's two D7 HGA deadlines additionally triggered the frozen supervisor's
overly narrow requirement for true proof-tree flags. Both solver exits were
valid. A separate audit verifies physical/event-linked routes, nonnegative
objective premises, exact-phase absence and whole-run deadline. Global LB0
covers the entire original domain without an invented tree or certificate;
raw false tree flags stay false. Two supervisor exceptions are retained,
no run was replaced, and only previously unlaunched arms resumed. Six invalid
in-memory variants of this deadline case are rejected. No measured C++,
binary, driver, plan or algorithm parameter changed during performance.

Final revision2 totals:27 performance+6 micro runs,133 Optimize calls,
6797.377s paid process wall, zero solver validity failures. Including all
revision1 attempts gives39 experiments,154 calls and6798.143s, within the
declared27-performance/12-micro and9240s stage maximum. The two CTest batches
consume24 additional native calls and191.134s configure/build/test wall;
20 no-opt P exports cost1.658s. Affinity qualification cost0.066s with no
optimizer call. All algorithm-internal construction, decoding, verification,
model, probe, mapping and exit work is included in paid experiment wall.

Full QA passes97 initial-witness/model checks (38 incompatible Gini intervals),
22 eligible/accepted/full-vector-observed Starts, every started tree's full
coverage, original P fingerprints and all133 actual native version/parameter
checks. Native MIPSOL equality is qualified C++ observer evidence; submitted
and readback vectors/rows are independently replayed, while unretained full
native event vectors cannot be replayed. The final offline model/Start audit
passes cost6.094/4.531s; these are last-pass costs, not cumulative costs of
all earlier QA invocations. Sixteen conservative300/600 checkpoints preserve
signed gaps, do not backdate final witnesses, and do not replace endpoints.
Startup-only300s rows deliberately provide no earlier UB rather than infer it.

The522 compact artifacts total2,190,217 bytes:489 lossless artifacts and33
exact-field result summaries. Hash/source/content checks pass, including all
ten input identities. Large models/logs and both binaries remain local at
manifest paths. Reproduce.md supplies the qualified same-byte replay and
read-only audits; the replay helper was not used for extra experiments.

## Stage decision and continuation

The stage contributes an admissible finite startup, actual small-instance
repairs and D6 improvement, plus evidence that limited intra-route descent
can lose essential primal quality on D7. Keep DS default-off and do not claim
overall acceptance. A separate stage will test uniform finite cross-route
tail relocation, preserving full decode acceptance and exact proof. The
long/confirmation proposal remains deferred; see next_hypothesis.md.
Latest resource read permits ordinary use with12% weekly remaining; no reset
credit was consumed. Continue bounded work after this independent draft PR.

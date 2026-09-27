# Round70 — finite decoded descent before VD-S

Base: completed Round69 PR130, final b87850c474c8cb9ac45b65f881ebc629bb137f24.
Owned branch codex/round70-vds-descent, same owned ExactEBRP-round66 checkout.
The original user checkout remains untouched. No subagents or parallel solvers.

Target: E7/S12's repeated startup losses, while keeping useful non-startup
and medium/large VD-S gains. Round69 confirms D6 long-window improvement
and D7 protection, but full HGA still costs hundreds of seconds on large
roles and dominates the two easy regressions. This stage changes the initial
witness search, not the original objective, exact model, or proof coverage.

Candidate DS is research-round70-vds-descent. Begin with the same24 random
route-separator permutations and seed20260626 as the native VD-S bridge.
Fully decode every initial seed; then run strict decoded-objective descent
on each seed using the existing guided intra-route moves. The proxy only
orders generated candidates. Each unsuccessful pass decodes all generated
neighbors; any strict improvement restarts that seed's neighborhood. Keep
the best independently verified physical witness. No crossover/evolution,
constructive initializer or cross-route switch is added. Finite strict descent
is the stopping rule, with only the complete global deadline or a verified
zero certificate stopping it early. No timed HGA cutoff or renamed iteration
resource quota is introduced. The seed count defines a fixed sampling method;
it is not tuned by instance ID, observed runtime, or historical winner.

The complete VD-S one-hot MIP/AM proof path, default Gurobi search and full
verified-witness Start mapping remain. A weaker seed may widen the proof
domain or change AM decisions, so reduced startup alone is not acceptance.
All initial construction, proxy evaluations, complete/cache decodes, physical
verification, LP/MIP work, mapping, rebuilding and finalization remain paid.
A generated-neighborhood minimum is not a globally optimal route or operation
plan. The general components are established techniques, not novelty claims.

Measurement: bind the owned experiment launcher to logical processor2,
mask4, before launching any complete algorithm. Read-only Round69 topology
reports it in efficiency class1, group0; no performance scan selected the
core. Child processes inherit affinity; record parent and child readback and
keep Threads1/Seed0/PresolveAuto/requested gaps0/original numeric rules.
This is a uniform measurement condition for every arm, not an algorithm gate.
Do not change OS services, priorities or unrelated process affinities. Do not
pool new timings with earlier default-affinity results. Record any remaining
variation without counterfactual corrections. Official P is newly built and
bound, original compact/default/no HGA/no external Start/cut/imported bound.

Bounded plan: at most27 performance launches, six correctness micros,
8880 performance seconds plus180 micro seconds worst case. No additional
long extension, repeat or confirmation is opened. Ten no-opt P reference
exports (eight performance roles plus two micro settings) are separate
qualification costs. This pre-measurement correction also freshly qualifies
both micro fingerprints. Build/CTest and independent audits
run only while no optimizer is active; record attempts and actual costs.

Performance arms P-GRB/VD-S/DS on all eight unchanged roles:

- E7, S12, N12 at120 each (nine launches): startup and non-startup small roles.
- D3 at300 (three launches): protection of the repeated certificate gain.
- C2, D4 at300 each (six launches): V20 short-T surplus and V12 hard protection.
- D6, D7 at600 each (six launches): V30 compact and V50 regional shortage.
- Fresh K1-R at the same caps on D3/D6/D7 only (three additional launches),
  to assess the necessary K1 references under the same new affinity condition.

The two inherited tiny instances micro and micro-zero use the same input
round59_tiny.txt, respectively T5/handling1+1 and T3/handling0+0. Each has
P-GRB/VD-S/DS at30 (six launches). The name micro-zero means zero handling,
not zero objective; expected nonzero optimum is5/24. Separate unit tests
cover verified-zero stopping, heterogeneous vehicle capacity, loaded return,
cache/fresh decode agreement and deadline interruption. Micros are correctness
only and never appear in performance comparisons.

First qualify the implementation/native integration and original-model
fingerprints. Then screen E7/S12/N12/D3 before the medium/large roles. A
correctness failure stops launches. If the short screen supplies no material
startup improvement on either declared startup role, review the hypothesis
before spending the remaining budget; retain all negative results. A single
protection loss is not an automatic K1 veto: examine the end-to-end tradeoff.
Any revision after performance starts gets a new declared identity, plan and
appropriate requalification; frozen results are never silently regenerated.

Use the same predeclared practical thresholds as Round69: both-certified
V<=12 and both under60, material>2s and20%, severe>5s and50%; otherwise
>10s/15% and>30s/50%. Both-open gap changes require>.001 and10% for material,
>.01 and50% for larger effects. UB/LB and certificates stay explicit; no
inconsistent bound clipping, native-final-witness backdating, or statistical
equivalence claim. Count24 seeds as seeds, not HGA generations. Use a separate
descent trace; do not reuse generation-based witness timestamps for DS.

All eight roles are exposed development/protection data, including former
Round69 historical validation now used to steer this revision. This stage is
not independent confirmation or overall acceptance. A promising revision
needs other representative nonzero/proof-hard medium/large confirmation and
informative matched long runs under a separately bounded plan. Finish with a
new draft PR, then continue if the sustained goal is unmet and resources allow.

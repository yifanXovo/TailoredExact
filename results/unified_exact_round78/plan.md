# Round78: balanced-block relocation across a fixed-inventory plateau

Base: published R77 final88e963a1f10cc4ff9f1d3a17950f0a5708f68318 / draft PR138,
freshly verified open/draft/unmerged. Owned branch codex/round78-balanced-block-descent.
Original dirty checkout remains untouched. Overall goal active/unmet.

R77's complete D7 JDS-C gap is44.35% worse than fresh P and loses K1 protection.
R75/R76 strict physical quantity/insertion work did not repair that deficit.
This stage asks a distinct finite-state assignment question before admitting
more full solves. The original-compact/same-starter alternative remains open;
do not indefinitely refine this neighborhood if it lacks meaningful benefit.

On two empty-return routes, a cross-vehicle +t/-t quantity pair gives return
loads t/-t, so none is feasible for nonzero t. An entire contiguous block with
zero signed net load can move between vehicles without changing final inventory.
Source prefixes outside it and both return loads remain unchanged. Target
prefixes and both actual travel/handling durations still require verification.
A block with a negative relative prefix is not feasible on an empty vehicle
merely because its net load is zero. Loaded return remains legal.

Candidate prototype: alternate the existing R76 strict original-F closure
with one best neutral balanced contiguous-block relocation. Neutral moves
preserve exactly the integer inventory vector and strictly decrease the vector
of all route durations sorted descending, under exact lexicographic comparison.
Enumerate every balanced source interval, every other vehicle (including unused)
and every target leg. Choose minimum duration vector, deterministic index tie.
Never ignore an earlier tiny increase through an epsilon comparator. All durations
must be finite; recompute actual route travel in order, without a metric shortcut.
Selected moves undergo the original full verifier and exact inventory equality.
After a neutral move, reopen strict insertion/quantity descent. Finite integer
route/operation states with strict (F,duration-vector) descent prevent cycles;
the only deadline ends the whole diagnostic/candidate, not an internal phase.
Zero F can end before further neutral balancing. No new tuning parameter or
claim of global neighborhood optimality, proof improvement or theoretical novelty.

## Initial bounded allocation, before results

Implement a standalone default-off module and diagnostic harness, directly
linked to the unchanged qualified R76 core library. Do not yet register a new
CLI preset or change existing production paths/CMake. One compile <=60s.
One structural/oracle process <=30s, then two fixed-witness diagnostics in
fixed order D6,D7 <=60s each, all zero Optimize. Inputs are the R76 JDS-C final
startup snapshots, with full frozen input/witness/library/source identities.
These archived witnesses are diagnostic only, never formal algorithm inputs.
Independent offline full physical and balanced-neighbor oracle replay <=60s
per role; retain every accepted neutral and strict transition. Reserve one
additional compile/failed-scope run only for an identified correctness defect;
record failed identities/costs, do not rerun already successful scopes without
new relevant changes. No optimizer, native test batch, full panel, long extension
or independent confirmation is admitted yet. Stop after a validity failure
until the defect is understood. Avoid concurrent heavy work and record all costs.

Structural checks must cover negative relative block prefixes, different Q,
loaded return, source deletion, nonmetric travel, exact T boundary, deterministic
selection and deadline/zero-F behavior. An independent brute force materializer
must compare every balanced placement's feasibility and best duration tuple on
small cases, and replay selected moves/original F on both physical roles.
The diagnostic's full finite descent tests whether neutral assignment changes
unlock meaningful strict F improvement; it does not establish complete-method
performance. All original objective/physical/numerical semantics remain fixed.

If useful, separately declare production integration, native qualification and
a compact informative fresh comparison within this substantive stage. If null,
retain the negative evidence and turn to the core comparison rather than simply
increase neighborhood/candidate/time limits. Review credibility, architecture
and final-goal contribution, then publish an independent draft PR. No main merge.

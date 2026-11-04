# Independent review of upper-only inventory-column discovery

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Decision: **ACCEPT_UPPER_ONLY_RESEARCH_DESIGN_AND_SMALL_INTERFACE_GATE**.
A finite column-discovery diagnostic is warranted if the completed queued
studies still leave a material interval. It does not establish that missing
primal columns are the principal bottleneck, and does not authorize a
change to the current queue, frozen core or production candidate. This
review used only source and one saved metadata snapshot; no Native,
Optimize, enumeration, compilation or heavy-I/O validation was run.

## Evidence motivating the diagnostic

The inspected K35 `near_optimal_zero_pool` checkpoint had two completed
records, 1064 retained columns and interval
`[0.2826236515522649, 0.2874822144241067]`. Its two numerical primals were
qualified, each with six positive lambda columns and true completion slack
approximately `1e-8`. Their beta values were approximately one, and the
qualified restricted-column dual values were about `1.1e-7` below the RMP
objectives. The completed prices returned 14 and 7 new columns, while the
qualified upper moved only slightly.

These observations make positive-lambda support a compact, relevant seed
set. They do not show that pricing uncertainty is the only cause, or that
negative reduced-cost columns must materially lower the RMP objective:
dual degeneracy and marginal compatibility can limit that inference. A
small targeted attempt to improve the upper tests a different part of the
remaining interval without inventing another full-domain lower.

## Safety of the upper and lower identities

Every candidate must be a stock in the same complete inventory domain,
checked by `stock_value` using exact fractions. A stock column need not
individually be a physically routable incumbent: the studied object uses
inventory columns coupled to the complete free routing LP. Such columns
must never be reported as physical routing incumbents.

The inspected producer rebuilds the same actual Q, keeps all inherited
columns, and adds only lambda columns through the already qualified
`Master.add`. Each f coefficient is rounded upward and the existing Gini
margin is retained. It reoptimizes with all original Q variables free.
An improved numerical upper is saved only after `Master.primal` checks
the entire master, lambda mass and negative mass, every station marginal
and the exact true-f completion slack. This retains the inherited
numerical-primal policy, not a rational primal certificate.

The heuristic creates no new lower. Its minimum sampled price is a price
upper, and neither that sample nor absence of a negative local candidate
can replace complete-domain pricing. The restricted-master objective or
dual is likewise not a full-hull lower. The implementation copies the
previous lower and valid support rows unchanged, with Q/scope/source
identity and a prior-result chain for independent final verification.

For an upper-only phase, an optimal LP status is not required to retain a
qualified feasible point. The revised code saves such an upper whenever
there is a solution, updates result.upper/gap, and only then stops on a
nonoptimal status. It does not read unavailable dual prices in that case.
The earlier upper remains available through the prior witness chain if
no qualified improvement is found.

## Neighborhood and complementary columns

The single-stock generator covers each one-station allowed state change
that respects the hard total and every two-station equal-and-opposite
allowed quantity change. This includes both signs and arbitrary allowed
steps, including gapped supports. Scores are floating candidate ordering
and coarse screening only. The top-64 selection per seed, limited seeds,
512-column cap and floating G screen do not prove complete neighborhood
exhaustion. The revised stop name correctly states
`NO_NEW_SELECTED_HEURISTIC_COLUMN_FULL_PRICE_UNDECIDED`.

The complementary exchange is more directly interpretable. Take two
positive-lambda stocks Y,Z and swap their states on one or two stations
to obtain Y',Z'. For every station the before/after multiset is identical.
If both children are legal, removing epsilon from each parent and adding
epsilon to each child, for epsilon no greater than either parent weight,
preserves total lambda mass and every state marginal. Its true completion
change is exactly

`epsilon * (f(Y') + f(Z') - f(Y) - f(Z))`.

A negative value gives a marginal-compatible completion improvement.
Unary potential terms cancel for the pair; filtering each child by its own
reduced-cost sign could discard a useful complementary member. The revised
implementation therefore admits both true-legal children without the
single-column RC filter. A child already in K need not be added again.

This is a completion direction, not an automatic reduction in the full
objective: the original Q may constrain G through other rows. The free
master reoptimization remains necessary. Also, exchanges sharing parent
weights cannot have their predicted gains added as though all were
simultaneously feasible. Each saved pair is an individual direction; the
master chooses a compatible distribution.

The proposed 16 positive-weight seeds, up to 64 ranked exchange pairs,
and at most 128 paired new columns keep this component finite. Its union
with at most 512 single-stock candidates is capped at 640 without slicing
off a member of an accepted pair. Ranking by min(parent weight) times the
floating f-sum change is appropriate as a heuristic; final feasibility
and strict f-sum decrease are checked exactly.

An inexpensive improvement is to screen both children's integer hard
totals before the top-64 pair selection. Otherwise impossible but
apparently attractive crossovers can occupy the finite candidate budget
before the exact filter rejects them. This screen cannot remove a legal
pair. Stopping once the inherited lower and qualified upper reach the
registered interval tolerance would also avoid unnecessary further sweeps.
These are efficiency recommendations, not false-bound defects.

## Concrete source and audit observations

The revised discovery code keeps single negative candidates and paired
candidates distinct in its evidence, then deduplicates their union. The
audit recomputes every single candidate's true f/price and the stated
negative-price test. For pairs it verifies both parents belong to the
pre-add stock prefix, reads their actual positive lambda weights from the
saved LP solution using that phase's insertion order, checks stationwise
multisets, and recomputes all four f values and the strict sum change.
It requires the new-column set to equal the selected singles plus paired
children, less already present columns, and checks count continuity.

The final selected upper is verified separately against actual Q, its
saved stock distribution and the inherited numerical policy. Intermediate
`primal_discovery.csv` rows are producer records; they must not be read as
additional full-price certificates. The new report path correctly keeps
these sweeps out of the full-domain pricing table. Nonoptimal terminal LP
raw and its fee remain evidence even if no discovery sweep was completed.

The small qualifier checks the exact neighborhood generator against full
Cartesian state enumeration, true candidate values, beta zero/positive,
signed costs, zero stock and fixed/gapped supports. It checks crossover
marginal identities and true legal complementary pairs, and requires a
nonzero accepted-pair count. It reuses the existing Master qualification
with explicit source hashes; no redundant full-Master test campaign is
needed for a new legal-column generator.

## Historical and experimental boundary

R75 quantity descent already uses single-station and opposite two-station
quantity moves, and R76 physical closure combines that neighborhood with
physical route improvements. Those are older applications of ordinary
local-search ideas. The present use is inventory-distribution column
generation followed by a free-Q LP, not a new general neighborhood theorem
or a restart of those physical-heuristic studies.

The current price Oracle already reads every stored Native solution, and
zero_pool already inserts all revalidated legal pool columns. There is
no omitted free pool to recover first. Changing pool-search parameters
would be another pricing experiment, not an equivalent bookkeeping fix.
Sparse marginal-preserving pairs provide a more specific diagnostic than
simply enlarging the Native pool.

After the current registered queue closes, the same-source small qualifier
may run serially under the meter. If it passes and the final K35/NC20
intervals remain materially open, the proposed uniform 1200-second offline
discovery windows with 1600-second outer reservations are reasonable
finite probes, subject to remaining budget and final-verification reserve.
Record added columns by family, actual new positive lambda use, qualified
upper movement and full cost. An improved upper establishes useful primal
column coverage; no improvement only establishes failure of this bounded
heuristic search, not optimality or a family-wide negative result.

## Final inspected interface gate

**ACCEPT_FOR_SERIAL_SMALL_DISCOVERY_QUALIFICATION** at these source hashes:

- `round153_primal_pool.py`:
  `ef8190f6b6aa12730d4f6ab82658345fbb44d1358f45cfed363b8b59afa95da5`.
- `round153_audit.py`:
  `6eca73800296fdbbf74a4d01337d1d10b24e140286f63e88a8c9669d591cf202`.
- `round153_reports.py`:
  `11a10d5b68c2fad3cf30ab5f3996fd5611697d9470a9929fb9de7587910d140a`.
- Reused `round153_coupled.py`:
  `7bdb6eb0957f4f9571a0d728ad07e30f055e3a301d0952e7310fc9ce509ee6c9`.

The pair search now applies the integer hard-total test before selecting
the best 64 candidates. The run accepts an explicit positive interval
tolerance and stops at `requested_interval_accuracy` when its inherited
lower and qualified upper meet it. Neither change alters a true domain or
creates a lower. The nonoptimal-solution preservation, selected-heuristic
stop wording and independent pair/single-column audit described above are
present. No false-upper or false-lower path was found in these new blocks.

The appropriate tolerances for the already discussed probes remain the
registered K35 `1e-4` and NC20 `1e-5`, passed as explicit run arguments.
Only if their completed queued results still justify a new probe should
the same-source qualifier and then the corresponding finite windows be
executed, all serially charged. This static gate is not a recorded PASS
from an execution, and does not alter the active followthrough queue.

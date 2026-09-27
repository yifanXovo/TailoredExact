# Next hypothesis: exchange served blocks with equal net load

This is a source-grounded research direction, not an implemented fix or a new
experimental allocation. Finish and publish R82 first; declare the next stage's
bounded qualification, diagnostic and full-run plan before launching it.

## Observed problem and limits of the inference

U6's complete BDS gap is34.3090% worse than P and59.0955% worse than K1-R.
The candidate's L is stronger than both; its U is weaker. Its cheap starter
F .214430471758 is much worse than K1's paid starter .145069572386. The starter
Gini terms .093736757064/.024687494085 differ far more than the unscaled
penalties .804624764624/.802547188676. K1 uses20 more pickup/drop units and
serves all50 stations; BDS serves49. The original BDS startup finishes25 paths,
4 insertion/20 quantity/1 neutral moves with physical and local-exhaustion
checks passing. Its maximum route duration13872.148s is below T18000, so this
particular starter does not use all available route time.

The current decoded cross-route neighborhood only moves selected unused tail
stations around anchors. Physical closure already allows cross-vehicle
quantity edits, so simply claiming that they are missing would be wrong.
R78's neutral operator moves one contiguous zero-net-load served block; it
does not exchange two served blocks. This is a specific missing rearrangement,
not proof that adding it will improve final MIP performance. R74/R77 already
show that better startup F alone can worsen complete performance. U6's new
adverse realization also needs a fresh matched check, not a noise label.

## Why an unbalanced one-way extension cannot help this witness

Let a block's net load be delta=sum(pickup-drop). If source and target both
return with load zero, a one-way transfer changes their return loads to
-delta and +delta. Nonnegativity requires delta=0. U6's final startup has
total pickup=drop=176 and all terminal loads nonnegative, hence every route
returns empty. Merely removing the balanced-block restriction therefore adds
no feasible one-way block transfer at this state. This is a property of this
starting witness; loaded returns remain legal in the original problem.

## Candidate mathematical extension to test

Exchange an ordered contiguous served block A from one vehicle with an ordered
contiguous block B from another, retaining their internal station order and
integer operations, and require delta_A=delta_B. The blocks may have nonzero
net load. Before-block loads are unchanged; after-block loads and terminal
loads are also unchanged by equal net load. For each inserted block, its
minimum/maximum relative prefix plus the recipient's entry load must lie in
that recipient's [0,Q] interval. Check the two actual capacities separately.
Recompute both routes' original travel/handling/loaded-return duration and
require the original T constraint. No station is duplicated and every integer
operation follows its station, so final Y and F are exactly preserved.

Empty blocks can represent the existing balanced relocations, including use
of an unused vehicle; exchanging two nonempty equal-net blocks expands the
declared neighborhood. A possible uniform rule compares all eligible duration
tuples, adopts only a strict decrease of the complete descending sorted tuple,
then re-enters the existing strict insertion/quantity closure. Fully verify
every adoption. Finite route/operation states and strict (F,duration tuple)
descent justify termination of the declared search, not BRP optimality or
faster solution time. Tie rules and implementation details must be frozen in
the next plan, not selected from performance outcomes.

This is a reuse/adaptation of a familiar block-exchange idea, with BRP-specific
net-load and prefix feasibility conditions; no new general neighborhood
theorem or causal speed benefit is claimed. Independently enumerate small
physical fixtures before trusting a fast implementation, including unequal
capacities, nonzero return loads, empty blocks and duration feasibility.

If implemented, use one default-off preset and the same rule on every input.
First determine whether the actual additional exchanges unlock strict original
F improvement. Then assess complete performance with current P/BDS/K1 controls,
including U6 and the established small/large protection roles as declared by
the next resource plan. Do not repair this failure through an instance switch,
internal seconds/Work slicing, seed selection or a best-of algorithm portfolio.
Any revision informed by R82 uses these six roles as development; a later
confirmation must not present them as untouched data for that revision.

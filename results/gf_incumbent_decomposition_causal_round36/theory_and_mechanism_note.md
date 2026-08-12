# Round 36 theory and mechanism note

## Definitions

`U_proof` is the best independently verified feasible objective available to
the exact proof. Only `U_proof` controls improving-solution cutoffs, objective
rows, incumbent pruning, penalty closure, the global upper bound, and the final
certificate. It may decrease after a newly found route plan passes the
original-problem verifier.

`U_anchor` is a launch-frozen value used only for the initial Gini grid and,
in BW-A, split-gain normalization. It is never proof evidence. Round 36 accepts
an anchor configuration only when `U_anchor >= U_proof` within the existing
certificate tolerance.

For `K=4`, let `A=min(U_anchor,G_max)` and define anchor endpoints
`e_j=(j/K)A`, `j=0,...,K`. The actual initial leaves are nonempty
intersections of `[e_j,e_(j+1)]` with the proof-relevant range
`[0,min(U_proof,G_max)]`. Thus an anchor tail that cannot contain a strict
improver is recorded but not solved.

## Proposition 1 — anchor coverage

Assume `P>=0`, `F=G+lambda P`, and `U_anchor>=U_proof`. Every strict improver
satisfies

`G <= F < U_proof <= U_anchor`.

Consequently its Gini value lies in the anchor grid. Intersecting every anchor
cell with the proof-relevant range preserves a gap-free cover of every strict
improver; discarding only the anchor tail above that range is safe.

## Proposition 2 — fixed-anchor incumbent improvement

Hold the anchor endpoints fixed and replace `U_proof` by a smaller independently
verified incumbent. A strict improver of the new incumbent is also inside the
old proof-relevant range and hence inside the same anchor cover. The smaller
incumbent can only strengthen or preserve proof cutoffs and can render
additional covered regions irrelevant. Existing boundaries are not redrawn.

## Proposition 3 — exactness preservation

Using `U_anchor` for geometry or diagnostic normalization does not alter
exactness provided that:

- every proof cutoff and the final certificate use verified `U_proof`;
- every strict improver remains covered;
- child replacement exactly covers its parent;
- no unresolved leaf is silently discarded;
- terminal MIPs retain the validated exact closure rules; and
- final routes and the objective are independently verified in the original
  problem.

Round 36 keeps those conditions. Split normalization changes guidance only;
it neither supplies a lower bound nor closes a leaf. These propositions are
correctness statements, not claims that a larger anchor, smaller proof
incumbent, or either normalization source is faster in wall-clock time.

# C5 exactness argument

The improving Gini range is initially covered by four closed intervals with
the existing endpoint convention. Every split replaces one parent by exactly
two children whose union is the parent and whose interiors do not overlap.
Replacement is atomic: the parent remains relevant until both children and
their inherited bounds are installed.

Every LP bound is accepted only after terminal optimal/infeasible status,
zero-gap parameter round-trip, canonical model fingerprint identity, and
feasibility-consistency gates. A child LP is speculative until the atomic
split. Declining a split leaves the complete parent interval and every parent
feasible solution unchanged.

For a partial parent MIP, only finite `GRB_CB_MIP_OBJBND` values and the final
`ObjBoundC` attribute may strengthen its leaf. These are dual bounds on the
complete interval MIP. Callback termination at a target does not close the
leaf. The parent remains open and its bound contributes through the minimum
over all relevant leaves. When it is later split, both children inherit that
valid parent bound because each child feasible set is a subset of the parent
feasible set.

Native optimality or infeasibility closes exactly the active complete
interval. An overall-deadline interruption leaves the interval open with its
last valid bound. No partial status is treated as closure.

The global lower bound is the minimum valid bound over all relevant,
nonreplaced open leaves. Closed leaves cannot contain a solution improving the
independently verified incumbent. Strict certification additionally requires
root coverage, every atomic replacement check, finite monotone bounds, all
relevant leaves closed, lifecycle symmetry, and independent verification of
the global incumbent. Therefore a strict C5 certificate proves optimality for
the original problem, not merely for a partition or relaxation.

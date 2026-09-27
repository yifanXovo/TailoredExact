# Family A: static single-tree K4

`ST-K4-P-Core` uses the exact four equal-width endpoints of validated external
C6-K4. The four complete quarter-width interval row packs coexist in one
canonical model under four one-hot selectors. It therefore retains K4-local
domains and strengthening while reducing the final integer proof to one native
tree.

The base encoding is flat. The required uniform refinement is a dyadic
hierarchy: two additional binaries choose lower versus upper half, and exact
linking rows make their values equal to the sums of their two quarter
selectors. The four leaf selectors and every Core perspective equation remain
unchanged, so the hierarchy changes search encoding rather than the integer
feasible set.

The optional common-row-factored writer is implemented and audited separately,
but the pre-frozen required Family-A refinement is hierarchical encoding. No
instance outcome, seed, size, elapsed time, Work, or node count participates in
the encoding.

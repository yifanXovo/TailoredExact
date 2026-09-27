# Common-row factoring audit

The transformation is uniform and exact: coefficient-identical rows present in
every segment are emitted once; shared LHS/sense rows with varying RHS use an
exact selector-weighted RHS; residual rows remain conditional. No row choice
depends on an instance or observed outcome.

- Paired-K4 base/refined comparisons: 10/10 complete.
- Terminal-sibling base/refined comparisons: 10/10 complete.
- Every reported strict result is independently re-audited in
  `certificate_audit.csv`; false certificates are zero.

Factoring does not provide a stable search improvement. On the major paired
case it removes 604 indicator rows but increases nonzeros from 341,315 to
342,713 and worsens Work from 4,132.98 to 4,421.22. In the coalesced major case
it reduces nonzeros from 355,422 to 354,588 and Work from 4,023.49 to 3,754.73,
but both variants reach the process cap and fail closed. On the strongest
control both factored variants reduce Work relative to their bases, yet remain
well above C6. Per-instance row, nonzero, Work, and shifted-time effects are in
`common_row_factoring_audit.csv`.

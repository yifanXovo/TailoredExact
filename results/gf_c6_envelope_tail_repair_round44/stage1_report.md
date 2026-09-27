# Round 44 Stage 1 structural atlas

The sealed atlas contains 372 interval decisions from
120 diagnostic-only runs on the frozen
development-10 panel. All profiles were complete and gap-free, every run used
one executable hash (`c6cd3f8c3d0220da87f96c891dc2cbbe493f6cc6e2d7b64b31210b7993e1e7fd`), and no algorithm
candidate result was observed before this freeze.

## Findings

- The corrected `D_R43` remains width-local: its denominator contains current
  interval width, so proportional residual profiles need not decay as the tree
  narrows. This explains the hundreds of rho=0.05 Round 43 splits; rho=0.10
  sharply reduced them by crossing a broad portion of the local-score mass.
- `M_root` retains absolute root-relative mass and therefore decays under
  narrowing. The frozen values are `[0.007, 0.02]`.
- `F` is zero unless genuine disjunction improves on the strengthened envelope
  toward the mathematical next frontier. The frozen grid is
  `[0.5, 0.75]`; `H=F*M_root` uses
  `[0.0004, 0.0009000000000000001]`.
- Frontier-d2 used 148 lookahead LP jobs versus 186 for
  fixed-d2 with active-one, avoiding 38 jobs while
  preserving exact nonuniform coverage. Fixed-d1 remains the secondary causal
  reference.
- Active-one and violated separation are retained. Active-one perturbs fewer
  rows; violated separation tests whether the extra valid rows buy enough proof
  progress. Parent-only and nested scopes must both reach Stage 2 because atlas
  runs do not exercise descendant inheritance.
- At rho_F=0.5 the veto prediction retains all four major-witness initial
  parents (4
  retained) rather than reproducing Round 43 fragmentation. On the strongest
  control it also vetoes the only old split, so exact Stage 2 evidence - not
  the atlas - must decide whether the P-GRB advantage-retention gate survives.
- Fixed-d1 yields F=0 on both principal witnesses. It is therefore a clean
  no-adaptive/overlay reference but cannot distinguish frontier-relevant splits
  there.
- Parent-only scope permits no descendant model reuse for new facets. Nested
  scope validly inherits only source-interval facets to nested descendants and
  may trade model strengthening for row-signature churn; Stage 2 measures it.

The selection freeze is [stage1_selection_freeze.json](stage1_selection_freeze.json).

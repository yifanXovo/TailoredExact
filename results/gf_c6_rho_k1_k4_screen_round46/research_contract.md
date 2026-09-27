
# Round 46 research contract

This is a focused, default-off parameter screen of the original C6 lifecycle.
The only algorithmic factors are `K0 in {1,4}` and
`rho in {0.01,0.12,0.15,0.20,0.50}`. Every split point is the midpoint.

K4 uses the original four-interval C6 cover. K1 uses only
`round40_c6_coarse_start=k1-adaptive`, begins with one complete
strict-improver interval, and then executes the identical C6 child-LP,
native-target, split/retain, requeue, and exact-closure lifecycle.

Gamma-veto, Gamma_sum, D_R43, Round 44 envelope-tail decisions, PMM/FPMM,
rank-1 CGLP cuts, frontier consolidation, verified MIP starts, and every
instance-, size-, time-, Work-, node-, memory-, or hardware-dependent choice
are forbidden. Round 43--45 results are historical context only.

All official comparisons use Gurobi Auto presolve, Seed 0, Threads 1, zero
relative and absolute MIP gaps, HGA-FULL, midpoint, certificate tolerance
1e-7, and an end-to-end process cap no greater than 1800 seconds. Timing and
Work are outcomes only.

The complete 100-row Stage 3 grid is mandatory. Stage 4 and Stage 5 arms are
selected only through the frozen gates. This round is screening and
confirmation, not paper-algorithm validation.

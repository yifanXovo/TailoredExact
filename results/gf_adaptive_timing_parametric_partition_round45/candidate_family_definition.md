# Candidate family definition

Part I uses K4-new (`K0=4`) and K1-new (`K0=1`) with one shared adaptive
timing code path. Every Part I split is the exact midpoint. Frozen references
are P-GRB, C6, fixed-d1 no-adaptive, frontier-d2 no-adaptive, no-envelope
no-adaptive, K1-single, K1-decisive, and Round 43 A(4,2,0.1).

Eligible timing scores reconstruct old C6, corrected D_R43, F, M_root, H, and
the new Gamma_sum residual-mass reduction. Gamma-veto and decisive-Gamma are
the only new thresholded families. A timing candidate is eligible only if it
is exact, produces both split and retain decisions, retains the major harmful
witness, and does not exceed the frozen false-split/severe-regression gates.
No-adaptive is never eligible for adaptive promotion.

After `timing_backbone_freeze.json`, Part II permits exactly three global point
arms: midpoint, PMM, and FPMM. Timing, K0, lookahead, envelope, incumbent,
solver, and certificate contracts are identical. PMM/FPMM solve the direct
continuous parametric LP max-min problem; there is no empirical point pool and
an uncertified parametric point retains the parent rather than falling back.

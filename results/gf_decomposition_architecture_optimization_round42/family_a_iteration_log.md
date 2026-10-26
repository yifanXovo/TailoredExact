# Family A iteration log

## Base: flat ST-K4-P-Core

All 10 development rows completed with one model, one native MIP optimize,
zero false certificates, and no certificate regression. The major witness
ratios were 0.780848 Work and 0.750059 shifted time, but the strongest K4
control regressed to 1.329846 Work and 1.299000 shifted time. Two instances
were catastrophic. The Work geometric mean is infinite because C6 records
zero Work on one easy case while this static arm records positive Work.

Dominant mechanism: the K4 root bound is preserved, but the monolithic integer
search is unstable across regimes; the positive-control regression is not a
model-build or lost-relaxation-strength effect.

## Required refinement: hierarchical selectors

The uniform dyadic hierarchy preserves the same four endpoints and exact
feasible union. It improves the major witness to 0.426242 Work and 0.409840
shifted time, but worsens the strongest control to 1.570105 and 1.570243. It
also has two catastrophic rows. Family A is rejected. No optional second
refinement is justified because the required refinement gives no stable
general signal.

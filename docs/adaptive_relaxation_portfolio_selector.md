# Adaptive Relaxation Portfolio Selector

Date: 2026-06-28

This round adds an interval-level selector for the lower-bound relaxation
portfolio.  The selector is available through:

```text
--relaxation-portfolio-mode fixed|adaptive|race
--relaxation-portfolio-probe-seconds <seconds>
--relaxation-portfolio-max-variants <int>
--relaxation-portfolio-min-improvement <value>
--relaxation-portfolio-keep-best-bound true|false
```

The implementation can try the baseline relaxation, compact-flow LP,
compact-flow mip-light, and connectivity/domain-strengthened candidates.  It
stores the chosen valid bound in the interval ledger and never uses timed-out
or incompatible artifacts as certificate evidence.

## Certificate Rule

Each variant is a relaxation containing every original route-load solution for
the interval.  The selector only takes the maximum lower bound among valid
variant solves.  Therefore selection cannot invalidate an original-problem
certificate.  If no variant proves the interval cutoff, the interval remains
unresolved.

## Round Finding

The current selector is not yet a paper-core default improvement.  The V20/M3
adaptive rows in `results/paper_candidate_relaxation_round/` show that short
probes and mixed connectivity/service/domain flags can be worse than the best
previous hand-picked LP or mip-light variant.  The selector is retained as an
experimental audit option; canonical `paper-bpc-core` is not changed.

The strongest previous V20 evidence remains:

- compact-flow `mip-light` helps the two high-imbalance rows and
  `tight_T_seed3101`;
- compact-flow LP remains better on moderate rows and `tight_T_seed3102`;
- the adaptive selector needs a better interval-budget policy before broad
  benchmark use.


# Scientific problem statement

External K4 decomposition has two opposing effects: quarter-width Gini ranges
strengthen the interval-local formulation, while independent terminal MIP jobs
fragment proof search. Round 41 showed that a static segmented Core model is
exact and feasible at K2, but changed both granularity and proof architecture.

Round 42 holds the validated K4 interval endpoints, HGA-FULL incumbent, rho,
presolve, seed, thread count, and certificate contract fixed while testing
three bounded architectures: one static K4 proof tree, two adjacent K4-pair
blocks, and C6 terminal sibling coalescing. The objective is either a unified
candidate that passes development, validation, and sealed holdout gates, or a
bounded systematic negative result after every feasible family and its
required uniform refinement is completed.

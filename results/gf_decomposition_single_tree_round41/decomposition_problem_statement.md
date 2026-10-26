# Decomposition problem statement

Current C6 obtains useful lower bounds by intersecting the compact formulation with narrow Gini intervals and adding interval-local rows. The external scheduler preserves exact coverage and certification, but a terminal interval is solved in an independent Gurobi model. On the Round 40 major regression, the resulting independent terminal trees repeat integer search. Conversely, a single coarse K1 model avoids fragmentation but is much weaker on the strongest K4 control. Existing parent/child LP-gain signals do not safely identify the regime.

Round 41 asks whether the two properties can coexist:

- retain interval-local domains and strengthening; and
- give Gurobi one static MIP and one native branch-and-bound tree.

The candidate encodes the midpoint disjunction inside the model. For the strict-improver range `[gamma_L,gamma_U]`, `tau=(gamma_L+gamma_U)/2` and the two closed intervals `[gamma_L,tau]` and `[tau,gamma_U]` exactly cover the range. Segment selectors choose one interval at an integer solution. The selector/indicator baseline tests technical feasibility; perspective product variables test whether important bilinear strength can survive the LP relaxation; one fixed Extended pack tests selected copies of `S`, `P`, and `H`.

This is not a claim that a static disjunctive formulation has the external disjunctive hull. Native indicators, partial perspective rows, and shared original variables can have a weaker continuous relaxation than independently optimizing both interval models. Root bounds, fractionality, ambiguity, model growth, and exact MIP effort are therefore separate outcomes.

The candidate is credible only if it handles both opposing mechanisms under the frozen Gate C: reduce fragmentation on the named medium witness and avoid coarse-MIP weakness on the named hard K4 control. Failure of either witness retains C6 unchanged and blocks K4 expansion and held-out validation.

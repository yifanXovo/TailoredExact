# First targeted deepening: N-B35 scalar value versus coupled degeneracy

The initial complete RMP has a one-stock feasible solution with objective
0.3960465589566612, including a 1e-8 true-completion margin. Its stock has
true inventory objective 0.3960465489566613 (binary64 coefficients evaluated
as Fractions). This is a complete free routing-LP upper witness, not a BRP
physical incumbent. The strengthened reference lower is 0.3929789535186394.

The unrestricted master duals repeatedly return beta approximately 1 with
large full-domain reduced-cost violations. Adding negative-price columns
leaves the same one-stock RMP objective. For example, iteration 3 has
D_K=.3960465489566576 but pricing [-.37678312760631094,-.17472927734050697]
against a=.3709951387430439, requiring correction .7477782663493543.
The bottleneck is therefore a poor/degenerate extending dual and hard
directional pricing, not absence of a useful complete upper witness.

An adaptive checkpoint was recorded and the owned diagnostic process ended
after saving completed iterations. The pending call is explicitly interrupted
and supplies no new bound; all 305.144343100 seconds are charged. This is
not a scientific stopping point. It avoids treating the initial 3000-second
checkpoint as compulsory spending and redirects effort at the identified
structure.

The next test is full-domain zero-potential phi pricing with the necessary
old NC1/NC2/TS strengthening in the normalized integer relaxation. Since Q
contains AP, a sufficiently strong global phi lower, with AP's tiny actual
coefficient transport accounted for, can meet the existing complete RMP upper.
This would determine the value of the entire coupled hull without solving
many arbitrary extending dual directions. A 600-second offline price cap is
allocated initially. If the interval remains important and wide, inspect
bound/incumbent gaps and deepen the unresolved mechanism rather than declare
the family ineffective. Other roles remain necessary structural controls.

The mathematical relation does not turn a stock incumbent into a lower bound,
does not remove Q's route/load/time/cutoff constraints, and does not import
offline floors into a production candidate. A production choice still needs
its own deterministic rule, current-domain construction and complete costs.

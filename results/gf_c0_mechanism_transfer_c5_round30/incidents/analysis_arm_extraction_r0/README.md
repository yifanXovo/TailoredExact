# Post-official analyzer incident: arm-aware bound extraction

The first frozen-analyzer pass completed after all 78 official processes.
It incorrectly preferred dormant zero-valued external-tree serialization
fields for P-GRB and S0-CPLEX instead of those arms' valid native
`lower_bound` and `upper_bound` fields.

The solver outputs, frozen C5 algorithm, executable hashes, official commands,
and all official rows were unaffected. This directory retains the complete
first-pass derived comparison evidence and analyzer log.

The general analysis-only correction selects external-tree bound fields for
C0/C3/C4/C5 and native original-problem bound fields for P-GRB/S0-CPLEX. A
regression fixture covers both cases. No official process was rerun and no C5
parameter, event rule, split rule, or callback semantic changed.

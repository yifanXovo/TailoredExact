# C4 incremental reoptimization

C4 retains one Gurobi model object for a leaf after its complete LP event. The
backend captures the canonical model's original variable types before making
the LP relaxation continuous. After the LP evidence is read, every original
type is restored and the model is updated. If the leaf is retained for an
exact parent MIP, that same model object is optimized again. If the leaf is
split, fathomed, empty, or only a rejected speculative child, the model is
explicitly released.

This mechanism proves only same-leaf model-object retention:

- no disk reread is needed for the terminal parent MIP;
- no parent is mutated in a way visible to a sibling;
- child models remain independent;
- canonical artifact hashes and row signatures remain audit evidence;
- model creation/free symmetry is required.

It does **not** claim LP basis reuse. Changing variable types is a
domain transition, and Round 29 submits no `VBasis`, `CBasis`, `PStart`, or
`DStart`. Basis available/mapped/submitted/accepted/rejected counts therefore
remain zero and the audit status is
`not_submitted_domain_transition_model_object_only`.

It does **not** claim native cuts, pseudocosts, a node queue, or a native
Gurobi tree is shared. No MIP start is submitted. Any incidental solver
internal state is not used as a mathematical bound or closure reason.

The retained pre-freeze Moderate4301 comparison used the same executable and
mathematical `paper-lp-event` strategy on the cold arm. All 54 common LP
terminal statuses/objectives matched within `1e-7`, all 49 common split
decisions matched exactly, and all 24 common terminal-MIP native statuses and
canonical model hashes matched. These are model-object lifecycle checks, not
evidence of basis or native-tree continuation.

# Round 38 candidate definitions

## Protected reference

`C6-HGA-FULL`, `K=4`, `rho=0.01`, proof normalization, Round 36 causal
arm off, Round 37 geometry off, single-threaded Gurobi seed 0.  This remains
the default and validated mainline.

## G2-A: pilot next-frontier completion

The explicit experimental option is:

```text
--round38-c6-frontier-policy pilot-next-frontier-complete
```

After every initial cell has a complete LP disposition, G2-A selects a cell
only when the open-bound minimum is unique and a next strict open-leaf
frontier `t` exists.  It evaluates the two complete midpoint child LPs and
sets `b+` to their minimum, treating a valid infeasible child as `+infinity`.
The parent is atomically replaced by the two children only when `b+ >= t`
within the existing certificate tolerance.  Otherwise both speculative child
states are discarded and the unchanged C6 native target resumes on the parent
at `t`.

The decision receives only complete LP dispositions, lower bounds, Gini
intervals, the verified cutoff, and the existing correctness tolerance.  It
does not receive IDs as semantic categories, V/M, scenario, seed, elapsed
time, Work, nodes, hardware state, or historical outcomes.  Structural leaf
ordering resolves only exact representation ties.

## G2-B: global-vector candidate selection

Not implemented.  Prior forensics and all G2-A experiments produced zero
next-frontier-completing midpoint refinements.  Enumerating more speculative
partitions would add pilot overhead without evidence that an online global
vector rule can produce an accepted lift.  The frozen fallback condition was
therefore not met.

## G2-C: bottleneck persistence

Diagnostic only.  Because every evaluated G2-A midpoint was rejected before
tree insertion, it created no live refined descendants: descendant
controlling time and terminal-descendant participation are not applicable.
The observed mechanism is instead a rejected-lookahead perturbation followed
by a C6 target on the unchanged parent at the next frontier.  Downstream
target, requeue, split, closure, trajectory, AUC, Work, node, and time fields
are recorded as outcomes, never decision inputs.

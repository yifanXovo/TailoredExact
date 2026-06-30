# Recursive Oracle Leaf Partitioning

Automatic interval closure now supports recursive splitting:

```text
--auto-interval-oracle-recursive-split true
--auto-interval-oracle-child-split-count <N>
--auto-interval-oracle-max-depth <N>
--auto-interval-oracle-min-width <double>
--auto-interval-oracle-max-children-total <N>
```

When a final frontier leaf times out in the exact interval oracle, the solver
can split that Gini band into child intervals. A parent is marked closed only
if every child closes by a valid basis. Partial child closure is diagnostic and
does not certify the parent.

Merge safety rules:

- no gaps or overlaps in the child partition;
- same instance hash, lambda, T, incumbent cutoff, and sealed-run settings;
- inherited lower bounds are preserved but do not close a leaf unless they are
  valid for the child interval;
- timeout children remain unresolved.

The partition trace for this round is:

```text
results/oracle_closure_round/leaf_partition_tree.csv
```

On `moderate_seed3301_oracle_deep`, recursive splitting reached depth 3 and
attempted 14 child oracle solves. Some children closed, but not all children of
the two remaining root leaves closed, so the full row remains noncertified.

# Paper-Strict Algorithm Audit

This audit covers the current paper-facing exact line:

```text
paper-gf-tailored-bc
= Gini-frontier decomposition
+ valid interval relaxation/frontier bounds
+ CPLEX-managed tailored fixed-interval branch-and-cut
+ optional paper-safe S-domain refinement
+ audited full-frontier / bucket ledger aggregation
```

The algorithm identity is unchanged. CPLEX is the internal LP/MIP proof engine
for fixed-interval Tailored-BC subproblems; plain CPLEX benchmark rows are not
paper-core evidence.

## Exactness Logic

Every Gini parent interval can be closed only by one of the following:

- a valid relaxation/frontier lower bound;
- an exact fixed-interval Tailored-BC proof on the original fixed interval;
- complete child coverage, such as an audited S-bucket ledger whose children
  exactly cover the parent domain and whose leaves are all closed by valid
  evidence;
- empty or out-of-range proof.

An S-bucket parent closes only when adjacent buckets exactly cover the parent
`S=sum_i r_i` domain, no child lies outside the parent, and every child is
closed/fathomed by valid evidence. Checkpoints, wrapper JSONs, diagnostic
S-buckets, and fixed-interval probes are useful diagnostics but do not close
parents unless accepted by the audited merge rules.

BPC, route-mask enumeration, archive scanning, known-UB injection, external
incumbent JSON, focus-only rows, heuristic rows, and plain CPLEX benchmarks are
excluded from the paper-gf-tailored-bc ledger.

## Active Mechanism Ledger

The machine-readable ledger is written to:

```text
results/gf_tailored_bc_dominant_s_bucket_round/paper_strict_algorithm_audit.csv
```

It lists each active paper-core mechanism, formula, implementation location,
proof source, audit script, and whether the mechanism is paper-safe,
conditionally valid, or diagnostic-only.

The current paper-safe mechanisms include direct Gini interval rows, objective
cutoff rows, S-bucket rows, bucket-tight `S*P` McCormick rows, bucket-tight
objective estimators, local centering, local q-centering, subset cross-H
centering, Gini subset-envelope cuts, variable-S centering, transfer cutsets,
compatible-source transfer cuts, required external-source cuts, subset
inventory movement bounds, and bucket ratio-domain tightening.

## No Special-Casing Policy

The implementation audit scans `src/` and `include/` for instance-name checks,
seed-specific logic, known-UB/archive imports, route-mask certificate paths,
BPC certificate sources, and plain CPLEX ledger imports. Experiment runner
target lists may mention instances because they define benchmark selection, not
algorithm behavior.

The audit script is:

```text
scripts/audit_paper_strict_algorithm.py
```

It fails if forbidden implementation-code patterns are detected.

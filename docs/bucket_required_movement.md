# Bucket Required Movement and Visit Cuts

This note documents required movement cuts derived from bucket-local integer
final-inventory bounds.

The compact model convention is

```text
Y_i + sum_k p[k,i] - sum_k d[k,i] = initial_i.
```

Thus a bucket-tight lower final inventory bound `Y_i^L > initial_i` implies a
required net delivery

```text
sum_k d[k,i] - sum_k p[k,i] >= Y_i^L - initial_i.
```

A bucket-tight upper final inventory bound `Y_i^U < initial_i` implies a
required net pickup/loss

```text
sum_k p[k,i] - sum_k d[k,i] >= initial_i - Y_i^U.
```

Either condition also implies that station `i` must be visited:

```text
sum_k z[k,i] >= 1.
```

For small station subsets `A`, summing the same inventory balance equations
gives the subset forms

```text
sum_k sum_{i in A} d[k,i] - sum_k sum_{i in A} p[k,i]
  >= sum_{i in A} Y_i^L - sum_{i in A} initial_i

sum_k sum_{i in A} p[k,i] - sum_k sum_{i in A} d[k,i]
  >= sum_{i in A} initial_i - sum_{i in A} Y_i^U.
```

The paper-safe implementation keeps subset size at most three and only enables
these rows when bucket integer inventory tightening is active under an enforced
paper-safe S bucket.

The implementation reports:

```text
bucket_required_movement_rows_added
bucket_required_visit_rows_added
bucket_subset_required_movement_rows_added
bucket_required_movement_violations
bucket_required_movement_max_violation
bucket_required_movement_proof_status
```

and is audited by `scripts/audit_bucket_required_movement.py`.

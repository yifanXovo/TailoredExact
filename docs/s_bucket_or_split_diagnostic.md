# S-Bucket Or Split Ledger

See [Diagnostic vs Paper-Safe Cuts](diagnostic_vs_paper_safe_cuts.md) for the evidence categories.

An S-bucket child model enforces `S_b_L <= sum_i r_i <= S_b_U`. This is a conditional fixed-interval subproblem. The child may use bucket-tight denominator rows and bucket-tight `S*P` McCormick envelopes.

A parent Gini interval is closed by an S-domain bucket ledger only when:

- `S_0 = parent_S_L` and `S_K = parent_S_U`;
- adjacent buckets touch within the recorded tolerance;
- no bucket lies outside the parent S-domain;
- every bucket has the same parent gamma interval;
- every bucket is closed, empty, or fathomed by valid evidence;
- no diagnostic-only row, checkpoint-only bound, plain CPLEX benchmark, BPC result, archive incumbent, or known-UB source enters the merge.

Diagnostic S-bucket rows remain useful development evidence, but they are not paper-core evidence unless the merge audit accepts the full parent ledger.

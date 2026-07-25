# C6 incremental reoptimization boundary

C6 retains the same in-memory Gurobi model object for a leaf across its
complete LP, native target, and exact closure phases. The backend records
model fingerprints, row signatures, model/free symmetry, domain restoration,
and optimize counts.

The implementation claims only same-object retention:

- no native branch-and-bound tree continuation claim;
- no LP basis transfer or simplex reoptimization claim;
- no warm start;
- no model reset call;
- no cross-child model reuse;
- no use of retained state as mathematical evidence.

Before an integer phase, the captured original variable domains are restored
and checked. Every mathematical decision uses complete LP status or a valid
native bound, so solver-internal reuse may affect effort but not correctness.

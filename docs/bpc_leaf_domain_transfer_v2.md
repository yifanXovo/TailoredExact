# BPC Leaf Domain Transfer V2

The paper-core BPC path must solve the same fixed Gini leaf that relaxation
screening failed to close.  The validation harness records whether the leaf
data passed to BPC matches the final frontier ledger.

Domain information that is relevant to BPC:

- `gamma_L` and `gamma_U`;
- incumbent cutoff;
- inherited relaxation lower bound;
- tightened final-inventory domains when available;
- required movement and service-operation constraints;
- singleton duration/transfer incompatibilities;
- Gini spread and interval cuts when active.

This round focuses first on auditing that the gamma range and cutoff are passed
correctly.  Additional domain transfer improvements are reported through the
BPC pricing counters:

- labels pruned by station feasibility;
- labels pruned by support or duration feasibility;
- labels pruned by reduced-cost completion bound;
- RMP rows and cuts added.

If BPC still fails after correct leaf transfer, the remaining bottleneck is in
pricing enumeration, RMP bound strength, cut separation, or branching rather
than a stale or mismatched interval.

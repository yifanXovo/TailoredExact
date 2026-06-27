# V20 Cover Cut Activity Audit

Date: 2026-06-28

The V20 multi-station cover cuts remain certificate-safe but mostly inactive on
the current hard stress suite.

The cut is:

```text
if travel_lb(S) > T_k then sum_{i in S} y[k,i] <= |S|-1
```

where `travel_lb(S)` is MST plus depot connection lower bound.  The
implementation uses zero minimum handling by default for certificate safety,
unless a separate service-operation lower-bound flag is explicitly enabled.

Round output:

```text
results/paper_candidate_relaxation_round/cover_cut_activity.csv
```

The audit shows no material V20 closure improvement from these cuts.  This
means the current stress gap is not explained by small infeasible service-set
covers; compact-flow variant choice remains the dominant relaxation lever.


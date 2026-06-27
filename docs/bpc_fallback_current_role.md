# BPC Fallback Current Role

Date: 2026-06-28

BPC fallback remains diagnostic.  Previous V12 M1 fallback launched one node and
one pricing call but reported a weaker final lower bound because it displaced
relaxation time.  V20 fallback rows remained relaxation dominated and did not
improve interval lower bounds.

Certificate rule: a BPC tree lower bound is usable only when exact pricing is
closed for every node contributing certificate evidence.  Incomplete fallback
pricing leaves the interval unresolved.

Round summary:

```text
results/paper_candidate_relaxation_round/bpc_fallback_retest.csv
```

Recommendation: keep fallback off by default.  Retest only after relaxation
portfolio selection produces a smaller set of controlling intervals.

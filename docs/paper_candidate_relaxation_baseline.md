# Paper-Candidate Relaxation Baseline

Date: 2026-06-28

Baseline table:

```text
results/paper_candidate_relaxation_round/baseline_best_by_instance.csv
```

The table fixes two integrity issues before comparing this round:

- instance names are explicit in every new CSV row;
- V20/M3 hard stress rows are labelled `hard_generated_v20_m3`, not historical
  paper targets.

## Previous Best Evidence

V12 M1 has a 300s noncertified row with LB `0.332675660948` and a certified
600s row around 481s.  V12 M2 has a canonical certified objective
`0.718504070755`.  For V20/M3, the previous best rows are fixed LP or
compact-flow mip-light variants, not adaptive selector rows.

The baseline is used only for comparison.  It is not imported as certificate
evidence into new runs.


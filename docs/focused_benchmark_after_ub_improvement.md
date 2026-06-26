# Focused Benchmark After UB Improvement

This round intentionally avoids a comprehensive benchmark matrix. The goal is
to test whether the strengthened paper-reproducible primal heuristic is enough
to recover relaxation-only certificates on regenerated V12 M1/M2 and improve
the existing generated-variant baseline.

## Commands

All focused commands are saved under:

- `results/primal_ub_improvement_round/logs/*.command.txt`;
- `results/generated_variant_round2/logs/*.command.txt`.

All route-bearing heuristic outputs are verifier-gated and saved under:

- `results/primal_ub_improvement_round/incumbents/`;
- `results/generated_variant_round2/incumbents/`.

## Headline V12 Results

Current regenerated V12 results with the improved reproducible heuristic:

- V12 M2 300s paper-core: noncertified, UB `0.745475`;
- V12 M1 300s paper-core: noncertified, UB `0.366800`;
- V12 M2 explicit incumbent JSON 300s: same UB and noncertified;
- V12 M1 explicit incumbent JSON 300s: same UB and noncertified;
- V12 M2 diagnostic archive 300s: certified, UB/LB/objective
  `0.719065249476`.

The diagnostic archive row is not a paper-core default and is used only to
show the UB quality threshold.

## Generated Variants

The generated variant rerun uses ten existing engineering variants:

- three V12 M1 variants;
- three V12 M2 variants;
- two V10 M2 variants;
- two V8 M2 variants.

The summary is written to
`results/generated_variant_round2/summary.csv` after all raw rows are audited.

## Interpretation

The improved heuristic provides a reproducible UB and improves V12 M2 relative
to the previous paper heuristic, but it is not yet close enough to the known
diagnostic archive incumbent. The next step should be another targeted
heuristic round focused on migrating the full compact TGBC decoder and guided
education from HybridGA.

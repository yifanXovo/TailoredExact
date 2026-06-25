# Generated Variant Benchmark Report

## Setup

Round data are under:

```text
results/generated_variant_round/
```

Twelve capacity/inventory variants were generated from V8, V10, V12 M1, and
V12 M2 regenerated engineering bases. Each variant received a verifier-gated
heuristic incumbent export. The first ten variants were run with
`paper-bpc-core` for 60 seconds using the exported incumbent as an explicit
paper-reproducible input.

## Summary

See:

- `results/generated_variant_round/summary.csv`;
- `results/generated_variant_round/variant_performance_by_base.csv`;
- `results/generated_variant_round/certificate_audit.csv`.

The generated rows produced five certified paper-core results in the 60-second
subset: three V10 M2 variants, one V8 M2 variant, and one V12 M2 variant. The
remaining V12 variants were noncertified and report positive gaps with
unresolved intervals. All optimal claims passed `audit_bpc_certificate.py
--fail-on-error`.

## Interpretation

The relaxation-only certificate path is strong on several regenerated V8/V10
and some V12 cases, but it remains sensitive to incumbent quality and
capacity/inventory distribution. The noncertified rows are still useful
engineering evidence because they identify intervals that fail cutoff-fathoming
within the short 60-second budget.

## CPLEX

A V4 CPLEX/compact availability probe succeeded. Full CPLEX rows for every
generated variant were not run in this pass to keep the matrix bounded.

# Stable-mainline assessment

## Decision

Corrected S0/F0 remains the stable paper mainline. The necessary general
correctness correction is part of that implementation: continuous generic
callback branching requires presolve, Reduce, and Linear all off with exact
set/get readbacks, and native local Gini intervals may contract but never
expand relative to inherited metadata.

P2 is valid and safe but remains research-only. It preserved both strict
certificates and caused no correctness failure, yet the preregistered six-pair
hierarchy classified only 2 improvements against 4 regressions. It therefore
fails decision D's requirement of more improvements than regressions and is
not eligible for a full-matrix promotion round in its current form.

## Targeted evidence

| Instance | Decision | Primary basis |
|---|---|---|
| V12_M1 | regress | both strict; P2 was 1.31 s (0.42%) slower |
| V12_M2 | regress | both strict; P2 was 17.61 s (2.28%) slower |
| high_imbalance_seed3202 | regress | final LB lower by 0.00000808 |
| high_imbalance_seed4201 | improve | final LB higher by 0.00022723 |
| tight_T_seed3101 | improve | final LB higher by 0.00093120 |
| moderate_seed4302 | regress | final LB lower by 0.00047405 |

There were no certificate gains, certificate losses, or preregistered material
regressions. The absence of a material regression is not sufficient for
promotion because overall pair direction is unfavorable. Estimate reach was
also sparse: 0, 1, 0, 0, 7, and 68 discriminated pairs respectively. On the
last instance, high discrimination coincided with worse final LB and AUC,
showing that a valid ordering signal is not automatically a useful one.

## Next scientific experiment

Run a preregistered corrected-S0/F0 full-matrix revalidation with the mechanism
off. This replaces potentially affected presolve-on historical certificates
with current safe evidence and establishes the reference matrix required
before another child-estimate mechanism is considered. P2 should not receive
a promotion-scale run without a new proof-strength/ordering rationale that
addresses the moderate_seed4302 regression.

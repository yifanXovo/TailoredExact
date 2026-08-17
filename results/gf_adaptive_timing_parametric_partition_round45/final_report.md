# Round 45 final report

## Decision

- Timing: **validated_adaptive_timing** — gamma-veto, rho_gamma=0.012.
- Point: **midpoint_not_improved** — PMM/FPMM remain audited research arms.
- Algorithm: **validated_k4_adaptive_midpoint** on the small material protocol.
- Scale: **complex_mixed**; neither V20 nor V50 support is claimed.

## Answers to the 26 questions

1. Beneficial recursive-split leaves: yes, 1 confirmed in 8 matched pairs.
2. Harmful leaves: yes, 1; 6 were neutral.
3. Gamma-veto and corrected D_R43 best distinguished them; old C6 over-split.
4. D_R43 remains selective but had one false split and one false retain.
5. Veto-F degenerated to always-retain on the matched set.
6. Gamma_sum improved timing when combined with the old-C6 veto.
7. Corrected D_R43 and gamma-veto tied at mean regret 1.01267; gamma-veto had
   zero false splits and was selected.
8. Yes: gamma-veto produced both actions in frozen small and complex atlases.
9. Yes: the major witness certified in 624.0 s/1353.2 Work versus P-GRB's
   1007.3 s historical classification reference and C6's 1911.5 s comparison.
10. Partly on small; the strong control remained 63x faster than P-GRB, but
    full complex C6-advantage retention is unproven.
11. No: K1 was 2.2x slower than K4 on the strong control.
12. Mainly removal of recursive splits, with a secondary envelope contribution.
13. Frontier-d2 improved the major witness and was neutral on the control.
14. Yes via the permitted deterministic monotone-root fallback; basis
    sensitivity was unit-tested but not exposed by the live shared builder.
15. Basis breakpoints found live: 0; deterministic root query rows: 32.
16. PMM differed from midpoint on 2/2 activated point rows.
17. PMM improved Work on 1/2, but neither activated split beat retain.
18. No; FPMM was identical to PMM on both rows.
19. Not reliably: stronger weak-child LP points did not uniformly reduce proof
    cost.
20. No global K4 improvement; one Work win and one loss plus overhead.
21. No; it did not make K1 viable.
22. V20 is mixed: the targeted development pair capped, while both confirmation
    arms certified. Gamma-veto substantially reduced the 300 s gap integral
    (0.097 vs 0.780 development; 0.080 vs 0.539 confirmation), but two pairs do
    not qualify the frozen panel.
23. V50 atlases are structurally valid and selective. Both targeted pairs capped
    at 300 s; gamma-veto reduced the gap integral (0.232 vs 0.842 development;
    0.695 vs 0.940 confirmation), but no scalability claim is made.
24. Small development/validation/holdout results are strict certificates;
    complex atlas rows are structural and targeted unfinished rows are capped.
25. Recommend K4 gamma-veto/rho=0.012/midpoint only for the validated small
    material scope; keep C6 as the broad validated mainline.
26. Unproven: full-panel 3600 s complex superiority, V50 scalability, a
    parametric point benefit, and a viable K1 unified framework.

## Gates

Validation material Work/time geometric means were 0.892148/
0.883008; holdout material means were 0.391771/
0.435608. All 19 reported
small candidate rows were strict certificates with zero false certificates and
zero severe P-GRB regressions.

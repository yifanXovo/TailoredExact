# Round 43 final report

## Terminal outcome

**bounded_systematic_negative_result**. No new algorithm is promoted. C6-HGA-FULL remains
unchanged at K0=4, rho=0.01, Gurobi Presolve Auto, Seed 0, one thread, and zero
gaps. All Round 43 mechanisms remain explicit and default-off.

The selected global development candidates were A(1,2,0.1) and A(4,2,0.1), both
with the single-pass affine envelope, D_d score, no lifted cuts, and no frontier
consolidation. Neither passed every frozen development gate.

## Decisive witnesses

| Candidate | Major Work | Major/P-GRB | Control Work | Control/C6 | Control shifted time/C6 | Development |
|---|---|---|---|---|---|---|
| A(1,2,0.1) | 1545.849 | 0.986 | 230.938 | 1.727 | 1.908 | fail |
| A(4,2,0.1) | 1346.050 | 0.858 | 203.525 | 1.522 | 1.715 | fail |

Both candidates repair the major P-GRB-relative fragmentation witness under the
1.25 Work gate, but neither preserves the strongest C6 control under the 1.20
Work and 1.25 shifted-time gates. This is a bounded, systematic negative result:
K0 in {1,4}, d in {1,2}, two globally frozen rho values, four envelope
modes, the old and D scores, no-adaptive closure, and all mandatory causal
references were evaluated. C_d was formally inadmissible; lifted cuts and
frontier consolidation were formally skipped only because their predeclared
entry conditions were false.

## Required questions

1. **Does K1-new repair the major C6 regression?** Yes on the frozen major
   P-GRB Work gate, but it is not promotable because it loses the strongest C6
   control.
2. **Does K4-new repair the regression while preserving the strongest C6
   control?** It repairs the major witness, but does not preserve the control.
3. **Attribution?** K4 initial granularity retains more local strength; the
   envelope and D recursion change proof allocation, but the mandatory
   ablations show no globally stable promotion.
4. **Is d=1 enough?** It exposes a real deficit but has weaker median envelope
   capture and was not selected.
5. **Does d=2 help?** Yes structurally: it adds stable D variation and higher
   median capture, so d=2 was frozen for exact tests.
6. **Can K4 local strength be transferred by affine envelopes?** Not as a
   material complete-root gain on the strongest control; K1 and K4 root LPs
   coincide and chi is vacuous.
7. **Is D_d stable?** It is valid, reconstructible, and hardware-independent,
   but its selected candidates fail the full performance envelope.
8. **Is C_d admissible/useful?** No; it is the constant `1-2^-d` here.
9. **Were lifted cuts required?** No. Their entry condition was false.
10. **Was frontier consolidation required?** No. The control was unprotected
    and the major selected rows did not show adjacent-descendant terminal
    duplication.
11. **Are decisions timing-independent?** Yes; the forbidden-input audit passes
    and decision hashes exclude telemetry.
12. **Are certificates exact and verified?** Yes for every claimed certificate;
    the audit has zero false certificates and keeps censored rows unsolved.
13. **Any severe material regression?** The complete development profile is in
    `performance_profile.csv`; its frozen tail gates are reported without
    suppressing startup-dominated rows.
14. **Recommended global configuration?** None. No promotion is recommended.
15. **Did validation pass?** Validation was not opened because development
    failed.
16. **Did the sealed holdout pass?** It remained sealed and was not run.
17. **Terminal classification?** `bounded_systematic_negative_result`.

## Exactness and disposition

Zero false certificates were observed. Default-off equivalence passed all
three sentinels. Stage 4 and Stage 5 disposition files record every false entry
condition with supporting evidence. Validation and holdout are intentionally
not run, rather than described as failures or inferred from matching objectives.

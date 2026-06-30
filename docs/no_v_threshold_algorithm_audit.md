# No V-Threshold Algorithm Audit

This round realigns the paper-core algorithm around a single framework:

1. native HGA-TGBC incumbent generation;
2. Gini-frontier interval decomposition;
3. valid non-enumerative relaxation lower bounds;
4. route-load BPC tree on unresolved intervals, with exact pricing closure required.

The new core preset is `paper-gf-bpc-core`.  It disables complete all-subset
route-mask enumeration for every instance size.  Any remaining V-dependent
guards in implementation code are resource guards or diagnostic backends, not
paper-core certificate logic.

Machine audit:

- Script: `scripts/audit_no_v_threshold_paper_core.py`
- Output: `results/paper_core_realignment_round/no_v_threshold_audit.txt`
- Result: PASS in this round.

Historical presets and diagnostics may still mention V12/V20/V50/V100 as
benchmark labels.  Those labels are not algorithm branches in `paper-gf-bpc-core`.

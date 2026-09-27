# Round 44 final report

Round 44 terminates as **`bounded_systematic_negative_result`** with scale **`small_panel_only`** and no
promotion. The development leader was K4, fixed-depth-1 lookahead, all affine
envelope facets at parent scope, no adaptive refinement, rank-1 off, verified
MIP starts, and consolidation off. Its only pre-frozen validation fallback was
C6 veto at rho_F=0.5 with starts off.

The major candidate/P-GRB shifted Work and time ratios are
`1.0397` and
`0.8127`. On the strongest C6-win row,
candidate/C6 Work is `1.2143` and
P-GRB/candidate is `63.47`.
Severe regressions: `0`.

- Development: pass; Work/time gmeans `0.4199` / `0.5256`.
- Primary validation: fail; Work/time gmeans `1.0243` / `1.5246`.
- Pre-frozen veto fallback validation: fail; Work/time gmeans `1.2076` / `1.6442`.
- Holdout: not opened because all pre-frozen validation candidates failed.
- Additional V12: not opened because holdout remained sealed.
- V20: not opened because holdout remained sealed.
- Rank-1: `13` audited parents and `0` violated cuts.
- Default-off: `3/3` sentinels.

The Round 43 erratum is documentary only. Historical results were not rewritten;
all invalidated diagnostics remain disclosed and excluded from performance.

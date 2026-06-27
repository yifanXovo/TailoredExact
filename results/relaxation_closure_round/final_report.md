# Relaxation Closure Round Final Report

Branch: `codex/longrun-round17-local-results`

Starting commit: `0c2627821415515973eccbc0e9b4d412d6e7167d`

Code/result commit before this report-reference correction:
`7c5e8cd2430a6f86ae4c28345e24651fe4313c5b`.

Final remote branch tip is reported in the final response after push.

## Implemented Changes

- Added V20 multi-station route-duration cover cut separation.
- Added station residual objective-cutoff domain tightening and projection
  penalty floor for large-instance relaxation rows.
- Added optional large compact-flow relaxation with modes `off`, `lp`, and
  `mip-light`.
- Extended relaxation cache/option signatures and JSON result fields for the
  new lower-bound components.
- Added frontier pre-split controls and explicit relaxation worker aliases.
- Retested controlled BPC fallback after the relaxation changes.
- Fixed V20/M3 metadata in new rows: hard stress instances are reported as
  `hard_generated_v20_m3`, not historical targets.

Proof sketches are in:

- `docs/v20_multistation_cover_cuts.md`;
- `docs/station_residual_cover_cuts.md`;
- `docs/large_compact_flow_relaxation.md`;
- `docs/parallel_relaxation_and_cache.md`;
- `docs/bpc_fallback_retest_after_relaxation.md`.

## V12 M1 Before/After

| row | status | LB | UB | gap | runtime |
|---|---:|---:|---:|---:|---:|
| previous/current 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 300.828s |
| critical pre-split 300s | not closed | 0.329549359470 | 0.357200583208 | 0.0774109143105 | 301.409s |
| parallel 2-worker 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 304.279s |
| BPC fallback 300s | not closed | 0.331296710948 | 0.357200583208 | 0.0725191208467 | 303.842s |
| canonical 600s | optimal | 0.357200583208 | 0.357200583208 | 0 | 481.106s |

Answer: V12 M1 did not certify within 300s. It certifies within 600s. The 300s
LB did not improve; pre-splitting and fallback both hurt short-run closure.
The bottleneck remains relaxation split scheduling and bound time.

## V12 M2 Regression

| row | status | LB | UB | gap | runtime |
|---|---:|---:|---:|---:|---:|
| canonical paper-core 300s | optimal | 0.718504070755 | 0.718504070755 | 0 | 205.628s |

V12 M2 remains certified with native HGA-TGBC UB and relaxation-only full
frontier certificate.

## V20/M3 Before/After

| case | previous 300s gap | best new gap | best row |
|---|---:|---:|---|
| `high_imbalance_seed3201` | 0.122744236967 | 0.0682096293371 | `miplight_300s` |
| `high_imbalance_seed3202` | 0.100084871258 | 0.0544001976401 | `miplight_300s` |
| `tight_T_seed3101` | 0.968587506517 | 0.333333333333 | `miplight_300s` |
| `tight_T_seed3102` | 0.218955510650 | 0.168318012854 | `lp_1200s` |
| `moderate_seed3301` | 0.130305288314 | 0.130305288314 | `lp_300s` |
| `moderate_seed3302` | 0.330217368450 | 0.330217368450 | `lp_300s` |

The `high_imbalance_seed3202_miplight_1200s` row reaches gap
`0.0317627113992`, below the requested `0.05` target for that representative
case.

## Which Component Helped

The effective component is the large compact-flow `mip-light` relaxation. It
materially improves three of six V20/M3 300s gaps. Station residual cuts add
valid evidence but are not the main driver. Multi-station cover cuts are valid
but inactive on the current stress suite.

## BPC Fallback Retest

| row | LB | UB | gap | nodes | pricing calls | conclusion |
|---|---:|---:|---:|---:|---:|---|
| `v12_m1_bpc_fallback_300s` | 0.331296710948 | 0.357200583208 | 0.0725191208467 | 1 | 1 | hurts by displacing relaxation |
| `high_imbalance_seed3202_miplight_fallback_300s` | 1.65415045452 | 1.74931345205 | 0.0544001976401 | 0 | 0 | same as relaxation-only |
| `tight_T_seed3102_lp_fallback_300s` | 0.469176890001 | 0.600704436685 | 0.21895551065 | 0 | 0 | same as relaxation-only |
| `moderate_seed3302_lp_fallback_300s` | 0.131033733249 | 0.195636206549 | 0.33021736845 | 0 | 0 | same as relaxation-only |

BPC fallback does not help after stronger relaxation and should remain
diagnostic.

## Audit

Command:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' scripts\audit_bpc_certificate.py results\relaxation_closure_round\raw --csv-out results\relaxation_closure_round\certificate_audit.csv --fail-on-error
```

Result: `audited_rows=27 failures=0`.

## Remaining Bottleneck

The next bottleneck is still relaxation, specifically per-interval variant
selection and stronger valid lower bounds for V20/M3. The next round should not
be a broad benchmark. It should implement an interval-level relaxation portfolio
selector that can choose between LP and `mip-light` compact-flow variants, and
then add stronger valid cuts for moderate rows where neither variant improves
the lower bound.

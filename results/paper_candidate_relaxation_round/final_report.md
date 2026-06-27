# Paper-Candidate Relaxation Round Final Report

Branch: `codex/longrun-round17-local-results`

Starting remote head: `4aee723e986bfe3e60e06a06fec9f8bfe26ff3b1`

Final commit SHA: see final response after push.  The exact SHA cannot be
self-embedded in this tracked file without changing the SHA.

## Code Changes

- Added `paper-bpc-core-adaptive` as an auditable candidate preset.
- Added adaptive/race relaxation portfolio options and JSON/interval metadata.
- Added optional compact-flow connectivity constraints.
- Added optional service-operation minimum handling cuts.
- Added optional penalty movement lower-bound cuts.
- Added disabled/plumbed transfer-subset capacity cut fields for future work.
- Extended result JSON and interval traces with variant-selection fields.
- Fixed `paper-bpc-core-adaptive` normalization so connectivity,
  service-operation, and penalty-movement cuts are not enabled implicitly by
  the preset or pre-split path; they remain explicit ablation flags.
- Added summary script `scripts/summarize_paper_candidate_relaxation_round.py`.

## V12 Results

| instance | row | status | LB | UB | gap | runtime |
|---|---|---:|---:|---:|---:|---:|
| V4 smoke | adaptive 30s | optimal | 0 | 0 | 0 | 0.751s |
| V12 M2 | adaptive 300s | optimal | 0.718504070755 | 0.718504070755 | 0 | 204.997s |
| V12 M1 | current 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 301.673s |
| V12 M1 | adaptive 300s | not closed | 0.332675660948 | 0.357200583208 | 0.0686586848205 | 310.083s |
| V12 M1 | adaptive 600s | optimal | 0.357200583208 | 0.357200583208 | 0 | 473.765s |

V12 M2 remains certified.  V12 M1 does not improve at 300s, but still certifies
inside a 600s run slightly faster than the previous 481s closure.

## V20/M3 Results

The adaptive selector did not beat the previous best LP/mip-light fixed
variants.  Most V20/M3 adaptive rows are worse than prior best; only
`moderate_seed3302` improves very slightly:

| case | previous best gap | adaptive/race best observed gap | conclusion |
|---|---:|---:|---|
| high_imbalance_seed3201 | 0.0682096293371 | 0.222215404482 | worse |
| high_imbalance_seed3202 | 0.0317627113992 | 0.139559874088 | worse |
| tight_T_seed3101 | 0.333333333333 | 0.639313781399 | worse |
| tight_T_seed3102 | 0.168318012854 | 0.218955510650 | worse |
| moderate_seed3301 | 0.130305288314 | 0.130305288314 | tied |
| moderate_seed3302 | 0.330217368450 | 0.329231102492 | slight improvement |

The decisive conclusion is that adaptive portfolio selection is not yet robust
enough for the paper-core default.  Fixed LP/mip-light selection remains the
stronger V20 evidence.

## Cut Activity

Compact-flow connectivity, service-operation minimum handling, and penalty
movement lower-bound cuts are proof-safe options, but their first combined V20
rows did not improve the best previous bounds.  Multi-station cover cuts remain
inactive on the current stress cases.  Transfer-subset capacity cuts are not
active in this round.

## BPC Fallback

BPC fallback remains diagnostic.  Previous fallback rows did not improve lower
bounds and can displace useful relaxation time.

## Audit

Commands run:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py --self-test
D:\msys64\ucrt64\bin\python.exe scripts\audit_bpc_certificate.py results\paper_candidate_relaxation_round\raw --csv-out results\paper_candidate_relaxation_round\certificate_audit.csv --fail-on-error
build\ExactEBRP.exe --method certificate-basis-test ...
build\ExactEBRP.exe --method option-consistency-test ...
```

Audit result: `audited_rows=14 failures=0`.

After the adaptive preset normalization fix, the final audit result is
`audited_rows=15 failures=0`.

## Recommendation

Do not start a broad benchmark matrix yet.  The next targeted round should
focus on per-interval variant budgeting and selection so that adaptive mode can
recover the best fixed LP/mip-light evidence before attempting to improve it.

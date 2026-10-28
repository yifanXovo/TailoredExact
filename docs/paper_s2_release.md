# GI-TBC release and paper-S2 run guide

This guide describes the Round137 branch from verified main
`b2b940c1e517a72e226ec60fc49ff19651737632`. The English Draft PR targets
`main` and must remain a Draft; its actual identity/readback belongs in the
continuation record. This record does not assert that the branch has merged. The accepted
Round136 mainline and all historical observations remain separately pinned.

## Algorithm, implementation and evidence identities

| Identity | Meaning |
|---|---|
| Formal method | **GI-TBC - Gini-interval tailored branch-and-cut** |
| Implementation | Historical S2, configuration `ms2`; the thin public entry keeps the name `paper_s2.py` |
| Current production source | `779713ad9a0b01edc538ecb64df9438739127be3`; actual frozen source/PE hashes are in the [candidate manifest](../results/unified_exact_round137/candidate_manifest.json) |
| Current Round137 profile | [gi_tbc_round137.json](../config/gi_tbc_round137.json), normalized against all 28 actual default vectors in the frozen 120-position matrix; actual guarded promotion and all 28 CLI checks passed with six refusal cases and zero native execution |
| Compatibility identities | Bare executable default remains ENS-C; immutable [paper_s2.json](../config/paper_s2.json) preserves the accepted R135 profile and its 16-vector provenance |
| Current paper | Maintained R135 lineage, now with Round137 question-led experiments, complete model/algorithm appendices and original bibliography |

GI-TBC independently pays complete own H, keeps M-B shared inventory/service
states, VD-P, uniform pair-only support, the current interval controller and
R134 proof policy. AP stays off. There is no instance/size dispatch, elapsed-time
algorithm switch or cross-method/Seed/weight Start transfer. Research-only
single-group flags change only their declared control.

The physical problem retains empty departure, loaded return including unloading,
unique nonzero one-way service, prefix vehicle-capacity constraints and depot
exclusion from the objective. Deliveries may free capacity for later pickups,
so cumulative pickups may exceed Q while each route-prefix load stays in [0,Q].
Initial/final inventory is integer and bounded by station capacity. Mathematical
targets satisfy D>0; the computational text format stores integer targets.
The present test targets additionally satisfy D<=C, without adding that
target-capacity condition to physical feasibility.

| Uniform parameter | Current setting |
|---|---|
| AM threshold | 0.08; actual post-preset field checked |
| Maximum outer depth / minimum width | 8 / 1e-4; recorded guard exposure and unknowns are reported |
| Support / AP | Pair-only / off |
| Own H seed | 20260626, distinct from Gurobi Seed |
| Gurobi | 13.0.2; one thread; presolve -1; Windows affinity mask 4 |
| Main / limited repeat Seeds | Seed0 / preselected Seed1 |
| Physical handling | Per-unit pickup/drop from the launch; study uses 60/60 seconds and includes return unloading |
| Experimental caps | 600/1200/2400 s by size; cap is a computing allowance, separate from physical T |

## Expand or run one independent command

Use `E:\codes\ExactEBRP-work\worktrees\paper-current`; keep the protected
original `E:\codes\ExactEBRP` unchanged. New runs/build/raw/temp/recovery assets
belong under `E:\codes\ExactEBRP-work\`. The verified local Python is
`D:\msys64\ucrt64\bin\python.exe`.

```powershell
Set-Location E:\codes\ExactEBRP-work\worktrees\paper-current
& 'D:\msys64\ucrt64\bin\python.exe' -B scripts\paper_s2.py `
  --input results\unified_exact_round130\inputs\UC-B20-B.txt `
  --out-dir E:\codes\ExactEBRP-work\runs\gi-tbc-example `
  --T 7200 --pickup-time 60 --drop-time 60 --lambda 0.15 --cap 1200 --seed 0 --json
```

This expands the full frozen command without starting the producer or creating
output. Append `--run` to execute; choose a new output directory each time.
Existing directories, nonfinite weights, negative Seeds, insufficient caps and
unrecognized algorithm overrides are refused. No extra-argv escape hatch exists.
`--exe` accepts a compatible local executable and records its actual hash; it
is not silently relabelled as the verified PE.

In the registered campaign, the whole-process cap, native `--time-limit=cap-6`,
shutdown margin 30 and supervisor hard stop `cap-2` keep their distinct roles.
Own H, construction, online checks,
solve/proof/output belong to production. Postverification and total clocks stay
separate; nested H/LP/MIP/Work are not added again. A producer journal by itself
is not the independent formal paper audit.

The actual [entry-check receipt](../results/unified_exact_round137/entry_check.json)
records 28 CLI vectors, physical/objective/cap/Seed/input identities, source and
local PE/DLL byte hashes and six refusal cases, with zero Optimize/build/vendor
library loads. Its ordinary verification clock is separate from experiment cost.

## Runtime and build identity

The frozen Round137 production executable is
`E:\codes\ExactEBRP-work\build-cache\round137\ExactEBRP.exe`, SHA256
`d6fd9e6687ac7d4377e2d7fd683d59bd3354d7dfb3a9e5b3723d0fe62b6c7fbd`.
Gurobi DLL `D:\gurobi1302\win64\bin\gurobi130.dll` has SHA256
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.

The actual incremental build and zero-Optimize deletion/default checks are in
[infra](../results/unified_exact_round137/infra) and
[qualification](../results/unified_exact_round137/qualification).
They reuse the verified MinGW UCRT64/C++17 caches and static core, including
retained historical dependencies. This is an identity-specific incremental
build record, not a clean-machine build prescription. Public recovery carries
source/evidence and attestations, never commercial native assets or credentials.

## Paper, finite experiments and interpretation

Start with the [advisor/coauthor reading packet](paper_review.md), then the
[PDF](../results/unified_exact_round137/manuscript.pdf),
[manuscript source](../results/unified_exact_round137/manuscript.md),
[supplement](../results/unified_exact_round137/supplement.md),
[bibliography](../results/unified_exact_round137/references.bib) and
[stage report](../results/unified_exact_round137/final_report.md).

The registered study comprises 120 method positions, 16 base inputs, 20 physical
configurations and 24 objective configurations. Seeds, weights, AM and mechanism
variants are not independent new inputs. Main Seed0 breadth gives GI-TBC 9/12
certificates versus P 7/12 and PS 7/12; positive-resource pairs give 4/8 versus 0/8
and 0/8. Open certificate times are null. PS's substantive X-35-B reversal, K-35-U's opposed
P/GI-TBC endpoints, all n35 resource open results, mixed conditional mechanism
costs and material descriptive Seed shifts remain visible.

Historical R132, R134 and R135 retain their original source, policy and
counts. The [research index](unified_exact_research_index.md) pins those studies;
none is relabelled as a current observation or pooled into a new success rate.
Historical S2 counts are R132 17/24 versus P 9/24 and PS 4/12, and R134
12/14 versus P 9/14 and PS 2/4. R135 retains its own AP-study panels.
AP stays off after its mixed/negative accepted study. Same-domain ideal LP
strengthening need not improve capped endpoints or complete certificate time.

The [finite recovery policy](../results/unified_exact_round137/reproducibility.md)
specifies one fixed commit; only a passed actual
[public restore receipt](../results/unified_exact_round137/public_restore_receipt.json)
establishes completion of that recovery. Recovery is a bounded anonymous
HTTPS read and pure 120-position replay, with no Optimize, compilation, Git
fallback or vendor DLL load. Resume only a failed transfer in its original
owned root; never repeat a passed recovery or R135's accepted recovery.

The [continuation record](../results/unified_exact_round137/RESUME.md) identifies
actual completion, PR readback and bounded cleanup when those steps occur. Stable historical refs and
old branches are retained. No automatic merge, force-push, old-PR cleanup,
email or submission is part of this delivery. Author facts and three concrete
next research questions are in the reading packet and stage report.

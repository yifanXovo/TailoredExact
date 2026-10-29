# Round138 inventory-product consistency study

The [scientific report](../results/unified_exact_round138/final_report.md)
answers the research questions and gives the actual stage decision. The
[incremental manuscript](../results/unified_exact_round138/manuscript.md)
and its [reading PDF](../results/unified_exact_round138/manuscript.pdf)
extend the accepted Round137 model and algorithm conventions. The complete
Round137 paper and its experiment identities remain the historical authority.

The stage decision is **RESEARCH_ONLY**. K20 adds a certificate in 101.64 s
on Seed0 and 90.23 s on the selected Seed1 while its baselines stay open at
cap1200. The n35 primary endpoints are mixed, and RB35-T2's Seed0 U regression
reverses in the paired Seed1. This supports further focused study without
promoting the candidate as the default. New charged computation is
18214.684111 s (5.059634 h) of the 86400 s allowance.

The stable GI-TBC entry is still `scripts/paper_s2.py`, using
`config/gi_tbc_round137.json`. Its [release guide](paper_s2_release.md)
and frozen PE remain usable. `config/paper_s2.json` keeps its original bytes.

## Explicit candidate entry

`scripts/paper_s2_stock_rlt.py` expands the separate research profile
`config/gi_tbc_stock_rlt_round138.json`. It adds four inventory RLT rows to
GI-TBC and adds no variables. It retains complete own H, M-B/VD-P,
pair-only support, AM .08, depth 8, minimum width 1e-4, and AP/TC off.
The C++ switch `--round138-stock-rlt` defaults off and applies only to ms2.

For example, this is a dry expansion using the actual K20 physical and
objective configuration. It creates no output directory and invokes no solver:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' -B scripts/paper_s2_stock_rlt.py `
  --input results/unified_exact_round132/inputs/K-20-S.txt `
  --out-dir E:/codes/ExactEBRP-work/temp/round138/example-k20 `
  --T 5400 --pickup-time 60 --drop-time 60 --lambda 0.15 `
  --cap 1200 --seed 0 --json
```

Use an actual unique output directory and add `--run` only to start a new
producer. This standalone entry does not replace the formal independent
postproduction evidence reader. The frozen campaign scripts, identities,
parameter/lifecycle/Start/physical/proof audits and qualified endpoints are
the authorities for the reported study. The [entry check](../results/unified_exact_round138/entry_check.json)
binds nine actual primary STOCK command vectors and explicit refusal cases.
Gurobi Seed and H seed are distinct; the latter remains 20260626.

Primary Seed0 measured candidate source is
`83928377336a860acf78f684d1723a5040467bb5`, with PE SHA256
`a41ea8eefd8551799a1d08e6d328beba1b70856433b07d96551790f0f5a4d8ae`.
The delivered entry and STOCK Seed1 confirmation use separately registered
V2 source `04506fa613446d2ef2bd19794f778909422c51fd`, with PE SHA256
`f4c764ff7164bf042ef612403f82b850698b97c80018bf06b2feff1167d65403`.
V2 repairs native import of tiny new-row coefficients by exact positive
power-of-two row scaling. All 33 used V1 STOCK calls have ordinary interval
endpoints and unchanged rows under V2; the finite Native bridge preserves
their original measured identity. Seed1 is disclosed as repaired-build
confirmation as well as a limited second Seed. The original tiny-coefficient
failure and unused pre-repair Seed1 registration remain retained.

The source/build recipes document the minimal object reuse from the verified
Round137 build and the independent V2 build cache. Commercial PE/DLL/license
assets are not published. `candidate_manifest.json` identifies V1;
`candidate_repair_manifest.json` identifies the delivered V2.

## Evidence and continuation

The [primary frozen matrix](../results/unified_exact_round138/matrix_frozen.json)
binds eleven new Seed0 positions: eight candidates on eight physical/objective
configurations, one K15 baseline bridge, and two micro controls. Eight matched
Round137 core baselines are reused with exact identity checks. The panel has
six base inputs. T1/T2 share an input but have different physical horizons.
The resource panel retains rho=1 and its original binary64 lambda=1/Omega.
The [Seed1 selection](../results/unified_exact_round138/seed1_selection.json)
and separately admitted matrix identify the limited result-selected pairs.

Actual computation is recorded by `scripts/round138_common.py budget` and
`cost_report.json`. Never rerun an existing position to replace an adverse
result. A healthy active PID/birth identity must be inspected before any resume.
Sealed native evidence is reused for a verification-only repair; native work
is not silently repeated. `RESUME.md` records the final state and any remaining
delivery continuation.

Pure report/tiny replay commands, run outside any formal timed computation:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' -B scripts/round138_common.py budget
& 'D:\msys64\ucrt64\bin\python.exe' -B scripts/round138_tiny_read.py check
```

`source_publication.json` and `carrier_manifest.json` bind new source, inputs,
necessary raw and failures, exact selected historical members, reports and
paper by hashes. Every new carrier contains a member index. The
`publication_pin.json` fixed commit and `public_restore_receipt.json` describe
the finite anonymous byte/member check; they do not assert a full public
semantic replay. R137's historical recovery limitation remains unchanged.
Late PR/cost/cleanup metadata are checked as differences without recursively
repackaging all fixed science.

## Workspace and delivery boundaries

Use `E:\codes\ExactEBRP-work\worktrees\paper-current`; keep all new
build/raw/temp/restore assets under `E:\codes\ExactEBRP-work`. Protect the
original `E:\codes\ExactEBRP`, user changes, old evidence and runtime assets.
The English PR remains Draft and targets the accepted R137 branch while main
has not absorbed it. No merge, force-push or old-branch deletion is part of
this study. The post-PR cleanup receipt records only the bounded current-round
reconstructible preview removal after evidence/public acceptance. Unique
science, failures, necessary PE/DLL and still-used trees remain retained.

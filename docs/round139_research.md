# Round139 inventory-product placement

The [scientific report](../results/unified_exact_round139/final_report.md),
[mathematical analysis](../results/unified_exact_round139/mathematical_analysis.md)
and [nine-page paper increment](../results/unified_exact_round139/manuscript.pdf)
give the finite placement result. **Retain the existing BOTH candidate as
research-only; stop expanding the two asymmetric placements.** The stable
Round137 GI-TBC entry and the separate Round138 research entry remain unchanged.

The three-role four-cell pilot has twelve actual complete cells: six accepted
BASE/BOTH references and six new Seed0 runs on K15, K20 and RB35-T2. LP-only
loses the main proof benefits. MIP-only certifies K15/K20 in 34.70/100.71 s,
without a substantive time improvement over BOTH, and exactly repeats BOTH's
RB35-T2 U/L (.4012002178390506/.22918159966432358). It does not reduce that
important upper-bound regression. LP-only only partly recovers RB35-T2 U and
remains worse than the stable baseline in both endpoints. Open certificate
times remain null; no cap is imputed as convergence time.

The retained BOTH eight-configuration/six-input panel is inherited R138
evidence, with original measured V1, accepted V2 bridge and limited paired
Seed1/build-confirmation identities. The other five configurations have no new
asymmetric results. No new Seed1 or TC experiment is claimed. All six new full
runs and four cap90 qualification runs retain their adverse/open results.

## Explicit research command

`scripts/paper_s2_stock_placement.py` requires an explicit `--placement` choice:
`base`, `both`, `lp-only`, or `mip-only`. It uses the separate
`config/gi_tbc_stock_placement_round139.json` and frozen Round139 PE. The
legacy `--round138-stock-rlt` continues to mean both locations and is not
combined with the new switch. The new C++ switch is limited to isolated ms2.

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' -B scripts/paper_s2_stock_placement.py `
  --input results/unified_exact_round132/inputs/K-20-S.txt `
  --out-dir E:/codes/ExactEBRP-work/temp/round139/example-k20 `
  --T 5400 --pickup-time 60 --drop-time 60 --lambda 0.15 `
  --cap 1200 --seed 0 --placement mip-only --json
```

This only expands a command. It creates no output directory and performs no
Optimize. `--run` starts a new independent producer and is not needed to
reproduce any delivered result. The completed campaign must not be repeated
to replace unfavorable observations. The formal postproduction evidence reader
and clocks are distinct from this standalone entry's producer output.

Outer LP means the controller's explicit root/child relaxation. Native MIP
includes target and terminal solves and their internal LPs/search. Asymmetric
placement verifies the old artifact, discards the retained native model and
builds a fresh immutable matrix for the other role, while retaining qualified
same-domain LP evidence. Cutoff epochs retain the original invalidation policy.
Model rebuild, lost reuse, Start mapping and online proof costs are paid by the
complete method. A stronger LP need not raise parent-relative AM gain.

The actual production source is `6b22433f525df4d1a6ce48a70b5b6414a53aa73b`,
PE SHA256 `e8ecdd503c7a46125ef54936a4cca4e00c3f78c4df30b252ee423df3e194e13e`.
The unchanged V2 writer is reused. Source, PE, exact input/configuration,
Seed, physical T and native parameters are bound by the candidate manifest,
batch identities and actual control audits. H seed is separately 20260626.
Every new solve is Seed0, one thread and serial; resource roles retain rho=1
and their original binary64 lambda=1/Omega.

## Evidence and boundaries

The [continuation record](../results/unified_exact_round139/RESUME.md) and final
delivery report identify the actual PR, fixed science pin and delivery state.
`round139_common.py budget` is a small read-only fee view. New experiment cost
is 6371.821016 s (1.769950 h) of 57600; nested H/LP/MIP/Work is not added twice.
Builds, postverification and explicit ordinary I/O are separately metered.
The early automatic Git maintenance is disclosed: its qualification clocks are
not performance samples, and it was stopped before the formal pilot. Subsequent
Git mutations disable automatic maintenance per invocation.

All used actual matrices receive exact stock-row multiplicity checks. The
qualification Native reads check coefficient maps/RHS and types; their artifact
path counts differ from distinct canonical SHA counts, as the identity-count
clarification records. All saved witness vectors in the selected eight sealed
trajectories are physically replayed. Same-call numerical matches to rounded
logs do not establish exact discovery times; zero in the native plot denotes
the submitted own Start. LP evidence is not relabelled as a native returned bound.

The current carrier manifest and public receipt cover new Round139 bytes and
members only. Local semantic checks and public readability are different
claims. The prior R137 public-semantic limitation and accepted R138 readback
are unchanged. No public check runs Optimize, compiles, or loads commercial
native assets. No merge, force-push, old-round deletion, email or submission is
part of this delivery.

Use `E:/codes/ExactEBRP-work/worktrees/paper-current`; preserve the original
`E:/codes/ExactEBRP` and user content. All new build/raw/temp/restore assets stay
under `ExactEBRP-work`. Post-PR cleanup is bounded to completed reconstructible
current-round previews, after evidence/public acceptance, retaining unique raw,
failures, necessary PE/DLL and all still-needed trees.

# Round140 two-sided inventory threshold counts

This research entry keeps the [R137 stable GI-TBC release](paper_s2_release.md)
and the separate R138/R139 entries unchanged. The governing task, mathematical
scope, evidence and actual completion state are in
[Round140](../results/unified_exact_round140/RESUME.md).

TC2 uses both physical total-inventory budgets to bound the number of station
ratios above each exact supported threshold. One aggregate old TC row is
retained, and one two-sided aggregate row is added, without new columns.
Negative selector coefficients and the nonzero constant are preserved with
directed rounding and exact power-of-two transport. The standard chord and
McCormick/RLT constructions are not claimed as new general theory. The
[mathematical note](../results/unified_exact_round140/mathematical_analysis.md)
states validity, conditional dominance, strict block separation and the limits
of the proposed full-route extension.

The [same-domain LP note](../results/unified_exact_round140/LP_report.md)
distinguishes saved-point separation from optimized bound gains. Five shared
domains improve over old TC+stock; the initial full candidate applies stock, TC
and TC2 uniformly in outer LP and native target/terminal calls. Each complete
method pays its own H, construction, validation, search and online proof.
Formal performance and the adoption decision are determined by the entered
complete runs, with old TC+stock necessary controls on K20 and RB35-T2.

The [final scientific report](../results/unified_exact_round140/final_report.md)
and [decision](../results/unified_exact_round140/candidate_decision.json) retain
both configurations **research-only and stop full promotion**. TC2 has an
important K35 complete regression. The selected old TC+stock combination
completes eight Seed0 configurations and preserves three proofs, but slower
K15/K20, horizon/bound tradeoffs and an adverse critical RB35-T2 Seed1 prevent
promotion. Those combination outcomes are not attributed to TC2. The one
confirmation reuses the accepted matched R138 BASE1/STOCK1 with their original
source, PE and clocks. No extra product LP/full line was opened after the
saved-point projection screens found no product signal.

## Explicit research entry

`scripts/paper_s2_tc2.py` resolves the separate
`config/gi_tbc_tc2_round140.json`. Its separate research default is the selected
uniform old-TC+stock candidate (`tc`); `--counts tc2` reproduces the initial
TC2+stock candidate with both count aggregates. It is research-only
and does not change the stable default. Bare C++ `--round140-counts off`
preserves legacy behavior; old stock and R139 placement flags retain their
meanings. The new count switch requires isolated ms2 and uniform placement.

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' -B scripts/paper_s2_tc2.py `
  --input results/unified_exact_round132/inputs/K-20-S.txt `
  --out-dir E:/codes/ExactEBRP-work/temp/round140/example-k20 `
  --T 5400 --pickup-time 60 --drop-time 60 --lambda 0.15 `
  --cap 1200 --seed 0 --counts tc --json
```

This only expands a command and performs no Optimize or output-directory
creation. `--run` starts a new independent producer. The standalone producer
does not replace the formal campaign's original complete physical/H/Start/
proof reader and clocks. Do not rerun sealed positions to replace unfavorable
observations. Resource roles keep their frozen rho=1 weight, not lambda=.15.

## Reproduction and evidence

`candidate_manifest.json` and each frozen batch matrix bind the actual source,
PE, Gurobi DLL, helpers, input, physical T, lambda, seed and cap. Seed0 is
explicit for every primary solve; any limited Seed1 result keeps its own
registered identity. H seed is separately 20260626. Solves are single-threaded
and serial. AP remains off, AM .08, depth 8 and minimum width 1e-4.

`round140_common.py budget` reads small durable accounting; `status <label>`
reads the PID birth/receipt. Existing pending fees are inspected rather than
automatically restarted. New complete outer costs are charged once; nested
H/LP/MIP/Work are not charged twice. Qualification and failures are included.
Builds, pure offline work, PDF and public I/O are separate and stay outside
timed runs. Open certificate times are null.

Local scientific/semantic checks and public byte/member readability are
different claims. Only this round's necessary carriers receive a bounded
public read. Old dependencies retain fixed commits and selected member hashes;
R137-R139 acceptance is not reopened. The final continuation record gives the
actual Draft PR, head/base, fixed science pin, public receipt and cleanup.

All new build/raw/temp/restore assets stay under `E:/codes/ExactEBRP-work`.
Protect `E:/codes/ExactEBRP` and user content. Post-PR cleanup is bounded to
completed reconstructible current-round duplicates after evidence/public
acceptance, retaining unique raw/failures, necessary PE/DLL and still-used
trees. No old-round deletion, merge or force-push is authorized by this study.

# Paper-S2 release and run guide

This is the authoritative current entry established in Round136 (27 October
2026, Asia/Shanghai). It accepts the completed R135 outcome and makes no new
algorithm or performance claim.

## Four identities

| Identity | Current meaning |
|---|---|
| Paper algorithm | **S2 / GI-TBC / ms2**: complete own H, M-B shared inventory/service states, VD-P, uniform pair-only support, existing controller and R134 proof policy |
| Code snapshot | R135 production source `29b3c8baa06ea3b1dc4cb4620c3040c3183cc0c4`; metadata head `25800aa6b51bf7607b51e5df14a10a5ca4571889`; AP disabled |
| Paper and evidence | Maintained R135 manuscript/PDF and supplement; R132 breadth, R134 final confirmation, R135 AP study keep their original versions and denominators |
| Compatibility CLI default | **ENS-C** when using the bare executable; recommending paper-S2 and updating Git `main` do not change that default |

The physical model remains empty departure, loaded return with unloading time,
unique nonzero one-way service, route-prefix capacity and depot exclusion from
the objective. No instance identity/size dispatch or time-based method switch
is introduced. AP stays research-only/off; TC and AP are completed studies.

## Run once

The active local checkout is `E:\codes\ExactEBRP-work\worktrees\paper-current`.
The shared original checkout `E:\codes\ExactEBRP` retains its R105 HEAD and
protected user changes. Use an installed Python 3 runtime; the validated local
one is `D:\msys64\ucrt64\bin\python.exe`.

```powershell
Set-Location E:\codes\ExactEBRP-work\worktrees\paper-current
& 'D:\msys64\ucrt64\bin\python.exe' -B scripts\paper_s2.py `
  --input results\unified_exact_round130\inputs\UC-B20-B.txt `
  --out-dir E:\codes\ExactEBRP-work\runs\paper-s2-example `
  --T 7200 --pickup-time 60 --drop-time 60 --lambda 0.15 --cap 600 --seed 0
```

This is a dry run: it displays the actual expanded command without creating
output or starting the solver. Append `--json` to inspect the full launch plan,
or `--run` to execute. Choose a new output directory each time; existing
directories are refused, including empty ones. The example is an entry check,
not another performance sample. This round uses zero new native solves.

| Option | Meaning |
|---|---|
| `--input` | Physical input, with fleet capacities from that input |
| `--T` | Physical route-duration horizon, in seconds |
| `--pickup-time`, `--drop-time` | Per-unit handling seconds; drop time also prices returned-load unloading |
| `--lambda` | Objective penalty weight, retaining the original objective convention |
| `--cap` | Whole native-process budget, integer seconds greater than 36; complete own H is included |
| `--seed` | Explicit Gurobi Seed; the accepted own-H policy/Seed remains unchanged |
| `--out-dir` | New output root; all result/log/phase/H/progress/native-evidence paths expand beneath it |
| `--exe` | Optional local executable implementing the R135 configuration; its SHA is recorded |

The [frozen full vector](../config/paper_s2.json) is extracted from actual R135
launches, not reconstructed from a shortlist of flags. All 16 S2 launch vectors
are identical after normalizing the executable, output paths and the explicitly
allowed data/experiment parameters. Native `--time-limit=cap-6`, process wall
limit `cap`, shutdown margin 30 and outer hard stop `cap-2` retain their original
roles. `--threads 1`, `--mip-threads 1`, presolve -1 and Windows affinity mask 4
are fixed. The full preset and research settings include `m-binary`, `ms2`,
LP-G split false, candidate mode off, witness audit true and HGA zero-stop true.
No AP-enable flag is present and there is no general extra-argv escape hatch.

The launcher records command, input/PE/config hashes, completion and affinity.
It launches the producer independently of campaign prepare/freeze/run code;
only the pure OS-affinity helper is reused. The producer's result and native
journal do not constitute a replay of the formal paper's independent audit.
Use the original finite reproduction policy for paper evidence and its clocks.
A rebuilt/custom PE has its actual hash recorded and is not represented as the
verified historical PE unless its bytes match.

## Runtime and build identity

Prefer the existing successful R135 binary:

* `E:\codes\ExactEBRP-work\build-cache\round135\ExactEBRP.exe`
* PE SHA256 `652335fbc004eb4799c01d074dd43c31a883ae40fc353ed37eaa82e98b53a3ed`
* Gurobi 13.0.2 DLL: `D:\gurobi1302\win64\bin\gurobi130.dll`
* DLL SHA256 `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`

The actual successful build is recorded in
[candidate_build.json](../results/unified_exact_round135/candidate_build.json)
and [round135_build.py](../scripts/round135_build.py): MinGW UCRT64 g++, C++17,
`-Wall -Wextra -Wpedantic -DEXACT_EBRP_ENABLE_GUROBI=1`, qualified include paths,
recompiled writer/main and the retained R133/R134 objects plus R120 static core.
The compiler SHA is `8cd0aa578687e4182532222c8734439b3f34ac78b6ce23cba1071c5838025fc1`.
This incremental build depends on those exact caches and the R120 core at its
recorded path. It is not a generic clean-machine CMake Release prescription.
The original build script is a historical campaign action; ordinary use should
invoke the verified PE through the thin launcher. Round136 performs no build.

## Paper, tables and finite reproduction

Start with the [two-page review note](paper_review.md), then the
[complete manuscript](../results/unified_exact_round135/manuscript.md),
[checked 38-page PDF](../results/unified_exact_round135/manuscript.pdf),
[supplement](../results/unified_exact_round135/supplement.md) and
[bibliography](../results/unified_exact_round135/references.bib).

| Version | Evidence and interpretation |
|---|---|
| R132 | Twelve inputs/two Seeds; 17/24 S2, 9/24 cold P, 4/12 paid-start PS qualified certificates under the original policy |
| R134 | Final six-known-role confirmation: S2 12/14, P 9/14, PS 2/4; four additional weight runs plus two reused points |
| R135 | AP comparison: 10+22 complete positions, 16 pairs on seven known inputs; S2 and AP each certify 10/16 |

Original-version links are in the [research index](unified_exact_research_index.md).
R134 [complete matched tables](https://github.com/yifanXovo/TailoredExact/tree/d3353749e6933e6685c7f0d92d153d0641816bcb/results/unified_exact_round134/reports)
and R135 [arms](../results/unified_exact_round135/reports/arms.csv),
[pairs](../results/unified_exact_round135/reports/pairs.csv),
[two roots](../results/unified_exact_round135/reports/roots.json) retain adverse
and open results. These denominators are not interchangeable. Twelve R135 S2
observations can be matched to R134 by role/Seed/repeat/input/weight, with the
same certificate/open status and U; eight also have equal caps. This does not
require a new baseline panel.

AP strengthens the two same-domain numerical roots but has no substantive
certified-time win, two substantive adverse Seed0 differences, and mixed open
endpoints. For the same domain/objective, feasible-set inclusion gives
`R_AP subset R_0 => min(R_AP) f >= min(R_0) f`. Finite complete searches can
follow different paths, so neither `L_AP(t) >= L_S2(t)` nor faster AP
certification follows. K35's stronger root and weaker final lower bound are
compatible; no specific native-branch/cut attribution is established.

[Finite reproduction](../results/unified_exact_round135/reproducibility.md),
[completed R135 RESUME](../results/unified_exact_round135/RESUME.md) and its
[public PASS receipt](../results/unified_exact_round135/public_restore_receipt.json)
describe the science commit `2b27711484d85afbbb3a8446df83da89fcc901ec`.
The existing `E:\codes\ExactEBRP-work\restore\round135-public-2b27711484d8`
is retained read-only. Do not rerun a passed recovery. Round136 verifies new
small entry files and identities without another raw recovery or panel.

## Stable references and integration

The small set of stable refs is `archive/main-round37-20260813`,
`paper-s2-round136` and `archive/round38-g2a-not-adopted`; actual targets and
remote readback are in [stable_refs.json](../results/unified_exact_round136/stable_refs.json).
No existing ref is overwritten. Keep long-term evidence pinned to commits.

[Round136 RESUME](../results/unified_exact_round136/RESUME.md) records the
actual English **base=main** consolidation PR, review/checks, cleanup and final
authorization state. The branch begins at the verified R135 head and preserves
all 735 existing commits. A normal merge is proposed. Old PRs are only closed
after that merge and the one final user authorization; PR85 is separately
archived as non-adopted, with its independent history retained.

Remaining author facts and feedback-triggered research conditions are in the
[review packet](paper_review.md). No fresh AP/TC research, formal panel, email
or submission is scheduled by this release.

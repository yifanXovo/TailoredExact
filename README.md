# TailoredExact

Exact solvers for the Equity-aware Bike Repositioning Problem.

The main paper algorithm is **GI-TBC/B** (historical S2/ms2), with AP disabled
and a uniform pair-support configuration. The current R165 manuscript includes
evidence through R164; its measured source/PE identities remain distinct from
document generation. Start with the
[paper-S2 release and run guide](docs/paper_s2_release.md), then the
[advisor/coauthor review packet](docs/paper_review.md).

From the current Windows checkout, display the complete verified command:

```powershell
& 'D:\msys64\ucrt64\bin\python.exe' -B scripts\paper_s2.py `
  --input results\unified_exact_round130\inputs\UC-B20-B.txt `
  --out-dir E:\codes\ExactEBRP-work\runs\paper-s2-example `
  --T 7200 --pickup-time 60 --drop-time 60 --lambda 0.15 --cap 600 --seed 0
```

Append `--run` to execute once into that new directory. `--T` is the physical
route horizon; `--cap` is the whole solver-process budget. The launcher keeps
complete own H and the full frozen parameter vector. It changes no C++ preset.

Read the [current complete manuscript](results/unified_exact_round137/manuscript.md),
[main + Appendix A/B PDF](results/unified_exact_round137/manuscript.pdf), and
[supplement PDF](results/unified_exact_round137/supplement.pdf).
The [contribution map](results/unified_exact_round165/contribution_positioning.md)
and [author memo](results/unified_exact_round165/author_decision_memo.md) explain
the integrated method's finite evidence and the unestablished independent
performance value of the outer controller. R165 adds no performance runs.
The bare executable retains its **ENS-C compatibility default**. AP and TC are
closed research studies, with AP research-only and default off.

Round136 was merged into Git `main` by ordinary merge commit in
[PR #198](https://github.com/yifanXovo/TailoredExact/pull/198). Its historical
checkout disposition is in the
[integration, PR disposition and local cleanup](results/unified_exact_round136/RESUME.md)
record. R165 uses an isolated `ExactEBRP-work/worktrees/round165` checkout
from verified R164, retaining the dirty R155 `paper-current` entry. The original `E:\codes\ExactEBRP` checkout retains
user changes and the shared Git store. New work belongs under
`E:\codes\ExactEBRP-work`; see [workspace policy](WORKSPACE_POLICY.md).

The former K1-AM-SF/R55-R58 entry is
[historical](https://github.com/yifanXovo/TailoredExact/blob/25800aa6b51bf7607b51e5df14a10a5ca4571889/README.md).
Use the [research index](docs/unified_exact_research_index.md) for fixed evidence
versions and earlier results. The root [Manuscript directory](Manuscript/README.md)
is also historical. Current paper sources and the component-only
`scripts/round165_documents.py` build are documented in the review packet;
historical release configurations keep their own identities in the run guide.

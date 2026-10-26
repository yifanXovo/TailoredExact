# TailoredExact

Exact solvers for the Equity-aware Bike Repositioning Problem.

The supported paper algorithm is **S2 / GI-TBC / ms2**, using the R135 source
snapshot with AP disabled. Start with the authoritative
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

Read the [complete manuscript](results/unified_exact_round135/manuscript.md),
[38-page PDF](results/unified_exact_round135/manuscript.pdf), and
[supplement](results/unified_exact_round135/supplement.md).
The bare executable retains its **ENS-C compatibility default**. AP and TC are
closed research studies, with AP research-only and default off.

Round136 prepares a normal, history-preserving merge into Git `main`;
[integration, PR disposition and local cleanup](results/unified_exact_round136/RESUME.md)
record the actual state. The original `E:\codes\ExactEBRP` checkout retains
user changes and the shared Git store. New work belongs under
`E:\codes\ExactEBRP-work`; see [workspace policy](WORKSPACE_POLICY.md).

The former K1-AM-SF/R55-R58 entry is
[historical](https://github.com/yifanXovo/TailoredExact/blob/25800aa6b51bf7607b51e5df14a10a5ca4571889/README.md).
Use the [research index](docs/unified_exact_research_index.md) for fixed evidence
versions and earlier results. The root [Manuscript directory](Manuscript/README.md)
is also historical. Build identity and the actual successful R135 configuration
are documented in the release guide.

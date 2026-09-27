# Round90 LP-G split static-review handoff

Implementation checkout: `E:/codes/ExactEBRP`, branch `codex/round90-ensc-lp-g-split`, based on root's Round90 plan commit `87369d8fd` and final Round89 evidence commit `fe19ca9d519d5c60e4b7bf37085645b41ae44723`. Git remains root-owned. The implementation changed only the seven files below; the three unrelated dirty result files were not touched.

| File | SHA-256 |
|---|---|
| `include/Instance.hpp` | `386ffd2a778d0fa8648f3eb2ef091d9742c7e25e0b947cf31aa7e1db99efcb3f` |
| `include/GiniFrontierGeometry.hpp` | `c6d8b45bb43027b0ecde60160501ca0a3c07877dbc35bbfbe5fbaaec72c94305` |
| `src/main.cpp` | `efe8b0598483c2c3d2b3afb611fd2352f2005c53fe4cb9de95ebeab553c61570` |
| `src/GiniFrontierGeometry.cpp` | `a4640594421ec578561ff19ee0125526b8c213ac26c2833299427caf6e03024f` |
| `src/PaperExternalGiniTree.cpp` | `d51adc6dcab78042d5e3453d4e40cabe98e85567bfafbb97a14d2de90d0cb436` |
| `tests/round90_lp_g_split_tests.cpp` | `2dd4582bb757624228fb610a2c9b3cc55fec0b84dca892601ecc1bec83a58d4d` |
| `CMakeLists.txt` | `4d1ad96639e1ef8a4093174636a1ef8e4563519485fc7d0ee82af68696057de0` |

Source review focus: `src/PaperExternalGiniTree.cpp` binds parent optimal LP G to the current epoch and canonical model/interval before selection; it validates identical closed child endpoints before tolerance coverage, rejects mismatched same-id cache artifacts before any bound/AM decision, and keeps both child Optimize calls and AM action untouched. The pure cache predicate in `GiniFrontierGeometry` checks state/model identity, with the controller reading actual model SHA. The candidate ledger distinguishes a proposed point from completed child evidence and an actual atomic split or native-target requeue. Check default-off output labels and candidate-only contraction labels. `src/main.cpp` rejects non-ENS-C, non-frontier and A1/B1 combinations and assigns one effective identity across snapshot/final/emergency paths.

Compilation-only evidence: `results/unified_exact_round90/compile_configure_001.{json,log}` and `compile_build_001.{json,log}`. Isolated build dir `build/research/round90-lp-g-split`; configure exit 0 in 1.4680975 s, build exit 0 in 32.2208135 s. Built targets: `ExactEBRP`, `Round90LpGSplitTests`, `GlobalGiniTreeTests`, `Round47AdaptiveMassTests`, `Round83ExchangeDiagnostic`; **none was executed**. The build log ends with 79/79 targets linked. Its warnings are in existing Gurobi/Round61/Round62 dynamic-API code, not a Round90 compile failure. The prior Round89 `ExactEBRP.exe` remains SHA-256 `8d5f0ad4a3cf588875a6a3b8ac67c5bdbb2b2df54a5fd49bea56de2034a17e8d`.

| Compiled artifact | SHA-256 |
|---|---|
| `build/research/round90-lp-g-split/ExactEBRP.exe` | `c1218c9fa164e969019e60573385d028d3c0777e8273a3400ebf4906c505daa0` |
| `build/research/round90-lp-g-split/Round90LpGSplitTests.exe` | `0d48ab2fb738b1c54553112910eacb01c5f618c5e2bc77faa1233f1ef96019d5` |
| `build/research/round90-lp-g-split/GlobalGiniTreeTests.exe` | `12500347604a10f9217cbfc2d233d6e12445b38766852d1e717d49ba90bd44db` |
| `build/research/round90-lp-g-split/Round47AdaptiveMassTests.exe` | `7ee3883c93ed59593eae72f40fd081fd6a8f0120e6aa502b6def84585b6c1e08` |
| `build/research/round90-lp-g-split/Round83ExchangeDiagnostic.exe` | `9a2be000c0b4aa9a55726474151ce8c686f810d137e6bfc8f04d01f2a1a6d45f` |

Remaining gates are independent static review, then separately admitted execution of focused pure/legacy tests and actual-model identity/coverage qualification. A successful compile is not a solver or certificate result; no performance claim is made. No source copy, historical build edit, Git write, test execution or solver call occurred.

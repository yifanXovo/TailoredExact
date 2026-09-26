# Round89 native B1 — static review handoff

State at handoff: implementation and compile-only engineering are complete. **No tests, native toy Optimize, production Optimize, or LP audit executed.** Root owns Git and all future computation admission. The independent reviewer should inspect mathematical validity, actual two-link model identity, callback failure semantics, and default-off isolation before any micro-test.

## Frozen paths and SHA-256

| Path | SHA-256 |
|---|---|
| `include/NativeOtB1.hpp` | `bd64c92a83d109c602dbb31bd10bbba524db857bb357fee6ba26c7d8da3df0eb` |
| `src/NativeOtB1.cpp` | `e4722c675c6470d85f369a80304adace4403b61c579d95c6ff62594b8576ef0b` |
| `src/GurobiBaseline.cpp` | `3a677115a2e01c13826162691c1dbb474f081d813dfa11280c7b84ab04522f25` |
| `include/Instance.hpp` | `fd081f82b114fe2bc5c9a23d08f50c50977c148ef7406b2c536f88757f4bd720` |
| `include/FixedIntervalMipBackend.hpp` | `5b6a7539593932f84bd8927319a81e8b64fec4842db5414b80c954dec3a4564b` |
| `src/main.cpp` | `bde69286c291d74abb719e9f266cb994133319fdfa3b5d5c71478d9ef92c7e20` |
| `CMakeLists.txt` | `eda744ecf2bdacfd596a2e1f6686209ab1288bcd632dc9a815e8b7b743020fb7` |
| `tests/round89_native_ot_b1_micro.cpp` | `ecc1f117dd012b7a1ad49dacce9eb18139b77dd8b3d6905cafc3249f0bb2f83c` |
| `tests/round89_native_ot_b1_fraction_oracle.py` | `8dc60a8d43ae9645c07acd3a0cac793d745ad6c170f0e21517a32f64be4127e6` |

Compile-only binary SHA-256: `build/research/round89-native-ot-b1/ExactEBRP.exe` = `3f943bfce50b8ccdcf34e60a3012f9bd59fbe8fa59df2906929c4106736dcd8d`; `Round89NativeOtB1Micro.exe` = `2f50fa2b33667c8e9a8bfec7e77bf25bcc834a21d77a2303e3e24982e3eb529e`. Neither binary has been run.

## Scope and exact model check

The source edits are limited to the nine paths above. There is no edit to `CplexBaseline.cpp`, `PaperExternalGiniTree.cpp`, `Round50IntervalMip.cpp`, any Round88 tool, or any frozen binary. `NativeOtB1.cpp` checks one-hot, `Y_i−Σ y state_i_y`, `r_i−α_iY_i`, `−G+Σ state_g_i_y`, and both pairwise `h` lower rows as actual imported CSR rows before separation. It fails closed if the canonical SHA, leaf/scope/row signature, policy, original columns, types, bounds, linearity, matrix, PreCrush, or feasibility-tolerance readback is invalid. The identity test currently requires exact row coefficients matching this writer's exported integer `y` and equality RHS; it obtains the actual binary64 `α_i` from the imported `r/Y` row. This is intentional fail-closed behavior if a different exporter changes the chain. No original-row feasibility assumption is made about a callback relaxation vector.

The new CLI flag is false by default and R83-only; `effectiveAlgorithmIdentity` and the snapshot label identify the opt-in arm. Only `PaperTerminalMip` and `PaperPartialBoundTargetMip` activate the new callback path. The existing callback remains registered and retains MIPSOL evidence, bound-target, progress, verified-start, and R53 branches. Only the candidate sets `PreCrush=1`; the deadline is re-read with paid setup elapsed before Optimize. Callback API/evidence failure terminates the MIP and invalidates its proof outcome, while arithmetic-unsafe rows are counted as skips. Production writes one per-MIP source/count/status summary, with no per-node primal or full cut-row journal.

## Compile receipt and next qualification boundary

Compile slot was checked for foreign solver/build processes and released after completion. Configuration with Visual Studio's bundled CMake/Ninja, UCRT64 GCC 14.2, and Gurobi 13.0.2 headers succeeded in **1.747 s**. First `ExactEBRP` + `Round89NativeOtB1Micro` build took approximately **45.216 s** and failed because the micro-test attempted to take the address of macro `GRBemptyenv`. It was corrected to dynamically resolve `GRBemptyenvinternal`. Second build succeeded in **9.415 s**; an incremental build after receipt edits succeeded in **2.161 s**. Root's static spot-check then led to removing production full-cut journaling and adding actual fixed-interval-backend toy integration; the final compile succeeded in **8.779 s**. All attempts are preserved in `build/research/round89-native-ot-b1-{configure,build-attempt1,build-attempt2,build-attempt3,build-attempt4}.log`. The remaining `GetProcAddress` function-pointer cast warnings follow the repository's dynamic C API pattern; no compile error remains.

After static approval and a separate execution lease, the proposed micro sequence is: run `Round89NativeOtB1Micro.exe pure`; run `pure-json PATH` and then `tests/round89_native_ot_b1_fraction_oracle.py --fixture-json PATH --receipt PATH`; run `native D:/gurobi1302/win64/bin/gurobi130.dll RECEIPT` with exclusive solver slot. The native command runs **six** toy Optimize arms: direct API off/static/callback, followed by actual `FixedIntervalMipBackend` LP negative control/terminal/partial-target. The direct toy's artificial `Cuts=0` and other exposure settings must not enter production; the backend integration uses toy-only `Presolve=0` but otherwise the native production path. Confirm three-arm integer optima and original `h` witnesses, fractional root event, reliable B1 row and `GRBcbcut` return 0, and backend candidate activation only for the two MIP kinds. Then a separately admitted real-source identity/matrix audit and bounded screen can follow. No test result or speed claim is implied by this compile receipt.

## Targeted xhigh review repairs

After the first independent static review, the runtime arithmetic gate now performs volatile subnormal addition and reads MXCSR FTZ/DAZ bits; the pure test deliberately enables those bits and requires rejection. The exact Fraction oracle now checks gamma 3/5 products that genuinely round, both CDF sign orientations, and all 18 submitted-row integer evaluations. The C++ pure fixture checks coincident and adjacent knots, nonfinite bounds and support overflow. Structural row lookup indexes the imported CSR once by participating column, then checks exact candidate rows and ambiguity. Callback failure clears native bound events and target flags before the paper controller's trace emission. Production remains aggregate-only.

Compile-only attempts 5, 6 and 7 succeeded in 8.844 s, 3.090 s and 3.185 s; their unmodified logs are in the same build/research directory. No test or Optimize was run. The hashes above supersede the first static review snapshot and identify this targeted re-review candidate.

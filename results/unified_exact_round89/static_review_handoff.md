# Round89 native B1 — static review handoff

State at handoff: implementation and compile-only engineering are complete. **No tests, native toy Optimize, production Optimize, or LP audit executed.** Root owns Git and all future computation admission. The independent reviewer should inspect mathematical validity, actual two-link model identity, callback failure semantics, and default-off isolation before any micro-test.

## Frozen paths and SHA-256

| Path | SHA-256 |
|---|---|
| `include/NativeOtB1.hpp` | `bd64c92a83d109c602dbb31bd10bbba524db857bb357fee6ba26c7d8da3df0eb` |
| `src/NativeOtB1.cpp` | `e4722c675c6470d85f369a80304adace4403b61c579d95c6ff62594b8576ef0b` |
| `src/GurobiBaseline.cpp` | `b12aa28adae1792b3ba7d3f75cedfec3ffc926410fe9a0f6daa0784b192a0eab` |
| `include/Instance.hpp` | `fd081f82b114fe2bc5c9a23d08f50c50977c148ef7406b2c536f88757f4bd720` |
| `include/FixedIntervalMipBackend.hpp` | `7c0f5e30752c64893cacfdb710930a72f477bef0928d5c89fb3ed0246d77756c` |
| `src/main.cpp` | `bde69286c291d74abb719e9f266cb994133319fdfa3b5d5c71478d9ef92c7e20` |
| `CMakeLists.txt` | `eda744ecf2bdacfd596a2e1f6686209ab1288bcd632dc9a815e8b7b743020fb7` |
| `tests/round89_native_ot_b1_micro.cpp` | `24e5b6c49dfa91108e1e1f4f538cc7c9a3a0564888670a02ce4fe8ac5b82d2e0` |
| `tests/round89_native_ot_b1_fraction_oracle.py` | `c772ea7a25f43f5027298e14f42a7ff32681ae17a71291a894b1ac8bb4926caf` |

Compile-only binary SHA-256: `build/research/round89-native-ot-b1/ExactEBRP.exe` = `8d5f0ad4a3cf588875a6a3b8ac67c5bdbb2b2df54a5fd49bea56de2034a17e8d`; `Round89NativeOtB1Micro.exe` = `678780b1109469080068720ad076be43589ccda164dff9c9f6004dc44803b947`. Neither binary has been run.

## Scope and exact model check

The source edits are limited to the nine paths above. There is no edit to `CplexBaseline.cpp`, `PaperExternalGiniTree.cpp`, `Round50IntervalMip.cpp`, any Round88 tool, or any frozen binary. `NativeOtB1.cpp` checks one-hot, `Y_i−Σ y state_i_y`, `r_i−α_iY_i`, `−G+Σ state_g_i_y`, and both pairwise `h` lower rows as actual imported CSR rows before separation. It fails closed if the canonical SHA, leaf/scope/row signature, policy, original columns, types, bounds, linearity, matrix, PreCrush, or feasibility-tolerance readback is invalid. The identity test currently requires exact row coefficients matching this writer's exported integer `y` and equality RHS; it obtains the actual binary64 `α_i` from the imported `r/Y` row. This is intentional fail-closed behavior if a different exporter changes the chain. No original-row feasibility assumption is made about a callback relaxation vector.

The new CLI flag is false by default and R83-only; `effectiveAlgorithmIdentity` and the snapshot label identify the opt-in arm. Only `PaperTerminalMip` and `PaperPartialBoundTargetMip` activate the new callback path. The existing callback remains registered and retains MIPSOL evidence, bound-target, progress, verified-start, and R53 branches. Only the candidate sets `PreCrush=1`; the deadline is re-read with paid setup elapsed before Optimize. Callback API/evidence failure terminates the MIP; any candidate engineering failure invalidates proof and native trace eligibility, while arithmetic-unsafe rows are counted as skips. Production writes one per-MIP source/count/status summary, with no per-node primal or full cut-row journal.

## Compile receipt and next qualification boundary

Compile slot was checked for foreign solver/build processes and released after completion. Configuration with Visual Studio's bundled CMake/Ninja, UCRT64 GCC 14.2, and Gurobi 13.0.2 headers succeeded in **1.747 s**. First `ExactEBRP` + `Round89NativeOtB1Micro` build took approximately **45.216 s** and failed because the micro-test attempted to take the address of macro `GRBemptyenv`. It was corrected to dynamically resolve `GRBemptyenvinternal`. Second build succeeded in **9.415 s**; an incremental build after receipt edits succeeded in **2.161 s**. Root's static spot-check then led to removing production full-cut journaling and adding actual fixed-interval-backend toy integration; the final compile succeeded in **8.779 s**. All attempts are preserved in `build/research/round89-native-ot-b1-{configure,build-attempt1,build-attempt2,build-attempt3,build-attempt4}.log`. The remaining `GetProcAddress` function-pointer cast warnings follow the repository's dynamic C API pattern; no compile error remains.

After static approval and a separate execution lease, the proposed micro sequence is: run `Round89NativeOtB1Micro.exe pure`; run `pure-json PATH` and then `tests/round89_native_ot_b1_fraction_oracle.py --fixture-json PATH --receipt PATH`; run `native D:/gurobi1302/win64/bin/gurobi130.dll RECEIPT` with exclusive solver slot. The native command runs **six** toy Optimize arms: direct API off/static/callback, followed by actual `FixedIntervalMipBackend` LP negative control/terminal/partial-target. The direct toy's artificial `Cuts=0` and other exposure settings must not enter production; the backend integration uses toy-only `Presolve=0` but otherwise the native production path. Confirm three-arm integer optima and original `h` witnesses, fractional root event, reliable B1 row and `GRBcbcut` return 0, and backend candidate activation only for the two MIP kinds. Then a separately admitted real-source identity/matrix audit and bounded screen can follow. No test result or speed claim is implied by this compile receipt.

## Targeted xhigh review repairs

After the first independent static review, the runtime arithmetic gate now performs volatile subnormal addition and reads MXCSR FTZ/DAZ bits; the pure test deliberately enables those bits and requires rejection. The exact Fraction oracle now checks gamma 3/5 products that genuinely round, both CDF sign orientations, 18 small-fixture and 36 genuine-rounded wide-fixture submitted-row integer evaluations. The C++ pure fixture checks coincident and adjacent knots, nonfinite bounds and support overflow. Structural row lookup indexes the imported CSR once by participating column, then checks exact candidate rows and ambiguity. Callback failure clears native bound events and target flags before the paper controller's trace emission. Production remains aggregate-only.

Compile-only attempts 5, 6 and 7 succeeded in 8.844 s, 3.090 s and 3.185 s; their unmodified logs are in the same build/research directory. No test or Optimize was run. The hashes above supersede the first static review snapshot and identify this targeted re-review candidate.

Second targeted static review exposed two further boundaries. The pure JSON now contains a submitted reliable B1 row from the six-state wide model, and the Fraction oracle checks its actual gamma-alpha dyadic supports and submitted binary64 coefficients/RHS at all 36 integer state pairs, in addition to the original 18 checks. The Round89-only final gate now invalidates proof bits and native trace events for any final external-gate failure (including native log API or domain restoration), not merely callback failure. A synthetic failure outcome and successful-outcome negative control were added to the pure micro-test. Compile-only attempt 8 succeeded in 9.378 s; no test or Optimize has run. All hashes above are the final candidate for this additional static review.

A final Status API boundary is now candidate-gated: a failed GRB_INT_ATTR_STATUS read or unsupported status becomes an explicit external-gate failure, followed by the same Round89-only proof/trace invalidation. The pure micro-test adds a synthetic Status-read failure receipt alongside the log-parameter failure. Compile-only attempt 9 succeeded in 8.601 s; final source and binary hashes are those in the table above. Executable tests and Optimize remain unrun.

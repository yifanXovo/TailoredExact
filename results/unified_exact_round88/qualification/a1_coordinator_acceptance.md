# A1 qualification decision

On 2026-09-26, the coordinator read the final source/test diff, independent review, and actual `a1_ctest_final.log`. All eight current file hashes match both the independent-review snapshot and `a1_source_hashes.json`. The executable hash also matches `a1_build.json`: `23d4fd53602d46f599f3f58e33c3ec96c4eec01b972e22ee0d4815cc42a54693`.

The 11 tests passed. The source preserves default ENS-C, changes only admission of the 24 initial orders when the explicit A1 switch is enabled, reuses its constructive descent and physical closure, and reaches the same complete exact-proof machinery. The tiny positive-objective CLI result verifies original-problem certification, while the nontrivial descent fixture compares the complete constructive path and physically verifies its output. Illegal combinations and emergency candidate identity are covered.

Decision: **qualified for the preregistered limited G3 comparison**, conditional on separate runner identity/cost review. This is not a performance acceptance or a promotion. Verified-zero early termination and shared global-deadline interruption use unchanged inherited code; the new switch has no separate qualification fixture for these paths. An interrupted descent must remain explicitly incomplete and cannot be reported as a completed local optimum. The forthcoming runner must preserve these distinctions.

Development build and qualification costs are recorded separately. No performance process has been started at this decision. Freeze the reviewed source in Git before preparing the final run manifest; any subsequent source change invalidates this executable's source match until reviewed and rebuilt.

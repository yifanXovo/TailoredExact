# C1 qualification decision

C1 completed the frozen nine-state 120-second core screen and all fourteen development states at 300 seconds with the same executable as v0 (`c847cf26a11da3e8d43a26f8c74afeb6625ee2a29628aaec06ab27f0b2dc65dd`). The model-delta audit proved that every candidate LP retained the identical objective, bounds, types, and every nonduplicate constraint; 51 second copies of zero-bound pickup/drop mode links were omitted over D1–D14.

The candidate did not materially improve a hard role. Excluding the invalid D12 terminal row, aggregate paired Work was 0.99956 of v0; individual exact rows were essentially identical, D11 improved only 0.47%, and D14 worsened 0.13%.

D12 is decisive. V0 strictly certified. C1's native solver returned `OPTIMAL`, but the native lower bound `0.64711626273386547` and independently verified original-objective upper bound `0.64711643345550207` differed by `1.707216366e-7`, above the frozen `1e-7` certificate tolerance. `result.json` correctly rejected the certificate. A duplicated completion-path predicate incorrectly wrote `exact` to the completion marker; that evidence inconsistency is preserved and the predicate has been corrected for future builds. The candidate row was not rewritten or upgraded.

C1 is rejected and the active formulation remains the original Interval-MIP-v0 cut/formulation pack. C2–C4 remain closed for the mathematical reasons in the audit gate: no complete delayed separator, no additional analytic tightening proof, and no isolated unaddressed relaxation defect.

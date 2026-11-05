# Target-coupling admission: unqualified stabilization fallback addendum

Reviewer: `/root/review_round154`, independent of implementation.
Disposition: **ACCEPT_THE_UNIFORM_SOURCE_REPAIR**. The active admission source
SHA is updated to
84ed0005049137bfb9dd88ac95dca8fa492666a277f332833f001f9bda1bd958.
The original gate is retained as
target_coupling_admission_before_basic_fallback.json; its qualified
Native target-stop interface and runtime limits remain unchanged.

The reviewer read the actual revised loop and the small saved failure
records. It ran no Optimize, model read, enumeration, compilation,
large pool scan or performance experiment.

K-35-U_target_residual_v1 completed an optimal current RMP:
its iter00000 RMP return is Status2 with about30.04 Native seconds.
The separate zero-center stabilization LP then returned Status9 at
120 seconds with solution_count0. The old assertion therefore ended
the outer before any inventory price. Its retained receipt is exit1,
178.80874749994837 seconds, no timeout/supervisor failure. This is a
failed direction-selection attempt, not a qualified negative oracle,
target refutation or completed K35 coupling phase. No unreturned price
bound or successful endpoint is inferred from it.

The repair acts only when select_dual returns None, meaning no eligible
selected candidate was obtained. It then reads c.Pi from the already
optimal current original RMP. The stabilization problem is a separate
model, so its failed candidate does not replace those optimal-RMP
multipliers. The source records current_basic_RMP_dual_after_unqualified_selection,
the selection status and saved selection SHA. A successful stabilization
continues to use its old selected candidate.

Both paths derive a/pi/beta and pass the same full original-Q residual
support and true-column a_K qualification. Price lower conversion,
zero/DP handling, target/ceiling test, support transport, all-stock
validation and final RMP refresh are unchanged. A numerical basic
dual is not itself promoted to a new full-hull lower. An unqualified
stabilization contributes no bound.

This is a uniform candidate-qualification fallback for either role,
with no instance/winner/size branch. The existing offline selection cap
is not a new production component switch after k seconds. The plan's
dual_rule and per-direction selection_method now disclose the fallback;
future reports must not describe a fallback direction as the result of
successful zero-center minimization.

The admitted8-iteration/600-second price/6000-second phase/tolerance1e-4
rule and serial outer-cost policy remain. Failed raw bytes and costs
remain retained, and any continuation uses a new paid phase identity.
The B/E/J production/helper/matrix chain is unchanged.


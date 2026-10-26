# Round 55 split-failure causal analysis

The frozen VD-P inner candidate failed the full K1 integration gate despite favorable aggregate performance: it produced 14 versus 12 effective certificates, shifted-Work geometric-mean ratio 0.5691998368030589, and aggregate GI ratio 0.6090974547960206, with zero false certificates and no V20/V50 material regression. The failure is the single severe regression on `round39_small_medium_V12_M3_Q30_slot08_seed1343324363`, which is the predeclared major-regression witness; therefore `major_repair_preserved=false`.

The complete adaptive-action diff contains materially changed actions on three other inputs: `round39_small_hard_V12_M3_Q30_slot08_seed1288546114`, `round39_small_hard_V12_M2_Q20_slot06_seed258908503`, and `moderate_seed3301`. The severe witness itself has only a bound-or-telemetry difference and no materially changed action. Consequently matched evidence does not link the K1 failure to a changed balanced-normalized-closure action. The Stage 22 causal entry condition is false, restricted-parent counterfactuals were not run, and their matrix is intentionally header-only.

No clean uniform split revision is authorized by this evidence. The original midpoint, balanced-normalized-closure rule with tau=0.08 is retained unchanged. Restricted-range diagnostics are not original-problem certificates.

# Objective Estimator Proof Notes

- Existing bucket-tight row `H + V*S_U^b*lambda*P <= V*S_U^b*(UB-eps)` is paper-safe as a necessary no-improver condition using the bucket-local upper bound on `S`.
- Candidate lower-S guarded row is rejected for paper evidence: replacing `S` by `S_L` can be too strong in the positive penalty term and may cut feasible improving points.
- P upper bound from `G >= gamma_L`, `P <= (UB-eps-gamma_L)/lambda`, is valid when lambda is positive; the implementation keeps this as existing cutoff/domain logic rather than a new certificate source.
- H upper cap `H <= V*gamma_U*S_U^b` is valid but dominated by direct Gini cap plus bucket S rows when both are present.
- H lower row is only paper-safe when H is exact absolute-spread sum; because H may be represented through upper-envelope auxiliaries in parts of the compact model, it remains diagnostic unless exactness is audited.
- Bucket-tight `S*P` McCormick rows are paper-safe relaxations under audited bucket-local `S` and penalty bounds.

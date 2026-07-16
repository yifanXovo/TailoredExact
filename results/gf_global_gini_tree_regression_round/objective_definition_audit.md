# Objective-definition audit

The authoritative original objective is

\[
F(x)=G(x)+\lambda P(x),\qquad
P(x)=\sum_i w_i\left|Y_i/T_i-1\right|.
\]

Direct source audit found consistent semantics:

- `src/Result.cpp::computeObjectiveParts` computes ratios, weighted penalty,
  pairwise Gini numerator, `G`, and finally `G + lambda * P`;
- `src/CplexBaseline.cpp::writeCompactLp` writes objective coefficient 1 on
  `G` and `lambda * weight_i` on every `e_i`;
- `src/Evaluator.cpp` calls the same authoritative evaluator for independent
  route verification;
- the native MIP-start mapper independently recomputes the objective before
  accepting a complete mapping;
- JSON serializes `objective`, `gini`, and `penalty` separately, allowing every
  retained result to be rechecked numerically.

A targeted search of README, exactness/certification documents, paper-facing
documents, source, logs, and serialization found no statement defining the
problem as `P + lambda G`. Existing exactness text explicitly uses
`G + lambda P`. No optimization semantics were changed.

Required assumptions are now enforced at input boundaries:

- parser: every `T_i` is strictly positive;
- parser: every `w_i` is finite and nonnegative;
- CLI validation: `lambda` is finite and nonnegative.

The package audit recomputes `objective = gini + lambda * penalty` for every
fresh retained JSON row. Any mismatch invalidates the row.

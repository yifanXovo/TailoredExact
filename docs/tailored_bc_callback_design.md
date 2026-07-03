# Tailored BC Callback Design

The intended callback implementation has four callback roles:

- user cuts: separate violated Gini-frontier and inventory/domain cuts at root and branch nodes;
- lazy constraints: reject candidate incumbents that violate verifier/model conventions;
- incumbent callback: recompute objective and feasibility through the ExactEBRP evaluator;
- branch callback: prioritize unresolved Gini/denominator structure and interval selectors.

The current build reports callback availability through:

- `tailored_bc_callback_available`;
- `tailored_bc_user_cut_callback_enabled`;
- `tailored_bc_lazy_callback_enabled`;
- `tailored_bc_incumbent_callback_enabled`;
- `tailored_bc_branch_callback_enabled`;
- `tailored_bc_callback_fail_reason`.

When callbacks are unavailable, the executable must not report callback events or callback certificate evidence. The fallback source class is `static_fallback`.

The current implemented callback path is minimal and fixed-interval only. It uses the existing LP writer, loads that LP into CPLEX through the dynamically loaded C API, and registers a generic callback. The first paper-safe user cut is redundant by design: `G <= gamma_U`, matching the fixed interval cap. This gives a safe callback smoke test before stronger hard-leaf cut separation is added.

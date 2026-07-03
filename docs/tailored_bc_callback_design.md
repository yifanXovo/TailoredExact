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

The current implemented callback path is minimal and fixed-interval only. It uses the existing LP writer, loads that LP into CPLEX through the dynamically loaded C API, and registers a generic callback. Relaxation callbacks can add the fixed Gini cap `G <= gamma_U`, inspect the relaxation point, and separate paper-safe visit-inventory linking rows, Gini subset-envelope rows, and the aggregate low-Gini L1 centering row when they are violated. Candidate callbacks extract candidate points and check that the reported `G` value stays inside the fixed interval; a numerical violation is rejected by re-adding the corresponding Gini interval row as a lazy candidate rejection. Branch-order priorities are applied through `CPXcopyorder` to compact model binary variables.

This still is not the full hard-leaf tailored BC design. Candidate validation is interval-consistency validation, not independent route-plan verification through the ExactEBRP evaluator. Custom Gini branch creation is implemented as a one-shot generic branch callback path but has not yet been observed or validated on hard leaves. The callback-separated visit-inventory, Gini subset-envelope, and low-Gini L1 cuts share the same proofs as the static rows, but they have only been exercised in smoke diagnostics so far.

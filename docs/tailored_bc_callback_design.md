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

The current implemented callback path is minimal and fixed-interval only. It uses the existing LP writer, loads that LP into CPLEX through the dynamically loaded C API, and registers a generic callback. Relaxation callbacks can add the fixed Gini cap `G <= gamma_U`, inspect the relaxation point, and separate paper-safe visit-inventory linking rows, Gini subset-envelope rows, the aggregate low-Gini L1 centering row, conservative subset-inventory imbalance rows, basic vehicle transfer cutset rows, and pair/triple/quad support-duration cover rows with conservative lifted right-hand sides when they are violated. Candidate callbacks extract candidate points and check that the reported `G` value stays inside the fixed interval and that the candidate satisfies the same visit-inventory, Gini subset-envelope, low-Gini L1, and subset-inventory rows. They also run two compact projection verifiers when the required variables are available:

- a route/service projection verifier for station disjointness, depot start/end flow, station flow, pickup/drop service linking, route duration under the current pickup-only handling convention, final-inventory balance, and reconstructed route load order;
- a final-inventory/objective projection verifier that recomputes `r_i`, penalty, Gini, and objective from `Y_i`.

A numerical violation is rejected only by re-adding an already-valid model row as a lazy candidate rejection. If route-load reconstruction or Gini/objective projection exposes a mismatch for which no safe generic lazy row is available, the callback records an unsupported mismatch and does not count the candidate as callback-verified. Branch-order priorities are applied through `CPXcopyorder` to compact model binary variables.

The callback round also includes `tailored-bc-branch-callback-smoke-test`, a diagnostic-only CPLEX toy MIP intended to exercise the generic branch callback boundary.  The current result applies branch priorities, records relaxation/candidate callbacks, enters CPLEX branch context, and creates two one-shot Gini branches.  This is reported as `diagnostic_passed`; it is not paper certificate evidence.

The model builder also exposes a diagnostic-only Benders-like inventory capacity row family through `--tailored-bc-benders-inventory-cuts diagnostic`. These rows are aggregate receiver-set capacity cuts, not callback cuts, and are deliberately excluded from paper-core presets and certificate claims until a full transfer-network min-cut proof and projection tests are available.

This still is not the full hard-leaf tailored BC design. Candidate validation is stronger than compact-row consistency because it now reconstructs route/service projections from compact variables, but it is still not independent route-plan verification through the ExactEBRP evaluator. Custom Gini branch creation is observed in a diagnostic toy MIP and in moderate low-Gini hard-leaf diagnostics. The callback-separated visit-inventory, Gini subset-envelope, low-Gini L1, subset-inventory imbalance, basic transfer-cutset, and lifted pair/triple/quad support-duration cover cuts share the same proofs as the static paper-safe rows, but hard-leaf closure evidence remains incomplete.

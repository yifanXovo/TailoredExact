# Transfer-Network Cut Proof Status

The basic empty-start vehicle transfer cutset remains paper-safe:

`sum_{j in D} d[k,j] - sum_{j in D} p[k,j] <= sum_{i notin D} p[k,i]`.

It states that positive net delivery into receiver set `D` by a vehicle must be sourced by pickups outside `D`, because vehicles start empty. The current validity smoke test for the basic transfer cutset passes.

The stronger Benders-like transfer-network inventory cuts are not promoted in this round. A paper-safe promotion still requires a conservative transfer network whose capacity into `D` is a true upper bound for every feasible route-load plan. Safe ingredients may include vehicle capacity, station inventory/room, pickup-only handling budgets, and depot-cycle lower bounds used only conservatively.

The current diagnostic Benders-like rows do not yet have:

- a complete min-cut proof for all emitted rows;
- randomized feasible route-load projection tests;
- no-false-rejection tests against small certified instances;
- candidate callback rejection proof for every rejected candidate;
- full paper-core audit flags proving no diagnostic row entered a certificate.

Therefore `paper_safe_transfer_network_cut=false` in `results/gf_tailored_bc_optimization_round/transfer_network_cut_audit.csv`.

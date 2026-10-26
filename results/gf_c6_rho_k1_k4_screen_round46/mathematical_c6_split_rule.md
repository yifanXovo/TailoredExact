# Round 46 mathematical C6 split rule

Round 46 changes only the scalar normalized split threshold `rho` and the
initial cover size `K0`. It preserves the existing pure-C6 midpoint lifecycle,
normalization, tolerances, coverage replacement, and certificate logic.

For a selected parent interval with valid lower bound `B_p`, verified incumbent
`U`, and terminal midpoint child-LP outcomes, let `B_L` and `B_R` be the finite
child lower bounds. An infeasible child is omitted from the finite minimum. For
two feasible children the post-split lower bound is

    B_post = min(B_L, B_R).

The strict child improvement is `Delta = B_post - B_p`. With certificate
tolerance `epsilon_cert = 1e-7`, the active implementation defines

    proof_gap = max(U - B_p, max(epsilon_cert, 1e-12))
    normalized_gain = Delta / proof_gap.

The implementation compares with a `1e-15` floating-point guard:

    normalized_gain + 1e-15 >= rho.

The deterministic actions are:

1. If either terminal child LP is infeasible, take the existing structural
   split action independently of `rho`.
2. If `Delta > epsilon_cert` and the normalized gain reaches `rho`, atomically
   replace the parent coverage by its two midpoint children.
3. If `Delta > epsilon_cert` but the normalized gain is below `rho`, retain the
   parent coverage and run the existing native parent MIP toward target
   `B_post`; later requeue/reconsideration behavior is unchanged.
4. If `Delta <= epsilon_cert`, retain coverage and launch the existing exact
   parent closure.

All child outcomes must be terminal-valid and either infeasible or optimal with
a finite available lower bound. Invalid evidence fails closed. K1-adaptive and
K4 call this identical evaluator; they differ only in whether the initial
strict-improver range has one interval or the historical four-interval cover.
The paper-facing preset and the Round 44/45 historical old-C6 reconstruction
remain fixed at `rho=0.01`.

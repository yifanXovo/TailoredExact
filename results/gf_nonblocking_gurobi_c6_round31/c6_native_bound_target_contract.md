# C6 native-bound target contract

For selected relevant leaf `I`, let `b_I` be its current valid lower bound and
let `B` be the multiset of valid lower bounds of all other nonreplaced,
relevant leaves after the complete parent-LP merge.

- If any `b in B` satisfies `b + tol < b_I`, retain and requeue `I`.
- Otherwise, if the leaf has not completed its frontier milestone, define
  `target = min { b in B : b > b_I + tol }`.
- If that set is empty, authorize lazy child lookahead.
- Ties within tolerance do not become targets.
- A target is frozen at launch and must be finite and strictly greater than
  the launch bound.
- The backend observes `GRB_CB_MIP_OBJBND`. It requests termination only
  after a validity-gated native bound reaches the target within certificate
  tolerance.
- The returned bound is merged monotonically. Target attainment changes an
  open state; it is not exact closure.
- Optimality or infeasibility may close. Overall deadline interruption leaves
  the interval open with the last valid bound.

For a strict current child gain below rho, the same contract applies with
`target = min(B_left, B_right)` from two complete child LPs. Reaching that
target retains the parent and cached children; it never forces a split.

No elapsed time, Work, node, solution, attempt, retry, family, size, seed,
path, or historical objective participates in either target.

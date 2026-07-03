# Gini Interval Split Policy

The implemented and evaluated policies are:

- `off`: no custom Gini branching inside the fixed interval.
- `callback_auto`: use the generic CPLEX branch callback when the in-process API enters branch context.
- `selector`: request selector-style Gini branching mode. In the current implementation this remains diagnostic unless the emitted row proves selector variables and coverage.
- `outer_controller`: the existing full Gini-frontier ledger controller, which is certificate-capable only when child intervals exactly cover the parent and all children close or fathom.

This round did not promote a new default split policy. The hard fixed-interval rows did not finalize under short wrapper caps, so no policy produced trustworthy bound movement on the hard leaves. The safe recommendation is:

1. Keep the current default for paper rows.
2. Treat callback and selector Gini branch modes as diagnostics until hard-leaf finalization is reliable.
3. Use the outer-controller only through the audited full-frontier ledger, never as an ad hoc timeout switch.

Future split-policy comparisons should use the same fixed intervals, one-thread settings, and completed solver-final or checkpointed bound artifacts.

## Next Optimization Round Note

The next-optimization hard-leaf runs confirmed that callback Gini branching can receive callback contexts, but the moderate low-Gini leaves did not expose a valid final best bound before wrapper termination. No new Gini split policy is promoted to paper default from those diagnostics. Any split-policy result without a solver-final or valid checkpointed bound remains diagnostic.

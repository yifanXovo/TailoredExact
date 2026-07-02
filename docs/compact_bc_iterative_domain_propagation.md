# Compact-BC Domain Propagation

The new options are:

- `--compact-bc-domain-propagation-mode off|static|iterative`;
- `--compact-bc-domain-propagation-rounds <N>`.

The current implementation applies the existing safe domain rules during model
generation and records the requested/active mode. The current domain rules are:

- penalty-budget final-inventory domains;
- movement-reachability final-inventory domains;
- low-Gini ratio-band domain tightening where enabled.

Repeated propagation is conservative: the current rules reach a fixed point in
one model-generation pass for the implemented families. Future work should add
new implications before increasing `rounds_completed` beyond one.

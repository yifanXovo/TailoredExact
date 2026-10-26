# Strengthening roadmap

This roadmap was frozen independently of the Round 54 runtime outcome. Round 54
implemented only Track A.

| Priority | Track | Motivation and expected benefit | Cost / parameters | Exactness, panel, stop condition, dependencies |
|---:|---|---|---|---|
| 1 | A — Gini-induced inventory--route cutsets | Couple final-inventory displacement to directed route capacity; potentially strengthen weak root LPs | Exact min-cuts plus fresh-model root closure; no tuning parameter | Prove global/local scope; census D/C/role/V50 states; stop if live Work/GI or certificates regress; depends on F0 freeze |
| 2 | B — value-disaggregated G times Y | Seek an ideal or tighter representation than binary-expansion products | Larger extended formulation; formulation granularity must be frozen before results | Prove projection equivalence; ablate on D1--D14 then confirmations; stop on memory/model-size or nonworse-gate failure; depends on a separate round and literature audit |
| 3 | C — V20/V50 proof tails | Determine proof-tail scalability after the final backend is frozen | 3,600-second ordinary rows and predeclared 7,200-second V50 extensions; no algorithm parameter | Matched sealed panel; stop if executable/source identity changes; depends on a promoted frozen backend |
| 4 | D — paper finalization | Attribute the benefit of active families and qualify novelty claims | Ablation matrix, literature review, final tables; no solver parameter | Preserve exactness/certificate audits; stop at reproducible table closure; depends on final backend |

## Round 54 disposition and one next step

IR1/IR2 were often violated and strengthened 25/34 frozen root states, so Track
A was not an offline-negative idea. However, selected IR1 lost two F0
certificates, worsened shifted Work geometric mean to 1.089432, and worsened
aggregate GI. Track A therefore stops as a bounded negative result.

**The single recommended next step is Track B:** study a value-disaggregated
ideal formulation for G times final inventory in a separately frozen round.
Do not reopen split gates, symmetry, branching priorities, Big-M tightening,
support-duration callbacks, or IR tuning in that round.

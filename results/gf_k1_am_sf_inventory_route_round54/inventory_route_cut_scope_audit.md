# Inventory-route cut scope audit

| Family | Scope | Bound dependence | Incumbent dependence | Round 54 status | Novelty wording |
|---|---|---|---|---|---|
| IR-IN | Global | None | None | Implemented in IR1/IR2 | Standard cutset technique adapted to this problem |
| IR-OUT | Global | None | None | Implemented in IR1/IR2 | Standard cutset technique adapted to this problem |
| IR-PROJ-IN | Interval-local | Lower inventory bounds `L_i` | Possible, through the bound proof | Implemented only in IR2 and suppressed when dominated | Potentially novel; literature review required |
| IR-PROJ-OUT | Interval-local | Upper inventory bounds `U_i` | Possible, through the bound proof | Implemented only in IR2 and suppressed when dominated | Potentially novel; literature review required |
| Cardinality companions | Not established here | Would depend on projected deficit | Possible | Not implemented | No novelty claim |

Mixed rows may be reused across intervals because their proof refers only to original route and inventory variables. Projected rows must not leak between intervals or incumbent epochs. The external closure keeps a per-model pool, and each terminal model is freshly built before its validated pool is added.

No literature search in Round 54 establishes novelty. The potentially novel label is deliberately provisional and cannot support a paper novelty claim.

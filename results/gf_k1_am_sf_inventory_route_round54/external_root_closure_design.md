# External root cutting-plane closure

IR1 performs full exact closure over mixed IR-IN and IR-OUT rows. IR2 performs the same closure and additionally admits nondominated interval-local projected rows. The conditionally predeclared IR3 performs one exact pass and may add at most the most violated inbound and outbound mixed rows.

Every closure round reads an immutable base F0-CLEAN artifact into a fresh Gurobi model, converts integer types to continuous types for the LP, adds the complete validated row pool, and solves. A separate freshly read integer model receives that same pool for the terminal solve. This construction avoids mutation leakage and makes integer-type restoration auditable.

Acceptance requires finite primal data, exact separator reconstruction, a directly recomputed strict violation, a new canonical signature, and correct scope. Repeated signatures, a numerical inconsistency, invalid reconstruction, a nonfinite LP result, a coefficient/name mismatch, or a row-count readback mismatch invalidate the candidate run. The runner then uses exact F0-CLEAN without inventory-route rows; that fallback protects correctness but is excluded from support for the new family.

The mathematical loop has no time-, Work-, node-, memory-, size-, instance-, `M`-, or `Q`-based stopping rule. Any external process cap is an experiment safety cap and produces an incomplete/invalid census row rather than a truncated closure certificate.

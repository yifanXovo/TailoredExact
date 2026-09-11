# Inventory-route cut validity proof

Let `A` be a nonempty subset of stations; the depot is not in `A`. For vehicle `k`, sum load conservation over all visits whose station belongs to `A`. Internal movements cancel. The remaining identity says that the vehicle's net delivery into `A` equals the load carried across arcs entering `A` minus the load carried across arcs leaving `A`.

Loads on leaving arcs are nonnegative, and the load on every arc of vehicle `k` is at most its capacity `Q_k`. Therefore the net delivery by `k` into `A` is at most

`Q_k * sum_{u notin A, v in A} x_kuv`.

Summing over vehicles and substituting station inventory balance,

`Y_i - b_i = sum_k (d_ki - p_ki)`,

gives the globally valid mixed inequality

`sum_{i in A}(Y_i-b_i) <= sum_k Q_k delta_k^-(A)` (IR-IN).

Applying the symmetric argument to net pickup from `A`—or negating the delivery identity—bounds it by capacity on arcs leaving `A` and gives

`sum_{i in A}(b_i-Y_i) <= sum_k Q_k delta_k^+(A)` (IR-OUT).

The proof uses no equal-capacity assumption: each boundary term retains its vehicle-specific `Q_k`.

For an interval state with valid inventory bounds `Y_i >= L_i` and `Y_i <= U_i`, IR-IN implies

`sum_k Q_k delta_k^-(A) >= max(0, sum_{i in A}(L_i-b_i))`,

and IR-OUT implies

`sum_k Q_k delta_k^+(A) >= max(0, sum_{i in A}(b_i-U_i))`.

These projected companions are valid only for the interval/incumbent epoch from which `L` and `U` were proved. The mixed inequalities are globally valid. No optional cardinality companion is implemented in Round 54.

The implementation directly reconstructs every returned subset and recomputes its left side, right side, and violation before accepting a row. Nonfinite values, reconstruction mismatch, or a false strict violation invalidate the candidate closure and require an exact F0-CLEAN fallback; fallback results are not positive evidence for the strengthening.

# Round 50 numerical-audit correction

Round 50 reported that its bounded search found no analytic numerical candidate worth opening. That conclusion remains part of the immutable Round 50 historical record and is not edited here.

Round 51 identified a narrower issue that the Round 50 audit did not isolate: the strengthened `V <= 12` exhaustive subset-duration conditional rows used the hard-coded coefficient `100000.0`, even though the writer had already computed the row-specific subset tour lower bound `tsp[mask]`. The formal argument in `big_m_validity_proof.md` shows that `M_S = max(0,tsp[S])` is sufficient for the existing conditional-row construction under the frozen formulation's nonnegative-distance, global-duration, and pickup/visit-linking assumptions.

This is a prospective correction to the interpretation of the Round 50 numerical search, not a retroactive change to its evidence. M1 is explicit and default-off: every historical Round 50 policy retains `100000.0`, while only named `m1-*` policies request the analytic coefficient. The Round 51 model-delta audit must show that no objective, domain, row sense, symmetry row, interval row, cutoff row, or non-target coefficient changes. Performance conclusions remain forbidden until that audit and the small exact validation pass.

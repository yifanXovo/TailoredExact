# BPC Cut Separation

The BPC preset records cut-family and separation-round settings:

- station-operation;
- subset-row;
- inventory-domain;
- duration-cover;
- transfer-compat;
- Gini-interval.

This round mainly improves diagnostics. The validation tables show `cuts_added=0` on the tested leaves, so cut separation is not yet materially improving RMP bounds.

Paper status:

BPC cuts remain a valid part of the intended algorithm, but empirical claims must state that this implementation did not close leaves via cuts in this round.


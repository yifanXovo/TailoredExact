# Receiver-Set Source-Cover Proof

The old aggregate receiver-cover form can be invalid because stations inside a receiver set may exchange bikes internally. It is therefore not enabled as a paper-core cut.

The implemented paper-safe singleton rule is narrower. If tightened final-inventory domains imply `Y_j >= L_j` and `L_j > initial_j`, then any original feasible solution must have total drops into station `j` at least `L_j - initial_j`, because `Y_j = initial_j - pickups_j + drops_j` and `pickups_j >= 0`. The valid row is `sum_k d[k,j] >= L_j - initial_j`.

Pair receiver-set source-cover cuts remain diagnostic/off until the internal-transfer issue is fully handled.

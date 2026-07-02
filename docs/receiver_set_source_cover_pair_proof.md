# Receiver-Set Source-Cover Pair Proof Status

The singleton receiver-source-cover cut remains paper-safe under the current
empty-start, one-service-mode station convention.

For a receiver station `j` with tightened lower inventory bound `L_j`, required
net delivery is `R_j = max(0, L_j - initial_j)`. A vehicle dropping at `j` must
source bikes from compatible pickup stations. The implemented singleton rows
preserve feasible internal model behavior and are valid paper-core cuts.

Pair/set receiver cover is not enabled as paper-core evidence in this round.
The simple drop-cover form is unsafe because transfers internal to the receiver
set can satisfy drops without outside pickups. The proposed net formulation is
promising:

`sum_{j in D} d[k,j] - sum_{j in D} p[k,j] <= outside compatible pickups`

but the compatibility superset proof and feasible-route projection tests are
not complete enough for paper-core use. Pair/set mode therefore remains
diagnostic only.


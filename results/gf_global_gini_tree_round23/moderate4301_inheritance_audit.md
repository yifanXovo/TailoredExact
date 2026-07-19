# moderate4301 inheritance audit

The root split has exact closed-interval coverage. The valid HGA witness has
G in the upper child (UID 2). Canonical inherited-state construction and
bound packing succeeded, and the child was returned by `makeBranch`; however,
UID 2 never reached its first relaxation, so deferred rows and post-row
reoptimization were never invoked for that child. The only processed sibling
was UID 1, which inherited and attached its rows successfully. Eager-row and
reduction-switch diagnostics reproduced the loss, while presolve-off S0/S1
processed many siblings through the native deadline. Thus inheritance and
deferred-row lifecycle are not the first failing invariants.

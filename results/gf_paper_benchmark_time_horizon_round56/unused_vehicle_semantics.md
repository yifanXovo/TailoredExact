# Unused-vehicle semantics

The formulation permits any available vehicle to remain unused; increasing M
does not require extra routes. In the authoritative archive every vehicle index
is represented. An unused index is materialized as `used=false`, `nodes=[0,0]`,
and an empty operation sequence with zero load, travel, operation, duration,
and utilization. This archive convention does not claim the native solver
selected a positive route for that vehicle. The Round56 test verifies the
original solution verifier accepts this depot-to-depot representation.

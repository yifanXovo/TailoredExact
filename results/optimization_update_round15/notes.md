# Round 15 Notes

Implemented projection-safe non-elementary relaxed route-load columns and relaxed-RMP CG reporting. Relaxed columns remain lower-bound-only and are blocked from incumbent/export paths.

CMake was unavailable. Fallback g++ builds succeeded for `ExactEBRP.exe` and `ExactEBRPCompare.exe`.

V4 gcap-frontier and V4 frontier-relaxed-rmp-cg-test both certified objective 0.

V12 and generated V20/V50/V100 rows remain noncertified or diagnostic. The relaxed path inserted non-elementary relaxed columns on V4, V12, and V20, but ng-relaxed pricing closure did not complete on the larger rows, so relaxed-RMP values remain diagnostic unless supported by another valid bound.

No memory/address errors were found in logs or raw outputs using patterns: access violation, segmentation, AddressSanitizer, out of memory, bad_alloc, ExactEBRP error.

CPLEX was skipped; no CPLEX speedup or comparison is claimed.

Known TODOs: complete true ng-relaxed state-space closure for V20+; improve large-instance relaxed column generation so V50/V100 produce nonzero diagnostic relaxed-RMP trajectories; investigate the V12 M2 full run where two-track relaxed columns did not improve the lower bound in this pass.

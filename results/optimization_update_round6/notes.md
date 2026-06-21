# Round 6 Notes

CMake was not available; fallback g++ build succeeded for ExactEBRP.exe and ExactEBRPCompare.exe.

Local runnable benchmark inputs were limited to:

- testdata/examples/gcap_smoke_V4_M1.txt
- reference/regen_candidate_V12_M1_average.txt
- reference/regen_candidate_V12_M2_average.txt

V8/V10 source text files were not found in this checkout. Plain CPLEX benchmarks were skipped in this pass.

No command exited nonzero. Captured stdout/stderr logs were scanned for memory and address failures: AddressSanitizer, access violation, segmentation/segfault, bad_alloc, out of memory, -1073741819, 3221225477, and STATUS_ACCESS_VIOLATION. No matches were found.

V4 gcap-frontier remains certified with objective 0, gap 0, verifier_passed true, unresolved_intervals 0, and open_nodes 0.

V12 results remain noncertified. Best round-six V12 rows:

- V12 M1 improved_full_300s: UB 0.367765009974, LB 0.281531929781, gap 0.234478750980.
- V12 M2 improved_full_300s: UB 0.719065249476, LB 0.585987841514, gap 0.185070003118.

Auto incumbents are upper-bound-only. Route-pool incumbent master is upper-bound-only. Transfer-cap flow and focused intensification are lower-bound progress mechanisms only. No positive-gap result is reported as optimal.

The progress-log implementation currently writes a final frontier checkpoint. It does not yet emit periodic 30-second checkpoints during the run; this is documented as a TODO.

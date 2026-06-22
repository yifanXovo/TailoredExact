# Round 12 notes

- This pass implements large-instance data-structure safety and scalable pricing diagnostics. It does not claim new original-problem certificates.
- CMake is unavailable in this environment; documented fallback g++ builds were used.
- Python is unavailable through the local `python` app alias, so deterministic generated benchmark files were produced with a PowerShell fallback after updating `scripts/generate_reference_instances.py`.
- V70/V100 parse, large-instance mode, dynamic `StationSet`, and ng-DSSR pricing diagnostics ran without crashes, access violations, segmentation faults, or `bad_alloc` messages in captured logs.
- Full gcap-frontier internals still use the established exact-label pricing path; the new hybrid/ng-DSSR engine is currently exercised through pricing diagnostics and is not yet a certifying replacement inside every BPC tree.
- V12 M1 and V12 M2 300s frontier rows remain noncertified because unresolved intervals remain.
- CPLEX was skipped; no CPLEX speedup or certificate comparison is reported.

# Round 13 notes

This pass wires explicit hybrid/ng-DSSR pricing requests through BPC column generation, tree, frontier, focused closure, and iterative closure paths. It also records BPC pricing-engine usage/fallback counters, DSSR memory/refinement counters, stabilization counters, and large-instance lower-bound scope fields.

CMake was not installed. The fallback `g++` build succeeded.

V4 `gcap-frontier` remains certified with objective 0 under exact-label and explicit hybrid. The hybrid V4 row used the hybrid engine and completed exact closure.

V12 M2 focus and full frontier rows remain noncertified. Hybrid reached the BPC pricing path with no fallback and returned elementary negative columns quickly, but DSSR did not prove exact closure. V12 M1 full frontier remains noncertified.

V20 generated hybrid frontier ran through the BPC hybrid path for 300s and remains nonclosed. V50 and V100 generated hybrid pricing diagnostics ran without mask overflow or memory/address failure signatures and correctly report incomplete DSSR/time-limit status.

`large-lb-test` on generated V100 reports a valid global movement-projection lower-bound scope, but the bound is zero for that instance. Restricted column-pool lower bounds remain diagnostic unless pricing closure proves no missing columns.

The external incumbent workflow was checked by exporting a verified V4 incumbent and re-importing it. A malformed V50 incumbent was rejected and did not update the incumbent.

Memory/address error scan: captured round-thirteen JSON/stdout/log files were scanned for AddressSanitizer, access violation, segmentation fault, segfault, bad_alloc, out of memory, fatal, exception, Traceback, and 0xC0000005 signatures. No matches were found except the intentional malformed-incumbent rejection note.

Plain CPLEX was skipped; no CPLEX speedup claims are made.

No new original-problem certificate was obtained beyond V4 smoke. V12 M1, V12 M2, V20, V50, and V100 rows remain noncertified or diagnostic.

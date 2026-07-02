# Large-V Compact-BC Diagnostic Report

Deterministic V50/V100 diagnostic instances are generated in `reference/large_diagnostics/manifest.csv`. The `paper-gf-compact-bc` V50 and V100 diagnostic rows hit `std::bad_alloc` during model/frontier construction before final solver JSON; wrapper error JSONs were written and are noncertified.

Plain single-thread compact CPLEX benchmark rows for one V50 and one V100 instance build and finalize, but remain noncertified. The compact-BC large-V blocker is therefore the frontier/interval model memory footprint, not the ability to parse or build a plain compact benchmark model.

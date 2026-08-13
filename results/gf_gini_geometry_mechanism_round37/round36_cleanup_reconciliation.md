# Round 36 cleanup reconciliation

The first cleanup pass removed 80 top-level local artifacts after proving that
the uncompressed trajectory was byte-identical to the committed deterministic
gzip. The subsequent full Python test sweep supplied new evidence: five frozen
Round 36 audit tests require `trajectory_events.csv` at its uncompressed local
path.

Under the cleanup rule that redundancy must be proved operationally, the file
is therefore not removable. It was restored from `trajectory_events.csv.gz` and
verified at 19,180,901 bytes with SHA-256
`5b665120c62f115d1370e0ee56c47a4bdcc891aa738d177baceb50def25fe310`.
The final net cleanup is 79 files and 17,209,698 bytes. No raw-run,
invalidation, equivalence, or representative-evidence directory was removed.

The same test sweep exposed that several Round 36 tests regenerated interim
completion files and rewrote frozen semantic audit outputs. The tests were
made read-only and historical-commit-aware; the four tracked audit outputs
were restored exactly, and the three regenerated interim files were removed
again as transient test products.

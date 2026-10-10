# Actual stacked Draft PR verification

Draft PR: https://github.com/yifanXovo/TailoredExact/pull/174.

The first actual remote check observed head
`1e90dbc5eacddedf925d88c8608e897c56b4ad69`, base
`codex/round111-seed-block-confirmation` at
`ded38c756a32a464bfa9800212da75778707d974`, state OPEN and draft true.
PR173 retained its original OPEN/DRAFT identity and R110 base.
The exact English body and raw metadata are preserved in remote01/pr174.stdout.

The read-only verifier checked GitHub metadata, actual git ls-remote and
targeted untruncated Git trees. All 890 required Git blobs matched local
committed object identities and sizes: every one of the 645 committed current
round files, all 206 measured sources, all 38 frozen performance helpers, and
the explicit public-restorer dependency. Overlaps are counted once.
The single archive's remote Git blob and size matched the committed local
82,842,777-byte archive. Its SHA256 and member bytes were already independently
checked during actual public recovery; this remote check did not download or
restore the archive again. There are no artificial parts or public native
binaries in the current round delivery.

Measured production source remains d0014a7163e3996fe120471420e56b089c9715ae.
Scientific payload is a3cac1df0ee1d4eaaeb87343508e0af31cfc3b40.
Actual recovery receipts were committed afterward at
1e90dbc5eacddedf925d88c8608e897c56b4ad69. This remote receipt observes that
existing revision and does not claim to verify the later commit carrying the
receipt itself. All verification is offline engineering or read-only remote
metadata, with native/Optimize/compiler starts zero. Scientific state remains
BLOCKED and no formal arm can be retried or automatically resumed.

The extra independent whole-goal review is now signed in
review/whole_goal01.json / .md: BLOCKED_DELIVERY_COMPLETE, delivery PASS,
science BLOCKED. It independently checked live metadata and the same 890
blobs, the actual Git commit-to-tree connection and all 10 committed Round112
scripts, including the current offline reader and comparison/publication tools.
Two overly broad reviewer engineering assertions are disclosed and resolved
by targeted actual metadata/diff checks; no measured source/helper was changed.

This new review and the earlier remote observation are committed afterward.
The final publication verifier also checks all current committed Round112
scripts, its own Git blob included. A final read-only check must follow this
last receipt push. Its actual output belongs outside the commit it verifies,
in F:/ExactEBRP-Round112-final-remote01; the directory is a designated future
output here, not an already-completed verification claim.

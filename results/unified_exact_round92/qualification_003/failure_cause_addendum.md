# Q003 pure-fixture cause clarification

This addendum leaves the original Q003 report and all raw receipts unchanged.
The first post-stop report suggested a stale `T`-only floor expectation. A
subsequent bounded source inspection found the concrete earlier failure:
`independentTwoStationRouteOracle` starts with `complete(..., pickup=1)`, then
sets `row.pickup=handling` for handling 2 and 3 without updating
`row.raw_pickup_time`. The v2 raw/emitted identity check correctly rejects
that inconsistent fixture before comparing integer capacities. The CTest
message `2-station independent integer route oracle differs` is generic and
does not itself identify the failing branch.

This source diagnosis was **not** tested or used to rerun Q003. No evidence
from this failed fixture establishes an invalid row or a physical/canonical
cut failure. Root owns any one-line test-only repair, renewed source identity
and separate execution admission.

# Exactness and validity note

All candidate certificates in `certificate_audit.csv` require complete exact
interval coverage, a monotone valid global lower bound, the native zero-gap
contract, and an independently verified original-space incumbent. Empty leaves
may contribute +infinity only when their native status is infeasible; this
fail-closed rule has a dedicated C++ regression test. Matching objective values
alone are never interpreted as optimality.

The final audit found zero false certificates. Right-censored rows remain
explicit noncertificates with their valid lower/verified upper bounds. The
Release/Gurobi clean build passed 21/21 CTest
targets and 20/20 Python protocol
tests. Default-off implicit versus explicit C6 equivalence passed
3/3
sentinels.

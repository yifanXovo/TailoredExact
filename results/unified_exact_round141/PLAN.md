# Round141 entered study

The governing goal is the supplied `goal.md`. New assets are under
`E:/codes/ExactEBRP-work`; the original workspace, user changes and old rounds
are protected. Main is b2b940c1e517a72e226ec60fc49ff19651737632 and does not
contain R140. This branch starts at verified R140 d00bcf415... and its Draft
PR will temporarily target `codex/round140-two-sided-threshold-count`.

The first stage enters three source-matched continuous domains: K35, RB35-T2
and K20. One exact-threshold rule maximizes Delta*(K-ell)*(u-K), with the lower
physical threshold as exact tie-break. Explicit count-range violations are
reported separately and would precede this rule. Balanced and LP-floor integer
pivots are compared, with duplicates removed. Parent old TC and TC2 rows remain
in every child. Plain count and nested conditional TC2 are solved on both
sides. Three reconstructed-parent controls check numerical/matrix transport.
All matrices are serialized with SHA before Optimize, roundtripped and checked.
The same cutoff, objective, supports, physical parameters and validated U are
held within each domain; the R140 source carrier and selected member hashes
are independently verified. These diagnostics are not NativeEvidence sources.

For the most informative pivot per domain, D0/D1 use the same two conservative
child floors (min(bound,cutoff), inherited 1e-7 margin and downward arithmetic).
The scalar projection and optimized root objective will be compared. Missing
Gini midpoint references must be reconstructed with their full canonical
support/product rows; editing G bounds alone is not a replacement.

Only useful qualified cover, D1 LP gain or actual scalar projection separation
supports proceeding to one frozen online rule and finite complete pilots.
One-sided floors or saved H-row violations alone do not. Both floors will
also be compared to the carrier's actual Native root/early bounds. A no-signal
stop is an authorized completed outcome. Any production implementation must
first add count-aware evidence and domain inheritance; the old R120 g-only
scope is insufficient. Stable and historical entry bytes remain unchanged.

All new solves use Gurobi Seed0, one thread, serial execution, affinity mask4.
H, if reached, retains seed20260626. The durable `round141_common.py` ledger
charges experimental outers once (nested work is observational); the absolute
ceiling is 36000 seconds. The planned finite diagnostic allowance is3600.
Build, pure analysis, document export and public I/O are separate; no build
or large I/O runs concurrently with timed solves. Independent preflight and
final integration review are required. After PR/public byte acceptance,
bounded cleanup applies only to completed current-round reconstructible
duplicates, retaining unique raw/failures and required runtimes/trees.

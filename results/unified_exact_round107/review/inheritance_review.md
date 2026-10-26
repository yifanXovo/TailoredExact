# Independent Round107 inheritance and historical public-recovery audit

**ACCEPT_INHERITANCE_ONLY.** R106 delivery head is
`0350dbcc60d1c68e5c499d2e9880ecc1deaf031c`; production source
`8a2af86155fa2ef206d8d5156a9efc14d0acb102` and campaign commit
`94860fd3515a5b18f408e3c64449dec2e52fa5a8` remain separate identities.
There are no `src/`, `include/` or CMake production changes from the campaign
commit to delivery. Actual historical PE and installed DLL were independently
read as bytes and match respectively
`1ad7b9128288ff06eed64ac91154c1863963827c5399083b1b233a24ee2d09b4` and
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
This audit ran no compiler, test executable, Optimize, IIS or native solver
process, and changed neither the historical tree nor the original user workspace.
It does not admit the new R107 candidate or reproduce engine performance.

The machine record is
[independent_inheritance_audit01.json](../inheritance/independent_inheritance_audit01.json).
It records exact source roots, hashes, public dependencies, rebuilt table fields,
live PE/DLL identities and the separate event-level net-return computation.

## Actual fresh recovery from public Git bytes

The auditor exported 27 exact public Git blobs, rather than using the historical
tree's untracked raw artifacts. R106 carrier files and public restorer came from
the specified delivery commit; the R105 archive dependency came from exact commit
`8dc274eb34ee6d8a575f0b94b57ef04476efc0f1`. The export root is `E:/r107p01`,
the exclusively created fresh restore is `E:/r107f01`, and reconstructed reader
outputs are `E:/r107r01`. These are new roots created for this audit.

The six public parts reassemble to 283820721 bytes and archive SHA
`c196bb62c84d7775c239fe466b436466b327988a031c2c6f75814fca5609ec3c`.
The exact R105 archive at
`results/unified_exact_round105/compact_evidence/evidence.tar.gz` has SHA
`fd546a17045c8f0cb886338a865df4abad3e8bfa20718bb8d253762516f45125`.
The explicitly published original R105 manifest bytes at
`results/unified_exact_round106/r105_supplement/inherited_compact_manifest_bytes.json`
have SHA `f1975056153d4dd8fd73d3713a649f0833a5914b831c554ed9192b288b7223cd`.
They are JSON-semantically equal to the old Git LF blob, whose byte SHA is
`5380f463e1b97f2ac093bd1453b2a51646c02baf8a847a4daabc0c5e8375c805`.
The restorer consumes the exact published manifest, so recovery is independent
of old checkout newline conversion. No historical file was rewritten.

The unmodified public `round106_restore.py` completed in 25.981253999983892
engineering seconds, verifying and restoring 45827 current members, 1556
inherited members and 66 exact recovered R105 ledgers. The unmodified restored
stdlib reader completed in 2.704803599976003 seconds. It reconstructed every
published current and inherited CSV/summary field from raw evidence and compared
them successfully. All 13 result-table/summary files are additionally byte-equal
to the frozen publication. The separate execution JSON correctly differs in its
fresh-root provenance. The CSV comparison covers 288221 cells; published tables
are comparison targets, not reconstruction inputs.

The historical independent checker's exact frozen bytes were then executed from
the fresh restore, using only its own SHA-bound arithmetic implementation. It
completed in 47.25440269999672 seconds, with 10695 source files all inside
`E:/r107f01`, and compared all semantic fields and source SHAs successfully to
its frozen baseline. It independently recomputed all 5120 raw candidates, all
5117 lazy submissions, 103 structural declarations, every startup/final/new
complete physical fleet, native acceptance and resource totals. Its original
4.3 MB result is preserved losslessly as
[inherited_independent_delivery01.json.gz](../restoration/inherited_independent_delivery01.json.gz).
The restorer, reader, checker and their launch/process/return/stdout/stderr
receipts are retained under `restoration/` and `engineering/inheritance_*`.

## Reconfirmed R106 evidence and limits

All eight preregistered arms completed. Same-PE F2 ENS-C certified in 577.344
fully observed seconds; EVENT-STRUCT, now called GLOBAL-STRUCT in R107,
did not certify by 1170.344 seconds. STRUCT's own UB was 0.8699780578 versus
P/ENS 0.8659435203. All five C2 arms were censored; P, ENS and STRUCT own UBs
were respectively 0.1983028486, 0.2167930653 and 0.3750564073. These are
budget endpoints, without a final proof-time ranking.

C2 STRUCT has 2357 events, 2352 distinct complete fleets, 2337 distinct Y,
2347 exclusions and four newly verified physical UBs. Its 71 A submissions
leave 2276 FULL submissions. F2's 32 B submissions are 16 EXACT plus 16
THRESHOLD, rather than 32 independent physical conflicts. C2 STRUCT master
exclusive time is 1589.160 seconds, oracle 38.270 and separation 0.346;
separator arithmetic is not the main observed cost. These data have moved beyond
R105's four same-Y/different-assignment events, while still showing poor route
conversion and lost F2 certification.

Independent fresh reading confirms natural A event5/C2 car2, natural B
event2/F2 car1, F2 FULL fallback event4, and C2 event1555's complete physical
fleet with Ftrue 0.3750564072917856 below modelObj 0.37618561539041984.
The submitted event1555 vector is observed at event1559 and matches the final
native vector. A/B/FULL proof, current lazy violation, paid Start retention and
next-event continuation remain different evidence from callback API return0.
C2 FULL's unresolved final event and provisional native objective are not
promoted into a physical UB or a qualified final native bound.

R106 is correctly retained as `RETAIN_COMPONENT_ONLY`; its cancelled F5/N36/S12
confirmation groups were unstarted and remain untested. The fixed-Y diagnostic
remains UNKNOWN, not INF, and does not exclude that Y. R105's exact supplement
retains 55 conservative starts, 12081.441783100076 outer seconds, 163 total
Optimize and 37 IIS, including one historical missing-after. R106 totals are
30 conservative starts, 13089.59282640001 outer seconds, 5778/5778 raw ahead/
after, 5634 total Optimize and 156 IIS, missing-after0. These inherited fees
are not recharged as R107 solver work. The F5 R105 correction retains native
550.0507931, algorithm571.422 and paid outer572.174668 seconds as different clocks.

## New zero-solver net-return census

For a vehicle starting empty, summing its load changes yields return load
`R_k=sum_i(p_ki-d_ki)`. The physical return capacity therefore implies
`0<=R_k<=Q_k`. This bounds net return, while cumulative pickup can exceed Q
through repeated capacity reuse. For binary original routes, first-station and
selected-successor load recurrences reconstruct every prefix; the last served
station's bounded load proves the upper inequality. After x is made continuous,
the inactive-arc Big-M recurrences no longer force that physical identity.

The new independent stdlib script
[independent_net_return_audit.py](independent_net_return_audit.py) parses every
raw candidate `.sol` p/d value using Decimal, checks integer tolerance, compares
the resulting operation vector to the exact event record, and scans the original
canonical net-return rows. It reads 5137 SHA-verified restored sources, and uses
no mode deduplication or production arithmetic functions. It covers all 5120
events and 15256 vehicle-event records.

| Historical arm | Events | Vehicle-event rows | Lower violations | Upper violating events |
|---|---:|---:|---:|---:|
| F2 STRUCT |104|208|0|0|
| C2 FULL |2509|7527|0|9|
| C2 CORE |150|450|0|0|
| C2 STRUCT |2357|7071|0|0|

All upper violations are C2 FULL car0 events
341,342,343,344,345,347,348,349,350, with net returns
23,24,24,22,22,25,23,25,25 against Q20. Event341 independently gives pickup44,
delivery21 and return23; its candidate SHA is
`bd2513c505c5b21b3de792e1735f0dbcf07ba60174af78b3cb4e06e1dd48f3f3`.
The canonical lower inequality is explicit for every vehicle: C2 rows
c10207/c12219/c14231 and F2 c3789/c4731. No corresponding explicit upper-Q
net-return row appears in any of the four EVENT canonical matrices.

The full event census is preserved in
[event_vehicle_net_return01.csv.gz](../inheritance/event_vehicle_net_return01.csv.gz)
and [net_return_audit01.json](../inheritance/net_return_audit01.json). This is a
future strengthening clue already related to R66's arc-flow conservation.
**Production rows added by this audit: zero.** It is not a new performance panel
or an explanation of the full R106 deficit. The independent result also records
7470 FULL, 443 CORE and 6981 C2 STRUCT vehicle-event
rows have pickup above their own Q and must not be rejected on that basis alone.

## Limited relevant historical conclusions

Exact Git commit/path/byte hashes for the inspected historical final reports are
in the audit JSON; checkout LF/CRLF differences are recorded separately. The
review scope is the requested historical mechanism and stop boundary, without
rerunning old solvers or reopening stopped families.

| History | Established conclusion relevant to R107 |
|---|---|
| R41/R42 | Static single-tree interval encodings can be exact and preserve root strength, yet architecture changes produce opposing performance effects. Fewer proof jobs or one tree does not imply faster certification. The tested architecture families stopped; R107 is not a renamed static segmentation or coalescing trial. |
| R59 | Startup changes U, cutoff/domain and controller geometry as well as elapsed cost. Simple-start Single-S gives no systematic outer benefit on that panel, but does not disprove all complete outer frameworks. Fixed-state formulation and complete startup/controller effects must remain separate. |
| R52/R53 | Dynamic support-duration enumeration/PreCrush/callback paths had bounded certificate regressions; F0's removal of exhaustive subset rows improved the qualified inner formulation. R106 A reuses the subset-duration principle; candidate extraction and event application are its increment. R107 does not reopen that dynamic enumeration matrix. |
| R54 | Necessary inventory-route mincut closure strengthened roots but lost complete proof certificates; its tested cut family stopped. Keeping the controller is not authorization to add its cuts to R107. |
| R64/R66 | Arc-load/time flows, conservation and loaded return are established resource constructions. They support the net-return identity and legal pickup>Q; stronger projection, equivalent LP projection, or fewer rows did not guarantee a qualified complete default upgrade. No arc-flow replacement enters R107. |
| R97 | A globally physical UB, compatible canonical feedback, attempted/API/deferred/observed acceptance and full coverage are distinct. High epigraph or out-of-domain physical witnesses cannot be rejected merely for incompatible injection. R97's separate feedback research remains disabled. |
| R98/R99/R100 | Integer-equivalent expressions and identical all-continuous LPs gave materially different full searches. Quantity declarations, service linking and AM interactions cannot be attributed through column counts or raw-LP values alone. Those type/expression studies stopped; their optional modes stay off here. |
| R101/R102 | Necessary fleet/service resource rows had independently valid separation but mixed complete effects, inactive C2/F5 opportunities and ENS protection losses. Their DP/cut families are not enabled by this round. |
| R103/R104 | Certified necessary-hull separation and objective compression did not turn into uniform complete-solve gains. R104 stops its self-paid necessary-resource preprocessing family; R107 neither reimports its historical rows nor relabels the same pool. |
| R105/R106 | Both use a global assignment master, losing the original ENS AM/full interval framework. R105 optimal-event waiting and R106 genuine event learning leave that combined architectural/integrality confound unresolved. R107's new scope adapter and complete eight-arm comparison address that confound without promising restoration will succeed. |

## Boundary on inheritance into R107

R106's global non-strict U0 domain always has a paid legal Start. Its global
`r106Finish` error assumptions for master INF or LB above own UB therefore do
not transfer unchanged to an ENS leaf or strict-improvement request. A local
empty domain, absent current Start, or qualified local LB above a global UB can
be normal. Native OPTIMAL alone is not a complete-frontier certificate; a
candidate's G epigraph need not equal true G. Per-car oracle and leaf bounds
must never become original global bounds without the complete ENS ledger.

Physical A/B/FULL proof semantics can be retained across requests only with
complete operation/physical/numerical keys. Old mapped column indices and omitted
state assumptions cannot transfer: a state absent and fixed zero in one old leaf
may exist in a later leaf. Rebuild the semantic row in the current canonical
domain and prove reliable current violation before lazy submission. These are
requirements for the new scope proof/qualification, not findings of a passed
R107 implementation.

Two collector-only failures and one failure-capture syntax error are retained
under engineering/inheritance_collect01, inheritance_collect02 and
inheritance_failure_capture01. They concern a provenance-key typo and an
overstrict historical LF/CRLF comparison, after the fresh restorer/reader/checker
had already passed. Correction preserved prior outputs byte-for-byte and reran
only the metadata collector; no solver or old measurements were rerun.

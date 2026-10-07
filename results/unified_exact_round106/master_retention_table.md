# Round106 actual master retention

The formal master is the existing R105 global VD-P/F0 strengthened compact
model in this run's non-strict U0 domain. Original cold P references are
separate controls. Every original solution with F<=U0 embeds using its
actual route, load, service and inventory columns, and the paid legal Start
is explicitly checked. No original better solution is excluded.

| Block | Actual change | Original-solution embedding / retained meaning |
|---|---|---|
| Inventory Y, pickup p, delivery d | Integer declarations retained | Y=b+sum(d-p), original station/total bounds |
| State selector s, ownership z, service direction | Binary declarations retained | At most one vehicle/one nonzero direction per station |
| Route arcs x | Binary to continuous [0,1] | Actual original route supplies binary x within the relaxation |
| Loads | Integer to continuous, original bounds retained | Original prefix/return loads embed; cumulative pickup can exceed Q |
| Order/resource continuous columns | Retained | Existing time/load/order necessary rows remain |
| Objective/Gini/shortage epigraph and auxiliaries | Retained | Exact true F embeds; a nonoptimal candidate epigraph may be higher |
| Global VD-P/F0 rows, stock and total relationships | Retained, same coefficients | Relaxing route types is the only base-matrix relaxation |
| Run domain | gammaL0, gammaU=min(1,U0), epsilon0 | Self-paid verified U0 remains legal; all better solutions included |
| New structural/full/core conflicts | Only qualified lazy rows | Valid for original integer routes; all actual submitted rows reliably violate raw current candidate |
| Callback adapter | MIPSOL_SOL/OBJ/BND, cblazy, cbsolution, deadline cancellation | Independent snapshot/base/mapping audit and verified physical-UB submission |

Raw variables.csv enumerates every original/master type rather than
inferring the matrix from documentation. Formal F2 has3488 columns/9269
checked base rows:840 binary arcs and40 integer loads become continuous;
727 binary and100 integer columns remain,1781 original continuous columns
remain. Formal C2 has8871 columns/31081 checked base rows:2790 binary arcs
and90 integer loads become continuous;1276 binary and210 integer columns
remain,4505 original continuous columns remain. Embedding audits report
max base-row violation0 and retain original.lp SHA, start.mst and raw
master export/quality results inside compact evidence.

Fresh original cold P reference counts are F2 1591/3689 and C2 4242/10627
columns/rows; their fingerprints and canonical SHAs match inherited
references. These different counts describe the original P control,
not a deletion from the larger strengthened EVENT matrix.

FULL, CORE and STRUCT share this same master, paid startup, event/UB/cache/
deadline contract and fixed vehicle order. Only conflict strategy differs.
Original P/ENS paths retain their prior contracts. --round106-events
defaults off; all formal strategy selection is explicit, with no runtime
dispatch by input identity, size, known answer or stagnation.

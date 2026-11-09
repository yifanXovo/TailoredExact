# Round159: joint quantities, ownership and physical realization

The frozen joint restriction produces two new qualified integer resource
uppers. It demonstrates a useful local quantity/owner interaction and
separates full-tour/handling obstructions from prefix-load penalties.
It produces no new physical route or global original-J lower. The sole
free-owner physical query is UNKNOWN; F is not entered. Stable GI-TBC/B
and the E+ reference remain unchanged.

## Resource upper chain and actual cost

| Role | Fixed physical reference | Fixed-owner resource upper | Joint resource upper | eta_R | Baseline / joint outer seconds |
|---|---:|---:|---:|---:|---:|
| RX35 | .2996694007364017 | .29453694232737326 | **.29118539321285497** | .8666399263552738 | 59.0775041 / 4.7645577 |
| NB35 | .450291503262878 | .425855686698408 | **.4235630179611202** | .5080806331775546 | 17.5808312 / 5.8791923 |

RX35 starts from the explicitly inherited review-side C resource point;
its baseline accepts no improvement at2048 nodes and does not prove local
optimality. The reduction from C is **.003351549114518293**. The total
.008484007523546722 difference from the older physical reference includes
the inherited C improvement and is not all credited to R159. NB35's new
fixed-owner quantity reference accepts seven improvements; joint release
adds **.002292668737287784**, for .026728485301757754 below its E+ physical
reference. The NB35 scope is the specified E+ source, not another B arm.

Each joint call completes all12 frozen blocks, with31/246 total nodes and
two/four accepted improvements. Every block has Native OPTIMAL status;
no unguarded exact-J local optimum or global bound is inferred from that
status. Every saved improvement passes exact original-J, nominal original-T
resource arithmetic. The four selected endpoint points have complete
independent old raw-resource lifts and saved-matrix residual checks.
[Exact fractions and intervals](final_intervals.json),
[all strict events and complete witnesses](trajectory_analysis.json),
[resource chain CSV](reports/resource_chain.csv).

The remaining resource/inventory widths are at most .05513329030539926 and
.027606609237029123. These upper-bound the possible gain of the same
standalone scalar resource domain over L_I. They do not bound every cut's
joint effect inside a full routing relaxation Q. Strict F_R>U_I and the
physical/resource optimum gap remain UNKNOWN. U_P minus U_R is a witness
price difference, not a lower bound on that optimum gap.

## What joint release adds, and what was observed

The same C++ rule chooses an eight-station block using current original-J
marginals, handling pressure and geometry. It opens all original supported
quantities and eligible owners inside the block, including activation,
zero service, direction change and unequal-net compensation. Outside
quantities and nonzero owners retain their entire service/balance effect.
The conditional <=3-station resource system updates with every active/owner
choice. There is no P<=Q restriction and no stale full-A travel budget on
changed ownership. Parameters, ties, strict acceptance and12-block/512-node
capacities are frozen in [the plan](research_plan.json).

Both traces actually use nonzero quantity-net changes on old owners
compensated by new ownership. RX35's first joint event changes quantities
at stations19/35 and moves station25. NB35 changes quantities at four
stations with owner changes at14/19, and separately activates station26.
No accepted zero or direction-flip event occurs; these freedoms remain
allowed but unobserved. A simultaneous eight-station domain exceeds the
single-step menu in R158. It is not a proof that every historical sequence
of exchanges/neutral moves is unable to reach the same point.

One post-trace, same-model/same-Start/same-block ablation only fixes owner,
using the same512-node policy without an extra full-A budget. It returns
normally at21 nodes in1.0197121 outer seconds. Its transported, guarded
restricted J lower **.2945344157494531** exceeds the joint event upper
**.2922946074975457**. This proves owner freedom is needed for that price
within that particular block/outside state. It does not close the full
fixed-owner problem or give a global lower.
[Ablation result](owner_ablation.json), [mathematics and algorithm](mathematical_analysis.md).

## Physical conversion and its scope

The same exact-dyadic subset/last DP opens every elementary order for fixed
Y and owner, with16777216 slots for either loaded or unloaded recurrence.
Capacity exhaustion is UNKNOWN. Here every selected DP completes.

| Joint point / car | P=D | Unloaded travel | Prefix extra | Minimum full time | T |
|---|---:|---:|---:|---:|---:|
| RX35 /0 |13|5335.2187581|0|6895.2187581|6300|
| RX35 /1 |16|3986.9507261|241.4856438|6148.4363699|6300|
| RX35 /2 |25|3412.0881518|0|6412.0881518|6300|
| NB35 /0 |32|3470.6062696|.6789577|7311.2852273|7200|
| NB35 /1 |29|4052.1162936|482.8031804|8014.9194740|7200|
| NB35 /2 |14|5740.6523735|74.3765755|7495.0289490|7200|

All returns are zero. RX35's inherited car2 obstruction persists; its
unchanged subproblem receives no heavy new search. The light new global
completion confirms it while exposing the new car0 tour obstruction:
the fixed-set unloaded tour permits at most8 pickups, versus actual13.
RX35 car1 has a prefix penalty but still fits. NB35 car1 already exceeds
T without prefixes; prefixes add482.803 seconds, reducing the guarded
fixed-combination pickup budget from26 to22. NB's baseline point also
fails cars1/2. The exact discrete recurrence and binary coefficients, not
symbolic Euclidean arithmetic, delimit this precision.
[All selected physical results and guarded budgets](reports/physical.csv).

Fixed-combination DP failure excludes only that Y/owner. The one E1 query
then fixes RX35's new Y while freeing all eligible owners, order and loads;
actual column bounds verify assignment was only a Start. It returns
**NODE_LIMIT / UNKNOWN**,8192 nodes, zero solutions,1329.5759356 outer
seconds; Native Runtime1328.9349999, Work2462.0511477,3580787 iterations.
No numerical warning is observed. It excludes neither that inventory nor
an objective level. Its zero feasibility bound is not a J lower.
The E1 model/Start/log and exact condition are in the new carrier.
[Pre-call reason and capacity](deepening_decision.json).

## Qualification, language and costs

The new service/resource construction, repeated block selection, callback,
completion and result return are C++. An offline Python adapter exports
the unchanged qualified R153/R157 RN objective. E1 explicitly reuses the
old complex Python fleet interface as an offline query; no Python timing is
used to accept or reject a final C++ production candidate. No final candidate
exists here, and no new production PE runs.

The new research PE SHA is
`9052e2c3d0403d59ae5c4d5bc3ef70d36e298ea61b46381175a5f1e193da256a`.
Its actual sources and inherited GNU C++17 compile flags are in
[build identity](build_manifest.json) and [source identity](source_manifest.json).
The old production source remains092bad58..., PEe5efe978..., and the
Gurobi13.0.2 DLL remains9b5fccef.... The new binary is included as a measured
artifact in the new carrier. Old PE/DLL and large carriers remain references.
No compiler optimization/fast-math change or language speedup is claimed.

Saved-model/Start checks preserve every RN row and objective; they verify
all eligibility/outside bounds and conditional budget RHSs, and independently
match every assignment/visit/P/D/return row to the old interface. Prefix
fixtures include exact brute-force costs29 loaded versus5 unloaded and
cumulative P4>Q3, plus empty/over-T/capacity UNKNOWN cases. Actual duration
matrices match sqrt(dx*dx+dy*dy)/1.5 at all arcs. All original numerical,
zero, cutoff and proof-consumption fixes remain. The [final audit](final_review.json)
is a separate routine by this same agent, not an independent-person review.

**Scientific outer cost:1438.3466242998838s /129600s**, with no open receipts.
All construction, solving, DP, validation and failures are included once.
Nested Runtime/Work is descriptive. The four failed metadata/readback
launches (nonfinite JSON metadata and follow-on syntax/admission failures)
retain their actual executed source bytes and fees. They change no accepted
resource point or physical conclusion. Compilation is separately5.8637514999s;
writing/render/public I/O are separately recorded. Prior R158 costs are
excluded. [Full outer ledger](cost_report.json).

## Stop/continue and paper boundary

E2 is not entered because no new generally valid structure beyond the
inherited tools is established. E3 is not entered because another whole-level
query lacks a new information source. F is not entered because there is no
useful physical U or global L improvement to consume. No empty panel, free
offline-witness injection, C++ production comparison or complete-method
gain is claimed. Unused budget is retained rather than spent on a repeated
UNKNOWN. A future mechanism needs new justified active-set tour/prefix
coupling or a qualified own-state physical benefit.

The incremental evidence is the simultaneous restricted-domain trajectory,
scoped owner-necessity contrast, two same-rule resource intervals and
explicit physical obstruction decomposition. Original J, handling identities,
DP and ownership exchange are inherited, not new theory. No broad novelty,
out-of-distribution, P-GRB superiority or publication-acceptance claim follows.
[History deduplication](history_dedup.md), [final decision](final_decision.json),
[paper source](manuscript.tex), [reviewable PDF](manuscript.pdf),
[finite reproduction](reproducibility.md).

Publication, the single bounded anonymous recovery, PR readback and the
post-PR bounded cleanup action are recorded in [RESUME](RESUME.md) and their
separate delivery receipts. The original tree, user changes, prior evidence
and stable GI-TBC entry are protected throughout.

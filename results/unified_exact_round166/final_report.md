# Round166: compact shared states and certified decision trade-offs

Retain uniform GI-TBC/B as the main method. C166 is mathematically valid in
the declared interface domain and reduces the state representation, but its
complete benefit is mixed: B certifies 3/6 inputs, C166 2/6. C166 improves
physical U on C35/B35 while weakening their proof L; X35 worsens on both
sides. C20 loses its certificate and X20 takes materially longer. Keep C166
default off as a separately named research candidate. No per-input
portfolio, released-default change or Round167 is introduced.

The paper now also contains new continuous-weight quality guarantees from
complete physical plans, and two-sided route-time value intervals for all
four requested resource pairs. These results give bounded decisions even
where full optimality remains open. They are actual scientific additions,
not document-identity maintenance alone.

## Representation result and actual integration

On a contiguous legal integer stock domain, the joint graph visible through
stock Y, absolute movement M, nonzero visits V, G and Z=GY has the same
continuous convex hull when supported on legal endpoints and b−1,b,b+1:
at most five stock supports. The constructive proof interpolates separately
on donor, initial singleton and receiver pieces. A separate inherited
absolute-Y binary-product layer makes the integer product exact. Its relaxed
bit lift contains the projected graph hull and uses disjoint auxiliaries,
so the common raw LP projection remains unchanged.

Full-model equality requires every removed-state dependency to pass through
that interface. Actual B satisfies it: the e epigraph, r/H/S, original
objective and physical/valid rows remain. Target deviation is not silently
replaced by a state equality. AP/count/CDF/theta/linked-direction/RN and
other unproved research combinations stay disabled and active incompatible
combinations error explicitly. Continuous breakpoints with integer Y alone
fail exact GY; binary breakpoint weights remove interior legal stocks.
Holed domains and new state functions require additional legal restrictions
or common pieces. Empty-domain infeasibility is retained.

For N legal stocks, k≤5 supports and d=max(1,ceil(log2(C+1))), the changed
blocks have B:2N columns/N binaries/2N+6 rows, and C166:2k+2d columns/d
binaries/2k+8+7d rows. Nonzero formulas and degeneracies are in
[compression_theory.md](compression_theory.md). These exclude unchanged
physical rows and use the inherited coefficient-omission convention; actual
emitted counts are authoritative. Rows/nonzeros can increase. Five-generator
necessity is confined to legal graph-point selection, not arbitrary
extended-formulation complexity. Standard disjunction, piecewise-affine and
binary-product tools retain attribution to McCormick, Gupte, Köppe, Vielma
and Huchette–Vielma. No general ideality, routing-hull or OR breakthrough is
claimed.

The distinct C++ mode, complete semantic Start interpolation, LP-to-MIP
type recovery and canonical matrix identities are integrated throughout
root/child/target/terminal paths. [Research design](research_design.md) and
the independent preformal mathematics review distinguish this object from
old LOG's retained continuous states, R104 row aggregation and physical/RN
product completion. [Reproduction](reproducibility.md) provides the actual
entry and dependencies.

## Qualification and complete fixed comparison

All new optimization/qualification/oracle core is C++. Diagnostics use96
actual Optimize calls:64 local LPs,16 global paired LPs,8 boundary/tiny
calls and8 complete nonzero-controller calls, inside539.080771s. The
independent finite tiny oracle, algebra, zero controllers and legacy-B
export add zero Optimize. Algebra covers4550 domains/77168 graph checks.
The nonzero tiny optimum has stock(1,1), objective.15, one returned loaded
unit and a donor stock outside the breakpoint set. Zero stock, independent
zero proof, loaded-return handling, cutoff boundaries, Starts and type
restoration are covered.

Eight full-model LP pairs—six roots and two fixed child scopes—have maximum
absolute signed objective difference3.3306690738754696e-16. Actual common
rows/objective/bounds/types agree after subtracting complete representation
blocks. [Qualification](qualification.json), [LP sizes](reports/qualified_LP_sizes.csv)
and the strict independent model checker preserve the actual evidence.
Two healthy-producer reader failures are retained and repaired read-only;
neither healthy B nor C166 producer is repeated.

The sole formal matrix completes all twelve frozen positions, serially,
with same-build fresh B controls, Seed0, own H seed20260626, one thread,
native default strategies, requested gaps0 and unlimited NodeLimit. The
original1200s n20/2400s n35 contracts, AM.08/depth8/min-width1e-4,
m-binary/pair-only/AP-off semantics and numerical policy remain. Every arm
independently completes and pays its own H. Corresponding H semantic/fleet
hashes agree. Offline archive plans/bounds enter no startup.

| Input | B state; U / L | C166 state; U / L |
|---|---|---|
| R163-C20-S | CERT; .1912805923 / .1912805923 | OPEN; .1912805923 / .1865980494 |
| R163-B20-B | CERT; .4232321817 / .4232321817 | CERT; .4232321817 / .4232321817 |
| R163-X20-S | CERT; .4477476266 / .4477476266 | CERT; .4477476266 / .4477476266 |
| R163-C35-U | OPEN; .1295663897 / .01983750282 | OPEN; .1210432700 / .01420654071 |
| R163-B35-S | OPEN; .1942903111 / .1202340026 | OPEN; .1792896268 / .1160532510 |
| R163-X35-S | OPEN; .4574753170 / .3949882559 | OPEN; .4758711528 / .3866997489 |

Values here are display approximations. [Complete arms](reports/complete_arms.json)
and [six pairs](reports/pairs.json) retain full precision, signed gaps,
qualification, all produce/verify clocks and provenance. OPEN T_cert is
null. Only the two joint-CERT pairs have time ratios: C166/B=1.1108187640
on B20 and4.3487828154 on X20. B20's .5647814283s difference is below the
fixed max(10s,.1 times faster) scale; X20's419.6022120845s difference is
substantive. C20's OPEN cap is never used as a convergence time.

All three n20 pairs have identical recorded AM action sequences and equal
initial raw LP values to numerical error. X20's accumulated Native Runtime
is122.891/542.289s, Work220.964/992.214 and nodes8842/66425 for B/C166;
writer time is.721/.724s. The extra paid time lies almost entirely inside
Native optimization. First MIP root/presolved counts and action sequences
are in [runtime metrics](reports/runtime_metrics.json). Printed MIP-root
values are explanatory and distinct from the raw-LP theorem and qualified
global endpoints. No particular cut/branching cause is established.

B's total T_produce is7454.335378s and C166's8836.531014s; separate T_verify
is16.200527s/20.726015s. Actual fresh-wrapper outer cost is16328.458215s,
including a small management difference. These censored complete costs are
not eventual proof-time estimates. Runtime/Work/H/build/read counters are
nested explanations and are not added again. Nominal caps21600s,
reservation25200s and cap+900 fault watchdogs are not consumed-cost claims.
The [cost report](cost_report.json) records the conservative shared science
window, actual per-position fees and independent diagnostic accounting.

## Complete-fleet decision findings

All 50 historical fleet records are recovered: 32 parameter observations and
24 resource observations, with six shared records. Every owner, original
method/Seed/run/objective/clock and global-lower qualification is retained.
Routes, unique one-way service, inventory, every load prefix, empty departure,
loaded return and unloading time are independently rechecked. Within each
family the original physical domain and normalized weights match. Old large
cover traces retain fixed audit/ZIP/member identities, a complete canonical
cover hash and the necessary scope summary; they are not duplicated50 times.

For fixed physical F, p=P/Omega and rho=lambda*Omega, v(rho)=min(G+rho*p)
is concave. Feasible fleet lines give an upper envelope; qualified global
lower anchors give chords only on their endpoint intervals. Every distinct
actual coordinate is retained; equal coordinates combine lowers by maximum.
All true finite line/chord intersections and endpoints are evaluated using
rational arithmetic. Lower sources are reduced by1e-7, and recomputed
feasible objectives receive1e-12 upward protection. No grid, extrapolation,
clipped crossing or new solver is used.

| Family | Covered actual rho, display | Supported archive lines | Whole-range regret upper, upward display |
|---|---|---|---|
| K-15-S | [.710502825,2.8420113] | 3 | .002356282 |
| UC-B20-B | [.88725,3.549] | 1 | .000000100002 |
| R-B20-S-T1 | [.5,2] | 3 | .015594269 |
| R-X35-S-T2 | [.49999999999999994,1.9999999999999998] | 1 | .136115162 |

K15's worst bound is at rho≈1.217804157, between sampled weights; a fixed
C-stage plan has the looser .008238592 bound. UC-B20 has one fixed fleet
with numerical-width quality over the whole range. B20 has genuine
component choices but a wider low-weight guarantee. X35's known stable
archive line still has a wide unresolved band. None is asserted to be the
complete Pareto frontier. The existing high-weight X35 fleet gives feasible
F=.3365058164688021 at the old unit coordinate, versus.40327199886285475
for the old fleet: improvement.06676618239405259. This does not backfill
historical U or discovery/certificate clocks.

All four T-pairs have nested physical feasible sets and the same objective.
The guarded two-sided optimal-objective improvements, rounded outward, are:

| Pair | Improvement interval | Displayed width |
|---|---|---|
| B20,3300→5100s | [.2822618761,.2822620892] | .0000002131 |
| X20,4800→7200s | [.2105292995,.2105295021] | .0000002026 |
| B35,4800→7200s | [.1112611656,.3725317852] | .2612706196 |
| X35,4200→6300s | [.0600858983,.3813035291] | .3212176308 |

Open n35 runs still prove strict optimal-objective improvement, with broad
magnitude uncertainty. The intervals are objective-value differences, not
money or general resource shadow prices. All four larger-T witnesses have
better G/p and more pickup. B35 returns2→3 units while X35 returns1→0;
final station stock changes234→233 and145→146 respectively. All four
inventory distributions and route travel/handling/unload/prefix/utilization
details remain in the archive. Near-full duration does not prove an unknown
optimum's time constraint binds. [Decision analysis](decision_analysis.md),
[exact envelope data](analysis/parameter_envelopes.json),
[resource data](analysis/resource_intervals.json) and the new figure preserve
the entire calculation.

## Current paper, CSV and delivery

The sole maintained English paper remains under `results/unified_exact_round137/`.
The introduction, compact-interface proposition/proof, comparator explanation,
continuous-weight figure/quality table, both-sided resource interpretation,
full C166 section, abstract and conclusions are directly revised. Appendix A.9
contains the compression/bit/embedding construction and boundaries; A.10
contains the continuous decision argument. Complete Appendix B is retained.
The mathematical companion, supplement and bibliography are current. All
historical adverse/open, Seed, C35/P, X35 fixed-target, E+ and full/root limits
remain. The private May30 antecedent's model/decoder credit is preserved;
the private original is not redistributed. The two editorial emphases and
remaining author facts are in the [author memo](author_decision_memo.md).

[Current manuscript](../unified_exact_round137/manuscript.md),
[main PDF](../unified_exact_round137/manuscript.pdf),
[supplement PDF](../unified_exact_round137/supplement.pdf),
[source/build manifest](source_manifest.json), [export record](document_build.json)
and [page/visual QA](document_qa.json) bind the same maintained components.
The builder inherits R165 typography and includes actual date, template/header
and toolchain in its cache identity. Outward-bound table decimals are preserved
against generic display rounding and read back from both PDFs.

The final main PDF has 60 pages and the supplement 44. Source assembly,
automated checks and actual contact-sheet/targeted high-resolution inspection
pass; no out-of-page text or abnormal blank page is found. The final navigation
fix changes only the current-manifest link; all 60 rendered main pages remain
byte-identical to the independently reviewed scientific version.

The requested106-row/28-column UTF8-BOM master (60603 bytes,
SHA2568f39e3a23b3b6df621139cb39b4db813ca3e992da091e97251ab8337fd2b0022)
was not found in the one bounded entry search. The103-row GB18030 working
copy and91-row user Desktop file remain unchanged. The three absent old
N/A-P identities are explicitly reconciled. A separate six-row28-column
B-control increment preserves the exact header and existing N/A-P semantics,
with empty P numeric fields, run/build/source mapping and zero old-row
overwrites. C166 remains in variant tables. Artifact Tool read-only CSV
inspection verifies the exact imported shape/endpoints and preserves both
source files. No XLSX variant is introduced. See
[reconciliation](CSV_reconciliation.json), [mapping](reports/CSV_increment_mapping.json),
[increment](reports/GI_TBC_R166_B_controls_increment_28col.csv) and [CSV QA](CSV_QA.json).
New benchmark inputs 0; new Seed values 0; new complete runs 12; new B/C166
pairs 6; new strict B/P pairs/wins 0. The two synthetic tiny fixtures are
diagnostics rather than independent benchmark inputs.

All three actual final independent reviews pass with zero unresolved blockers.
The implementation/data reviewer independently checks all 63,594 raw members,
62 formal calls, 44 actual models and 18 complete Start vectors. The single
new P3 navigation-link finding is fixed and independently read back.
Mathematics/model, implementation/data and research/manuscript findings and
fixes are linked in
[review dispositions](review/final_review_dispositions.json). The measured
new C++ source is0298dd45fbc3645af927c4a4dd1d43ecbdb567a9, PE SHA256
27e71873536bcd8e6001aee0c2514a5cc8122763728c62e6d467cd528b48daba.
Historical measurements retain source e920b92e199e825ec89a2932f701861ff158e0d4
and PE fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93.
The same external Gurobi13.0.2 DLL hash is recorded separately; commercial
DLL/license/credentials and the private antecedent are not published.

New raw, tiny/LP/build/failure evidence and own runtime are in the
[new-only carrier map](evidence_archives.json). Exact new/changed scientific
Git blobs are pinned by [source publication](source_publication.json);
the subsequent receipts do not invent their own not-yet-existing self-SHA.
Normal push and English Open Draft PR head/base/state readback, anonymous
normal-TLS public recovery of only new content, and zero-delete bounded
cleanup/protected-tree receipts are recorded in
[delivery receipt](delivery_receipt.json). The Draft stacks on verified
R165 while main lacks the dependency. No merge or force push is performed.

The concrete remaining scientific limits are Native search consequences of
equivalent integer extensions, the wide X35 continuous quality band, and
the incremental computational value of external interval scheduling.
They are disclosed research limits, not unfinished tasks silently converted
into positive results. This delivery ends Round166.

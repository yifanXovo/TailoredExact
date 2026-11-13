# Round166: compact shared stock states and certified decisions

One representation is studied: C166 replaces the complete continuous state
support of the shared VD-P/movement/visit graph by its legal affine-piece
endpoints, and retains P's absolute-Y binary product layer. B remains frozen
and default. No root-bound improvement is an admission condition: equality
of the common raw LP projection is the intended result.

The joint interface is (Y,aggregate pickup+drop,aggregate visits,G,Z=GY).
The original e epigraph, pairwise H, S, original objective, SCF/MTZ, service,
physical time, cutoff, valid rows, own H and native policies remain. No
direction/state, theta, state-weighted penalty, RN, count, new cut, E+, new
Seed or full/root study is added. Continuous-only breakpoints fail integer
product exactness; binary breakpoint selectors exclude legal interior Y.

## Nearest historical objects (read-only, no reruns)

R55/R67 VD-P/VD-J and LOG preserve all continuous state selectors/products;
LOG reduces only the integer encoding. R98-100 established the common
movement/visit links and conditional service integrality; current B uses
m-binary, with both A/B links and without linked-direction or vehicle-state.
R101-107 event/rank/resource and decomposition models retain other
state-dependent interfaces. R104 preserves a selected root objective through
row aggregation, not every common raw LP point. R130/R137 architecture and
row ablations remain historical controls. R132/133/135 already separate the
local/product hull from the integer route/objective epigraph. R138-162
inventory/resource/physical product studies do not compress this support;
their gains and failures remain visible. R163-165 freeze the six exposed
inputs and existing Seed evidence. None supplies the present five-support
joint graph plus independent absolute-product integration. Detailed source
positions and historical readback are in review/math_preformal.md.

## Propositions and decision criteria

Prove two-way affine-piece interpolation, perspective representation,
integer physical equivalence, redundancy of the relaxed bit extension on
the joint hull, and the full-model interface condition. Check all degeneracy
and explicit failure cases. Report encoding columns/binaries/rows/nonzeros
and actual construction cost. This is an application of standard finite
disjunction and binary-product tools, not a claim of new general hull theory.

Only after the proof, independent mathematical review and finite C++ checks
pass, enter one paired batch in fixed manifest input order:

| Input | Seed | Order | Cap per method |
|---|---|---|---|
| R163-C20-S | 0 | B, C166 | 1200 s |
| R163-B20-B | 0 | C166, B | 1200 s |
| R163-X20-S | 0 | B, C166 | 1200 s |
| R163-C35-U | 0 | C166, B | 2400 s |
| R163-B35-S | 0 | B, C166 | 2400 s |
| R163-X35-S | 0 | C166, B | 2400 s |

The 12-arm cap sum is 21,600s; scientific reservation is 25,200s and at least
7,200s is retained for manuscript/review. At admission at least 32,400s must
remain. All arms are serial, same new build, Threads=MIPThreads=1, Seed0,
H seed20260626, default native strategies, requested gaps zero, unlimited
NodeLimit. No offline fleet/bound enters formal startup. Judge CERT counts,
both physical U and qualified global L, produce/verify cost and trace facts;
certificate-time ratios use only the joint CERT denominator, with the
inherited max(10s,0.1*faster) substantive-difference threshold. OPEN times
remain null. No per-instance portfolio or universal single-Seed conclusion.

## Fixed diagnostic list, before any new Optimize

At most 120 actual native Optimize calls and 3,600s diagnostic outer window.
The C++ driver has 64 local LP calls (8 listed boundary domains, 4 fixed
representations, 2 fixed objectives), 16 global LP calls (all six roots and
two deterministic left-half children, B/C166), and at most40 other calls.
The latter cover a manually enumerable nonzero tiny physical optimum with
an internal non-breakpoint Y, loaded return, S=0, independent zero proof,
inclusive cutoff/G boundaries, complete Starts, native MIP and LP-to-MIP
type restoration. No-solver enumeration/interpolation does not add Optimize.
Calls, attempted failures and outer wall cost are recorded, with no hidden
qualification solves. Fixed test objectives are in the C++ source; no
random-objective or favourable-root search is used. Technical failures are
retained and a corrected call consumes another slot.

Offline decisions use every available original fleet from four specified
weight families and all four time pairs. Parameter analysis uses exact
finite intersections, qualified global lower chords only inside their
intervals, and conservative numerical margins. It creates no performance
observation or new B/P advantage.

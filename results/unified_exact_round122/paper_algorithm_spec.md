# Frozen exact methods for the first two-source paper panel

This specification binds production source-before-native commit
`355eefd2be3fe5651195681faf7b3a63ee4032f8`, production PE SHA256
`5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba`
and Gurobi 13.0.2 DLL SHA256
`9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`.
All 216 production-source bindings are retained in production_identity.json.
The original executable is reused without compilation or algorithm changes.
Cold P-GRB is the primary benchmark. ENS-C remains the project default;
M-B is the retained existing complete-method paper reference; MB-D1 is the
frozen tested candidate. The completed panel gives
BENCHMARK_MIXED_NO_NEW_PRIMARY_SELECTION because only one exposed new role
provides a material D1/M-B gain, below the required two. The complete
interpretation and reference rationale are in paper_result_interpretation.md. No method dispatch depends on instance identity,
V, inventory regime, time, Work, observed progress or stagnation.

## Physical problem and objective

Service stations are indexed 1 through V; depot 0 is excluded from every
inventory, ratio and weight sum. Station i has integer capacity C_i,
initial stock b_i and target 0<D_i<=C_i. Vehicle k has capacity Q_k and
physical horizon T and starts empty. At most one vehicle visits a station,
once, for a nonzero one-direction integer pickup p_ki or drop d_ki.

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\quad 0\leq Y_i\leq C_i,
\quad r_i=Y_i/D_i,\quad S=\sum_i r_i.
\]

Every route prefix and return load belongs to [0,Q_k]. Loaded return is
allowed. Duration is Euclidean travel/1.5 plus pickup handling and station
drop/return-unloading handling, equivalently
travel+(pickup_seconds+drop_seconds)*cumulative_pickup. Capacity limits
simultaneous load; cumulative pickup can exceed Q. The compatibility field
min_ratio imposes no minimum inventory. Station totals can decrease through
loaded returns: sum(Y)+sum(return_load)=sum(b).

\[
G_{\rm true}=\frac{\sum_{i<j}|r_i-r_j|}{VS}\quad(S>0),
\qquad F=G_{\rm true}+\lambda\sum_i\omega_i|r_i-1|.
\]

At S=0 the original evaluator defines G_true=0 and retains the penalty.
Every accepted own upper bound is a replayed complete physical fleet with
this original objective. The model epigraph g is not assumed equal to
G_true. Native incumbent objectives and the method's own verified U are
reported separately.

## One complete integrated method

Each of ENS-C, M-B and MB-D1 independently pays for the same complete H:
joint insertion construction, the original 24 orders with Seed20260626,
the constructive 25th seed, full decoding and guided strict descent for
every seed, then the inherited insertion/quantity/R76 closure alternating
with the union of R78 balanced relocation and R83 equal-net block exchange.
Neutral accepted union moves improve the complete sorted-duration tuple.
The original bounded decoded-order cache, deterministic ties and outer
objective-improvement handoff remain. H ends at its finite neighborhood
closure or the common absolute work deadline. Neighborhood closure is not
original-problem optimality. A verified zero can terminate the original
method before any backend is exposed.

Otherwise the original interval controller covers all improving physical
true-G values under the own U. It builds scoped VD-P/F0 models, obtains only
its own paid and returned LP/MIP evidence, applies the original AM rule,
keeps the parent or atomically replaces it with both midpoint children,
maps an eligible own complete Start, and preserves every unresolved
obligation until qualified closure or deadline. No sibling obligation is
dropped because another region looks promising. The full method includes
H, all LP/model generations, target and terminal requests, Starts, online
verification, callbacks, normal native cleanup and producer sealing.

For parent bound B and valid child LP bounds b0,b1, AM uses
gap=max(U-B,max(certificate_tolerance,1e-12)), normalized clipped gains
gj=clip((bj-B)/gap,0,1), eta=min(g0,g1), mu=(g0+g1)/2 and score=eta*mu.
Its original threshold is .08. Original infeasible-child handling and
natural splits remain. K0=1, midpoint, depth8 and width1e-4 are uniform;
logical limits never justify discarding an unresolved original region.

## Representation and the M-B reference

The exact inventory-product block has binary s_iy, sum_y s_iy=1,
Y_i=sum_y y*s_iy, gamma_L*s_iy<=q_iy<=gamma_U*s_iy,
sum_y q_iy=g and Z_i=sum_y y*q_iy. At the selected integer inventory it
embeds Z_i=g*Y_i. Its exactness is conditional on valid inventory domains
and interval coverage; it is not an integer-hull claim for the route LP.

ENS-C declares pickup/drop quantities integer. M-B and MB-D1 declare p/d
continuous while retaining integer inventories/loads and binary state,
assignment and direction variables. With unique service, integer b/Y and
one direction, the serving quantity equals b-Y or Y-b and is implicitly
integer. Existing A/B rows express total absolute inventory movement and
the equivalence between service and a noninitial inventory state. They are
valid strengthening, not additional premises for that integrality proof.
The implication does not cover split service, simultaneous pickup/drop or
fractional direction, assignment, b or Y. ENS-Q remains false. F0 and
original support families (size<=3, maximum50000 subsets) are unchanged.

## MB-D1: one paid-root extension

Only the original root's own complete returned child-LP proof pair can
support installation, before that root's first integer Optimize. For side
j, the conservative proof endpoint is

\[
\beta_j=\max(0,\operatorname{down}(\min(\ell_j,c_j)-10^{-7})).
\]

Here ell is the qualified native bound and c is the actual proof cutoff.
For root interval [a,b] with midpoint m, one binary h and three ordinary
linear rows represent, ideally,

\[
g\geq a+(m-a)h,\quad g\leq m+(b-m)h,
\quad F_{\rm model}\geq\beta_0+(\beta_1-\beta_0)h.
\]

The actual complete objective includes its native ObjCon. Serialized base
and difference arithmetic is checked at h=0/1 using both exact decimal
arithmetic and actual binary64 native readback. Outward endpoint extensions
are retained; no inward gap at m is introduced. Original objective, rows,
types and bounds remain, with exactly one added binary and three rows.
An original physical point has the same objective-preserving model
embedding and an appropriate h (left at the midpoint tie). Every actual
Start is mapped, checked against all complete rows/bounds/types/objective,
submitted and read back. Submission, API acceptance, physical validity and
new native incumbent are separate observations.

An incomplete proof pair, original direct split to descendants, exhausted
window or zero-H termination leaves the method unexposed. There is no
added probe, forced root request or later descendant installation.
Subsequent original MIP requests retain the installed extension or carry
it into a separately identified contained domain/epoch. Installation,
expanded Optimize calls, observed h/objective and performance are distinct;
internal h fixing or branching is unknown without actual evidence.

## Proof coverage and numerical qualification

Every proof is bound to its input, actual model SHA, call, epoch/domain,
true-G interval, nonstrict cutoff, Seed and returned status. A local
OPTIMAL/INFEASIBLE result covers only that scope. Transfer requires a
containing proved domain and applicable cutoff. Global lower bounds use
the minimum over a complete valid cover, including the analytic cutoff
complement. F>=G_true and F>=0 justify the original improving-domain and
zero rules. A same-domain contradiction revokes the source and dependent
D1 search. A legal own fleet or later floor0 cannot repair invalid pruning.
Source-reduced physical/open results are identified separately and receive
no dependent nonzero certificate credit.

Calls in reused logs are matched by actual segment byte spans, full
models/settings/Starts and scope, not the first dimensions or last objective
of a file. Explicit not_started is distinct from missing return or unknown
disposition. Actual Seed1 evidence is reconstructed from returned complete
models and actual settings without editing raw callback/global flags.
Tiny signed gaps are retained; contradictory bounds are not clipped into
validity. Certificates follow the inherited 1e-7 floating-point evidence
policy and are numerical certificates, not rational exact proofs.

## Cold baseline and measurement

Cold P-GRB runs the original complete canonical compact formulation from
scratch without H, another method's U, proof, hint or Start. Every method
uses the same frozen PE/DLL, one native thread, one MIP thread, fixed
Gurobi Seed0 or the preregistered Seed1, PresolveAuto, requested MIPGap and
MIPGapAbs zero, original FeasibilityTol/OptimalityTol1e-6 and IntFeasTol1e-5.
Changing Gurobi Seed never changes H's seed. Original affinity and
30-second native shutdown reserve remain.

T_produce starts at the arm origin and includes all own online work,
supervision, cleanup and required producer seal. Post-seal T_verify ends
only after the full required read-only verification and serialization,
including D1 model/event checks. T_total is their sum. Cross-arm
reconciliation is separate group cost. Native component timers are nested
and never added twice. Only two certified methods support an actual
certification-time ratio; a time cap is not an unknown certification time.
No post-seal solution/bound is fed back into production. All four methods
use the same E-root execution environment; historical disk differences do
not justify precise cross-round speed ratios.

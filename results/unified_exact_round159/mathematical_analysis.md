# Inventory, integer resources, and fixed-combination physical realization

All objectives use J=G+H with the original binary64 input coefficients,
H already weighted by lambda, and gamma_L=0. For S=sum_i c_i Y_i>0,
G=sum_{i<j}|c_iY_i-c_jY_j|/(nS). The zero branch remains separate;
these two exported RN scopes have a qualified positive hard stock total.
The RN objective is centered and scaled. Native objective plus the recorded
anchors/scale recovers original J; a native bound is never copied as J.

Let D_I be the inherited integer inventory scope, D_F remove precisely the
R157 original 26 RX35 vectors (D_F=D_I on NB35), D_R(T) retain unique legal
one-direction service, eligible owner, per-car balances/return capacity,
complete handling and all <=3-station necessary tours, and D_P(T) be the
physical projection. In this unchanged contract D_P subset D_R subset D_F
subset D_I. R157's resource exclusions and R158's actual-coefficient budget
qualification establish the middle inclusion; physical impossibility alone
would not establish it. The inherited attach function installs no forbidden
inventory table. No later finite-family exclusion changes D_F's definition.

Every independently verified integer resource point supplies U_R. Thus
0 <= F_R-F_I <= U_R-L_I. For a separately defined scalar relaxation with
D_R subset D_C subset D_I, F_C <= F_R <= U_R. This does not bound the
joint benefit of those rows in the full routing relaxation Q: the resource
point may lack a shared full resource lift into Q. No Q-extension ceiling
is claimed here. A resource point is not a physical incumbent. U_P-U_R is
a difference of witness prices, not a lower bound on F_P-F_R.

For each k, P_k=sum(b_i-Y_i)_+, D_k=sum(Y_i-b_i)_+ over its assigned stations.
Empty departure implies return R_k=P_k-D_k and 0<=R_k<=Q_k. Depot unloading
is paid, so handling t_p P_k+t_d(D_k+R_k)=(t_p+t_d)P_k. Cumulative P_k can
exceed Q_k. The model only bounds each station's service by Q_k and the
return; prefixes enter the physical checker, not the resource relaxation.

The fixed-owner baseline lets all supported quantities vary on the initial
disjoint owner sets A_k, including zero and direction changes; initially
unassigned stations retain Y=b. It uses the full-A three-stop budget as a
conservative inner restriction even after a station becomes zero. It does
not claim to exhaust every fixed-owner resource point after deletions.
Rounded floors and forbidden/dominated subsets come from the qualified
actual-coefficient envelope and guarded horizon, never a bare nominal floor.

The joint block domain fixes outside Y and its nonzero owner, includes all
outside pickups/drops/returns, and releases all original supported quantities
and eligible owners inside a block. A released station can activate, vanish,
flip direction or move between vehicles. No per-vehicle equal-net restriction
is imposed. Conditional visit/subset budgets are rebuilt for every vehicle;
new owners never inherit an uncovered old A budget. Thus the domain is an
inner subset of D_R; an integer point can give a global resource upper but
its optimality/bound/infeasibility stays restricted. No bound or rejection
reaches the exact-engine proof ledger, global cutoff or cache.

Frozen pseudocode (same rule on both inputs):

1. Read the best qualified resource point; compute each station's best
   unconstrained single-stock J gain only as a score.
2. Multiply its score by one plus owner handling pressure. Select the
   step-ranked anchor; select seven further stations by that score plus
   geometric proximity weighted by the anchor gain. Break ties by index.
3. Solve the joint block with the unchanged original RN objective and
   complete conditional integer resource system, Seed0/Threads1 and at most
   512 nodes. Use a complete feasible Start. Retain strict true-J decreases.
4. Repeat at most 12 blocks; no nondecreasing intermediate moves. The
   ordinary whole-method deadline can end the call, without switching
   algorithms. Save every accepted integer improvement durably.
5. Independently recompute original J, nominal-T resource arithmetic and
   complete old raw-resource lift before reporting U_R. Inspect selected
   representatives by the same finite fixed-combination completion.

These blocks can coordinate eight changes atomically, exceeding one R158
single change/owner swap/pair transfer. This is a statement about the
declared simultaneous domain, not a proof that a trace is unreachable by
every sequence of older moves. Saved trace analysis must establish which
of these freedoms was actually used. Finite iteration/node capacities do
not imply a polynomial running time or global optimality.

For fixed (Y,owner), after a visited set S the load is sum_{i in S}(b_i-Y_i).
The classical state (S,last) therefore covers all elementary visit orders;
keep only 0<=load(S)<=Q_k. Exact dyadic arc costs at scale 2^53 are added
in unsigned 128-bit integers, then include complete handling. A second
unloaded recurrence gives a Y-independent tour minimum on that fixed active
set. At most 16777216 subset/last slots are admitted for either recurrence;
capacity exhaustion is UNKNOWN. The work is O(m^2 2^m), storage O(m 2^m),
subject to this common capacity. Fully exhausted states certify only the
fixed combination. An unloaded tour exceeding T-handling identifies a pure
tour/handling obstruction; any extra loaded-tour cost identifies a prefix
effect. Neither excludes all owners at the same Y. A load-constrained tour
minimum at old Y is not a necessary lower for new variable quantities.

No new general cut or variable-Y tour feedback is installed in this version.
The optional standalone C++ tool does not modify stable production source,
CLI defaults or E+'s common helper. Its offline RN export is explicit; a
qualified integrated own-state C++ candidate would still be needed before F.

With s=sum_i |support_i| and M vehicles, the new model has O(Ms+n^2)
columns and O(Mn^3+s+n^2) rows, using subsets of size at most three.
The RN objective and optional integer consequences are inherited. The node
bound limits branch-and-bound work, not root/presolve time or a universal
number of machine instructions. Construction, source parsing, all callbacks,
optimization and saves stay inside each outer measured call.

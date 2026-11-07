# Physical realization of inventory relaxation optima

The parent is the verified, unmerged R156 head e10ffd01de6cf2fa9db71ba5a51f7d9eab8efb05.
The stable GI-TBC algorithm remains the default. All new objects stay under
E:/codes/ExactEBRP-work. WORKSPACE_POLICY.md and its per-round recovery and
bounded-cleanup conventions are inherited. No user-modified tree is used as
a destination. The attached goal is copied byte for byte to goal.md.

## Projection and scope (pre-long-run review)

For the saved root scopes gamma_L=0. Therefore the independently recomputed
inventory price equals the original objective J=G+H, with H already including
lambda. Inventory lower/upper bounds do not by themselves bound a physical
incumbent. A fixedY query covers one integer vector; a family query covers
exactly the class-count assignments, restricted to each station's support.
Neither INFEAS result excludes all inventories at that objective level.

The physical projection follows R61: one nonzero, one-direction service per
station; free vehicle attribution and ordering; at most one depot tour per
vehicle; heterogeneous original Q; empty departure; loaded return allowed;
and original model T, independent of the experiment window. The depot's
placeholder inventory never supplies a vehicle. No original route template,
assignment, original objective row, or historical start is imposed.

The new implementation uses binary selectors z_iv and service assignments
w_kiv. For v different from b_i, sum_k w_kiv=z_iv; for v=b_i no service is
needed. Vehicle k can serve a state only when |b_i-v|<=Q_k, a necessary
single-service condition. Its service indicator is sum_v w_kiv, and its
pickup/drop quantities are the positive/negative parts of b_i-v. Arc
in/out degrees equal that indicator. Depot departures equal returns and
are at most one. Continuous ordering variables satisfy 0<=u_ki<=n*s_ki,
u_ki>=s_ki and u_kj>=u_ki+1-(n+1)(1-x_kij) away from the depot. Thus an
integer solution contains only a single simple depot tour per used vehicle;
disconnected directed station cycles are impossible. n+1 is valid for the
whole domain, not fitted to a witness.

Replacing R61's node-load big-M implications, arc loads satisfy
0<=f_kij<=Q_k*x_kij, f_k0j=0 and outgoing flow minus incoming flow =
p_ki-d_ki at every station. Given a real tour, put its physical load on
each arc to obtain a lift. Conversely, degrees and ordering give tours;
flow conservation then gives their unique load sequence from zero, within
Q_k. Return-arc flow is free within Q_k and is the returned load. Hence the
integer physical projection is the same as the R61 model. There is no
load big-M. These standard flow and ordering formulations are not claimed
as new theory.

For each route, total pickups P equal station deliveries D plus returned
load R. The established evaluator charges pickup_time*P + drop_time*(D+R),
which is exactly (pickup_time+drop_time)*P. Each model time row therefore
is travel plus that quantity <= original T. It charges depot unloading
even on a loaded return. All original Euclidean arcs between potentially
serviced stations are present. Unchanged zero-service stops can be omitted
without increasing travel on these metric inputs. Eliminating G/H modeling
is legitimate because the permitted inventories have a fixed true J and
have already passed the original scope and objective evaluation. The
feasibility objective is constant zero; no native objective bound is
consumed as a lower bound on J or on required time.

Classes use identical actual floating input coefficients c and omega,
tested by their exact binary representations, with no epsilon merging.
Class counts preserve the ratio multiset, S,A,G,H,J and unweighted stock
total. Geography and initial inventory can differ. The saved RX35 best
family has six legal members and pickup total 56 or 57; NB's best family
has one member. Exhaustive finite enumeration independently verifies all
members' exact rational prices and supports. The second distinct saved
families are selected by increasing exact original objective, before any
route result: RX35 size 20, NB size 21.

## Necessary new qualification

qualification/v1 maps the two actual R156 physical incumbent routes into
every new row, exports and reopens the resulting matrices, and verifies
zero bound/row violation. Free solves accept these starts without fixing
any route decisions. A separate ordered-partition exhaustive reader agrees
with the new solver on eight tiny cases: heterogeneous capacity, loaded
return and depot unload time, original-T failure, empty zero stock, absent
depot supply, and a geography-sensitive class permutation that changes
fixedY infeasibility into family feasibility. Neighboring unequal binary
coefficients are explicitly kept separate. Review is by the same agent
using separate reconstruction routines; no delegated reviewer is claimed.

Native status, row qualification and independent physical route verification
remain separate. A node/time-truncated solve without a checked witness is
UNKNOWN and changes neither physical U nor physical L. Even a family INFEAS
has only its recorded finite-family scope. Any future original-objective
level query must cover all physical inventories in that level and preserve
the inherited global coverage rules.

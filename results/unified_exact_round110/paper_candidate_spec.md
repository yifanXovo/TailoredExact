# Frozen ENS–M-B research candidate

Round110 stage: **BLOCKED**, because the required complete observation of
arm42 exceeded its frozen3600-second cap. All42 actual native processes
returned normally under the same final PE;41 have qualifying complete clocks.
The final Seed1 G100-R2 pair is formally UNEVALUABLE. Its own physical and
native evidence remains published, and its clock is not truncated.
ENS-C remains the default reference algorithm.

Round109 remains BLOCKED: its 24 normal arms covered eight original roles;
arm25 failed before parsing completed, and arms26-42 never started. Round110
repairs that actual common-entry fault and measures all42 original arms afresh
under one frozen final PE. Its own42 attempts are the sole comparison source;
41 satisfy the frozen complete-clock qualification.
Eight roles have prior observations, and four were previously unseen; these
are the recovery confirmation of the original prospective frozen panel.

## Problem and physical meaning

Let stations be \(i=1,\ldots,n\), vehicles \(k=1,\ldots,M\), depot 0,
initial integer inventory \(b_i\in[0,C_i]\), positive target \(D_i\), and
vehicle capacity \(Q_k\). Pickup \(p_{ki}\ge0\) and delivery \(d_{ki}\ge0\)
are integer physical operations. Each station has at most one vehicle and one
nonzero, single-direction service. Final inventory and target ratio are

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\qquad r_i=Y_i/D_i.
\]

Vehicles leave empty, follow depot-to-depot routes, and maintain every prefix
and return load in \([0,Q_k]\). Loaded return is permitted; returned stock is
unloaded at the depot. Consequently \(\sum_iY_i=\sum_ib_i-\sum_k\ell_k^{\rm return}\).
Capacity bounds load, rather than cumulative pickups. Euclidean travel time
is distance divided by 1.5. With pickup/drop handling costs \(t_p,t_d\),
closed route time is travel plus \((t_p+t_d)\sum_i p_{ki}\), including return
unloading, and must not exceed physical horizon \(T\).

\[
F=G_{\rm true}+\lambda P,\quad
P=\sum_i\omega_i|r_i-1|,\quad
G_{\rm true}=\frac{\sum_{i<j}|r_i-r_j|}{n\sum_i r_i}.
\]

At zero denominator the original evaluator sets \(G=0\), retaining the
penalty. Original inventory/capacity domains apply. `min_ratio` is retained as
a compatibility field; it imposes no extra \(Y_i\ge R_iD_i\) constraint.
The frozen Round109/Round110 protocol uses \(\lambda=.15\), \(t_p=t_d=60\), and weights normalized by their
maximum. Their sum varies with \(n\); this does not hold penalty balance
constant across sizes. Lambda sensitivity is untested.

## One uniform representation and complete framework

The actual ENS CLI preset is `research-round83-vds-equal-net-exchange`.
M-B adds only `--round98-state-service m-binary`; its effective identity is
`research-round99-ensc-discrete-structure-m-binary`. The separate ENS-Q option
`--round100-continuous-quantities` remains false. Route, load and inventory
variables retain integer domains; state, visit/assignment and direction
variables retain binary domains. M-B changes only the original pickup and
delivery declarations from integer to continuous and includes the original
two rows per station:

\[
\sum_k(p_{ki}+d_{ki})=\sum_{y\in S_i}|b_i-y|s_{iy},\qquad
\sum_kz_{ki}=1-s_{i,b_i}.
\]

An absent initial-state selector is fixed zero. The existing direction upper
bounds, nonzero-service row, inventory balance, capacity prefixes, timing,
state domains, original rows and tolerances remain. LP and child-LP quantities
can be fractional. In a complete integer-domain solution, binary visit and
direction permit at most one nonzero pickup or delivery at station \(i\).
Integer \(b_i,Y_i\) make that quantity \(|b_i-Y_i|\), hence integer even when
its declaration is continuous. This equivalence does not require the two
additional rows. Those rows are valid state/service strengthening; the proof
does not extend to split service, simultaneous pickup/drop or fractional
input inventories. Every physical UB still requires finite, bounded,
integer-tolerance checks on all quantity columns before route decoding and
full physical evaluation.

The retained algorithm is the complete original ENS outer controller with
VD-P/F0, independently paid 24+1 startup, physical closure/handoff, AM .08,
original depth/width/cover rules, cutoff epochs, child-cache, milestone and
terminal behavior. It does not select a mode by instance ID/SHA, size,
geography, inventory category, physical horizon, known optimum or elapsed
search behavior. P-GRB is the original cold unstrengthened compact model and
receives no ENS route, UB, Start, row, cut or cache. Each arm owns its evidence.

```text
Run original 24+1 ENS startup; independently evaluate its complete fleet.
If the physical objective is zero, combine its witness with F >= 0.
Otherwise initialize the full potentially improving true-G root interval.
Repeat the original controller until its legal termination:
    select an eligible active interval under the original scheduling rules;
    load/build its canonical model, original cutoff and M-B representation;
    run the original LP/lookahead, AM action and partial/terminal MIP steps;
    restore the captured integer/binary types before every original MIP;
    map only eligible own physical Starts using the original full-column mapper;
    verify each own native witness before publishing physical U;
    update scoped lower bounds and the original complete interval cover;
    commit an actual split only when the original controller chooses it.
Return own physical U, qualified complete-cover L and exact cover obligations.
```

Equal-capacity vehicle normalization retains the original stable order by
decreasing operation count within each capacity class and assigns ascending
vehicle IDs. Start validity covers every column, bound, type, row, objective
and native readback. Model/cache bindings include canonical bytes and epoch.
Lookahead child models are not evidence of active decomposition.

## Bound scope and termination correctness

For nonnegative penalty, a true-G interval's lower endpoint is an objective
floor. Scoped LP/MIP bounds apply only to the matching model, physical true-G
interval and qualified cutoff. Original improving solutions lie below the
own incumbent cutoff; the high-G complement is excluded by its objective
floor. A committed parent split must cover its entire original interval
without a hole. Aggregate lower bounds require every improving interval,
successful returned native proof or already committed callback, and complete
partition discharge. A saved `open` leaf may be irrelevant or discharged by
an independently supported whole-leaf bound; its label alone is insufficient.

A local native optimum or numerical \(U-L\) closure does not certify the
original problem. Complete certification additionally needs the own physical
witness, covered true-G domain and all relevant obligations discharged with
the original \(10^{-7}\) closure tolerance. Signed tiny negative gaps remain
visible. Valid `overall_global_deadline` and time limits are ordinary censored
results. Physical \(T\), experimental cap and complete observation time are
different quantities; the 30-second safe shutdown reserve lies inside cap.

## Conditional zero-optimum interpretation

If lambda>0 and every station weight is positive, F=0 is equivalent to Y=D.
If total initial inventory also equals total target, nonnegative return loads
then force every vehicle to return empty. A balanced or surplus label alone
does not establish that this Y=D fleet is route/time feasible.

For a role with an actually proved feasible Fstar=0 fleet, the original global
floor L=0 is already optimal. When own U is still positive, that zero fleet
can be legally embedded in both the root and left-child domains, both child
LPs are feasible, and the original controller actually enters AM scoring,
root/left LP optima are zero in exact mathematics. Their minimum child-domain
gain is zero, so this positive-gain score does not trigger a split. This
argument is conditional on the domains and actual path: own U=0 at startup
closes independently, and an INF child retains the original separate
partition/contraction logic. A stronger representation may affect integer
search, but its gain on such a role cannot be explained as raising a valid
global lower bound above zero. No forced split or new cut is introduced.
## Numerical evidence and the entry repair

The only production repair replaces the payload-length regular expression in
`Parser.cpp::namedBracketPayload` by the unchanged first legal name/whitespace/
equals/left-bracket prefix match, followed by a first-right-bracket scan.
Number token conversion, integer rounding, legacy weights, point order,
distance evaluation and all model/search parameters retain their old behavior.
The final PE has a new SHA256 identity and the original 2MiB stack. Same-
toolchain old/new C++ mathematical dumps agree byte for byte for all12 inputs;
the final PE itself passed all12 zero-Optimize common-main entries and the five
fixed functional CLIs before performance admission. This is engineering
recovery, with no new mathematical mechanism. See `repair_scope.md`,
`repair_evidence.json`, `production_identity.json` and the qualification raw.

Raw flags, callback bounds, API journals and native statuses remain distinct
from independent physical and mathematical qualifications. A numerical lower-
bound contradiction requires a witness in the exact questioned call's domain,
including model, types, all rows/bounds, true-G interval and cutoff. Reject all
native lower claims of that call and every necessary dependent closure or
cover discharge; rebuild the full-domain cover from surviving legal evidence.
An outside-domain better solution cannot refute a local bound. Cross-arm
witnesses are offline counterexamples, never that arm's UB, Start or route.

The original F>=0 floor follows from the current input's nonnegative weights,
lambda and true G. Its own exact physical F=0 witness can certify independently
against that floor; a positive own U with only that floor is still open. This
evidence repair does not repair native numerical behavior. Missing returned
journal events, raw false flags and unavailable exact whole-arm clocks remain
missing, false and null respectively. Outward timing intervals justify a class
only when the entire interval rectangle gives the same class and severe flag.
Actual failure sources and separately signed current-call corrections remain
in `current_numerical_evidence.md` and the raw/review directories.

The corrected historical G50-C1 account is three LP calls plus one terminal
MIP for each ENS/M-B arm, including an ENS native_MIPSOL F=0 witness. It must
not be described as zero Optimize or HGA-only. Actual Round110 call/Start,
coverage, split and cost findings are reconstructed from its own42 raw arms.

The last G100-R2 Seed1 M-B native process ended within its original cap, but
required postexit audit completed at3600.707823600038 seconds and the whole
receipt records3600.7215734999627. A native-only within_cap flag does not
qualify this complete clock. The final offline reader retains the exact time,
marks that formal arm invalid, and forces BLOCKED. No clock forgiveness,
window extension or performance rerun is used. This is a resource/protocol
failure rather than an observed Seed loss or an integer-model defect.

## Established components and this round's new evidence

The original formulation and controller are inherited contributions.
[R100 mathematics](../unified_exact_round100/mathematical_algorithm.md) gives
the quantity-integrality equivalence, two valid rows, all-quantity guard and
Start/domain contracts. [R108 representation](../unified_exact_round108/representation_contract.md)
and [R108 report](../unified_exact_round108/final_report.md) establish the
unchanged uniform candidate and finite measured advantages: six P wins and
one tie, with ENS losses on F2/F5/N36 and a severe F5 loss. R108 L48 exercised
two real parent splits, one AM-scored split, and two simultaneous relevant
leaves; this does not reopen the stopped R107 assignment/STRUCT configuration.

Round109 originally froze 12 public-source geographic derivatives at real
V20/V50/V100, 36 Seed0 arms and three predetermined repeated roles with six
P/M-B Seed1 arms. Round110 keeps the same bytes, draw, order, caps, thresholds
and candidate. It adds an entry repair and new confirmation observations,
without an identified causal effect of p/d declarations, the two rows or native
branching. Coordinates/capacities derive from one public 443-station source;
targets, inventory, depot, fleet and horizon are synthetic, and subsets can
overlap. These are not independent cities or 12 iid geographical samples.

The present decision is BLOCKED, rather than broad-panel support or a measured
performance rejection. Main M-B/P and ENS/P each give11WIN/1TIE. M-B/ENS gives
5WIN/3TIE/4LOSS, with severe G50-C1 and G100-R2 losses. The qualified Seed1
pairs give G20-C2 TIE and G50-R1 WIN; G100-R2 is UNEVALUABLE due to its complete
clock. Thus all measured main P gates pass, but the required all42 qualification
and complete three-role Seed assessment do not hold. No formal stability or
completed paper-benchmark claim follows.

The new G50-C1 arms both execute3LP+terminal MIP, start from equal complete
physical fleets, and repeat the one-bike completion gap. M-B serves all50
stations, with Y20=8 versus D20=9; vehicle1 pickup4 at20 and a different
vehicle2 return1. Reducing only that pickup by one gives vehicle1 a negative
later prefix at47. ENS obtains its own exact zero fleet by native_MIPSOL;
M-B remains ownU=.008182628062360805/L0. G100-R2 M-B has ownU
.011434738339920945 versus ENS.005528455284552848 and both remain uncertified;
its zero optimum is unproved. See final_report.md and mechanism_analysis.json
for every loss, G/P/stock/route trajectory and the limits of causal inference.

Formal native calls are93LP+7child-bound-target MIP+41terminal/cold MIP;
there are zero NEXT-target calls and zero real parent splits, with at most
one relevant active leaf. R108's prior multi-leaf exposure remains separate.
Actual V100 LP cost is substantial on C2; R1 is predominantly MIP, and C1/R2
have substantial startup/MIP costs. No uniform new bottleneck is identified.
These are additional finite observations of the inherited candidate, not new
mathematical or algorithmic contributions. No stage changes ENS defaults,
claims statistical significance or authorizes a new variant.

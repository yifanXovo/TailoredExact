# Frozen ENS-MB research candidate

Round111 stage: **CONFIRMATION_SUPPORT**. Evidence layer: `R110_MAIN_36_PLUS_R111_SEED_6`.

This is the unchanged R110 production candidate and equivalent engineering audit, with inherited36 main observations plus six new fixed Seed1 observations. ENS-C remains default; cold P-GRB remains primary. The old R110 BLOCKED and arm42 UNEVALUABLE are immutable. All six current arms ran once; no new independent sample or cross-wrapper exact speedup is claimed.

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

## Current finite support and limits

Current fixed Seed pairs: G20-C2 TIE, G50-R1 WIN, G100-R2 WIN. Stage reason codes: []; blockers: [].

Main M-B/P and ENS/P each11WIN/1TIE on the same eleven roles. M-B/ENS5WIN/3TIE/4LOSS includes severe G50-C1/G100-R2 costs. R108 C2 is the distinct historical benchmark-gap repair; F5 and other ENS costs remain disclosed. No ENS pointwise-dominance gate is introduced.

R108 L48 has two real parent splits per method, one INF-half retaining partition and one AM positive-score split, at most two relevant active leaves. R110 has zero real splits and at most one leaf. Lookahead/child-target models do not establish committed multileaf decomposition. G50-C1 repeatedly shows equal initial fleets,3LP+terminal MIP and the one-bike gap under the same Seed0; its prescribed pickup20-minus-one replay violates the later vehicle1 prefix at47. That finite fact identifies no general cause. R110 G100-R2 was mostly an own-UB gap. G100-R2 has no established zero-optimum proof in the retained historical or new current observations. F2 separately distinguishes a target-valued witness from completed certification.

Single-source geographic coordinates/capacities, synthetic inventories/targets/fleets/T, overlapping subsets, fixed lambda/max-normalized weights and few Seeds limit external validity. V100 startup/LP/MIP costs depend on role; constant lambda does not imply scale-invariant tradeoffs. The audit reduction is engineering, not a new mathematical mechanism. Numerical native-bound rejection still needs an exact in-domain current-call counterexample and removal of all dependent claims; root zero is outside a positive-G right domain. OwnU>0 with floor0 is open; missing raw events and null times remain missing/null.

Two remaining questions: (1) Does the G50-C1 one-bike gap survive controlled causal separation of representation and integer-search trajectory? Equal starts and calls are known; identification is missing. (2) Can a valid Windows/IO trace consume the measured reserve? Finite replay costs qualify this campaign but do not prove a worst-case bound. No further mechanism, solver run or default change is authorized by this specification.

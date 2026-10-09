# Frozen ENS–M-B research candidate

Round109 stage is BLOCKED: the first V100 native entry suffered an actual
stack overflow, leaving24 valid normal arms, one failed arm and17 unstarted
arms. A different-PE repair would require all42 arms and exceed the frozen
resource limits. This specification establishes no broader performance
support or rejection from the incomplete panel. ENS-C remains the default
reference algorithm. Actual evidence is in `main09_stack_failure.md`.

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
Round109 uses \(\lambda=.15\), \(t_p=t_d=60\), and weights normalized by their
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

Round109 adds 12 prospectively frozen public-source geographic derivatives
at real V20/V50/V100, 36 Seed0 paired arms, and three predetermined repeated
roles with six P/M-B Seed1 arms. It adds neither a mathematical mechanism nor
an identified causal effect of p/d declarations, the two rows or native
branching. Coordinates/capacities derive from one public 443-station source;
targets, inventory, depot, fleet and horizon are synthetic, and subsets can
overlap. These are not independent cities or 12 iid geographical samples.

`BROAD_PANEL_SUPPORT`, if all frozen conditions hold, supports closing this
uniform candidate for paper research with the disclosed finite claims.
`BROAD_PANEL_NOT_SUPPORTED` prevents that promotion while retaining this
specification and all results. `BLOCKED` records unresolved evidence or
resource faults. No stage changes ENS defaults, claims completed paper
benchmarks, establishes statistical significance or authorizes new variants.

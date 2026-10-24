# A tailored exact method for static bicycle redistribution with inventory-ratio dispersion

## Abstract

Static bicycle redistribution couples final station inventories with time- and capacity-feasible vehicle routes. We minimize the Gini dispersion of inventory-to-target ratios plus weighted relative target deviation, under empty departure and unique nonzero one-way service. GI-TBC in its uniform pair-support implementation, S2, combines a paid finite feasible startup, shared inventory-state/service reconstruction, valid physical and objective-domain rows, and a complete Gini-interval controller around native LP/MIP calls. Standard product linearizations are distinguished from problem-specific linking and scoped proof coverage.

On six known final-version problems at two solver Seeds, S2 and cold compact P certify ten and five observations; two comparisons remain open. A separate repeated tiny layer contains nine strict time Wins and three strict Losses. Both final-version V35 boundary observations remain open. We add a fixed twelve-input validation across known sources and a third geography, together with equivalent-expression cost diagnostics and a bounded joint-structure study. Their complete results are reported by evidence layer without treating Seed repeats as new problems. All certificates follow an explicit floating-point qualification policy. Neither universal speedup, matched performance on different BRP variants, nor a stronger relaxation from an equivalent expression is presumed.

## 1. Motivation and research questions

A redistribution plan cannot choose station inventory independently of the vehicles that realize it. Limited travel and handling time restrict attainable movement, while intermediate vehicle loads couple pickups and deliveries. The objective adds a second interaction: its dispersion denominator depends on the same final inventories that routes determine. A low ratio-Gini score alone can therefore mask undesirable target shortages, and a strong local relaxation need not improve complete certification time.

We ask three questions. First, how can finite station inventories share product and service representations without changing the physical problem? Second, what complete-method evidence supports that representation relative to a cold compact model and independently paid feasible-start controls? Third, which apparent strengthening mechanisms actually change the physical/objective projection, and which instead change the native processing of an equivalent relaxation?

Our contribution is the specified integration and its problem-specific derivations, complete covering algorithm and finite evidence. Binary-continuous envelopes, value-disjunction ideas, native presolve, cuts and branching have established origins. Source identities and reproduction records support the claims but are not counted as separate scientific innovations. A contribution/history table in the supporting material states the exact scope of each claim and its latest corrections.

Related work must be compared by semantics as well as size. Gupte et al. study bounded integer-continuous products and MILP representations; Köppe et al. formalize value-disjunction linking and aggregation [@gupte2013; @koppe2008]. Neighboring redistribution models prescribe different target fulfillment, visits, depot supply and uncertainty [@bruck2019; @bulhoes2018; @bruck2025]. Their station counts do not establish a matched speed comparison. The compact literature table records the original text/version and the exact level read.

## 2. Physical decisions and objective

Let \(N\) be the set of \(n\) service stations and \(0\) the depot. Each station has integer initial inventory \(b_i\) and capacity \(C_i\), integer target \(0<D_i\le C_i\), and nonnegative weight \(\omega_i\). Vehicle \(k\) has capacity \(Q_k\) and physical route-duration limit \(T\). Routes leave empty and return to the same depot; loaded return is allowed and its unloading is charged. A station has at most one nonzero service by one vehicle in one direction. Inventory, assignment, route arcs and prefix load retain their original integer logic. The validated distance convention is Euclidean travel seconds from serialized metre coordinates at 1.5 m/s.

With pickup \(p_{ki}\) and delivery \(d_{ki}\),

\[
Y_i=b_i+\sum_k(d_{ki}-p_{ki}),\qquad
R_k=\sum_i(p_{ki}-d_{ki})\in[0,Q_k],\qquad
\sum_iY_i=\sum_i b_i-\sum_kR_k.
\]

The depot enters none of the inventory, target-penalty or Gini sums. Total final station inventory need not equal its initial total. No external depot supply or split service is assumed. \(Q_k\) bounds instantaneous loads and individual operations, not cumulative pickup. Route travel plus handling is bounded by \(T\), where

\[
t_p\sum_i p_{ki}+t_d(\sum_i d_{ki}+R_k)
=(t_p+t_d)\sum_i p_{ki}.
\]

For \(\lambda\ge0\), define

\[
r_i=Y_i/D_i,\quad S=\sum_i r_i,\quad
A(r)=\sum_{i<j}|r_i-r_j|,\quad
P_{true}=\sum_i\omega_i|r_i-1|,
\]
\[
G_{true}=\begin{cases}A(r)/(nS)&S>0,\\0&S=0,\end{cases}
\qquad F=G_{true}+\lambda P_{true}.
\]

The zero-denominator branch is explicit. \(G_{\mathrm{true}}\) measures station ratio dispersion, not distance to targets. The second term discourages uniformly low inventory ratios that could otherwise have zero dispersion. These quantities do not by themselves establish population, income or demand fairness.

For \(\Omega=\sum_i\omega_i>0\), define \(P_{\mathrm{avg}}=P_{\mathrm{true}}/\Omega\) and \(\rho=\lambda\Omega\). Then \(F=G_{\mathrm{true}}+\rho P_{\mathrm{avg}}\). The generator normalizes weights by their maximum, not their sum. Fixed \(\lambda=.15\) therefore gives different \(\rho\) across inputs and sizes. We retain those objectives and report \(\Omega,\rho\); no sensitivity claim across \(\rho\) is made without a corresponding experiment.

Appendix A gives the complete canonical model, actual bounds, physical embedding, strengthening formulas and numerical qualification. Its \(e_i\ge|r_i-1|\), \(P=\sum_i\omega_i e_i\) and epigraph \(g\) need not be tight at arbitrary relaxation points. A claim about physical objective equality refers to tight completion, not to every native feasible point.

## 3. Shared station states, service and valid strengthening

For the finite inventory domain \(\mathcal Y_i\), S2 uses binary selectors \(s_{iy}\) and continuous \(q_{iy}\) to represent inventory and \(gY_i\) products by

\[
\sum_y s_{iy}=1,\quad Y_i=\sum_y ys_{iy},\quad
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\quad
\sum_yq_{iy}=g,\quad Z_i=\sum_y yq_{iy}.
\]

At a one-hot inventory selector, these equations give \(Z_i=gY_i\). The retained common-state service relations are

\[
\sum_kp_{ki}=\sum_y(b_i-y)^+s_{iy},\quad
\sum_kd_{ki}=\sum_y(y-b_i)^+s_{iy},\quad
\sum_kz_{ki}=\sum_{y\ne b_i}s_{iy}.
\]

They share the inventory mixture with movement and unique service. This is useful in a problem in which route resources constrain exactly those movements. It is not a claim that a local state hull is the full routing hull. With integer \(Y_i\) and binary unique assignment/direction, the single nonzero operation is already the integer inventory difference; continuous \(p_{ki},d_{ki}\) therefore preserves the stated integer physical solutions. The A/B linking rows strengthen and organize the relaxation but are not a necessary premise for that direct integrality argument.

For an isolated product, the convex hull over finite y equals the rectangle McCormick hull with the same extreme inventory bounds. The four graph corners give one inclusion and each allowed state line lies in that hull, giving the reverse. Thus the mere VD-P label does not establish strict dominance over a correct aggregate MC block. Shared service/cost links, actual domains and the native expression must be examined separately.

The remaining valid static rows use inventory, direction, reachability, ordered supply, pair-support duration and objective-domain information. Pair support is retained uniformly; triple support is omitted uniformly. All other frozen components remain active according to their actual resolved profile. Physical validity is proved by embedding every legal original fleet into the strengthened interval formulation at its true G and tight penalty. Appendix A states each row family and its assumptions; the method does not choose a different expression by input identity or elapsed machine time.

## 4. A complete interval algorithm

H is a finite construction and descent procedure. It builds a verified fleet by joint insertion; generates 24 shuffled station/separator orders under a fixed seed and a completed constructive order; fully decodes them; performs guided first-improvement order descent; and alternates strict physical quantity/insertion closure with neutral balanced relocation and equal-net exchange. This active path runs no genetic generations. Every integrated comparison pays for its own H, mapping, physical checks and Start. H supplies an upper bound, never an optimality certificate.

The controller maintains an own verified fleet, U, incumbent epoch, complete interval coverage and source-qualified regional bounds. It starts with [0,min(U,(n-1)/n)] for n>1, and [0,0] for n=1. Nonnegative penalty and the bound G<=(n-1)/n ensure coverage of every physical improving solution. The cutoff complement has floor U. A leaf's NEXT milestone and child-lookahead target are search controls; requesting a target is not evidence that it was reached.

~~~text
Algorithm 1  S2
Input: physical instance, frozen settings, one complete process deadline
Output: own verified fleet/U, qualified global L, unresolved cover/status
1 Run the complete own H. Admit only physically verified fleets.
  If the inherited verified-zero policy qualifies, certify F>=0 and return.
  Without an admissible finite U, report startup failure; do not invent a cutoff.
2 Initialize root L0=[0,min(U,(n-1)/n)], or [0,0] when n=1.
  Keep the analytic cutoff complement and the complete coverage registry.
3 While the common deadline and unresolved coverage permit:
    select a controlling unit with the declared plateau/tie rule;
    process its paid LP, NEXT milestone, midpoint-child lookahead or MIP;
    qualify the actual returned source and any own physical improvement;
    atomically install both covering children only after their checks pass;
    retain all unresolved regions on timeout, UNKNOWN or engineering failure.
4 Finalize native cleanup and required outputs. Reconstruct complete coverage.
  Return the raw signed U-L with source, physical and numerical qualification;
  report a certificate only when every inherited admission condition holds.
~~~

Appendix B supplies both complete subprocedures and their precise ties, score, depth/width, caching, epoch, deadline and return definitions. No leaf decision is based on an input's identity or a machine-speed threshold. Depth/width limits terminate geometric lookahead by requesting complete MIP, not by discarding an unresolved domain.

For a model that embeds every physical point in a region with F<=c, a qualified model bound ell gives an unconditional regional floor min(ell,c). Infeasibility of that cutoff model gives c, not an infinite original-problem bound. A complete cover combines regional floors by minimum, while independent floors on the same region can be combined by maximum. Both closed midpoint children preserve their parent's union. This induction is the correctness duty of the controller; its empirical speed is a separate question.

The physical embedding and coverage proofs concern ideal arithmetic under their assumptions. Actual matrices use binary64 and native feasibility/integrality/optimality tolerances. Reported certificates use the inherited signed 1e-7 evidence policy, with settings and lifecycle checks. Tiny negative signed gaps remain raw; no clipping is used to claim strict rational equality.

## 5. Complete-method evidence and new inputs

### 5.1 Protocol and interpretation

P is the primary cold original compact benchmark. PS pays the same complete H independently and maps its fleet to the original compact model. S2R is the valid pair-only inclusive-root LP-plus-MIP control. Every arm pays H when applicable, modeling, all native calls, full Start/physical checks and required output under its own cap. Production T_produce is the certification time only for a qualified certificate. Independent postproduction verification T_verify is separate; T_total=T_produce+T_verify. Open T_cert is null, with the actual observation horizon retained. Physical T is unrelated to these computational clocks.

Threads and MIPThreads are one, H seed is fixed, and native Seeds 0/1 are repeated observations of the same problem. Native defaults and requested zero gaps are fixed. Method order is counterbalanced prospectively. Native optimization is serial and does not compete with compilation or PDF export. No arm receives another arm's incumbent, Start, bound, parameter, basis, tree or cache.

The timing environment has a recorded limitation: an initial dependency waiter repeatedly parsed completed evidence files in the background until it was repaired partway through the first new 35-station group. Immutable producer intervals determine conservative overlap with the original waiter's lifetime in the supporting timing-environment table. These durations are not measured parsing, CPU-contention or slowdown seconds; absence of that overlap also does not prove a quiescent machine. Earlier partial table refreshes also involved brief decoding work. The repair changed neither production code nor native caps and did not restart an arm. We retain the observed clocks and certificate qualifications without estimating counterfactual clean-machine times. Timing directions describe these observations; they do not isolate a causal algorithm effect under a quiescent machine, and differences between source layers cannot be attributed solely to geography.

For each comparison distinguish both certified, only left certified, only right certified, both open and unevaluable evidence. Both-certified time directions use unrounded complete certification time; one-sided certificates determine the corresponding direction. Both open is UNDETERMINED. Time ratios are confined to explicit both-certified intersections. No cap is substituted for an unknown certification time, and endpoint gaps do not predict final certification speed. Near-zero objectives are reported separately. Each arm's attained endpoint is distinct from the problem-level zero/positive/unknown stratum. A qualified legal zero establishes a zero optimum for that problem; a positive qualified lower bound establishes positivity under the numerical policy. Otherwise the optimum class remains unknown. This descriptive classification changes no other arm's U, L, certificate or time and supplies no information to production.

For magnitude only, a both-certified delay is material when slower minus faster is at least max(10 seconds, 0.10 times faster); this threshold never changes a strict Win/Lose direction. Displayed seconds are rounded to three decimals. All directions, signed differences and ratios use the unrounded supporting records, so equal-looking printed times need not be a Tie.

### 5.2 Current S2 on the known main, tiny and size-boundary panels

The main final-version evidence measures six known SC inputs at two Seeds, with 600-second caps at 15 stations and 1200 at 20. These twelve observations are not unseen validation. S2 and P certify 10 and 5 observations; strict directions are 10 Win and 2 UNDETERMINED. No predecessor M-B or ENS time is relabelled as final S2. C denotes qualified T_cert; O @ gives actual open T_produce with null T_cert.

**Table 1. Every known-main final-version observation (seconds).**

| Known problem / Seed | P | S2 |
| --- | --- | --- |
| SC-C15-S / 0 | C 460.809 | C 33.167 |
| SC-C15-S / 1 | C 469.536 | C 35.538 |
| SC-B15-S / 0 | C 12.875 | C 2.851 |
| SC-B15-S / 1 | C 16.181 | C 2.245 |
| SC-C15-B / 0 | C 242.256 | C 57.928 |
| SC-C15-B / 1 | O @ 570.429 | C 33.444 |
| SC-B20-S / 0 | O @ 1170.605 | C 982.279 |
| SC-B20-S / 1 | O @ 1170.903 | C 676.371 |
| SC-C20-S / 0 | O @ 1171.043 | O @ 1170.676 |
| SC-C20-S / 1 | O @ 1170.577 | O @ 1171.035 |
| SC-B20-U / 0 | O @ 1170.574 | C 26.893 |
| SC-B20-U / 1 | O @ 1171.024 | C 15.998 |

The separate tiny layer has two inputs, three Seeds and two opposite-order repeats per Seed. It gives 9 Win and 3 Lose; the three strict reverse differences are subsecond, while no >=10-second delay and no P-only certificate is observed. This finite absolute-overhead result is not a population noise bound.

**Table 2. Every repeated tiny final-version observation (seconds).**

| Tiny problem / Seed / repeat | P | S2 |
| --- | --- | --- |
| SM-C8-S / 0 / 1 | C 5.568 | C 2.645 |
| SM-C8-S / 0 / 2 | C 5.143 | C 2.865 |
| SM-C8-S / 1 / 1 | C 3.904 | C 3.227 |
| SM-C8-S / 1 / 2 | C 4.197 | C 2.845 |
| SM-C8-S / 2 / 1 | C 4.611 | C 3.781 |
| SM-C8-S / 2 / 2 | C 4.307 | C 4.126 |
| SM-B10-B / 0 / 1 | C 0.778 | C 0.792 |
| SM-B10-B / 0 / 2 | C 1.122 | C 0.461 |
| SM-B10-B / 1 / 1 | C 1.067 | C 0.511 |
| SM-B10-B / 1 / 2 | C 0.708 | C 0.801 |
| SM-B10-B / 2 / 1 | C 0.794 | C 0.800 |
| SM-B10-B / 2 / 2 | C 1.129 | C 0.461 |

Both original 35-station roles remain open for both methods at their 2400-second caps and original Seed 0. Their final certification-time ordering is unknown. Earlier results at 50/60 stations retain their historical M-B/ENS identity and do not extend final-S2 validation. The complete signed endpoints and all three clocks are in the supporting tables.

**Table 3. Every original known 35-station boundary observation (Seed 0; seconds).**

| Known role / method | U / L | Signed U-L | T_produce | T_verify | T_total | T_cert |
| --- | --- | --- | --- | --- | --- | --- |
| PB-C35-U / P | 0.17477189 / 0.05970290 | 0.115069 | 2370.823 | 1.107 | 2371.930 | null |
| PB-C35-U / S2 | 0.18370156 / 0.08472828 | 0.0989733 | 2370.592 | 5.475 | 2376.067 | null |
| PB-B35-B / P | 0.30555578 / 0.00000000 | 0.305556 | 2370.555 | 0.546 | 2371.101 | null |
| PB-B35-B / S2 | 0.24650447 / 0.12194212 | 0.124562 | 2370.807 | 5.246 | 2376.053 | null |

P retains the lower physical U on PB-C35-U, while S2 retains the lower U on PB-B35-B. These endpoint directions do not rank the unobserved certification times. All four T_cert entries remain null; T_total includes the separate independent verification.

### 5.3 Prospective known-source and geography-transfer validation

The new study fixes six K and six X inputs before H or optimization. K uses the existing CITI/CABI source snapshots and generator; X uses an official Chicago Divvy station snapshot with UTM16N conversion and the same synthetic target, inventory and weight rules. This changes geography, not the demand-generation mechanism and not real operational validation. The source snapshots, field provenance, missing/duplicate handling, IDs, coordinates, transformations and one-time seeds are retained. No difficulty-based filter or redraw is applied.

The six roles per layer cover shortage, balanced and surplus scenarios and compact/regional geometry at 15, 20 and 35 stations. New sets from the same source are disjoint, rather than nested enlargements. Five K roles have no overlap with the recorded historical small selections. K-35-B follows the preregistered next exposure tier and has partial historical overlap, so its stations are not all unseen. Shortage is guaranteed structurally by total initial stock below total target and positive weights/lambda; balanced or surplus zero objectives remain legitimate outcomes.

**Table 4. Fixed new-input design, physical/computational limits and effective weights.**

| Input | Source / inventory / geography | n / Q | Physical T / cap (s) | Omega / rho |
| --- | --- | --- | --- | --- |
| K-15-S | CITI / shortage / compact | 15 / [30, 30] | 3600 / 600 | 9.473371 / 1.421006 |
| K-15-B | CABI / balanced / regional | 15 / [30, 30] | 5400 / 600 | 3.312808 / 0.496921 |
| K-20-S | CITI / shortage / compact | 20 / [30, 30] | 5400 / 1200 | 11.312498 / 1.696875 |
| K-20-U | CABI / surplus / compact | 20 / [30, 30] | 7200 / 1200 | 10.561986 / 1.584298 |
| K-35-B | CITI / balanced / compact | 35 / [25, 25, 25] | 7200 / 2400 | 16.722652 / 2.508398 |
| K-35-U | CABI / surplus / regional | 35 / [20, 25, 30] | 10800 / 2400 | 15.005326 / 2.250799 |
| X-15-S | DIVVY / shortage / compact | 15 / [30, 30] | 3600 / 600 | 5.106124 / 0.765919 |
| X-15-B | DIVVY / balanced / regional | 15 / [30, 30] | 5400 / 600 | 3.678125 / 0.551719 |
| X-20-S | DIVVY / shortage / compact | 20 / [30, 30] | 5400 / 1200 | 6.585322 / 0.987798 |
| X-20-U | DIVVY / surplus / compact | 20 / [30, 30] | 7200 / 1200 | 7.899997 / 1.185000 |
| X-35-B | DIVVY / balanced / compact | 35 / [25, 25, 25] | 7200 / 2400 | 9.884375 / 1.482656 |
| X-35-U | DIVVY / surplus / regional | 35 / [20, 25, 30] | 10800 / 2400 | 9.621875 / 1.443281 |

All twelve inputs have independently paid P and S2 at both Seeds: 48 arms. The preselected 15-S, 20-U and 35-B role in each layer also has PS at both Seeds: 12 additional arms. The PS subset is fixed without reference to which method wins. K/X, sizes and positive/zero outcomes are reported separately; shared controls and Seed repeats are not independent new problems.

The prospective layer currently has 20 of 60 sealed formal observations. Results are pending until the fixed complete table and its final evidence review are available; no provisional trend is used for method selection.

**Table 5. Every fixed new-input method position (seconds).**

| New input / Seed | P | S2 | PS (preselected subset) |
| --- | --- | --- | --- |
| K-15-S / 0 | O @ 571.093 | C 112.642 | O @ 570.602 |
| K-15-S / 1 | O @ 570.746 | C 114.759 | O @ 571.207 |
| K-15-B / 0 | C 478.447 | C 29.201 | not selected |
| K-15-B / 1 | C 465.514 | C 36.323 | not selected |
| K-20-S / 0 | O @ 1171.019 | O @ 1171.416 | not selected |
| K-20-S / 1 | O @ 1170.687 | O @ 1171.715 | not selected |
| K-20-U / 0 | O @ 1170.818 | C 5.800 | O @ 1171.322 |
| K-20-U / 1 | O @ 1171.688 | C 5.158 | O @ 1170.895 |
| K-35-B / 0 | pending | pending | pending |
| K-35-B / 1 | pending | pending | pending |
| K-35-U / 0 | pending | pending | not selected |
| K-35-U / 1 | pending | pending | not selected |
| X-15-S / 0 | pending | pending | pending |
| X-15-S / 1 | pending | pending | pending |
| X-15-B / 0 | pending | pending | not selected |
| X-15-B / 1 | pending | pending | not selected |
| X-20-S / 0 | pending | pending | not selected |
| X-20-S / 1 | pending | pending | not selected |
| X-20-U / 0 | pending | pending | pending |
| X-20-U / 1 | pending | pending | pending |
| X-35-B / 0 | pending | pending | pending |
| X-35-B / 1 | pending | pending | pending |
| X-35-U / 0 | pending | pending | not selected |
| X-35-U / 1 | pending | pending | not selected |

## 6. Expression mechanisms and joint-structure limits

### 6.1 What existing paid-start and root controls establish

Known paid-H controls provide scoped backend evidence. On UC-B20-B, S2 saves 233.716 and 123.613 seconds against independently paid PS at the two Seeds. On UC-C20-U, S2 certifies at both Seeds while PS remains open. Every method stays open on the UC-B30-S shortage boundary. These three known problems are attribution evidence, not new-input validation.

The outer-package comparison is mixed/time-close. UC-B20-B exposes three natural splits at each Seed, yet S2R certifies in 1.398 and 1.586 seconds versus S2 in 3.559 and 3.504. Across the four both-certified S2/S2R observations, strict directions are three Lose and one Win; all are time-close under the declared absolute/relative materiality rule. A zero split count also does not mean no child LP was probed. Accordingly we do not attribute all speed to decomposition or disaggregate a bundle's effect among its individual rows. Earlier reverse/open outcomes and the selected tuned-P holdout's adverse 0/3 versus cold-P 1/3 certificate result remain in the historical supplement.

### 6.2 Two equivalent-expression propositions

Compare models on the same input, domains, G interval, cutoff and objective, projecting to all common physical/target-objective coordinates while allowing other auxiliaries to reoptimize. Projection inclusion, the current LP optimum and full search cost are different questions.

First, deleting only H-spread and the two centering families leaves the ideal projection unchanged under the audited H-use and additive-bound conditions. At a zero lower endpoint set H_ij=|r_i-r_j|. At a positive endpoint retain enough additional H mass to meet the total floor, interpolating between absolute differences and the truncated individual upper bounds. The capacity inequality for that interpolation is proved in Appendix C. The remaining Gini epigraph, total cap/floor, scalar/SP rows, bounds and domain generation stay in the model; the entire geometry package is not declared redundant.

Second, eliminate continuous zero-cost W_SP from its actual MC rows, SP cutoff and bounds by retaining every lower/upper compatibility and lower-plane cutoff combination. This is complete Fourier-Motzkin projection. Inflated native P can lie outside the tight physical penalty estimate, so discarding the compatibility rows or retaining only two cutoffs without proved domain premises can be invalid. The original unmultiplied objective cutoff is retained at S=0. Degenerate boxes and lambda=0 are treated explicitly.

These are ideal algebraic projection results. Serialized H bounds and projected coefficients have rounding effects, separately audited against the original numerical policy. Finite LP agreement and residual checks are implementation evidence, not a theorem of exact rational equality for every binary64 matrix. Equivalent projections can still differ in size, presolve, native cuts, root processing and branching.

The known-role cost panel contains four problems, two Seeds and three expressions: same-build S2R, deletion of exactly the three geometry families, and full W projection. It has 24 independently paid workflow arms and eight shared baseline observations. Each candidate has eight repeated baseline comparisons; their sixteen typed comparisons are not independent trials. No combined candidate or input-specific expression is run.

Both research expressions passed their actual-matrix, default-off, behavioral and physical Start qualification. The fixed cost panel is awaiting serial execution; this qualification is not a performance result.

**Table 6. Every fixed same-build expression workflow (seconds).**


### 6.3 What a new joint quantity structure would have to add

Let R_k be a complete finite necessary service domain and v_k its pickup, delivery and assignment vector. Convexifying each vehicle independently and then imposing unique service gives P_sep. Convexifying jointly unique integer selections gives H_joint, which is contained in P_sep. That elementary inclusion is not itself a new result. A useful increment must survive the current canonical model, single-station theta, event rank and relevant inventory-route structure, with exactly the same R_k on both sides.

The existing independent-support/unique-access bound cannot separate points already in the product of those vehicle hulls with unique service. A genuinely joint weighted support maximum is a possible stronger object. Its exact maximum or a reliable upper bound is required as a valid cut RHS; a feasible solution or a restricted column maximum supplies only a lower bound. Quantity-weighted supports must be distinguished from event-count ranks that already exist.

The finite complete four-station joint-structure comparison is preregistered. Its required computation remains pending; later full-source diagnostics and any production algorithm are conditional on a valid incremental structure and a complete outside-station interface.

The complete tiny universes have four stations with capacity 2, target 1 and weight 1; all station and depot coordinates coincide. Both pickup and drop take 60 seconds per bicycle, including return unloading, and lambda is 0.15. J2/J3 cover shortage under two handling budgets; J1 is a balanced control and J4 is the physical startup-zero control. The current canonical continuous reference uses the same complete car plans on both sides, together with theta, exact same-domain threshold ranks and all 30 inventory-route subset rows. The original micro objective is reoptimized after adding every joint column. An artificial canonical model for J4 is reported separately from production backend exposure.

**Table 7. Complete tiny domains and their actual joint-structure outcomes.**

| Case / initial inventory | Q / physical T | Car plans / joint pairs | Reference / joint objective | Full-reference witness |
| --- | --- | --- | --- | --- |
| J1 / [2, 0, 1, 1] | [1, 2] / 240 | pending | pending | pending |
| J2 / [2, 1, 0, 0] | [1, 2] / 240 | pending | pending | pending |
| J3 / [2, 1, 0, 0] | [1, 2] / 360 | pending | pending | pending |
| J4 / [1, 1, 1, 1] | [1, 1] / 240 | pending | pending | pending |

An exact strict entry denotes a rational extension in the entire saved reference matrix and an exact complete-universe support RHS. A numerical-only entry lacks that strict extension. No separated tested normal means only that the fixed finite directions did not separate; it is not a hull-equivalence conclusion. Original-objective values remain qualified native floating-point observations rather than exact rational optimality proofs. The supporting joint note retains controls, coefficients, witnesses or explicit obstacles and measured costs.

## 7. Operational meaning, limitations and next step

Reported fleets are interpreted through physical Gini, P_avg, final inventories, serviced stations, pickups/deliveries, loaded return and route travel/handling/prefix resources. A smaller ratio dispersion can coexist with target shortages; the penalty and actual service outcomes must be read together. Omega/rho varies because the original weights are not sum-normalized. No policy or sensitivity conclusion is inferred for an untested weight range.

**Table 8. Operational outcomes of existing and new legal S2 fleets.**

The complete operational table is pending the sealed workflows; no synthetic service outcome is invented.

An existing valid 35-station S2 fleet illustrates why these definitions matter. Its first vehicle picks up 58 bicycles over its route with Q=20 and a maximum prefix load of 20. Across the fleet, 38 bicycles return to the depot, reducing station stock from 660 to 622. This legal loaded return and repeated use of vehicle capacity would be excluded by the incorrect bound \(\sum_i p_{ki}\le Q_k\) or a fixed station-stock equality. The example remains an open historical timing observation; its physical validity does not certify optimality.

The finite inputs, synthetic inventory mechanism, Euclidean distance convention, current parser/physical semantics and single backend limit performance generalization. Finite manageable inventory states, nonnegative inventories, positive targets and unique one-way service are explicit mathematical premises. A constructible formulation in another problem does not imply measured cross-problem performance. Timeouts, reversals and lack of objective increments constrain the claims.

Fractional reformulations remain a possible separate comparison. For S>0,

\[
F=\frac{A(r)+n\lambda S P_{true}}{nS},\qquad
\min\{A(r)+nS(\lambda P_{true}-\eta)\}
\]

is the corresponding parameter subproblem. Its numerator is not simply linear because S P_true remains. Existing MILFP work is relevant background [@yue2013], but applying it here requires an exact treatment and globally qualified subproblem bounds plus the separate S=0 branch. We do not infer that general methods are mathematically unusable from an old toy comparison, nor report an unimplemented method as a weak benchmark.

The final research recommendation is tied to the completed new-input and structural evidence. The frozen S2 paper does not wait for a new candidate to win. A negative or mixed bounded study can support freezing the current method and preparing a scoped submission, while a proved and computationally meaningful increment can motivate one separately frozen next study. No universal speed or target-journal guarantee is part of this conclusion.



\clearpage

# Appendix A. Complete model, scoped strengthening and proof obligations

**Current frozen method.** The sole method is S2/MS2. All R125 equations, physical embeddings and valid-cut derivations below are retained. Only two-station support is active in S2; the general three-station proof describes the historical full-M-B option and is not an active-row claim. Numerical proof-shortcut and inclusive-root qualifications retain their stated domains.


This appendix is the single maintained model specification for the manuscript. It transcribes the frozen writer, including constraints sometimes redundant for integer solutions. It does not replace the implemented model by a different vehicle-routing formulation. Equations are mathematical real-arithmetic expressions; A.7 states the separate numerical implementation boundary. Historical source-line pointers retained in this derivation refer to snapshot 355eefd2be3fe5651195681faf7b3a63ee4032f8. The current frozen E3 production source base is 7564a5415331b380e24d1ec06936dcfd56557e67 [@frozenImplementation]; E3_binding.json supplies its exact current source identities. The active state/service, H-use, uniform pair-only and legal inclusive-root conditions are checked against that current source, rather than inferred from historical line numbers.

## A.1 Sets, data and variables

Let \(N=\{1,\ldots,n\}\) be service stations, \(N_0=N\cup\{0\}\), \(K=\{1,\ldots,m\}\), and \(A=\{(i,j)\in N_0^2:i\ne j\}\). Depot 0 is absent from every inventory, ratio, weight and Gini sum. Vehicle indexing is shifted by one relative to source indices \(0,\ldots,M-1\). All vehicle-indexed formulas hold for each \(k\in K\); all station formulas hold for each \(i\in N\), unless otherwise stated.

Station capacity \(C_i\) and initial inventory \(b_i\) are integers with \(0\le b_i\le C_i\); target inventory \(D_i\) is a positive integer no larger than \(C_i\). The parser's depot capacity/stock fields do not provide departure supply. Vehicle capacity \(Q_k>0\) is integer. A vehicle starts empty and returns to the same depot, possibly loaded. Travel time \(\tau_{ij}=\|v_i-v_j\|_2/1.5\) uses the serialized planar coordinates. The route horizon is \(T\); unit pickup/drop times are \(t_p,t_d\), with \(h=t_p+t_d\). Penalty multiplier \(\lambda\ge0\) and station weights \(\omega_i\ge0\) are data; the study uses \(\lambda=.15\), positive weights and \(t_p=t_d=60\). No inventory floor is imposed by the compatibility field min_ratio.

The binary variables are arc decisions \(x_{kij}\), station service assignments \(z_{ki}\), and pickup-direction indicators \(a_{ki}\). Source calls the last variable mName(k,i); we rename it \(a\) to avoid confusing it with the fleet size. Pickup \(p_{ki}\), drop \(d_{ki}\), final inventory \(Y_i\), and post-service load \(\ell_{ki}\) are nonnegative. The rank \(u_{ki}\) is continuous. Define \(\bar p_{ki}=\min(b_i,Q_k)\) and \(\bar d_{ki}=\min(C_i-b_i,Q_k)\).

| Variable | Domain and bound in the active formulation |
|---|---|
| \(x_{kij},z_{ki},a_{ki}\) | Binary, for all stated indices; no self arcs |
| \(p_{ki},d_{ki}\) | Integer for cold P and ENS-C; continuous for M-B; upper bounds \(\bar p_{ki},\bar d_{ki}\) |
| \(\ell_{ki}\) | Integer in \([0,Q_k]\), retained by all three methods |
| \(u_{ki}\) | Continuous in \([0,n]\) |
| \(Y_i\) | Integer in \([\underline y_i,\bar y_i]\); plain model has \([0,C_i]\) |
| \(r_i\) | Continuous in \([0,C_i/D_i]\) |
| \(e_i\) | Continuous in \([0,\max(1,C_i/D_i-1)]\) |
| \(H_{ij}\), \(i<j\) | Continuous in \([0,C_i/D_i+C_j/D_j]\) |
| \(g,Z_i\) | Continuous; \(g\in[0,1]\) in the unsliced writer, \(g\in[\alpha,\beta]\subseteq[0,1]\) for an interval; \(Z_i\in[0,C_i]\) |
| \(f_{kij}\) | Continuous in \([0,n]\), F0 connectivity flow only |
| \(s_{iy},q_{iy}\) | Binary inventory selectors and continuous selected-G products, for \(y\in\mathcal Y_i=\{\underline y_i,\ldots,\bar y_i\}\), VD-P only |
| \(b_{it}^{\rm bit},w_{it}\) | Binary inventory bits and continuous products, plain P only |
| \(W_{SP}\) | Continuous in \([\max(0,\underline S\underline P),\max\{\max(0,\underline S\underline P),\bar S\bar P\}]\), when the aggregate SP estimator is active |

The model objective is \(f=g+\lambda P\), where \(P=\sum_i\omega_i e_i\); \(f,S=\sum_i r_i\), and \(H_\Sigma=\sum_{i<j}H_{ij}\) are expressions, not new columns. Constants \(\underline y,\bar y,\underline S,\bar S,\underline P,\bar P\) are defined in A.5. Bound-only extrema columns r_min,r_max may still be allocated by the writer; with the shared factory their centering inequalities use the projected pair form below and those columns have only their original bounds \([0,\max_i C_i/D_i]\). No additional vehicle-used binary exists: \(v_k=\sum_jx_{k0j}\) is an expression.

## A.2 Routing, service and physical resources

The complete routing core is

\[
\sum_{j\in N}x_{k0j}=\sum_{i\in N}x_{ki0},\qquad
\sum_{j\in N}x_{k0j}\le1,
\tag{A1}
\]
\[
\sum_{j\in N_0\setminus\{i\}}x_{kji}
=\sum_{j\in N_0\setminus\{i\}}x_{kij}=z_{ki},\qquad
\sum_kz_{ki}\le1,
\tag{A2}
\]
\[
z_{ki}\le u_{ki}\le nz_{ki},\qquad
u_{ki}-u_{kj}+nx_{kij}\le n-1
\quad(i,j\in N,\ i\ne j).
\tag{A3}
\]

These are the writer's original depot degree, station degree and MTZ rows. Any selected station cycle contradicts the sum of (A3) around the cycle. Thus an integer nonempty selection has one depot-connected elementary tour; an unused vehicle has all arcs and assignments zero. A depot-to-depot empty route is represented without a self arc. The MTZ rows remain when F0 also adds the following connectivity flow:

\[
0\le f_{kij}\le n x_{kij}\quad((i,j)\in A),\qquad
\sum_{j\ne i}f_{kji}-\sum_{j\ne i}f_{kij}=z_{ki},
\tag{A4}
\]
\[
\sum_{j\in N}(f_{k0j}-f_{kj0})=\sum_{i\in N}z_{ki}.
\]

F0 here means the round20-current flow variant, including return-arc columns, with no \(f\ge x\) normalization or start-coupling additions. A route visiting \(q\) stations admits downstream-count flows \(q,q-1,\ldots,1,0\). These flows establish validity for every original route, independently of MTZ. Cold plain P does not receive this strengthening. The row package also called F0 has additional families in A.5; these two uses of the historical label must not be confused.

All protected service rows are retained:

\[
p_{ki}\le\bar p_{ki}z_{ki},\quad d_{ki}\le\bar d_{ki}z_{ki},\quad
a_{ki}\le z_{ki},\quad p_{ki}\le\bar p_{ki}a_{ki},
\tag{A5}
\]
\[
d_{ki}\le\bar d_{ki}(z_{ki}-a_{ki}),\quad
p_{ki}+d_{ki}\ge z_{ki},\quad
0\le\ell_{ki}\le Q_kz_{ki}.
\]

The first pair is not silently dropped even where implied by direction rows. Zero directional bounds cause no division. Unique service, a binary direction and the last service inequality forbid split service, simultaneous pickup/drop and zero-operation visits.

Loads are the writer's original two-sided Big-M recurrences:

\[
-Q_k(1-x_{k0i})\le\ell_{ki}-p_{ki}+d_{ki}
\le Q_k(1-x_{k0i}),
\tag{A6}
\]
\[
-Q_k(1-x_{kij})\le\ell_{kj}-\ell_{ki}-p_{kj}+d_{kj}
\le Q_k(1-x_{kij})\quad(i,j\in N,\ i\ne j),
\tag{A7}
\]
\[
R_k:=\sum_i(p_{ki}-d_{ki})\ge0,\qquad
\sum_{(i,j)\in A}\tau_{ij}x_{kij}+h\sum_i p_{ki}\le T.
\tag{A8}
\]

The first selected arc fixes departure load to zero. Selected internal arcs propagate each post-service load. A return has no service operation: its load equals the last \(\ell\), hence is at most \(Q_k\). Summing the recurrence gives \(R_k\) as that load, so its upper bound follows without a separate \(R_k\) column or explicit upper row. Inactive recurrence rows are valid because their difference is between a feasible before-service load and another feasible post-service load, each in \([0,Q_k]\). Empty vehicles have \(p=d=\ell=R=0\).

In (A8), let \(P_k=\sum_i p_{ki}\) and \(D_k^{\rm drop}=\sum_i d_{ki}\). Since \(R_k=P_k-D_k^{\rm drop}\), original handling time is

\[
t_pP_k+t_d(D_k^{\rm drop}+R_k)=(t_p+t_d)P_k.
\tag{A9}
\]

Return unloading is paid. Capacity \(Q_k\) limits every load, not cumulative pickup \(P_k\), which may exceed \(Q_k\) after intermediate drops. There is one physical time limit per vehicle and a separate computational deadline.

Inventories and objective auxiliaries satisfy

\[
Y_i+\sum_k(p_{ki}-d_{ki})=b_i,\quad r_i=Y_i/D_i,\quad
e_i\ge r_i-1,\quad e_i\ge1-r_i,
\tag{A10}
\]
\[
H_{ij}\ge r_i-r_j,\quad H_{ij}\ge r_j-r_i\quad(i<j).
\tag{A11}
\]

Consequently \(\sum_iY_i+\sum_kR_k=\sum_i b_i\). Loaded returns permit a decrease of station inventory; no external depot inventory can increase it.

## A.3 Original and disaggregated Gini objective

The physical objective is

\[
F(Y)=G_{\rm true}(Y)+\lambda\sum_i\omega_i|Y_i/D_i-1|,\quad
G_{\rm true}=\begin{cases}
\dfrac{\sum_{i<j}|r_i-r_j|}{n\sum_i r_i},&S>0,\\
0,&S=0.
\end{cases}
\tag{A12}
\]

The native epigraph is

\[
n\sum_i Z_i/D_i\ge H_\Sigma,\qquad\min f=g+\lambda\sum_i\omega_i e_i.
\tag{A13}
\]

Cold P uses inventory bits. With \(B_i=\max(1,\lceil\log_2(C_i+1)\rceil)\), for \(t=0,\ldots,B_i-1\),

\[
Y_i=\sum_t2^t b_{it}^{\rm bit},\quad Z_i=\sum_t2^t w_{it},\quad
0\le w_{it},\quad w_{it}\le g,\quad w_{it}\le b_{it}^{\rm bit},
\quad w_{it}\ge g+b_{it}^{\rm bit}-1.
\tag{A14}
\]

The capacity bound removes unused bit encodings. These products are exact at binary bits. ENS-C and M-B instead use the finite value-disaggregated perspective block VD-P:

\[
\sum_{y\in\mathcal Y_i}s_{iy}=1,\quad
Y_i=\sum_y y s_{iy},\quad
\alpha s_{iy}\le q_{iy}\le\beta s_{iy},\quad
\sum_yq_{iy}=g,\quad Z_i=\sum_y yq_{iy}.
\tag{A15}
\]

The active mode is VD-P, not VD-J: equalities reconstructing \(r_i\) or \(e_i\) from selectors are not substituted for (A10). The shared factory's bit-product McCormick rows are skipped for this block because those bit columns are absent. Products (A15) already use interval bounds. M-B additionally writes the original A/B rows

\[
\sum_k(p_{ki}+d_{ki})=\sum_{y\in\mathcal Y_i}|b_i-y|s_{iy},
\qquad \sum_kz_{ki}+s_{i,b_i}=1.
\tag{A16}
\]

A missing initial state means \(s_{i,b_i}=0\), not a new selector. The independent ENS-Q option is false. The mode-linked direction equality of another variant is absent; M-B retains its original binary \(a_{ki}\). ENS-C uses integer \(p/d\) and omits (A16). These are the material representation differences; the complete H and controller are shared.

## A.4 Integrality, embedding and fairness propositions

**Lemma A1 (implicit service integrality).** With integer \(b_i,Y_i\), (A2), (A5), and binary assignments/directions, M-B's continuous quantities are integer.

*Proof.* If \(z=0\), its quantities and direction are zero. At the only assigned vehicle, direction 1 forces \(d=0\), so \(p=b_i-Y_i\) is integer. Direction 0 forces \(p=0\), so \(d=Y_i-b_i\) is integer. No other vehicle contributes. Retained integer loads are not needed for this argument. Removing unique service, one-way direction or integer inventory invalidates the inference. The statement concerns integer feasible solutions, not equality of LP convex hulls. ∎

**Validity of A/B.** For an integer original service, total movement at a station equals \(|b_i-Y_i|\), which its selected state reproduces. An assigned service is nonzero and one-way, so \(Y_i\ne b_i\) exactly when the station is served. This proves both (A16); neither is an extra premise of Lemma A1.

**Lemma A2 (physical objective embedding).** Assume inventory domains and rows preserve all physical points assigned to a true-G interval \([\alpha,\beta]\) and cutoff \(F\le c\). Every such fleet has an extension satisfying the applicable original or VD-P groups, with \(g=G_{\rm true}\) and \(f=F\), up to permutation of identical vehicle labels if symmetry rows are present.

*Proof.* Use the physical arcs, service, load prefixes, tour ranks and downstream flows. Select its integer inventory state, put \(q_{iy}=g\) at the selected state and zero at others; (A15) yields \(Z_i=gY_i\). Set \(e_i=|r_i-1|\) and \(H_{ij}=|r_i-r_j|\). Then (A13) holds, with equality for \(S>0\). At \(S=0\) all inventories, ratios and differences are zero and \(g=0\) realizes the stipulated convention. Bounds and valid strengthening are satisfied by assumption. Conversely an integer product completion has \(Z_i=gY_i\), hence \(g\ge G_{\rm true}\) for \(S>0\) and \(f\ge F\); at zero sum, \(g\ge0\) suffices. ∎

Arbitrary native \(g\) may exceed physical Gini. A fleet with \(G_{\rm true}<\alpha\) can have an inflated-g auxiliary completion. The proof assigns physical points by their true Gini and requires their objective-preserving extension; it does not classify every completion by its auxiliary g. An inventory vector without compatible routes is not an upper-bound witness.

For \(n>1\), triangle inequalities give \(A:=\sum_{i<j}|r_i-r_j|\le(n-1)S\), so \(G_{\rm true}\le(n-1)/n\). For \(S>0\), \(G_{\rm true}=0\) means every ratio is equal; at \(S=0\) all are zero by nonnegativity. A common ratio below one is a common proportional shortage, not target attainment. If \(\lambda>0\) and all \(\omega_i>0\), \(F=0\) if and only if every \(Y_i=D_i\). These are dispersion and target-deviation statements, with no implied demographic/service/revenue interpretation.

## A.5 Enabled strengthening: construction, proofs and scope

The finite list below describes the actual M-B path, not every option in the repository. All rows are assembled **statically when a canonical interval model is written**, before its LP or MIP request. A new cutoff epoch rewrites the relevant model; it does not separate these rows at fractional native nodes. The writer supplies physical rows, and the shared interval factory supplies the interval rows. Families registered by the factory are not all rows emitted by it. In particular, the factory's bit-product rows are filtered out for VD-P. The original objective and physical constraints remain present.

### A.5.1 Construction of the inventory rectangle (D1)

Let the current true-G interval be \(I=[\alpha,\beta]\), the independently verified own incumbent be \(U_e\), and the cutoff be \(c=U_e\). **The active controller sets incumbent_epsilon to zero**, so this is a non-strict objective cutoff; a generic writer can subtract an epsilon, but that is not this frozen request. Start with \(l_i=0,u_i=C_i\). With \(\lambda>10^{-12}\), finite positive \(U_e\), and \(B=(c-\alpha)/\lambda\ge-10^{-10}\), for each \(\omega_i>10^{-12}\) intersect with

\[
l_i\gets\max\{l_i,\lceil D_i(1-\max(0,B/\omega_i))-10^{-9}\rceil\},\quad
u_i\gets\min\{u_i,\lfloor D_i(1+\max(0,B/\omega_i))+10^{-9}\rfloor\}.
\tag{A19}
\]

This is followed by one intersection with physical movement reachability. Write \(t_i=\tau_{0i}+\tau_{i0}\) and

\[
\begin{aligned}
M_{ki}&=\begin{cases}
\min\{Q_k,\lfloor(T-t_i)/h+10^{-9}\rfloor\},&T+10^{-9}\ge t_i,\ h>10^{-12},\\
Q_k,&T+10^{-9}\ge t_i,\ h\le10^{-12},\\0,&\text{otherwise}.
\end{cases}\\
l_i&\gets\max\{l_i,b_i-\max(0,\max_k\min(b_i,Q_k,M_{ki}))\},\\
u_i&\gets\min\{u_i,b_i+\max(0,\max_k\min(C_i-b_i,Q_k,M_{ki}))\}.
\end{aligned}
\tag{A20}
\]

The outer max with zero transcribes the actual zero-initialized reachability accumulators, including a slightly negative quotient admitted by a floating travel guard. The mathematical version omits the floating guards, uses \(h=0\) for the second case, and clips movement below at zero. Positive published \(h=120\) avoids the small-positive-h threshold ambiguity. If an interval becomes empty, the code flags domain infeasibility, resets that station's storage bounds to \([0,C_i]\), and emits an impossible row. The reset prevents malformed column ranges; it does not reinstate the excluded domain as feasible.

**Proposition A5 (budget and reachability).** Every physical point in \(I,F\le c\) satisfies the ideal versions of (A19)–(A20). Indeed \(F=G+\lambda P\), \(G\ge\alpha\), and nonnegative weighted deviations imply \(\omega_i|Y_i/D_i-1|\le(c-\alpha)/\lambda\). Integer \(Y_i\) gives the rounded bounds. A visited station requires a depot tour with travel at least \(t_i\). Its pickup is at most \(Q_k,b_i\), and its drop is at most \(Q_k,C_i-b_i\); because \(D_k^{\rm drop}\le P_k\), either operation is at most cumulative pickup, which has handling cost \(hP_k\le T-t_i\). Maximize over its unique possible vehicle. These are necessary, not sufficient, attainability conditions: a delivery still needs a source. Zero weight or zero lambda supplies no individual penalty bound and is skipped. ∎

**Actual order and pass count.** The writer first computes budget bounds, intersects reachability, and derives interval extrema; the shared factory recomputes this same sequence from \([0,C_i]\) and replaces the local arrays. It does not feed the first result into a second tightening pass. There is no propagation loop in this enabled path and no iterative fixed point. The preset advertises `iterative` and requested rounds 2, but the legacy completion field is capped at 1. Thus the operative definition is one budget intersection plus one reachability intersection, independently recomputed by the factory. R124's “original two passes” description was incorrect; production is unchanged.

Set \(\underline y_i=l_i,\bar y_i=u_i,\mathcal Y_i=\{l_i,\ldots,u_i\}\), and

\[
\begin{aligned}
\underline r_i&=l_i/D_i,\quad\bar r_i=u_i/D_i,\\
\underline S&=\sum_i\underline r_i,\quad\bar S=\sum_i\bar r_i,\\
\underline e_i&=\operatorname{dist}(1,[\underline r_i,\bar r_i]),\quad
\bar e_i=\max\{|\underline r_i-1|,|\bar r_i-1|\},\\
\underline P&=\sum_i\omega_i\underline e_i,\quad\bar P=\sum_i\omega_i\bar e_i.
\end{aligned}
\tag{A21}
\]

The last extrema bound the **tight physical completion** of \(e\). They do not assert that every nonminimal native epigraph \(e_i\) is at most \(\bar e_i\). There is no stock-weighted knapsack or optimization in the denominator calculation: these are sums over the rectangle, with no extra conservation-driven tightening.

### A.5.2 Physical conservation and activation (P1–P4)

The following rows hold on the full physical domain, independently of (I,c):

\[
\sum_i b_i-\sum_kQ_k\le\sum_iY_i\le\sum_i b_i;
\quad -b_i\sum_kz_{ki}\le Y_i-b_i\le(C_i-b_i)\sum_kz_{ki}\quad(i\in N);
\tag{A22}
\]
\[
h\sum_{k,i}p_{ki}\le mT;
\qquad z_{ki}\le0\quad\text{if }t_i+h>T+10^{-9}.
\tag{A23}
\]

**Proof.** Each return load lies in \([0,Q_k]\); insert this into conservation (A10). If no vehicle serves \(i\), inventory balance fixes \(Y_i=b_i\); otherwise unique assignment makes the visit sum one and the two activation bounds reduce to \(0\le Y_i\le C_i\). Sum (A8) and drop nonnegative travel for global handling. Any nonzero integer service has at least one pickup somewhere on the vehicle: for a drop use empty departure and load nonnegativity. Consequently a tour through \(i\) takes at least \(t_i+h\). The physical meaning of the historical `transfer_subset_capacity` flag here is this singleton visit exclusion, not a separate general subset-flow formulation. All vehicles and stations are enumerated in increasing index order. These inequalities are implied for integer physical points, but can strengthen the relaxation. The global-handling impossible-row diagnostic based on accumulated required pickup is inactive in the shared-factory path because that legacy accumulator is not populated there. ∎

### A.5.3 Ordered supply compatibility (P5)

For every vehicle \(k\) and receiving station \(j\), define

\[
\mathcal C_{kj}=\{i\in N\setminus\{j\}:\tau_{0i}+\tau_{ij}+\tau_{j0}+h\le T+10^{-9}\}.
\qquad d_{kj}\le\sum_{i\in\mathcal C_{kj}}p_{ki}.
\tag{A24}
\]

All stations passing this test enter the set, even those with zero stock; their pickup column is then fixed at zero. Common \(T,h,\tau\) make the sets identical across vehicles, but their pickup bounds still use \(Q_k\). No demand assumption or target sign is used.

**Proposition A6.** (A24) is necessary for a physical fleet under metric travel and empty departure. Label the integer units collected by a vehicle. Scan its route in order, assigning each delivered unit to one previously collected, not yet delivered unit. Every prefix load is nonnegative, so this matching always exists. If a unit received at \(j\) came from \(i\), the route includes the ordered subsequence (0,i,j,0). Repeated triangle inequalities give travel at least \(\tau_{0i}+\tau_{ij}+\tau_{j0}\), and its at least one collected unit entails \(hP_k\ge h\). Hence \(i\in\mathcal C_{kj}\). Counting matched units at \(j\) proves the row; a pickup unit can be delivered only once. Intermediate stations can add travel or receive other units but cannot create supply. Unmatched collected units may return to depot. An unvisited source has \(p_{ki}=0\); an empty compatibility set forces \(d_{kj}=0\). Preloading, cross-vehicle handoffs, or nonmetric shortcut assumptions would break this proof and are excluded. ∎

The row is a coarse aggregate necessity, not a claim that all compatible pickups can simultaneously reach \(j\). It neither imposes \(P_k\le Q_k\) nor substitutes for prefix loads.

### A.5.4 Two- and three-station support (P6)

For \(W=\{a,b\}\),
\[
\tau(W)=\min\{\tau_{0a}+\tau_{ab}+\tau_{b0},\tau_{0b}+\tau_{ba}+\tau_{a0}\}.
\]
For \(W=\{a,b,c\}\), take the minimum of the six expressions

\[
\tau_{0\pi_1}+\tau_{\pi_1\pi_2}+\tau_{\pi_2\pi_3}+\tau_{\pi_30},\quad \pi\text{ a permutation of }(a,b,c).
\tag{A25}
\]

These are explicit finite formulas, not new shortest-route optimization calls. Metric shortcutting of a complete tour yields one such order, so its travel is at least \(\tau(W)\).

**Lemma A7 (integer handling).** If all stations in \(W\) are served by \(k\), their nonzero integer operations give

\[
|W|\le\sum_{i\in W}(p_{ki}+d_{ki})\le P_k+D_k^{\rm drop}\le2P_k,
\quad P_k\ge\lceil |W|/2\rceil.
\tag{A26}
\]

Here \(P_k=\sum_{i\in N}p_{ki}\), not \(\sum_{i\in W}p_{ki}\): supplies may lie outside \(W\). Integer \(P_k\) gives the ceiling; the LP relaxation alone cannot justify it. Capacity does not bound cumulative pickup. Therefore the writer emits exactly one of the following rows for each selected support:

\[
\begin{aligned}
&\begin{cases}
\sum_{i\in W}z_{ki}\le |W|-1,&\tau(W)+h\lceil|W|/2\rceil>T+10^{-9},\\
h\sum_{i\in W}p_{ki}+M_{kW}\sum_{i\in W}z_{ki}\le T-\tau(W)+M_{kW}|W|,&\text{otherwise},
\end{cases}\\
&M_{kW}=T+\tau(W)+h\max\{1,\sum_{i\in W}\min(b_i,Q_k)\}.
\end{aligned}
\tag{A27}
\]

**Proposition A8 (both branches).** The cover branch follows from (A8), (A25), (A26). In the conditional branch, if every station is served, cancel \(M_{kW}|W|\). Since full travel is at least \(\tau(W)\) and \(\sum_Wp\le P_k\), the remaining inequality is necessary. If at least one is unserved, put \(q=|W|-\sum_Wz\ge1\), \(B_W=\sum_W\min(b_i,Q_k)\). The right side after moving the visit terms is \(T-\tau(W)+qM_{kW}\ge2T+h\max(1,B_W)\ge hB_W\ge h\sum_Wp\). This proves deactivation for all nonnegative \(T,h\), including \(B_W=0\), empty vehicle and \(h=0\). It does not rely on an invalid cumulative-capacity bound. ∎

**Selection is finite and ordered.** For k increasing, enumerate every increasing pair \(a<b\), then every increasing triple \(a<b<c\). One shared counter starts at zero outside the vehicle loop. The helper returns without adding a row once the counter is 50000; it increments once before choosing cover versus conditional. Outer loops continue (and can still evaluate cycle formulas), but no more rows are added. This is not “stop after 50000 violated covers”, not 50000 per vehicle, and not pairs interleaved with triples. At n=50 each full vehicle contributes 1225+19600=20825 supports; the third vehicle receives only the prefix needed to reach the shared limit. Row validity is independent of this selection policy. The dormant exhaustive-subset and rank3 variants have different coefficients/order and are excluded.

### A.5.5 Dispersion, spread and centering (G1–G4)

For every pair \(i<j\), let \(d_{ij}=|r_i-r_j|\). For each \(u\notin\{i,j\}\), triangle inequality gives \(d_{iu}+d_{ju}\ge d_{ij}\). These pairs are distinct in the unordered numerator; the omitted pairs among the other stations are nonnegative. Hence

\[
A=d_{ij}+\sum_{u\ne i,j}(d_{iu}+d_{ju})+\sum_{u<v;\ u,v\ne i,j}d_{uv}
\ge[1+(n-2)]d_{ij}=(n-1)d_{ij}.
\tag{A28}
\]

For \(n=2\) the other sums are empty and equality holds. For \(n=1\), spread and centering are skipped. For true \(G\in[\alpha,\beta]\) and \(S>0\), \(n\alpha S\le A\le n\beta S\). At \(S=0\), all ratios and \(A\) are zero; only the interval containing true \(G=0\) needs that physical embedding. With **tight** \(H_{ij}=d_{ij}\), the emitted rows are

\[
n\alpha S\le H_\Sigma\le n\beta S;\qquad
(n-1)H_{ij}\le n\beta S\quad(i<j).
\tag{A29}
\]

This proves existence of an objective-preserving completion. It does **not** prove that an arbitrary inflated native \(H_{ij}\), even at integer physical variables, satisfies the new row. For example \(r=(1,1),g=.5,H_{12}=1\) satisfies the unsliced original epigraph \(2gS\ge H\); the true-G-zero cap excludes this completion while preserving \(H=0,g=0\). Accordingly these static rows are not advertised as callback user cuts preserving all original native integer completions.

Using the retained \(H_{ij}\ge\pm(r_i-r_j)\) in the pairwise row gives the two variable-S rows, and \(S\le\bar S\) then gives the fixed rows:

\[
(n-1)(r_i-r_j)\le n\beta S,\quad(n-1)(r_j-r_i)\le n\beta S;
\quad \pm(r_i-r_j)\le\frac{n\beta\bar S}{n-1}.
\tag{A30}
\]

The fixed form is the projection of a common min/max ratio band. The allocated extrema columns do not receive that extended formulation in the shared path. All increasing pairs, forward then reverse, are generated. The ideal implication chain is (A29)+absolute-value lower rows → variable-S → fixed-S. Redundancy in ideal arithmetic is not an ablation and authorizes neither row deletion nor an individual speedup claim. The cap/floor, H-spread and signed-difference rows constrain different auxiliary completions even though they preserve the same tight physical embedding.

### A.5.6 Required movement and penalty closure (C1–C3)

For each station, emit only the applicable bound consequence:

\[
\sum_k(d_{ki}-p_{ki})\ge l_i-b_i\quad(l_i>b_i),\qquad
\sum_k(p_{ki}-d_{ki})\ge b_i-u_i\quad(u_i<b_i).
\tag{A31}
\]

These follow by substituting inventory balance in \(Y_i\ge l_i\) or \(Y_i\le u_i\). Their scope inherits the domain: a cutoff-derived \(l_i\) is not an unrestricted physical bound. If \(b_i\notin\mathcal Y_i\), A/B forces service, consistently with required movement. If \(\mathcal Y_i=\{b_i\}\), A/B forces no service. A singleton zero domain and zero operation bounds require no divisions.

For all active finite positive-cutoff requests write

\[
g+\lambda P\le c,\qquad P\ge\underline P,\qquad
e_i\le\max(0,B/\omega_i)\ (\omega_i>10^{-12}).
\tag{A32}
\]

The last row uses the same budget activation tests as A19. The floor follows station by station from the distance to 1 in (A21); the original e upper bound is retained and the budget row intersects it. \(\alpha+\lambda\underline P>c\) proves ideal cutoff infeasibility. The implementation instead tests \(\alpha+\lambda\underline P\ge c-10^{-9}\), writes an impossible row, and uses its numerical closure policy. In particular equality to c is not strict infeasibility of the non-strict cutoff set. A.7 explicitly limits this claim. The factory's “Global” metadata on the incumbent row means the entire current model, not all physical objectives at every cutoff.

Round128 clarification (the frozen ordinary rule is unchanged): if the actual cutoff-domain bound is \(L_a=\alpha+\lambda\underline P\), its unconditional regional bound is \(\min\{L_a,c\}\) by coverage with the cutoff complement. \(L_a>c\) excludes the inclusive cutoff domain; \(L_a=c\) permits equality and excludes only strict improvement. For \(c-10^{-9}\le L_a<c\), the raw supported bound remains \(L_a\) and does not rule out every arbitrarily small improvement. The impossible-row shortcut is not a physical embedding inequality for all \(F\le c\). A known witness contradicting its alleged own-domain bound takes priority for investigation. The separately defined MD-R omits only this named shortcut and checks its own Start against the inclusive root; no frozen production numerical policy is upgraded by that control.

### A.5.7 Scalar objective estimate and SP lifting (C4–C6)

For \(S>0\), multiplying the true cutoff inequality by \(nS\) gives

\[
A+n\lambda SP\le ncS.
\tag{A33}
\]

Since \(A\ge0\), \(\bar S\ge S\) gives \(A/(n\bar S)\le A/(nS)\), so \(A+n\bar S\lambda P\le n\bar Sc\) when \(\bar S>0\). Equivalently A33 implies \(A\le nS(c-\lambda P)\le n\bar S(c-\lambda P)\), because the original cutoff and nonnegative G imply \(c-\lambda P\ge0\). The emitted scalar row is

\[
H_\Sigma+n\bar S\lambda\sum_i\omega_i e_i\le n\bar S c\quad(\bar S>10^{-12}).
\tag{A34}
\]

The bound on S is the rectangular upper estimate (A21), not a new optimum of S. Tight H/e complete every physical point. If \(S=0\), then \(A=0\), \(P=\sum_i\omega_i\), and the original condition is \(\lambda P\le c\). Multiplication alone makes A33 tautological and cannot enforce that condition. Thus the original objective cutoff (A32) remains essential. A34 also holds directly at S=0 if that cutoff holds.

Introduce \(W=W_{SP}\) and take \(W=SP\) on physical completions. The four nonnegative products on the rectangle are \((S-\underline S)(P-\underline P)\), \((\bar S-S)(\bar P-P)\), \((\bar S-S)(P-\underline P)\), and \((S-\underline S)(\bar P-P)\). Expanding them proves respectively

\[
\begin{aligned}
W&\ge\underline S P+\underline P S-\underline S\underline P,\\
W&\ge\bar S P+\bar P S-\bar S\bar P,\\
W&\le\bar S P+\underline P S-\bar S\underline P,\\
W&\le\underline S P+\bar P S-\underline S\bar P.
\end{aligned}\tag{A17}
\]

These are the standard McCormick envelopes [@mccormick1976], derived here without attributing an unread theorem number. They are relaxations, not an exact continuous-product identity. The writer bounds \(W\) by \(w_l=\max(0,\underline S\underline P)\), \(w_u=\max(w_l,\bar S\bar P)\), and emits

\[
H_\Sigma+n\lambda W-nc\sum_i r_i\le0.
\tag{A35}
\]

Every coefficient is explicit: H coefficients 1; r coefficients \(-nc\); W coefficient \(n\lambda\); e coefficients in each McCormick row are the corresponding S coefficient times \(\omega_i\). The active objective remains \(g+\lambda\sum_i\omega_i e_i\) with **ObjCon=0**; W is absent from the objective. Equal S or P bounds cause valid degenerate envelopes. Zero S forces the physical W to zero but does not remove the original penalty. These rows preserve a joint tight completion of g,e,H,W and must not be claimed to preserve all loose auxiliary assignments. No GS or disaggregated-SP lift is enabled.

### A.5.8 Symmetry, skipped rows and dependency order

With the active symmetry option, if **all** capacities are equal and \(m>1\), the writer adds \(\sum_i z_{ki}\ge\sum_i z_{k+1,i}\) for adjacent vehicles. Common T, travel and handling make those vehicles interchangeable; relabel routes by nonincreasing visits to obtain an objective-preserving representative. Heterogeneous capacities skip the whole writer family. Start normalization may sort within equal-capacity classes, which is harmless relabelling but does not add mixed-fleet symmetry rows. A physically feasible labelled route need not itself satisfy the symmetry rows before relabelling.

Bit-only interval envelopes are \(\alpha b\le w\le\beta b\), \(g-\beta(1-b)\le w\le g-\alpha(1-b)\). They follow by the cases b=0,1; they are **not emitted in active VD-P**, whose q block already embeds its interval bounds. Dormant receiver-source covers, Benders, pricing, D1, exhaustive subset duration, dynamic resource cuts, custom branch priorities, S buckets, GS, AMF/RC, and old timed quanta are not part of this specification. Monitoring/target callbacks do not turn the static strengthening into dynamic separation.

The proof dependency is: physical core → implicit integer service and conservation → reachability/transfer/support; budget plus reachability → rectangle → movement/penalty/S bounds; triangle lemma plus true-G membership → Gini rows; rectangle plus original cutoff → SP/scalar rows. A/B use unique nonzero one-way service independently of the implicit-integer lemma. All can be satisfied by the same physical completion, which avoids circularly assuming the validity of a tightened domain to prove its own construction. Analytic validity and actual partial support selection are separate from computational contribution; no family-level performance attribution is made without an ablation.

## A.6 Cutoff and coverage proof

**Lemma A3 (cutoff complement).** Suppose a returned lower bound \(\ell\) is qualified for a model containing objective-preserving embeddings of every physical point with \(G_{\rm true}\in I\) and \(F\le c\). Then \(\min(\ell,c)\) is an unconditional regional lower bound.

*Proof.* A point in the cutoff set has \(F=f\ge\ell\). A point outside has \(F>c\). The minimum covers both. If the cutoff model is infeasible, only that cutoff set is empty, so c, rather than \(+\infty\), is the original-region floor. ∎

**Lemma A4 (complete cover).** Let every possible improving true-G value belong to at least one registered unit \(I\), with a qualified unconditional floor \(\beta_I\). Include the analytic complement, whose applicable floor is U. Then

\[
L=\min\{U,\min_{I\in\mathcal C}\beta_I\}
\tag{A18}
\]

is a lower bound on the original optimum.

*Proof.* Any feasible point is in the complement or at least one covering region. Its corresponding floor bounds its objective. Taking the minimum is safe for the union. Initially \(F\ge G_{\rm true}\) allows \([0,\min((n-1)/n,U)]\) as the improving Gini range. Replacing \([\alpha,\beta]\) by both closed children \([\alpha,\mu]\), \([\mu,\beta]\) preserves coverage, including the shared endpoint. Replacement commits both children atomically with their evidence. An unsplit parent, unresolved leaf, or qualified closed leaf remains represented. Induction over updates proves the invariant. ∎

Bounds on the same physical domain can be combined by maximum; the union of sibling domains requires minimum. Transfer to a narrower domain requires containing scope and a handled cutoff complement, and does not construct that domain's feasible Start. Proof identities include actual model SHA, input, call, epoch, domain, cutoff and return. A local terminal status cannot certify the whole original problem. Depth/width/scheduling limits can select a request or leave an obligation open; they cannot delete it.

For a compatible own fleet, the mapped complete Start includes unused vehicles and all auxiliaries. Setting \(g=G_{\rm true}\) outside a leaf is not a valid exact-g Start. Submission, API acceptance and an improved native incumbent are different observations. No optimality proof follows from H, repeated physical U or Start acceptance.

## A.7 Numerical implementation boundary

Lemmas A1–A4 concern ideal exact arithmetic and valid mathematical domains. Stored matrices use binary64 arithmetic and Gurobi 13.0.2. Native FeasibilityTol and OptimalityTol are \(10^{-6}\), IntFeasTol \(10^{-5}\), requested MIPGap/MIPGapAbs zero; retained evidence closure uses \(10^{-7}\). A qualified result is a numerical certificate under this policy, not a rational exact proof.

In particular, the implemented guard \(\alpha+\lambda\underline P\ge c-10^{-9}\) can serialize \(0\le-1\) while a mathematical point satisfies \(c-10^{-9}\le F<c\). Therefore it is numerical closure, not strict infeasibility of every arbitrarily small improver. Its local cutoff discrepancy does not supply a bound on accumulation of all native arithmetic errors; \(10^{-9}<10^{-7}\) alone proves no such global guarantee. This manuscript changes neither guard nor tolerance. No new contradiction with the stated numerical evidence policy was found; claims of error-free rational certification are excluded.

Every numerical original-problem certificate additionally requires a physically verified own U, qualified complete source/return chains and cover, normal lifecycle completion, and the post-seal signed-gap test −1e−7≤U−L≤1e−7. Appendix B.4.1 fully distinguishes that policy, the one-sided native function and the own-zero/source-reduced branches. Tiny signed gaps are reported unchanged. A same-domain counterexample revokes its source and dependent pruning; an independent fleet can remain valid, but floor zero or a good U cannot repair invalid proof dependencies. Source-reduced results are separately labelled and get no dependent nonzero certificate credit.

The single total process deadline guarantees finite execution of this implementation, not certification within every finite window. The finite physical space and ideal complete search do not imply a linear forecast from the remaining gap.

## A.8 Writer and variable map

| Appendix group | Frozen source authority / mapping |
|---|---|
| Data, travel, physical objective | Parser.cpp; Evaluator.cpp; Result.cpp physical objective evaluator around line 109 |
| Variables and VTypes | CplexBaseline.cpp 890–1005; \(a\leftrightarrow mName\), \(Y\leftrightarrow yName\), \(\ell\leftrightarrow lName\), \(H\leftrightarrow hName\), \(Z\leftrightarrow zprodName\) |
| A1–A4 | Same writer 1600–1695 and 1807–1824; ConnectivityFlow.cpp downstream-count embedding and Round20Current bounds |
| A5–A9 | Same writer 1826–1932; no Round66 arc-load replacement or Round92 handling activation |
| A10–A11 | Same writer 2241–2274 and 2329–2335 |
| A13–A16 | Same writer 2975–3154; stateName and stateGName give \(s,q\); bitName and prodName give plain bits/products |
| F0 configuration and domains | PaperK1AmSf.cpp 38–114; IntervalRowFactory.cpp 391–807; writer 1697–1750, 2049–2108, 2203–2238, 2311–2327 |
| Factory global/local metadata | IntervalRowFactory.cpp 402–451; verified-incumbent “Global” remains cutoff-scoped |
| M-B mode isolation | include/Round98StateService.hpp; no projected direction, linked direction, ENS-Q or other opt-in mode |
| AM, targets, cover and lifecycle | PaperExternalGiniTree.cpp; GurobiBaseline.cpp; ProcessPhaseLedger.cpp; MipStartMapping.cpp |

The source is public at the fixed [implementation snapshot](https://github.com/yifanXovo/TailoredExact/tree/355eefd2be3fe5651195681faf7b3a63ee4032f8). The finite production_identity authority records all 216 bindings. Line locations aid review; they do not replace derivations. This appendix supplies constraint groups and validity premises without claiming every engineering identifier as a mathematical contribution.


\clearpage

# Appendix B. Executable method specification

**Current frozen method.** S2/MS2 uses the unchanged H and controller specified below with uniform pair-only support. Historical full-M-B traces and development variants retain their named identity. S2R is a diagnostic deletion control, not a second proposed method.


This supplement defines the controller and finite feasible startup H shared by the adopted S2/MS2 method and its full-M-B predecessor. The current S2 row policy is uniformly pair-only; the underlying H and controller definitions are unchanged. Algorithm 1 and its two complete subprocedures are in manuscript Section 5; this appendix supplies their data, numerical decisions, decoding and return semantics. Mathematical symbols refer to Appendix A. Historical names are source-map aliases, not additional algorithm variants. The definitions and proofs are retained from R125. Round126 executes only the fixed complete M-B and cold P-GRB entries on the declared new panel; it changes no algorithm.



## B.0 Complete leaf and cover subprocedures

~~~text
Algorithm 2  ProcessLeaf / ChooseAction
Precondition: selected unit is still represented; no pending native call.
1  Validate/rebuild artifact for current epoch; reuse a qualified same-epoch
   parent LP or request its complete LP relaxation.
   On deadline/invalid LP return OPEN_STOP/ERROR, with parent unchanged.
   On qualified infeasible LP return CLOSE(parent,cutoff evidence).
   Merge a finite optimal parent-LP bound on this same domain.
   If b >= current U-epsilon return FATHOM with its bound source.
2  Apply NEXT rule (M5) in its stated priority order:
       noncontrolling -> REQUEUE;
       strict target -> Native(parent MIP,target NEXT), then RETURN_NATIVE;
       otherwise proceed to 3.
3  If depth>=8 or width<=1e-4+1e-12:
       Native(complete parent MIP,no target), then RETURN_NATIVE.
4  Form midpoint children [alpha,mid],[mid,beta], ids parent.0,parent.1.
   Obtain both complete current LP results or reuse B.2's valid cached pair.
   A child starts with max(parent bound,its qualified finite LP bound),
       but retain raw child LP fields for AM. Children are not active leaves.
   On either incomplete/invalid result return OPEN_STOP/ERROR; keep parent.
5  If either child is qualified infeasible: return SPLIT(children,empty flags).
   Otherwise compute (8), (B2), b+=min(raw child bounds):
       b+<=b+epsilon -> Native(complete parent MIP,no target);
       score+score_tolerance>=.08 -> return SPLIT(both children);
       otherwise -> Native(parent MIP,target b+,kind CHILD).
   For a native action return its actually finalized outcome and source identity.
Postcondition: no unresolved domain removed; no target value admitted as proof
   merely because it was requested; no speculative child counted as active.
~~~

~~~text
Algorithm 3  FinalizeAndUpdateCover
Input: ProcessLeaf outcome, current cover, own witness/epoch/runtime caches
1  For native outcomes require actual return and request cleanup first.
   On failed engineering qualification: stop ERROR; leave unresolved region.
   Admit any finite qualified native bound only on its recorded domain/cutoff.
   Retain the source cutoff for proof accounting in A.6; do not clip the
       raw stored numerical bound (B.4).
2  Replay a candidate fleet and original objective. If own U improves by >1e-9,
       replace own witness, increment epoch and tighten current cutoffs.
       Keep qualified old scoped floors; invalidate retained models/LP/children
       on next access using B.2; never transfer a child-only floor upward.
3  SPLIT: validate parent identity, both child ids/lineage/endpoints, shared
       midpoint, inherited bounds and full union. Install both in one transaction,
       mark parent Replaced, then mark proved infeasible children Empty.
       Discard replaced/empty backend models; failed transaction retains parent.
4  CLOSE/FATHOM or qualified native OPTIMAL/INFEASIBLE: close only this
       cutoff obligation and keep its complement floor and evidence.
   Target reached + termination requested + bound>=target-epsilon:
       set NEXT milestone only for NEXT, then requeue parent (no forced split).
   REQUEUE: retain all state/coverage, return to selection.
   TimeLimit/interrupted before proof/target: retain eligible partial bound,
       keep unit Open, stop common lifecycle. Unknown/error is never Empty.
5  Recompute full-cover minimum; output unresolved units if any remain.
Postcondition: every potential physical improver is still covered by an open
   obligation or a qualified closed/complement floor.
~~~

## B.1 Active entry and parameters

The inherited settings below originate in the saved R123 full-M-B command. The current S2 command additionally selects `--round127-mode ms2`, so every three-station support predicate is false. Both versions select `gcap-frontier`, preset `research-round83-vds-equal-net-exchange`, `round98-state-service=m-binary`, `round90-lp-g-split=false`, candidate mode off, witness audit on and H verified-zero stop on. The preset recursively selects joint-seeded interroute decoded descent, VD-P and verified Start; the canonical paper configuration supplies the static row package and first-class interval controller. R122 uses this same M-B method with the panel's declared limits/Seeds. Input, lambda, capacities and physical times remain data, not tuned choices in this round.

| Item | Frozen active value / interpretation |
|---|---|
| Initial geometry | One true-G interval \([0,\min(U,(n-1)/n)]\), n>1; n=1 has G=0 |
| Split | Midpoint; two closed children; depth <8 and width >\(10^{-4}+10^{-12}\) |
| Score | Balanced normalized closure, threshold .08; exact formula B.3 |
| Infeasible child policy | Two-child split, then mark proved children empty; contraction_enabled=false |
| Native work | Gurobi 13.0.2; one thread; Seed from arm; PresolveAuto; requested MIP gaps 0 |
| Numerical policy | Scheduler epsilon \(10^{-7}\); FeasibilityTol/OptimalityTol \(10^{-6}\), IntFeasTol \(10^{-5}\) |
| Cutoff | Current own U; writer epsilon=0; ObjCon=0 |
| Resource | One process deadline; 30 s shutdown reserve in the saved runs; preparation and H are charged |
| Products | VD-P; continuous p/d; binary direction retained; A/B on; integer loads retained |
| Row generation | Uniform two-station support, no three-station support; static physical plus shared interval factory; no dynamic user/lazy cut separation; native Gurobi cuts remain available |
| Domain option vs execution | Requested iterative/2; operative one budget intersection plus reachability intersection, recomputed by shared factory; no feedback iteration |
| H orders | 24 shuffled chromosomes from mt19937 seed 20260626; appended constructive order; no genetic generations |
| H decoder | Full compaction mode 1; cache limit 200000 complete decoded orders; no generation/stagnation quota in this active branch |

The “interval-mip-core-no-exhaustive-subset-duration” policy is overridden by the VD-P preset to `round55-vd-p`, still excluding exhaustive subset duration. Compiler identity is the frozen MSYS2 UCRT64 g++ binary SHA256 `8cd0aa578687e4182532222c8734439b3f34ac78b6ce23cba1071c5838025fc1`. Library shuffle and equivalent-key sort order are implementation-version details; the paper does not invent a canonical cross-library tie rule absent in the source.

The unique paper entry is fully resolved in [paper_method_config.json](paper_method_config.json); [argv_freeze.json](argv_freeze.json) contains the exact six current S2 argument vectors, six independent cold controls and twelve diagnostic control vectors. PE and DLL SHA256 bind every preset/default value that has no separate CLI option. H seed 20260626 and all native settings are explicit configuration values, not instance-dependent choices. The template below is one token vector (line breaks are presentation only); INPUT, OUT, physical T, producer B and B_MINUS_6 and SEED take exactly their fixed group-table values. The existing supervisor starts the complete production clock before admission, invokes this vector, and seals normal output; direct native Runtime alone is not T_cert.

~~~text
PE --input INPUT --lambda 0.15 --T T
   --pickup-time 60 --drop-time 60 --time-limit B_MINUS_6
   --process-wall-time-limit B --process-shutdown-margin 30
   --threads 1 --mip-threads 1 --gurobi-seed SEED --gurobi-presolve -1
   --method gcap-frontier
   --algorithm-preset research-round83-vds-equal-net-exchange
   --round90-lp-g-split false --round61-candidate-mode off
   --round65-witness-audit true --round65-hga-zero-stop true
   --out OUT/result.json --log OUT/native.log
   --process-phase-ledger OUT/phases.csv
   --external-gini-artifact-dir OUT/external
   --primal-heuristic-generation-log OUT/hga.csv
   --progress-log OUT/progress.csv --native-evidence-dir OUT/journal
   --round98-state-service m-binary --round127-mode ms2
~~~

## B.2 State, identity and order

A coverage unit has id, interval endpoints, parent id, child index, depth, base/inherited bound, current bound and sources, cutoff, status, and replacement flag. Active statuses are Open (Invalid may remain selectable as an unresolved obligation); Closed, Empty and Fathomed retain their proof role. Replaced parents are represented by their committed children. TerminalReady/Coalesced are dormant sibling-coalescing states, not normal M-B actions. Native status is not interchangeable with coverage status.

Runtime state separately contains canonical artifact path/SHA/row signature, generation and incumbent epoch; LP result (terminal-valid, optimal/infeasible, bound available, raw bound), LP epoch/SHA/endpoints; cached speculative child objects; terminal-started state; native phase count; and the NEXT milestone bit. Own witness state contains complete routes, integer operations, inventory, recomputed U and true G. The model's epigraph G never replaces the latter. Epoch starts at zero and increments on an independently verified incumbent improvement exceeding \(10^{-9}\). Callback observations and physical witnesses retain separate identities.

Selection uses the **current own U** as cutoff, not an old source cutoff. It considers unreplaced Open/Invalid units with α<U−epsilon and b<U−epsilon. Find their minimum bound and form the epsilon plateau \(b_I\le b_{min}+\epsilon\). Sort the plateau by decreasing width, increasing lower endpoint, increasing upper endpoint, then lexicographic id (the first three comparisons use \(10^{-12}\)). Cycle through this order. Reset the cursor when the plateau membership/order changes or its minimum changes by more than epsilon; after a full cycle increment the tie round. Effort, elapsed time and requested_quantum fields do not affect this `selectNextByBoundOnly` call.

On a new epoch, before reusing a selected artifact verify its old saved bytes, discard its retained backend model, clear artifact/LP state, terminal flags and child cache, and build a new generation at the current cutoff. Qualified old-domain lower bounds remain on their covering units: a smaller cutoff does not invalidate a bound already completed by its old cutoff complement. The NEXT milestone bit is initialized false in each newly created runtime and set true only by a returned NEXT target. **It is not reset in the active epoch invalidation block.** Child-target returns do not set it. No stronger child bound is sent upward to the parent merely because the child has a higher value.

Parent LP reuse requires complete evidence and the same incumbent epoch. A retained artifact must exist and match its SHA. The ordinary cached-child reuse gate requires the parent's ready flag, exactly two cached children and complete child runtime LPs; epoch invalidation clears that flag before reuse. The more elaborate endpoint/path/SHA `validRound90LpGCachedChild` check is conditional on round90 and is off here; its existence is not claimed as an active gate. When reusing children, their stored bounds inherit max(old child bound,current parent bound) and their cutoff is refreshed. AM still reads the **raw LP bound fields**, not those inherited maxima. Missing/incomplete cache falls back to constructing and solving both children; it is never interpreted as infeasible.

## B.3 NEXT, child target and terminal decisions

Call NEXT after the selected parent has completed its LP and merged any qualified bound; re-read the current bound b. The function first rejects nonfinite bounds, and first requeues if any other relevant bound satisfies \(b_j+\epsilon<b\), even if the milestone was already reached. Otherwise, if the milestone is false and any \(b_j>b+\epsilon\), return NEXT with \(t=\min\{b_j:b_j>b+\epsilon\}\). If there is no such bound, or the milestone is true, allow lookahead. The caller supplies only other **Open/Invalid schedulable units** whose current bound is below current U−epsilon (and whose interval remains relevant). Closed, Empty, Fathomed and replaced units are excluded from NEXT competitors even though their floors remain in proof coverage. Thus a lone closed unit at .40 does not supply a NEXT target to an open unit at .20. Source-cutoff metadata governs bound scope, never this current scheduling filter. The function does not use a timed quantum.

If geometry is ineligible, proceed to terminal MIP after NEXT permits lookahead. If eligible, form closed midpoint children in index order 0,1. Each is speculative until the complete replacement transaction. Solve both complete LP relaxations, or use the current admissible cache. A terminal valid child means either proved infeasible, or optimal with an available finite bound; TimeLimit/UNKNOWN is not terminal valid. Deadline exits retain the parent; an unexpected nonterminal/invalid LP is an engineering failure with the parent retained, not permission to prune it. The optional UNKNOWN→core-due research branch is off.

If either qualified child LP is infeasible, AM immediately requests a two-child atomic split. With contraction=false this applies also when both are infeasible; only after installing both does the controller mark the infeasible child or children Empty and discard those backend models. The inactive one-child contraction/both-child parent-close code is not part of M-B.

For two finite optimal LPs with raw bounds ℓ0,ℓ1, use

\[
\Delta=\max(U-b,\max(\epsilon,10^{-12})),\quad
v_j=\min(1,\max(0,(\ell_j-b)/\Delta)),\quad
\eta=\min(v_0,v_1),\quad\mu=(v_0+v_1)/2.
\tag{B1}
\]
\[
\begin{aligned}
s&=\max(1,|b|,|\ell_0|,|\ell_1|,|U|),\\
\delta_b&=\max(\epsilon,32\epsilon_{mach}s),\\
\delta_{score}&=\min(1,\delta_b/\Delta+32\epsilon_{mach}),\quad \epsilon_{mach}=2^{-52}.
\end{aligned}
\tag{B2}
\]

Put \(b_+=\min(\ell_0,\ell_1)\). If \(b_+\le b+\epsilon\), return terminal; else if \(\eta\mu+\delta_{score}\ge.08\), split; else request a **parent-domain MIP** with bound target \(b_+\). A child target is an intended stopping threshold, not a bound to merge into the parent before native evidence returns. A returned target requeues the parent and re-evaluates the current rule; it does not force a delayed split. This distinguishes NEXT (competitors), child target (lookahead), and terminal (complete parent MIP without a bound-target stop). The recorded adaptive rho is \(\min(1,.08/\max(\mu,\max(\epsilon,10^{-12})))\); it is diagnostic, not another active score rule.

## B.4 Native requests, Starts and returned actions

An LP request relaxes the actual original VTypes, keeps the complete row set, and retains the model when permitted. A MIP request restores the exact saved VTypes before optimization. Targets and terminal requests receive the remaining common deadline after preparation, with native TimeLimit set/read back; no new per-leaf budget is created. Native bound callbacks can request termination when the qualified target is reached. Such a request is not the native return itself.

For enabled verified Start, normalize the current own fleet only among equal-capacity vehicle classes, stable sorting by decreasing number of operations and assigning smaller vehicle ids first. Clear explicit previous Starts even if the replacement is ineligible. Reverify routes, true G and F. Check interval membership with \(10^{-8}\) and non-strict cutoff with \(10^{-8}\max(1,|F|,|c|)\). An outside-interval/cutoff fleet is simply ineligible, and the MIP can run without it. Other mapping failures fail the request's engineering gate; they do not establish infeasibility.

For each used route set selected arcs to one, visit z=1, direction to pickup indicator, quantities to its integers, load to each prefix and rank to position. Flow along a q-station route is q,q−1,...,1,0. All absent route columns, including unused vehicles, are zero. Set (Y,r,e,H,G,Z) to physical values, state selector to one at Y, state_g to true G there and zero elsewhere, W_SP=SP, and the unused extrema to actual min/max ratios. Check every actual column bound/type, every actual linear row at \(10^{-7}\), and actual objective including ObjCon at \(10^{-7}\); require minimization and no unexpected nonlinear structure. Then submit a complete Start and read it back. Submission, native-log acceptance, integer-vector observation and a later improved incumbent are different observations.

The outcome object is consumed only after the optimize call returns and request finalization detaches callbacks/settles native data. Retaining the same in-memory model can preserve useful solver state, but this paper does not promise that the entire native branch-and-bound tree survives type changes or later calls. Once returned, merge finite qualified bounds only on the actual interval/cutoff; replay a proposed fleet before accepting an improved own U. This order precedes the next controller transaction.

| Returned condition after required identity, finalization, zero-gap-setting and consistency gates | Coverage action |
|---|---|
| LP optimal with finite qualified bound | Merge into that parent, or save on speculative child; child alone changes no active cover |
| LP infeasible | Parent Empty, or speculative infeasibility retained until atomic split |
| Target MIP OPTIMAL with bound / INFEASIBLE | Close selected cutoff obligation; retain cutoff-complement floor; discard its model and speculative child models |
| Target reached flag, termination-request flag, available bound ≥target−epsilon | Merge returned bound; set milestone only for NEXT; requeue; preserve parent and siblings |
| MIP interrupted/TimeLimit before target | Keep qualified partial bound if engineering gates passed; leave region open and end the common lifecycle |
| Terminal MIP OPTIMAL / INFEASIBLE | Close its own cutoff obligation; never certify siblings by this status |
| Terminal MIP interrupted | Leave region open and stop |
| Unsupported status, missing optimal bound, failed identity, incomplete LP or native error | Stop with explicit failure; preserve unresolved coverage; dependent unqualified evidence is not admitted |
| No launch because deadline expired | Leave region and previous evidence unchanged; finalize open result |

The implementation merges same-unit bounds with max(old bound,new bound), without clipping to U. Empty/Fathomed stores max(previous bound,cutoff); Closed keeps its qualified returned floor. The raw returned L is the scheduler's complete-cover minimum, also **without clipping to U**. Tiny negative signed gaps can therefore occur and remain recorded. On the empty relevant-set path the scheduler helper alone returns 0; the enclosing lifecycle/closure logic determines the outcome.

For the exact mathematical proof, each cutoff-bound source has unconditional regional floor min(bound,source cutoff), and the analytic complement contributes its cutoff floor (A.6). This is proof accounting, not an extra min-assignment performed by the frozen scheduler. Raw numerical evidence and exact proof-accounting expressions must not be interchanged. A.7's numerical closure exception still applies.

### B.4.1 Certificate admission: native function and sealed evidence

The native certificate function requires valid complete coverage, all relevant leaves closed, all used bounds certified, monotone bound history, a verified own finite U, completed lifecycle, and source consistency. It then accepts the one-sided test L+max(0,tolerance)≥U. It does **not** enforce a lower bound on the signed gap U−L. In particular, a negative gap of −2e−7 is not rejected by that predicate alone.

The published post-seal reader applies the stronger admission policy. Each native source must have a finished request with matching interval, epoch, model bytes/row signature and parentage; the saved parameters must match the frozen original model (including requested zero relative/absolute MIP gap); every used bound must be finite, available and sourced to the corresponding returned native request, without a counterexample or consistency failure. It reconstructs the represented children and their full interval union, preserves unresolved obligations, requires every relevant unit closed for certification, replays the own physical fleet and objective, and requires normal process completion (no killed, timed-out producer, missing seal, or failed engineering gate). These gates are conjunctions, not substitutes for one another. A clean nonzero certificate additionally requires −1e−7≤U−L≤1e−7; gaps are never clipped. Thus the above −2e−7 case is rejected after sealing.

The clean independent own-zero branch requires a physically replayed own U≤1e−12, nonnegative lambda and weights, and **no started native request**; it returns L=0 and a synthetic complete zero cover. The startup early-stop test is 0≤verified F≤1e−12; the neutral physical loop itself stops only on exact F=0. If native sources are damaged, the source-reduced fallback is stricter: it needs every Y_i=D_i and recomputed F=G=P=0 exactly. Its independent L=0 does not restore any invalid native source or dependent nonzero certificate. A retained positive feasible fleet alone supplies U, never certificate credit for damaged proof dependencies.

These are distinct functions in the frozen evidence chain: ExternalGiniTree.cpp:460–489 for native admission; read_round122/123 → read_round118.item/finalize → read_round116.reconstruct_arm → round108_reader.endpoint (328–391), with CLOSURE_TOL=1e−7 and ZERO_TOL=1e−12; round114_claims/round114_audit supplies damaged-source fallback. The rules are stated here so those links are audit references, not missing algorithm definitions.

## B.5 Teaching states and a separately sourced event

These first numbers are **synthetic teaching states**, not measurements. Take U=1, epsilon=\(10^{-7}\). With selected b=.20 and competitor bounds (.20,.35,.60), the plateau contains the tied .20 units and NEXT=.35. After a qualified NEXT return b=.35 the milestone is true; if all other relevant bounds are at least .35, lookahead is permitted. (If the tied .20 unit still exists, the requeue check wins first.)

For a fresh controlling parent b=.20 with no strict competitor, children (.21,.30) give Δ=.8, v=(.0125,.125), score=.000859375, b+=.21: run parent MIP to .21. Children (.20,.90) instead give b+=b: terminal, regardless of the strong sibling. Children (.50,.60) give v=(.375,.5), score=.1640625: split, install both children, with union floor .50. If the other covering unit has floor .25, global L remains .25. A target TimeLimit at .205 keeps the parent open at its qualified .205 bound; a missing Start changes none of these implications.

The following is an **actual R123 saved event** from M-B's `adaptive_mass_decision_ledger.csv` and `paper_tree_events.csv`, selected as a finite trace excerpt. On L0.0.0=[0,.09308544387476185], depth 2, b=.33371261877766062, raw child LPs (.34112380854511071,.35882784229299913), U=.3723417754990474 give eta=.19185481632186216, mu=.42100858578645295, score=.08077252489598688 and score tolerance=.0000025887181797865216. The decision is split; the event at telemetry 127.2749697 records atomic replacement and global floor .34112380854511071. Earlier recorded splits at 38.3552841 and 72.829994 used the infeasible-child two-child branch. These times are native-run telemetry, not newly measured clocks or a reconstructed unknown checkpoint. Compact source excerpts and hashes accompany the finite checks.

## B.6 H encoding and top-level procedure

Physical routes are labelled lists \(0,i_1,\ldots,i_q,0\) with one signed integer operation \(a_i=p_i-d_i\ne0\) per station; missing vehicle means empty route. H's **order encoding** is different: M ordered lists partition all n stations, including a tail that the decoder may not execute. A chromosome is a permutation of station ids 1..n and M−1 identical separator tokens; splitting at separators preserves empty vehicle lists. Reordering an encoded tail does not itself describe a feasible service plan. Decoding returns signed operations; materialization deletes zero-operation stations, closes used routes at depot and verifies the entire fleet.

~~~text
H(instance, common deadline):
    C := empty physical fleet, verify Y=b
    repeat choose and admit best joint insertion (B.7) until none/deadline
    keep verified C as an own candidate
    generate all 24 shuffled order chromosomes with mt19937(20260626)
    append C's order after deterministic tail completion (below)
    initialize a shared complete-decode cache, empty
    decode all 25 orders in order, publishing verified improvements
    for each seed in order:
        repeat generate guided candidates (B.10), order by proxy fitness
        fully decode candidates in that order
        accept first fitness improvement >1e-12; restart this seed's pass
        if every candidate checked without improvement: finish this seed
        honor verified-zero/deadline between calls and candidates
    take the best independently verified candidate, including C
    run strict insertion/quantity closure followed by best neutral block move;
        repeat these two phases (B.11) until zero/no neutral/deadline/failure
    return best admitted complete fleet and stop reason
~~~

Constructive tail completion starts with C's visited order and each vehicle's complete physical duration as a proxy. For each unvisited station i in increasing id, append it to the vehicle minimizing proxy[k]+tau(last,i)+tau(i,0)−tau(last,0), choosing the first vehicle on an exact tie; update that proxy. The remaining operations are decided by the same full decoder. Twenty-four shuffles are generated before appending this extra seed, preserving random draws. `constructive_mode=0` means there are no additional biased population members. The snapshot's C++ shuffle is authoritative for exact seed orders; the algorithm specifies the generator/seed/order and permits cross-library sequence differences. HGA crossover, mutation, education generations, 2000-generation stagnation and obsolete “10 iterations” fields do not run in this decoded-descent branch.

The outer physical candidate store keeps a candidate only after full verification and an improvement greater than \(10^{-10}\), unless no incumbent exists. Verified-zero can terminate startup early. This publication threshold differs from inner \(10^{-12}\) move thresholds; an internally accepted tiny improvement need not replace the outer witness.

## B.7 Joint insertion

At a verified fleet let \(L_k(a)\) be load on leg a, numbering the original legs from 0 through the number of visited stations. For each ordered (pickup station i or 0,drop station j or 0), excluding (0,0), i=j, and already visited nonzero stations, enumerate vehicles and positions. Zero denotes an absent side, not depot stock. Both sides use the same integer quantity q. For a pair choose original legs a≤b, inserting i then j; on one leg the sequence is predecessor,i,j,successor. Travel increment is the sum of replaced arc differences (one combined expression when a=b).

The load upper amount is \(Q_k-\max_{v=a..b}L_k(v)\) for a pair; \(Q_k-\max_{v=a..end}L_k(v)\) for pickup only; \(\min_{v=a..end}L_k(v)\) for drop only. Intersect with available inventory at i, room at j and max vehicle capacity. Complete duration increment is travel increment plus hq when a pickup is inserted, and just travel increment for drop only (that drop replaces return unloading). The time test uses T+\(10^{-7}\). For each amount, retain the cheapest feasible travel placement, ties (vehicle,a,b), by a suffix scan of placement amount limits. Evaluate all amounts 1..limit using F on the changed one/two inventories; accept only gain>\(10^{-12}\).

Choose globally: nonpositive added duration before positive; then greatest gain per added duration (compare cross products, or gain for both nonpositive), greater gain, smaller added duration, and lexicographically (i,j,q,k,a,b). Apply and fully replay; require objective agreement within \(10^{-10}\) and verified gain>\(10^{-12}\). Every insertion adds at least one previously unvisited station, so construction has at most n accepted insertions. This finite placement/amount scan is a heuristic neighborhood, not an optimization backend.

## B.8 Single and paired quantity modification

Only currently served stations participate. Enumerate a increasing, then b=0 (single) and each served b>a (pair). For every nonzero integer t set \(a'_a=a_a+t\), and \(a'_b=a_b-t\) if b exists. Station bounds give

\[
b_a-C_a-a_a\le t\le b_a-a_a;\qquad
a_b-b_b\le t\le a_b-b_b+C_b\quad(b\ne0).
\tag{B3}
\]

Intersect these with every affected prefix load \(0\le L+\chi t\le Q_k\), where chi is +1 after a, −1 after b, zero before/beyond the cancelling pair. This includes cross-vehicle modifications; each route has its own capacity. Enumerate all integers in the resulting interval increasing, skip zero. Convert signed operations to pickup=max(a',0), drop=max(−a',0), remove zero stops and shortcut travel. Sign reversal is allowed. Check complete duration, including depot unloading, at \(10^{-7}\); evaluate F; require gain>\(10^{-12}\). Choose lowest proposed objective, tie (a,b,t). Full replay and objective agreement within \(10^{-10}\) precede acceptance. Missing stations cannot be added by this operator; insertion handles them.

Strict closure computes both the best insertion and best quantity move on the same current fleet, chooses smaller proposed F, insertion on an exact tie, admits the verified strict improvement, and repeats. If neither exists, that union neighborhood is exhausted. Verification failure retains the previous fleet and records failure. This is exactly the Round76 subprocedure called by active exchange descent; the standalone Round75/76 preset entry branches are not separately run by main.

## B.9 Complete greedy decoder and its compensating moves

For each encoded route take its maximal prefix whose travel with direct return stays within T+\(10^{-12}\), stopping at the first exceeding station. Fix this travel during that decoder pass. Set the cumulative pickup budget \(B_k=\max(0,\lfloor(T-travel+10^{-12})/h\rfloor)\) (an integer sentinel max-int/4 if \(h\le10^{-12}\)); this is a handling budget, not Q. Initialize all operations zero and Y=b. The single-route proxy version instead keeps other-route operations fixed. The active mode is 1: visit vehicles and stations forward, greedily match each current surplus above clipped target to later deficits, as much as remaining supply, demand, station bounds, all intervening load bounds and pickup budget allow; leftover surplus may be collected for depot return. This constructive initialization does not require each step to decrease F.

Define an interval move by vehicle k, positions a<b, sign \(\sigma\in\{+1,-1\}\), amount \(q\ge1\). Increase a's signed operation by sigma q and decrease b's by sigma q. The sink may instead be the depot after the last position, in which case only a changes. Loads on [a,b) change by sigma q. Each final inventory must stay in [0,C], loads in [0,Q], and total positive operations in [0,B_k]. Thus an earlier delivery can be reduced/reversed and a pickup compensated elsewhere; there is still only one net one-way operation per physical station. Feasible amount bounds come from station room and the minimum/maximum load on the changed interval; the positive-part pickup change is piecewise linear with breakpoints at operation sign changes. The implementation finds the largest feasible q by these segments, then evaluates every positive integer up to it. The feasible amount sublevel contains q=0 and is an interval, so no integer hole is skipped. Objective arithmetic updates the changed ratios, pairwise absolute sum and penalties; it is not an LP/DP solve.

The active decoder loop is:

~~~text
repeat:
    repeatedly apply the best strict atomic interval move, until none
    if a strict same-route composite exists: apply best; restart
    if a strict two-route composite exists: apply best; restart
    if a strict unit interval polish exists: apply best; restart
    if a strict flow-pair redistribution exists: apply best; restart
    if no atomic move occurred in this pass: return current operations
~~~

Atomic enumeration is vehicle, source position, later sink positions then depot, sign + then −, amount increasing. Keep the best move and the eight best atoms per route. To update the best, initialize value F−EPS and replace only when candidate+EPS<best, EPS=\(10^{-12}\); this gives an effective initial gain test >2EPS. For each bounded list, append candidates until size K (\(K=8\) atoms or \(K=6\) local candidates), maintaining a max heap with comparator a.objective<b.objective. Once full, replace its front only if candidate.objective+EPS<front.objective, then restore the heap. Final sorting compares only ascending objective, with no secondary key. Equivalent-key heap positions consequently depend on the frozen standard library. Local candidates comprise each retained atom and each pair of distinct atoms on one route, adding their operation deltas simultaneously. Recheck all combined loads, positive-operation budget and station bounds, then retain at most six best candidates per route using the same bounded-heap objective logic. Candidates can individually worsen F: their combination may compensate that worsening. Same-route best selection uses F−EPS and candidate+EPS<best. Cross-route candidates combine one retained local candidate from each pair of vehicles, recompute the full common Gini/penalty objective for their jointly changed (up to eight) stations, and use the same strict test. Distinct routes have disjoint stations, so combined physical feasibility follows from their checked local feasibility; joint objective evaluation remains necessary.

Unit polish checks amount 1 for every legal atomic interval, with initial best F−\(10^{-14}\) and candidate+\(10^{-14}\)<best. Flow-pair polish ignores zero operations, partitions the route into consecutive same-sign runs, and pairs each pickup run with its immediately following drop run. For each ordered pair of distinct such run pairs, choose one pickup and drop position in each: subtract one unit from the first pickup/drop flow and add one to the second. Check both interval load changes together, station bounds and original signs; pickup total is unchanged. Its candidate helper still requires gain>\(10^{-12}\), followed by the \(10^{-14}\) best-comparison guard. Residual pair-unit, route-exact and pair-exact neighborhoods return false in this active implementation; they are not hidden optimization oracles.

After a first full decode, if its executed prefix contains zero-operation stations, delete them, keep only its nonzero active order, and run this same full decoder from zero operations **once more** on those compacted routes. Return whichever has smaller F, first decode on exact tie. This does not repeat compaction to a fixed point and does not restore the removed tail. The cached object contains complete signed operations and fitness=−F. Materializing that object removes remaining zero operations and independently checks the original physical route duration.

Decoder cache key is compaction mode plus the ordered lists with separators; it includes tail positions, even if they decode identically. On a hit return the entire stored decode. On a miss at size≥200000 clear the whole map before inserting; this is neither LRU nor a permanent visited-state ban. Internal atomic/local caches are tied to an incremented operation-state epoch and cleared after accepted updates. The static ratio/penalty preprocessing cache keys capacities, targets and weights (including source slice offsets); it affects arithmetic reuse, not candidate admission. No general accepted-state de-duplication is claimed.

## B.10 Guided order descent and ties

For each route compute the travel-only executable prefix as above. Within it record first negative-operation position and last positive-operation position. A station's role is pickup if its decoded operation>0, drop if <0; if zero, use surplus/shortage of decoded final inventory relative to target, otherwise neutral. Supply anchor is first drop, or position 0; demand anchor is immediately after last pickup, otherwise prefix end.

Generate, in vehicle order: move the last zero-operation prefix station to that route's end; collect every nonneutral prefix position plus the first supply and first demand in its tail. Move a supply lying after first drop, or in tail, to the supply anchor; move a demand before last pickup, or in tail with a last pickup present, to the demand anchor. Duplicate generated candidates are not globally removed. Same-route erase/insert decrements destination position if it originally lay after the erased position; skip unchanged order. For interroute proposals take only the first supply/demand in each source tail, each different destination in order: insert supply at destination's supply anchor if that route contains any demand-role station; insert demand at its demand anchor if it has an executed pickup.

The proxy fully runs the single-route incremental decoder with other-route operations fixed. For a two-route change try both route decoding orders and take the larger fitness (smaller F). Proxies only order proposals: sort decreasing proxy fitness, then fully decode in that order and accept the first fitness increase>\(10^{-12}\). An unsuccessful pass evaluates every generated proposal, including a poor proxy. There is no top-k rejection here.

The guided comparator has no secondary key: equal proxy values are equivalent to C++ `std::sort`, which is not stable. Likewise internal bounded-heap/objective-only sorts have implementation-dependent equivalent-key order. For the frozen compiler/library they supply the recorded run's repeatable behavior; a cross-language implementation may choose a different equivalent-key order and consequently a different heuristic path. Specifying lexicographic ties here would change the frozen algorithm. By contrast B.7/B.8 and the physical block operators do have explicit deterministic ties. This limitation affects path-level reproduction, not feasibility, exact model scope or native lower-bound validity.

## B.11 Neutral block moves and exit argument

Strict closure is followed by one best neutral move from the union below. The potential is the **complete** vector of all vehicle durations, sorted decreasingly, including zeros for unused vehicles; compare it with exact C++ lexicographic `<`, never by an aggregate sum or a tolerance that ignores an earlier increase.

Balanced relocation enumerates source vehicle, all nonempty contiguous half-open position blocks [a,b), other target vehicle and every insertion leg. Require net signed operation zero. If relative prefix load extrema inside the block are lo,hi, require target load+lo≥0 and target load+hi≤Q_target. Removing a net-zero block leaves source suffix loads unchanged; inserting it leaves target suffix loads unchanged. Keep operation quantities and order inside the block; recompute both full durations and accept only if each≤T+\(10^{-7}\) and the sorted vector strictly improves. Choose smallest potential, tie (source,a,b,target,leg).

Equal-net exchange enumerates every contiguous nonempty block per route, bucketed by integer net operation in increasing net order; pair vehicles s<t and blocks from equal-net buckets. At each insertion prefix require its old load plus the incoming block's relative extrema in that vehicle's [0,Q]. Equal net preserves all suffix loads, even when the common net is nonzero. Replace the two blocks in their original internal order, preserve all station operations, recompute complete durations and compare the same potential. Choose smallest potential, tie \(kind,source,a,b,target,target_a,target_b\), with kind 0 relocation before kind 1 exchange. `bestRound83Neutral` evaluates the whole relocation neighborhood first and then exchanges.

Before accepting a neutral candidate, independent replay requires identical final-inventory vector, **exactly equal recomputed objective**, and exact equality between recomputed duration potential and the proposed potential, which must strictly improve the prior one. Failed admission retains the prior fleet. After an accepted neutral move, run strict closure again. Stop on exact verified objective zero, common deadline, failed verification, or closure plus no improving neutral move. A selected no-move event is an exhaustion claim only for these enumerated neighborhoods.

In ideal arithmetic, after the finite construction the accepted physical phases strictly decrease (F,sorted durations) lexicographically, and the finite space of labelled routes/integer quantities excludes cycles. The order-descent phase strictly increases its deterministic decoded fitness on a finite set of orders. The implementation uses incremental floating arithmetic and tolerances in the decoder; these comparisons are not a proof of exact rational monotonicity or an accumulated error bound. The physical block phases have exact inventory/objective equality for neutral steps, unlike a merely tolerance-neutral rule. There is no fabricated de-duplication argument. The common deadline and external lifecycle cap are the operational stopping boundary; expensive decoder calls are finite routines and do not have a separate native optimization timeout. H neighborhood closure never certifies the original optimum.


## B.12 Separately identified inclusive-root research control (Round128)

MD-R version 1 is a research ablation, not another proposed algorithm. Section 6.8 and the root contract define its same-H inclusive domain, semantic shortcut omission, mandatory actual own-Start pre-LP check, one LP plus one integer MIP, fixed cutoff and complete native optimal-root return obligation. It retains the physical and signed numerical evidence policy. TIME_LIMIT/INTERRUPTED may yield a qualified open endpoint with null T_cert; a near-equal bound alone cannot satisfy its missing optimal-return obligation. Its extra checks and complete costs are paid. These control-specific guards leave the frozen ordinary procedure and the historical evidence in this appendix unchanged.


## B.13 Uniform support candidate confirmation (Round129)

Round129 changes no production source, H, model generator, numerical policy or controller. It reuses original E2 modes mb/ms2/p. The sole candidate MS2 suppresses triple support for every input while retaining pairs, ordered supply and the shared enumeration order/cap. The five fixed candidate rules and thirty complete paid observations are in Section 6.9. At the R129 selection stage, MS2 was the proposed candidate and full M-B was the then-current frozen method. That historical distinction and all tables remain; R130 now adopts S2/MS2 as the sole paper method. The independent finite review and public recovery are evidence checks, not new native solves or rational proofs of all matrices.

## B.14 Current pair-support version and fixed attribution controls

The sole paper method is original E2 `ms2`, called S2. E3 retains its source behavior and adds the off-by-default unique `s2-root` identity plus PS parameter evidence readback. E2 is retained unchanged. PS reuses the full original-compact mapper/validator; S2R reuses R128 inclusive-root semantics with triple emission disabled. Section 6.10 states the paid workflows, exact cutoff complement, nonzero LP/MIP obligations, source/return/coverage requirements, actual exposure and attribution limits. No individual cut, H, threshold or native parameter is optimized here. The passed R129 candidate selection is not rerun.


\clearpage

# Appendix C. Equivalent-expression proofs and actual-model conditions

## C.3. Projection of the three geometry row families

Delete only H-spread, variable-S centering and fixed-S centering. Keep all H absolute-value lower bounds, individual bounds, total cap/floor, original Gini epigraph, scalar/SP estimators, cutoff, real domains and domain-generation rules. For n>=2 the ideal three families are

\[
(n-1)H_{ij}\le n\beta S,\quad
\pm(n-1)(r_i-r_j)\le n\beta S,\quad
\pm(r_i-r_j)\le n\beta\bar S/(n-1).
\]

Let H_sum=sum H_ij. The retained original epigraph is H_sum<=n sum_i Z_i/D_i. Nonnegative states and q_iy<=beta s_iy give Z_i<=beta Y_i, hence H_sum<=n beta S. Triangle inequalities give A>=(n-1)|r_i-r_j|: for each third station t, |r_i-r_t|+|r_t-r_j|>=|r_i-r_j|, together with the pair itself; unused pair distances are nonnegative. Thus both centering families follow from the retained inequalities and S<=Sbar.

### Root interval

When alpha=0, replace every H_ij by |r_i-r_j|. This decreases the sum, respects its upper bounds and all individual upper bounds under the audited conditions, and the floor reduces to nonnegativity. The new H satisfies H-spread and leaves all non-H variables and the objective unchanged. Reverse inclusion follows by adding constraints. Thus projecting away all H gives equal LP sets and equal ideal LP objective values. Because H is continuous, the same extension preserves any remaining integer restrictions.

### Positive lower endpoint

Assume 0<=alpha<=beta, r_i>=0, S<=Sbar; individual H upper bounds U_ij=c_i+c_j with c_i>=0 and r_i<=c_i; and outside the deleted families H appears only in absolute lower bounds, individual bounds, a total floor/cap and other uniform total upper bounds. H has zero objective coefficient and no additional individual positive lower bounds or nonuniform linear uses.

Fix every non-H variable in a feasible point of the deletion model. Put d_ij=|r_i-r_j|, A=sum d_ij, L=n alpha S and t=n beta S/(n-1). Let B be the smallest retained total upper bound, including the implied n beta S. Feasibility gives

\[
T^*=\max(A,L)\le\min(B,\sum U_{ij}).
\]

The triangle argument gives d_ij<=t. Let U'_ij=min(c_i+c_j,t). With C=sum c_i>0, f(c)=sum_{i<j}min(c_i+c_j,t) is concave on the nonnegative simplex of sum C. Express c=sum_i(c_i/C)Ce_i. Concavity then gives

\[
\sum U'_{ij}=f(c)\ge(n-1)\min(C,t)
=\min(\sum U_{ij},n\beta S)\ge T^*.
\]

If sum U'>A, set theta=(T*-A)/(sum U'-A) and H'_ij=d_ij+theta(U'_ij-d_ij). Then 0<=theta<=1; every individual bound and spread bound holds, sum H'=T*<=B, and the floor holds. The centering rows already follow without H. All non-H variables and their objective remain unchanged. If the denominator vanishes, T*=A and H'=d suffices. If C=0, all c,r,S,A,L vanish and H'=0. If S=0, nonnegative ratios vanish and H'=0. For n=1 none of these three families is generated. This proves both projected inclusions, including the nonzero-floor case in which setting H=d alone can fail.

### Actual-model application and numerical boundary

The current shared canonical factory generates the named three families, and the frozen paper profile disables local/subset nonuniform H uses. The Cplex writer sets H upper bounds to fl(C_i/D_i+C_j/D_j), with zero H objective coefficients. The independent reviewer inspected an actual saved S12 S2R matrix: 66 H bounds, five uniform full-H rows and 198 individual-H rows. W appears in five rows, as required below. This is a canonical-model result, not a theorem about arbitrary native node cuts.

The exact additive upper-bound hypothesis concerns real algebra. In the saved S12 matrix, 41 of 66 serialized H bounds differ from the exact rational sum of the two serialized r upper bounds at roughly 1e-16. Therefore the ideal theorem is not asserted as strict rational equality for every serialized floating matrix. Necessary actual coefficient/domain checks and extension residuals accompany the research comparisons. The production S2 bytes are unchanged; no hidden outward correction is applied. Equal projections do not imply identical presolve, native cuts, search paths or elapsed time, and do not make the entire C_G package redundant.

## C.4. Exact elimination of W_SP, including its real bounds

In the active shared model W is continuous, has zero objective coefficient and is used by four MC rows, one SP cutoff and its own box. No other use is present in the qualified canonical scope. Preserve all W-free original rows, variable types and bounds, particularly g+lambda P<=c, which a cross-multiplied row cannot replace at S=0.

For actual W bounds w_l,w_u and MC parameters s_l,s_u,p_l,p_u define

\[
L_0=w_l,\quad L_1=s_lP+p_lS-s_lp_l,\quad
L_2=s_uP+p_uS-s_up_u,
\]
\[
U_0=w_u,\quad U_1=s_uP+p_lS-s_up_l,\quad
U_2=s_lP+p_uS-s_lp_u.
\]

The original system is L_j<=W<=U_k and H_sum+n lambda W<=ncS. For lambda>0 its complete projection is all nine compatibility rows L_j<=U_k and all three lower-cutoff rows H_sum+n lambda L_j<=ncS. Necessity is immediate. Conversely, W=max_j L_j satisfies every upper bound and the SP cutoff, proving sufficiency. This is standard one-variable Fourier-Motzkin elimination applied to this formulation, not a new linearization theorem or an exact continuous product identity.

Only after proving the same explicit nonnegative rectangle s_l<=S<=s_u, p_l<=P<=p_u, and that the actual W box is no tighter than the product box, may compatibility and W-box rows be removed. The true SP is then an extension for MC feasibility. Since L_1-s_lp_l=s_l(P-p_l)+p_l(S-s_l)>=0, the constant lower plane is dominated. The two lower-plane cutoffs then suffice, with W=max(L_1,L_2). Current inflated e can violate the tight physical P upper estimate; that estimate cannot simply be assumed to bound the whole epigraph.

For positive width s_u>s_l, MC lower/upper pairings imply P>=p_l and P<=p_u after cancellation. These consequences must survive projection. Example: s_l=1,s_u=2,p_l=0,p_u=1,S=1,P=2,H_sum=0 and sufficiently large c satisfies both lower-plane cutoffs but L_2=3>U_2=2, so no original W exists. Two cutoffs alone would incorrectly enlarge the domain.

When S is fixed, derive compatibility directly rather than dividing by its width. At S=0, W=0 need not imply P<=p_u. The full pair system handles that case without adding an unauthorized P bound. When lambda=0, retain H_sum<=ncS and every W-feasibility compatibility row; removing the whole block would again change its projection. Zero-width P and simultaneous degeneracy are also covered by the pair construction.

### Implemented research expression

The research writer reads the actual shared canonical row coefficients, normalizes their senses, includes the exact actual W box, and combines every lower/upper pair. There are three lower rows and four upper rows including the SP row: 12 projected rows. It retains even constant or duplicate compatibility rows. All remaining original rows, objective, bounds and integer types stay intact; only the W column and its rows are replaced. Its physical Start is mapped to the remaining actual columns and validated before use.

The independent checker reconstructs these combinations with exact rational arithmetic on source binary64 coefficients. It separately bounds the output coefficient-serialization residual over actual remaining-variable bounds. The candidate binary64 output is qualified as numerically consistent, not asserted to equal the exact rational projected matrix. `C_matrix_wording_addendum.json` makes this distinction explicit. Four saved interval/input configurations have equal canonical all-continuous LP objectives within the inherited 1e-7 policy. These finite observations check implementation and numerical behavior; they do not replace the general projection proof.

## C.5. Qualification and relation to costs

The research default-off writer and original E3 produce identical complete canonical LP bytes on the qualified small and medium fixtures, at a root interval and a positive lower endpoint. Actual S12 CLI runs bridge original E3 to research default-off, and validate independent H and full Start submission for both candidates. Each uses the legal inclusive-root LP then restored-integer MIP workflow. Default-off equivalence is a semantic/matrix bridge; the two executable byte strings are different and are never described as identical.

C cost diagnostics remain required after these qualifications. Their known-role panel, two Seeds and three same-build expressions are frozen separately. D remains the original frozen algorithm, and its measurements do not come from this research build. Native process differences can be reported without claiming a stronger ideal LP relaxation.


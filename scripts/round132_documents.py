"""One research-question manuscript source, derived from retained full methods."""
from round132_common import *
import re,copy,collections,types,inspect,csv

def table(head,rows):
    return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+'\n'.join('| '+' | '.join(str(c) for c in row)+' |' for row in rows)+'\n'
def fmt(x,digits=3):return 'null' if x is None else f'{x:.{digits}f}'
def cell(a):
    if a is None:return 'pending'
    if a.get('formal_performance_evidence_eligible') is False:return 'E (own zero)' if a.get('own_exact_zero') else 'unevaluable'
    if not a.get('formal_protocol_qualified'):return 'unevaluable'
    return 'C '+fmt(a['T_cert']) if a['certificate'] else 'O @ '+fmt(a['T_produce'])

def draft():
    prior=ROOT/'results/unified_exact_round131';old=(prior/'manuscript.md').read_text(encoding='utf-8-sig')
    pobs=read(prior/'observations.json');pby={(a['id'],a['seed'],a['repeat'],a['method']):a for a in pobs['arms']}
    known=['SC-C15-S','SC-B15-S','SC-C15-B','SC-B20-S','SC-C20-S','SC-B20-U']
    known_table=table(['Known problem / Seed','P','S2'],[[f'{id} / {s}',cell(pby[id,s,1,'P']),cell(pby[id,s,1,'S2'])] for id in known for s in [0,1]])
    tiny=table(['Tiny problem / Seed / repeat','P','S2'],[[f'{id} / {s} / {r}',cell(pby[id,s,r,'P']),cell(pby[id,s,r,'S2'])] for id in ['SM-C8-S','SM-B10-B'] for s in [0,1,2] for r in [1,2]])
    boundary=table(['Known role / method','U / L','Signed U-L','T_produce','T_verify','T_total','T_cert'],[
        [f'{id} / {method}',f"{pby[id,0,1,method]['U']:.8f} / {pby[id,0,1,method]['L']:.8f}",
         f"{pby[id,0,1,method]['U']-pby[id,0,1,method]['L']:.6g}",
         *[fmt(pby[id,0,1,method][k]) for k in ['T_produce','T_verify','T_total','T_cert']]]
        for id in ['PB-C35-U','PB-B35-B'] for method in ['P','S2']])
    roles=read(OUT/'input_manifest.json')['roles']
    design=table(['Input','Source / inventory / geography','n / Q','Physical T / cap (s)','Omega / rho'],[
        [p['id'],f"{p['source']} / {p['inventory']} / {p['geometry']}",f"{p['V']} / {p['Q_vector']}",f"{p['T_seconds']} / {p['cap_seconds']}",f"{p['Omega']:.6f} / {p['rho']:.6f}"] for p in roles])
    current=read(OUT/'observations.json') if (OUT/'observations.json').exists() else dict(arms=[],pairs=[])
    by={(a['id'],a['seed'],a['method']):a for a in current['arms']}
    new_table=table(['New input / Seed','P','S2','PS (preselected subset)'],[
        [f"{p['id']} / {s}",cell(by.get((p['id'],s,'P'))),cell(by.get((p['id'],s,'S2'))),
         cell(by.get((p['id'],s,'PS'))) if p['id'].split('-',1)[1] in ['15-S','20-U','35-B'] else 'not selected'] for p in roles for s in [0,1]])
    completeD=sum(a.get('line')=='D' for a in current['arms'])
    results_text=f'The prospective layer currently has {completeD} of 60 sealed formal observations. Results are pending until the fixed complete table and its final evidence review are available; no provisional trend is used for method selection.'
    if completeD==60 and (OUT/'stratified_summary.json').exists():
        sm=read(OUT/'stratified_summary.json')
        results_text='All 60 fixed D positions are sealed. Across the full 24 S2/P positions the directions are 16 Win, 1 Lose, 6 UNDETERMINED and 1 UNEVALUABLE. Performance-eligible certificates are 17/24 for S2 and 9/24 for P; one further own-zero S2 proof is excluded from formal timing after native source loss. '
        results_text+='In K, S2/P certificates are 6/2 on 12 repeated comparisons over six problems, with 6 Win and 6 both-open. In X they are 11/7 on 12 comparisons over six problems, with 10 Win, 1 Lose and 1 UNEVALUABLE. These are finite within-mechanism and geography-transfer observations. Seeds are repeats and shared controls do not create independent trials. PS attribution is limited to the preselected six-problem subset. Problem-level zero/positive/unknown status remains distinct from each attained endpoint; zero-optimum 35 cases do not establish positive-objective35 proof performance.'
    ctext='Both research expressions passed their actual-matrix, default-off, behavioral and physical Start qualification. The fixed cost panel is awaiting serial execution; this qualification is not a performance result.'
    ctable=''
    if any(a.get('line')=='C' for a in current['arms']):
        ids=['SC-C15-B','SC-B20-S','UC-C20-U','PB-C35-U']
        ctable=table(['Known role / Seed','S2R','Delete geometry','Project W'],[[f'{id} / {s}',*[cell(by.get((id,s,m))) for m in ['S2R','S2R-GEOM','S2R-SP']]] for id in ids for s in [0,1]])
        if (OUT/'stratified_summary.json').exists():
            ctext='All 24 same-build cost workflows are sealed. Against S2R, geometry deletion records 2 Win, 4 Lose and 2 UNDETERMINED; full W projection records 3 Win, 3 Lose and 2 UNDETERMINED. Each candidate has eight repeated comparisons across four known problems. These mixed cost effects do not establish a stronger ideal relaxation. Unrecorded root/node fields remain unknown.'
    cmechanism=''
    if sum(a.get('line')=='C' for a in current['arms'])==24:
        with (OUT/'mechanism_costs.csv').open(encoding='utf-8',newline='') as f:mr=list(csv.DictReader(f))
        mb={(r['id'],int(r['seed']),r['method']):r for r in mr if r['line']=='C'}
        display=[]
        for id in ['SC-C15-B','SC-B20-S','UC-C20-U','PB-C35-U']:
            for method in ['S2R','S2R-GEOM','S2R-SP']:
                a,b=[mb[id,s,method] for s in [0,1]]
                assert (a['root_rows'],a['root_columns'])==(b['root_rows'],b['root_columns'])
                both=lambda k,d=2:' / '.join(fmt(float(r[k]),d) if r[k] else 'unknown' for r in [a,b])
                display.append([id+' / '+method.replace('S2R','root'),a['root_rows']+' / '+a['root_columns'],
                    both('canonical_continuous_LP_bound',6),both('H_plus_admission_seconds',3),
                    both('MIP_Work'),both('nodes',0)])
        cmechanism='\n\n**Table 6a. Actual expression size and costs. Paired values are Seed0 / Seed1; nodes and Work refer to MIP calls.**\n\n'
        cmechanism+=table(['Role / expression','Root rows / columns','Continuous LP bound','H + admission (s)','MIP Work','MIP nodes'],display)
        cmechanism+='\nAll16 candidate/baseline comparisons have identical complete realized H fleets/traces and matching actual root intervals/cutoffs; all expose their own native backend. Every workflow submits one restored-integer Start and retains its native-log acceptance evidence. Thus these comparisons control the paid startup and root domain. H + admission includes the recorded pre-exact boundary rather than an inferred pure-H CPU cost.\n\n'
        cmechanism+='Deleting geometry reduces rows without changing the audited ideal projection. On SC-C15-B at Seed0 it reduces MIP Work from 93.23 to 43.86 and complete time from 57.898 to 26.059 seconds, but Seed1 reverses the cost direction (Work 54.61 to 73.04; time 32.462 to 42.838). On SC-B20-S Seed0 GEOM returns open with U 0.31538912105343897 and L 0.31538869722423574, despite a shorter observed process than the certified baseline; that return is not a time Win. W projection is also mixed. None of these observations identifies a unique presolve/cut/branching cause.\n\n'
        endpoint=[]
        for seed in [0,1]:
            endpoint.append([seed,*[f"{by['PB-C35-U',seed,m]['U']:.8f} / {by['PB-C35-U',seed,m]['L']:.8f}" for m in ['S2R','S2R-GEOM','S2R-SP']]])
        cmechanism+='**Table 6b. All open PB-C35-U diagnostic endpoints, U / L.**\n\n'+table(['Seed','S2R','Delete geometry','Project W'],endpoint)
        cmechanism+='\nAt Seed0 SP has the best attained U while GEOM has the best L; at Seed1 GEOM has the best U while SP has the best L and a worse U than baseline. All six remain open, so no certification-time ranking follows. Canonical continuous LP bounds, actual MIP initial-root observations and terminal search bounds are separate fields. Unrecorded presolve/root-end Work or post-cut bounds remain unknown; a last zero-node callback is not declared the exact end of root processing. Full per-call logs, all24 cost rows, production/verification/total clocks and trajectories accompany the paper.\n'
    etext='The finite complete four-station joint-structure comparison is preregistered. Its required computation remains pending; later full-source diagnostics and any production algorithm are conditional on a valid incremental structure and a complete outside-station interface.'
    if (OUT/'joint_structure_note.md').exists():
        etext=(OUT/'joint_structure_note.md').read_text(encoding='utf-8').split('<!-- manuscript-summary -->')[1].split('<!-- /manuscript-summary -->')[0]
        etext='The four-case complete tiny study is finished. J2 retains an exact full-reference service-coordinate witness with weighted value 15/2 above the complete joint support maximum 7. Its full rational extension satisfies every saved reference row and bound. Reoptimizing the original complete micro objective after adding all joint columns gives no qualified increment in any case. This is a strict projection difference on that finite loaded reference, rather than a theorem for all inventory-routing instances. Finite failure to separate other tested normals does not establish hull equality. No full-size production cut is admitted: the tiny support maxima do not include outside donors and receivers.'
    ej=read(OUT/'joint_results.json') if (OUT/'joint_results.json').exists() else dict(cases=[])
    ecase={x['id']:x for x in ej['cases']};erows=[]
    for x in read(OUT/'E_experiment_plan.json')['cases']:
        y=ecase.get(x['id'])
        erows.append([x['id']+' / '+str(x['b']),str(x['Q'])+' / '+str(x['T']),
            str(y['single_plans'])+' / '+str(y['joint_pairs']) if y else 'pending',
            fmt(y['full_current_micro_objective_reference'],6)+' / '+fmt(y['full_current_micro_objective_joint'],6) if y else 'pending',
            'exact strict' if y and y['best_strict'] else 'numerical only' if y and y['best_numeric'] else 'no separated tested normal' if y else 'pending'])
    etable=table(['Case / initial inventory','Q / physical T','Car plans / joint pairs','Reference / joint objective','Full-reference witness'],erows)
    operational='The complete operational table is pending the sealed workflows; no synthetic service outcome is invented.'
    if completeD==60 and (OUT/'historical_physical_outcomes.json').exists():
        with (OUT/'physical_outcomes.csv').open(encoding='utf-8',newline='') as f:physical=list(csv.DictReader(f))
        display=[]
        for a in physical:
            if a['line']!='D' or a['method']!='S2' or int(a['seed'])!=0:continue
            display.append(dict(a,pickups=json.loads(a['pickups']),drops=json.loads(a['drops']),return_loads=json.loads(a['return_loads']),route_resources=json.loads(a['route_resources'])))
        display=read(OUT/'historical_physical_outcomes.json')['rows']+display
        operational=table(['Role / evidence','G / P_avg','Omega / rho','Initial / final stock','Pickup / delivery / return','Max route use'],[
            [a['id']+(' (known)' if a['line'].startswith('R131') else ' (new)'),
             f"{float(a['G_true']):.5f} / {float(a['P_avg']):.5f}",f"{float(a['Omega']):.4f} / {float(a['rho']):.4f}",
             f"{a['total_initial_inventory']} / {a['total_final_inventory']}",
             f"{sum(a['pickups'])} / {sum(a['drops'])} / {sum(a['return_loads'])}",
             f"{max(q['total_seconds']/q['T'] for q in a['route_resources']):.3f} T"] for a in display])
        operational+='\nThe display fixes S2 at Seed0 for every new input, plus two existing final-version fleets with their historical identities. It is descriptive, not another performance panel. Full per-arm inventories, station counts, per-vehicle quantities, route travel/handling and prefix peaks are in the physical outcome tables.\n'
    main=r'''# A tailored exact method for static bicycle redistribution with inventory-ratio dispersion

## Abstract

Static bicycle redistribution couples final station inventories with time- and capacity-feasible vehicle routes. We minimize the Gini dispersion of inventory-to-target ratios plus weighted relative target deviation, under empty departure and unique nonzero one-way service. GI-TBC in its uniform pair-support implementation, S2, combines a paid finite feasible startup, shared inventory-state/service reconstruction, valid physical and objective-domain rows, and a complete Gini-interval controller around native LP/MIP calls. Standard product linearizations are distinguished from problem-specific linking and scoped proof coverage.

On six known final-version problems at two solver Seeds, S2 and cold compact P certify ten and five observations. A fixed twelve-input validation gives seventeen performance-eligible S2 certificates versus nine for P, with sixteen strict time/certificate Wins, one Loss, six both-open comparisons and one UNEVALUABLE source-loss comparison. The excluded S2 arm retains its own physical zero proof but no qualified native proof or formal comparison time. Zero-optimum 35-station observations do not resolve the positive-objective boundary. Same-build equivalent-expression diagnostics have mixed cost effects. A complete tiny joint-structure study supplies one exact reference-projection witness, but no original-objective increment. Evidence layers remain separate, with solver Seeds treated as repeats. All numerical certificates have explicit qualification; no universal speed or exact serialized-projection equivalence is claimed.

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

'''+known_table+r'''
The separate tiny layer has two inputs, three Seeds and two opposite-order repeats per Seed. It gives 9 Win and 3 Lose; the three strict reverse differences are subsecond, while no >=10-second delay and no P-only certificate is observed. This finite absolute-overhead result is not a population noise bound.

**Table 2. Every repeated tiny final-version observation (seconds).**

'''+tiny+r'''
Both original 35-station roles remain open for both methods at their 2400-second caps and original Seed 0. Their final certification-time ordering is unknown. Earlier results at 50/60 stations retain their historical M-B/ENS identity and do not extend final-S2 validation. The complete signed endpoints and all three clocks are in the supporting tables.

**Table 3. Every original known 35-station boundary observation (Seed 0; seconds).**

'''+boundary+r'''
P retains the lower physical U on PB-C35-U, while S2 retains the lower U on PB-B35-B. These endpoint directions do not rank the unobserved certification times. All four T_cert entries remain null; T_total includes the separate independent verification.

### 5.3 Prospective known-source and geography-transfer validation

The new study fixes six K and six X inputs before H or optimization. K uses the existing CITI/CABI source snapshots and generator; X uses an official Chicago Divvy station snapshot with UTM16N conversion and the same synthetic target, inventory and weight rules. This changes geography, not the demand-generation mechanism and not real operational validation. The source snapshots, field provenance, missing/duplicate handling, IDs, coordinates, transformations and one-time seeds are retained. No difficulty-based filter or redraw is applied.

The six roles per layer cover shortage, balanced and surplus scenarios and compact/regional geometry at 15, 20 and 35 stations. New sets from the same source are disjoint, rather than nested enlargements. Five K roles have no overlap with the recorded historical small selections. K-35-B follows the preregistered next exposure tier and has partial historical overlap, so its stations are not all unseen. Shortage is guaranteed structurally by total initial stock below total target and positive weights/lambda; balanced or surplus zero objectives remain legitimate outcomes.

**Table 4. Fixed new-input design, physical/computational limits and effective weights.**

'''+design+r'''
All twelve inputs have independently paid P and S2 at both Seeds: 48 arms. The preselected 15-S, 20-U and 35-B role in each layer also has PS at both Seeds: 12 additional arms. The PS subset is fixed without reference to which method wins. K/X, sizes and positive/zero outcomes are reported separately; shared controls and Seed repeats are not independent new problems.

'''+results_text+r'''

**Table 5. Every fixed new-input method position (seconds).**

'''+new_table+r'''
E denotes the disclosed source-reduced own-zero proof, excluded from formal timing; C denotes a performance-eligible certificate and O an ordinary open result. On X-35-U Seed1, S2's own exact-zero fleet refutes three call4 local bounds above zero by more than1e-7. The whole call's dependent native claims are rejected. Its raw 448.483-second production clock and own physical zero remain, but derived formal T_cert is null and the comparison is UNEVALUABLE. No favorable Win is recovered from that arm, and native source reliability remains an unresolved limitation. The separate source-loss note retains the exact values and complete receipt chain.

The finite new-input results do not show uniform dominance. K-20-S and both K35 roles remain open at both Seeds; better endpoints do not order their final certification times. X-15-B Seed1 is a strict small reversal (P 2.524 versus S2 2.633 seconds). In the preselected PS subset S2/PS gives 8 Win, 2 Lose and 2 UNDETERMINED; PS/P gives 3 Win, 1 Lose and 8 UNDETERMINED. Both X-35-B Seeds are physically zero and PS certifies in 6.850/7.537 seconds versus S2 17.198/17.994. On X-20-U Seed1, however, PS takes 585.777 versus P 149.774 seconds. All 12 S2/PS comparisons have equal complete realized H and actual native exposure, supporting a scoped complete-backend comparison rather than attribution from equal startup rules alone. Neither those reversals nor geography-transfer successes erase the positive K35 proof boundary or the numerical source loss.

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

'''+ctext+'\n\n**Table 6. Every fixed same-build expression workflow (seconds).**\n\n'+ctable+cmechanism+r'''
### 6.3 What a new joint quantity structure would have to add

Let R_k be a complete finite necessary service domain and v_k its pickup, delivery and assignment vector. Convexifying each vehicle independently and then imposing unique service gives P_sep. Convexifying jointly unique integer selections gives H_joint, which is contained in P_sep. That elementary inclusion is not itself a new result. A useful increment must survive the current canonical model, single-station theta, event rank and relevant inventory-route structure, with exactly the same R_k on both sides.

The existing independent-support/unique-access bound cannot separate points already in the product of those vehicle hulls with unique service. A genuinely joint weighted support maximum is a possible stronger object. Its exact maximum or a reliable upper bound is required as a valid cut RHS; a feasible solution or a restricted column maximum supplies only a lower bound. Quantity-weighted supports must be distinguished from event-count ranks that already exist.

'''+etext+r'''

The complete tiny universes have four stations with capacity 2, target 1 and weight 1; all station and depot coordinates coincide. Both pickup and drop take 60 seconds per bicycle, including return unloading, and lambda is 0.15. J2/J3 cover shortage under two handling budgets; J1 is a balanced control and J4 is the physical startup-zero control. The current canonical continuous reference uses the same complete car plans on both sides, together with theta, exact same-domain threshold ranks and all 30 inventory-route subset rows. The original micro objective is reoptimized after adding every joint column. An artificial canonical model for J4 is reported separately from production backend exposure.

**Table 7. Complete tiny domains and their actual joint-structure outcomes.**

'''+etable+r'''
An exact strict entry denotes a rational extension in the entire saved reference matrix and an exact complete-universe support RHS. A numerical-only entry lacks that strict extension. No separated tested normal means only that the fixed finite directions did not separate; it is not a hull-equivalence conclusion. Original-objective values remain qualified native floating-point observations rather than exact rational optimality proofs. The supporting joint note retains controls, coefficients, witnesses or explicit obstacles and measured costs.

## 7. Operational meaning, limitations and next step

Reported fleets are interpreted through physical Gini, P_avg, final inventories, serviced stations, pickups/deliveries, loaded return and route travel/handling/prefix resources. A smaller ratio dispersion can coexist with target shortages; the penalty and actual service outcomes must be read together. Omega/rho varies because the original weights are not sum-normalized. No policy or sensitivity conclusion is inferred for an untested weight range.

**Table 8. Operational outcomes of existing and new legal S2 fleets.**

'''+operational+r'''

An existing valid 35-station S2 fleet illustrates why these definitions matter. Its first vehicle picks up 58 bicycles over its route with Q=20 and a maximum prefix load of 20. Across the fleet, 38 bicycles return to the depot, reducing station stock from 660 to 622. This legal loaded return and repeated use of vehicle capacity would be excluded by the incorrect bound \(\sum_i p_{ki}\le Q_k\) or a fixed station-stock equality. The example remains an open historical timing observation; its physical validity does not certify optimality.

The finite inputs, synthetic inventory mechanism, Euclidean distance convention, current parser/physical semantics and single backend limit performance generalization. Finite manageable inventory states, nonnegative inventories, positive targets and unique one-way service are explicit mathematical premises. A constructible formulation in another problem does not imply measured cross-problem performance. Timeouts, reversals and lack of objective increments constrain the claims.

Fractional reformulations remain a possible separate comparison. For S>0,

\[
F=\frac{A(r)+n\lambda S P_{true}}{nS},\qquad
\min\{A(r)+nS(\lambda P_{true}-\eta)\}
\]

is the corresponding parameter subproblem. Its numerator is not simply linear because S P_true remains. Existing MILFP work is relevant background [@yue2013], but applying it here requires an exact treatment and globally qualified subproblem bounds plus the separate S=0 branch. We do not infer that general methods are mathematically unusable from an old toy comparison, nor report an unimplemented method as a weak benchmark.

The evidence supports freezing the adopted method for scoped manuscript and submission preparation. The positive-objective 35 boundary, the disclosed unreliable native source and the paid-start reversals remain explicit limitations. Equivalent-expression costs are mixed, so neither candidate replaces S2. J2's exact joint witness is a useful structural lead, but zero original-objective gain and the missing full-universe support interface do not justify a production separator or a larger matrix now. A future study would first need to repair and qualify source reliability where relevant, and prove objective-relevant full-domain structure at an affordable cost. No universal speed or target-journal guarantee follows.

'''
    model=(prior/'model_appendix.md').read_text(encoding='utf-8-sig')
    model=model.replace('**Current-version map (Round130).**','**Current frozen method.**')
    model=model.replace('Source locations refer to production snapshot 355eefd2be3fe5651195681faf7b3a63ee4032f8 [@frozenImplementation].',
        'Historical source-line pointers retained in this derivation refer to snapshot 355eefd2be3fe5651195681faf7b3a63ee4032f8. The current frozen E3 production source base is 7564a5415331b380e24d1ec06936dcfd56557e67 [@frozenImplementation]; E3_binding.json supplies its exact current source identities. The active state/service, H-use, uniform pair-only and legal inclusive-root conditions are checked against that current source, rather than inferred from historical line numbers.')
    model=model.replace('No new contradiction with the stated numerical evidence policy was found; claims of error-free rational certification are excluded.',
        'Claims of error-free rational certification are excluded. Round132 retains a same-domain rejected native source on X-35-U Seed1: its own physical zero proof remains valid, while formal performance is excluded as described in Section 5.3 and source_loss_dispositions.json. This disclosure does not restore the rejected bound, pruning or dependent proof.')
    model=model.replace('The finite production_identity authority records all 216 bindings.',
        'That historical source map is distinct from the current frozen byte identities in E3_binding.json and D_execution_binding.json.')
    algorithm=(prior/'algorithm_appendix.md').read_text(encoding='utf-8-sig')
    algorithm=algorithm.replace('**Current-version map (Round130).**','**Current frozen method.**')
    algorithm=algorithm.replace('Algorithm 1 and its two complete subprocedures are in manuscript Section 5;',
        'Algorithm 1 appears in Section 4; its two complete subprocedures are given below in B.0;')
    algorithm=algorithm.replace('Round126 executes only the fixed complete M-B and cold P-GRB entries on the declared new panel; it changes no algorithm.',
        'The historical Round126 panel used the fixed full-M-B predecessor and cold P-GRB; it is retained under its own identity in historical_evidence.md.')
    old_entry='The unique paper entry is fully resolved in [paper_method_config.json](paper_method_config.json); [argv_freeze.json](argv_freeze.json) contains the exact six current S2 argument vectors, six independent cold controls and twelve diagnostic control vectors.'
    assert algorithm.count(old_entry)==1,'The inherited command-identity paragraph changed; inspect its actual Markdown'
    algorithm=algorithm.replace(old_entry,
        'The frozen paper entry is resolved by [current_method_manifest.json](current_method_manifest.json) together with the [inherited R130 configuration](../unified_exact_round130/paper_method_config.json). Round132 [D_argv_freeze.json](D_argv_freeze.json) fixes all 60 P/S2/preselected-PS positions; [C_argv_freeze.json](C_argv_freeze.json) separately fixes 24 same-build research-root positions. The displayed S2 command is a template, not the complete list of actual launches.')
    assert 'six current S2 argument vectors' not in algorithm
    algorithm=algorithm.replace('Section 6.8 and the root contract define',
        'Historical supplement historical_evidence.md Section 6.8 and the root contract define')
    algorithm=algorithm.replace('are in Section 6.9.',
        'are in historical_evidence.md Section 6.9.')
    algorithm=algorithm.replace('R130 now adopts S2/MS2 as the sole paper method.',
        'R130 adopted S2/MS2 as the sole paper method, unchanged through Round132.')
    algorithm=algorithm.replace('Section 6.10 states the paid workflows,',
        'Historical supplement historical_evidence.md Section 6.10 states the paid workflows,')
    subprocedures='\n\n## B.0 Complete leaf and cover subprocedures\n\n'
    for number in [2,3]:
        pattern=rf'~~~text\nAlgorithm {number} .*?\n~~~'
        match=re.search(pattern,old,re.S);assert match
        subprocedures+=match.group(0).replace('Otherwise compute (8), (B2),','Otherwise compute score (B2) in B.3,')+'\n\n'
    algorithm=algorithm.replace('## B.1 Active entry and parameters',subprocedures+'## B.1 Active entry and parameters')
    math=(OUT/'mathematical_analysis.md').read_text(encoding='utf-8')
    math=math[math.index('## 3. Projection'):math.index('## 6. Joint structure:')]
    math=re.sub(r'^## ([345])\.',lambda m:'## C.'+m.group(1)+'.',math,flags=re.M)
    appendix='\n\n\\clearpage\n\n'+model+'\n\n\\clearpage\n\n'+algorithm+'\n\n\\clearpage\n\n# Appendix C. Equivalent-expression proofs and actual-model conditions\n\n'+math
    (OUT/'manuscript.md').write_text(main+appendix,encoding='utf-8')
    # These are source-extracted supporting views, not independent manuscript
    # authorities; only manuscript.md is consumed by the PDF exporter.
    (OUT/'model_appendix.md').write_text(model,encoding='utf-8');(OUT/'algorithm_appendix.md').write_text(algorithm,encoding='utf-8')
    history=old[old.index('### 6.1 Historical'):old.index('### 6.11 Primary')]+old[old.index('## 7. Extended endpoint'):old.index('## 8. Discussion')]
    (OUT/'historical_evidence.md').write_text('# Historical evidence with original version identities\n\n'+history,encoding='utf-8')
    write(OUT/'manuscript_lineage.json',dict(authoritative='manuscript.md',PDF_input='manuscript.md + references.bib only',
        base_source_SHA=sha(prior/'manuscript.md'),full_model_and_H_controller_derivations_retained=True,
        chronological_evidence_moved_to='historical_evidence.md',body='research questions; physics; representation; one main algorithm; current final-version evidence; equivalent expressions; joint structure; operations and limits',
        current_D_sealed=completeD,provisional=completeD<60 or not (OUT/'joint_results.json').exists()))
    print('SUBSTANTIVELY_REORGANIZED_MANUSCRIPT_SOURCE_WRITTEN; PDF export is a separate checked delivery step.')

def pdf():
    # Keep the standalone entry under the same all-stages idle gate as its
    # separately metered delivery caller. No temporary PDF source is created
    # while a current research/native stage or G1 receipt remains active.
    from round132_release import idle
    idle()
    import hashlib
    import round126_export as old
    paths=[p.resolve() for p in [OUT/'manuscript.md',OUT/'references.bib',Path(__file__),Path(old.__file__)]]
    bindings=[dict(path=p.relative_to(ROOT).as_posix(),SHA=sha(p)) for p in paths]
    source=inspect.getsource(old.export)
    replacements=[
        ("for name in ['model_appendix.md','algorithm_appendix.md','tables/historical_display.md']:","for name in []:"),
        ("Path(os.environ.get('ROUND126_PDF_DEST',str(OUT/'manuscript.pdf')))","OUT/'manuscript.pdf'"),
        ("Path(os.environ.get('ROUND126_PDF_RECEIPT',str(OUT/'pdf_export.json')))","OUT/'pdf_export.json'"),
        ('text=landscape_tables(text)','text=caption_breaks(landscape_tables(text))'),
        (r'\usepackage{etoolbox}',r'\usepackage{etoolbox}'+'\n'+r'\usepackage{needspace}')]
    for before,after in replacements:
        assert source.count(before)==1,('export adaptation no longer matches',before)
        source=source.replace(before,after)
    local_date=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%d %B %Y')
    assert source.count('date=19 October 2026')==1
    source=source.replace('date=19 October 2026','date='+local_date)
    def caption_breaks(text):
        prefix='\n```{=latex}\n\\Needspace{8\\baselineskip}\n```\n\n'
        text=re.sub(r'^\*\*Table[^\n]*\*\*$',lambda m:prefix+m.group(0),text,flags=re.M)
        return re.sub(r'^For two finite optimal LPs[^\n]*$',lambda m:prefix+m.group(0),text,flags=re.M)
    ns=dict(vars(old),OUT=OUT,TEMP_PARENT=TEMP/'pdf',caption_breaks=caption_breaks)
    exec(compile(source,__file__+'::single_authority_export','exec'),ns);ns['export']()
    for row in bindings:
        assert sha(ROOT/row['path'])==row['SHA'],('PDF source changed during export',row['path'])
    receipt=OUT/'pdf_export.json';v=read(receipt);pdf=OUT/'manuscript.pdf'
    assert Path(v['PDF']).resolve()==pdf.resolve() and pdf.is_file()
    intermediate=Path(v['intermediate_root'])
    assert intermediate.resolve().is_relative_to((TEMP/'pdf').resolve())
    v.update(maintained_source='manuscript.md (including complete appendices) + references.bib',
        source_bindings=bindings,PDF_SHA=sha(pdf),
        reading_md_SHA=sha(intermediate/'reading.md'),reading_tex_SHA=sha(intermediate/'reading.tex'),
        export_function_assembly_SHA=hashlib.sha256(source.encode('utf-8')).hexdigest(),
        external_appendix_concatenation=False,output_paths_fixed_to_current_round=True,
        source_bytes_unchanged_during_export=True,
        current_native_and_closed_G1_stage_gate=True)
    write(receipt,v)
if __name__=='__main__':{'draft':draft,'pdf':pdf}[sys.argv[1]]()

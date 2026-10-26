"""Academic editing of the complete R134 manuscript; no native computation."""
from round135_common import *
import inspect, re, shutil

INTRO=r'''## 1. Introduction

Redistribution vehicles can improve station availability only when the chosen inventory vector can be realized by feasible routes and loading operations. Supply must be collected before it is delivered, capacity applies at every route prefix, and handling consumes the same time budget as travel. When equity is measured by inventory-to-target ratios, the final inventory vector also determines both the numerator and denominator of the Gini coefficient. These dependencies make routing and inventory allocation inseparable.

We study static bicycle redistribution with empty vehicle departure, loaded return, and at most one nonzero one-way service at each station. The objective combines ratio-Gini dispersion and weighted relative target deviation. The model and HGA-TGBC framework originate in the project manuscript *Equity-aware Bike Repositioning in Station-based Bike-sharing Systems* [@hgaTgbcManuscript]. The present contribution is an exact solution method for that operational setting. The supplied decoder remains a feasible-solution component; the exact method supplies the bounds, coverage and termination arguments needed to distinguish a good plan from a certified optimum.

Our first contribution is a shared finite-state representation of final inventory, service and objective information. Unique service and binary direction imply integer pickup and delivery even when these quantities are declared continuous. Linking the same states to movement and visits prevents the relaxation from treating service decisions independently of the inventory mixtures used in the objective. We develop this representation with ordered supply compatibility and support/handling inequalities, and state their assumptions and physical embeddings.

Second, the Gini-interval tailored branch-and-cut method (GI-TBC, implemented as S2) combines a fully paid feasible startup, the shared representation, valid inequalities and complete interval coverage. The controller preserves the physical problem while refining objective intervals. Its correctness depends on applicable bounds and complete coverage; numerical source qualification and physical solution verification are stated separately.

Third, the computational study measures complete-method cost against cold compact and independently paid-start compact controls. Historical breadth and final implementation confirmation retain their own versions and denominators. The study identifies substantial certification and runtime advantages, paid-start reversals and a positive-objective size boundary. A within-instance weight experiment relates the equity-target trade-off to actual vehicle operations. A bounded formulation study explains why retaining more state information can improve an LP without guaranteeing a faster complete algorithm.

### 1.1 Relation to previous work

Static bike redistribution has been studied under several target, service and vehicle conventions. Raviv et al. develop static repositioning models; Chemla et al. study static rebalancing; Erdogan et al. address demand intervals and an exact rebalancing algorithm [@raviv2013; @chemla2013; @erdogan2014; @erdogan2015]. Schuijbroek et al. connect inventory requirements to routing [@schuijbroek2017]. Forbidden temporary operations, repeated visits, robust inventory requirements and demand-interval disjunctions give related but different feasible sets [@bruck2019; @bulhoes2018; @bruck2025; @ikonen2025]. The HGA-TGBC manuscript is the direct same-problem antecedent; the other studies supply routing and formulation context rather than matched performance baselines.

Station-ratio dispersion measures a different object from vehicle-workload equity [@matl2018]. Recent fairness-aware rebalancing and equity-based micromobility models motivate distributional objectives, while their distinct inventory, vehicle and operational definitions preclude a claim of model equivalence based on their abstracts alone [@qiao2026; @caggiani2026]. Here zero Gini means equal proportional inventory, which can still represent inadequate stock. The deviation term gives a separate incentive to approach station targets.

McCormick envelopes, value disjunctions and convex state epigraphs are established formulation tools [@mccormick1976; @gupte2013; @koppe2008; @boydVandenberghe2004]. Our claim concerns their connection to this problem's service structure and the resulting complete method. The state-penalty comparison in Section 6 applies Jensen's inequality and an elementary projection construction; it is not a new general theory of aggregation. Source access and the remaining narrowly defined bibliographic questions are documented in the supplement.

'''

STRENGTH=r'''
**Lemma 1 (implicit service integrality).** Suppose initial and final inventories are integer, a station is assigned to at most one vehicle, and a binary direction permits either pickup or delivery at its unique service. Continuous pickup and delivery variables then take integer values at every integer solution of the remaining model.

**Proof.** An unassigned vehicle has zero quantities. At the unique assigned vehicle, pickup direction fixes delivery to zero, so inventory balance gives \(p_{ki}=b_i-Y_i\). Delivery direction fixes pickup to zero and gives \(d_{ki}=Y_i-b_i\). Each is integer. Integer load variables are unnecessary for this implication. The claim concerns integer feasible solutions; it does not equate the continuous relaxations of alternative formulations. \(\square\)

For an integer service, total movement is \(|b_i-Y_i|\), and nonzero one-way service occurs exactly when \(Y_i\ne b_i\). Hence the shared equations above reproduce the original operations without changing the physical problem. They also couple fractional inventory mixtures to the movement and visits that must support them.

### 3.2 Ordered supply and support/handling information

Let \(\tau\) be metric travel time and \(h=t_p+t_d\). For each receiving station \(j\), define

\[
\mathcal C_{kj}=\{i\ne j:\tau_{0i}+\tau_{ij}+\tau_{j0}+h\le T\}.
\]

**Proposition 1 (ordered supply compatibility).** Every physical fleet with empty departure satisfies

\[
d_{kj}\le\sum_{i\in\mathcal C_{kj}}p_{ki}.
\]

**Proof.** Label the units collected by a vehicle. In route order, match each delivered unit to an earlier collected unit that has not yet been delivered. Nonnegative prefix loads guarantee such a match. A unit delivered at \(j\) from source \(i\) entails the ordered subsequence \((0,i,j,0)\), whose travel lower bound follows by metric shortcutting. Collecting at least that unit incurs handling of at least \(h\), including delivery or final unloading. Thus its source lies in \(\mathcal C_{kj}\). Counting distinct matched units proves the inequality. Unmatched collected units can return to the depot. \(\square\)

For a set \(W\) of served stations, let \(\tau(W)\) be the shortest depot tour through \(W\), computed by explicit orders for pairs or triples. Write \(P_k^{\rm pick}=\sum_i p_{ki}\). Nonzero integer service and empty departure give

\[
|W|\le\sum_{i\in W}(p_{ki}+d_{ki})\le2P_k^{\rm pick},\qquad
P_k^{\rm pick}\ge\lceil |W|/2\rceil.
\]

Consequently \(\tau(W)+h\lceil|W|/2\rceil>T\) rules out serving all of \(W\) with that vehicle. Otherwise a conditional duration inequality combines the tour lower bound and pickup handling. Supply for \(W\) may come from outside \(W\); cumulative pickup is not bounded by \(Q_k\). Appendix A gives the exact conditional coefficients, deactivation proof and finite selection rule. S2 keeps pair support uniformly and omits triple support. These rows strengthen necessary physical conditions without replacing route-prefix capacity.

### 3.3 Complete startup and interval search

'''

DESIGN=r'''## 4. Computational design

P starts the original compact model independently with no startup or MIP Start. PS pays its own complete startup \(H\) and then solves that compact model. S2 pays its own \(H\) and full interval method. Each comparison uses single-threaded native solves, serial independent launches and a fixed parameter policy. No fleet, bound, tree or Start crosses methods, Seeds or objective weights. The complete production clock includes startup, modeling, online verification, solving, proof formation, cleanup and required output; subsequent offline verification has its own measured clock.

Table V identifies the evidence versions. Solver Seeds repeat a fixed problem and are not independent problem samples. The R134 confirmation targets six known roles, and the AP study targets structural and protection roles; neither is described as a random holdout.

**Table V. Evidence identity and purpose. Historical outcomes retain their original admission policies.**

| Version | Algorithm or change | Evidence used here |
|---|---|---|
| R132 | Frozen S2 and compact controls | Twelve inputs at two Seeds; breadth and original mechanism studies |
| R133 | Source/correctness repair | Fourteen exposed qualification positions and four old/new S2 bridge pairs |
| R134 | S2 with independent zero finalization | Final confirmation: 32 method positions; four new weight runs plus two reused points |
| R135 | Same S2, optional AP row | Two incremental LPs; preregistered 10-arm first stage and conditional 22-arm second stage |

The R134 confirmation uses opposite-order micro repetitions at Seeds 0/1 (90-second cap); K-15-S (600 seconds); UC-B20-B (1,200 seconds); and K-35-U, X-35-U and X-35-B (2,400 seconds). P and S2 appear at every paired role, with PS additionally present for K-15-S and X-35-B. Four S2 runs at \(\lambda=.075,.30\) supplement the fixed \(.15\) Seed0 baselines for K-15-S and UC-B20-B. The supplement gives every position, cap, Seed, repeat and measured cost.

An open run has no certification time. For two certified methods, a time difference is substantive when

\[
t_{\rm slow}-t_{\rm fast}\ge\max\{10\text{ s},0.10t_{\rm fast}\}.
\]

Micro observations retain their absolute repeated times. Open comparisons retain both \(U\) and \(L\), the signed gap \(U-L\), and source qualification; better primal and weaker dual endpoints are stated separately. Historical clocks are descriptive across environments, whereas each matched comparison shares its timing environment.

Coordinate sources and generated operational data are separate. CITI instances use the archived 443-station Citi Bike coordinate/capacity table; CABI instances use the archived Capital Bikeshare station table, and X instances use the archived Chicago Divvy station snapshot. Selection manifests identify source rows, hashes and projected coordinates. Depots are synthetic centroids; inventories, positive targets and weights follow recorded generation rules. D13 is entirely synthetic; the micro regression input uses CABI coordinates with generated operational data. These inputs test a static operational model and do not reconstruct observed trips or live station demand. The supplement records the source-to-input chain and the specific source-capture facts still needing author confirmation.

'''

SECTION6=r'''## 6. State information, relaxation strength and complete search

An objective epigraph can discard information retained in a finite inventory mixture. Let \(\rho_{iy}=y/D_i\) in the ideal model and define

\[
\phi_i(s)=\sum_y|\rho_{iy}-1|s_{iy},\qquad
a_i^+=\sum_y(\rho_{iy}-1)_+s_{iy},\quad
a_i^-=\sum_y(1-\rho_{iy})_+s_{iy}.
\]

Since \(r_i-1=a_i^+-a_i^-\), the state penalty exceeds the absolute deviation of its mean by

\[
\phi_i(s)-|r_i-1|=2\min\{a_i^+,a_i^-\}\ge0.
\]

This is the familiar convexity loss under mixing [@boydVandenberghe2004]. States on opposite sides of the target can cancel in the original epigraph; one-sided support gives no such loss. The diagnostic does not itself equal the improvement after reoptimization.

The historical VD-J formulation already tested stationwise joint penalty equalities. It reached root, pilot and development studies, but its stronger root bounds did not prevent a certificate loss and severe MIP regression on D13. The later S2 baseline has a shared inventory/service representation. We therefore test only the aggregate lower bound

\[
\sum_i\omega_i e_i\ge\sum_i\omega_i\phi_i(s),\tag{AP}
\]

which adds one row and no variables. Under compatible local \(e_i\) bounds and exclusive use of \(e\) through the total weighted penalty outside its own local constraints, AP has the same \((x,P_e)\) projection as all stationwise lower bounds \(e_i\ge\phi_i(s)\). The supplement gives the constructive proof, handles zero weights and states why this does not imply equivalence to VD-J equalities or independent \(Se_i\) products.

The two fixed S2 root domains confirm the intended numerical effect. K-20-S increases from 0.1951491524 to 0.3187585426; K-35-U increases from 0.2001776619 to 0.2738576813. AP matches the previously observed stationwise optima within the existing numerical policy. All layers use the same input, support, interval and cutoff. The original and stationwise optima are reused; exactly two new continuous LPs add only AP. Production coefficients use the loaded binary64 ratio coefficients and downward-rounded nonnegative state coefficients. The ideal projection result and floating-point observations are distinct statements.

@@AP_COMPLETE_METHOD@@

A separate inventory-threshold count inequality has a strict exact increment of \(3/16\) on two named tiny joint-service references while adding no reliable increment on these real roots after retaining the old state-penalty control. Its full derivation, controls and negative real-root evidence remain in the supplement. These comparisons distinguish useful state information, stronger relaxations and faster complete algorithms.

'''

ABSTRACT=r'''## Abstract

Static bicycle redistribution couples final station inventories with vehicle routes, prefix loads and handling time. We minimize ratio-Gini dispersion plus weighted relative target deviation under empty departure, loaded return and unique nonzero one-way service. Our exact method shares finite inventory states between service and objective representations, uses problem-specific supply and support inequalities, and maintains complete Gini-interval coverage around native LP and MIP solves. We prove implicit service integrality and establish the physical embeddings and coverage conditions needed for certification. In historical twelve-input/two-Seed validation, the method obtains 17/24 qualified certificates versus 9/24 for a cold compact control. Final implementation confirmation on six known roles obtains 12/14 versus 9/14, while retaining two substantive paid-start compact reversals and unresolved positive-objective 35-station endpoints. Six certified within-instance weight points show an equity-target trade-off on one input and a stable operating platform on another. The results support the integrated exact method within the specified model and test scope, and a bounded state-penalty study distinguishes relaxation improvement from complete-search performance.

'''

def prepare():
    assert not (OUT/'paper_body.md').exists(), 'One-time preparation; edit the maintained manuscript sources in place'
    old=ROOT/'results/unified_exact_round134';text=(old/'manuscript.md').read_text(encoding='utf-8-sig')
    main,appendix=text.split('# Appendix A.',1)
    main=main[:main.index('## Abstract')]+ABSTRACT+INTRO+main[main.index('## 2. Physical model and objective'):]
    a=main.index('**Proposition 1 (an independent zero certificate).**');b=main.index('## 3. Shared inventory states and the S2 algorithm')
    zero=main[a:b].replace('**Proposition 1 (an independent zero certificate).**','**Independent zero termination.**')
    main=main[:a]+main[b:]
    main=main.replace('## 3. Shared inventory states and the S2 algorithm\n\n','## 3. Shared inventory states and the S2 algorithm\n\n### 3.1 Discrete states and implicit service integrality\n\n')
    a=main.index('S2 retains the A/B links,');b=main.index(r'The startup \(H\)',a)
    main=main[:a]+STRENGTH+main[b:]
    main=main.replace('from Proposition 1.','from the independent zero rule.')
    a=main.index('## 4. Computational design');b=main.index('## 5. Complete-method and operational results')
    main=main[:a]+'### 3.4 Numerical qualification and termination\n\n'+zero+DESIGN+main[b:]
    main=main.replace(r'The present change adds independent proof finalization and leaves the production matrices, \(H\), representation, support, search and numerical tolerances fixed.',
        'R134 adds independent zero finalization while preserving S2 matrices, startup, representation, support, search and tolerances. R135 evaluates AP as a separate default-off candidate.')
    a=main.index('All 32 fixed positions completed,');b=main.index('**Table 1.',a)
    main=main[:a]+('The final confirmation produces 12/14 S2, 9/14 P and 2/4 PS certificates. Against cold P, S2 has nine both-certified comparisons and three additional certificates; two pairs remain open on both sides. A repeated advantage on the actual split/child-target role UC-B20-B saves about 315 seconds at each Seed. X-35-U includes a large complete-time improvement, and all micro repetitions have lower S2 absolute time.\n\n'
        'Paid-start compact remains effective on X-35-B: PS certifies in about 7.2 seconds while S2 takes about 18 seconds at both Seeds. Both reversals meet the substantive-difference rule. Table 1 retains them alongside the S2 gains. One independently certified exact-zero observation retains its rejected native-source flag.\n\n')+main[b:]
    a=main.index('K-35-U Seed0 has');b=main.index('### 5.4 Within-instance objective weights',a)
    main=main[:a]+('The unresolved K-35-U endpoints delimit the positive-objective size evidence. The complete endpoint tables retain both bounds at each Seed. At Seed0 cold P has the better primal endpoint while S2 has the better lower bound; at Seed1 S2 improves both endpoints. This differs from the certified zero objectives on X-35-U and X-35-B: station count alone does not describe proof difficulty. K-35-B\'s optimum class remains unconfirmed.\n\n'
        'Physical operation tables retain all quantities, final stocks, returns, prefix peaks and durations. A legal historical fleet collects 58 units with capacity 20 by delivering at intermediate stations; cumulative pickup remains compatible with prefix capacity. Loaded returns remove stock from station inventories and incur depot unloading time.\n\n')+main[b:]
    a=main.index('All six prescribed weight points');b=main.index('Figure 1 locates',a)
    main=main[:a]+('All six points are certified. On K-15-S, increasing the weight reduces average relative deviation and increases Gini; pickups rise from 26 to 28 units, and the longest route uses over 99% of its duration budget. On UC-B20-B, all three weights give the same observed Gini/deviation values and aggregate operations: 14 pickups and 6 units returned. This platform is consistent with the optimality relations above. Effective weights and full-precision endpoints accompany the vehicle records; accepted objective gaps, rather than feasibility tolerance, control the numerical interpretation.\n\n')+main[b:]
    a=main.index('## 6. Inventory-threshold counting');b=main.index('## 7. Conclusions and implications')
    tc=main[a:b];main=main[:a]+SECTION6+main[b:]
    a=main.index('## 7. Conclusions and implications')
    main=main[:a]+r'''## 7. Conclusions and implications

Shared inventory/service states provide a coherent exact formulation for ratio-Gini bicycle redistribution. Unique one-way service yields implicit service integrality; ordered supply and support/handling information connect attainable inventory to vehicle resources. Complete interval coverage and physical verification turn qualified native bounds into whole-problem evidence.

The supported S2 implementation improves certification coverage and complete runtime against cold compact on the stated historical and final panels. Independently paid-start compact reversals and open positive-objective 35-station cases remain meaningful limits. The weight experiment shows why normalized penalty weight and actual vehicle operations are needed to interpret equitable service restoration.

@@AP_CONCLUSION@@

The principal limitations are targeted rather than random validation inputs, synthetic operating data on geographic coordinate sources, a single qualified native backend, and unresolved positive-objective scale. Future evidence should address these boundaries while retaining the full cost and proof-source distinctions used here.

'''
    appendix=('# Appendix A.'+appendix).replace('in Proposition 1;','in Section 3.4;')
    # Editorial source is maintained in model_and_algorithm_appendices.md after preparation.
    end=appendix.index('## B.12 Separately identified inclusive-root research control')
    history=appendix[end:]
    appendix=appendix[:end]+'\nThe separately evaluated inclusive-root, support and equivalent-expression controls are documented in Supplement S11 with their original evidence identity.\n'
    for name,value in [('paper_body.md',main),('model_and_algorithm_appendices.md',appendix),
                       ('threshold_count_supplement.md',tc),('historical_controls_supplement.md',history)]:
        (OUT/name).write_text(value,encoding='utf-8')
    shutil.copyfile(old/'references.bib',OUT/'references.bib')
    with (OUT/'references.bib').open('a',encoding='utf-8') as f:f.write(r'''
@misc{hgaTgbcManuscript,
 title={Equity-aware Bike Repositioning in Station-based Bike-sharing Systems},
 year={2026}, howpublished={HGA--TGBC project manuscript, local draft available May 2026},
 note={The inspected draft does not list bibliographic authors or a subsequent publication identifier; final attribution and current status await author confirmation}
}
@book{boydVandenberghe2004,
 author={Boyd, Stephen and Vandenberghe, Lieven}, title={Convex Optimization},
 publisher={Cambridge University Press}, year={2004},
 url={https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf},
 note={Sections 3.1.7--3.1.8: convex epigraphs and finite Jensen inequality}
}
''')
    (OUT/'figures').mkdir(exist_ok=True)
    for n in ('weight_tradeoff.png','count_bound_scope.png'):shutil.copyfile(old/'figures'/n,OUT/'figures'/n)
    write(OUT/'document_edit_plan.json',dict(UTC=utc(),base_manuscript_SHA=sha(old/'manuscript.md'),
        main_contributions_recentered=True,service_integrality_supply_support_proofs_promoted=True,
        zero_rule_moved_to_termination=True,TC_moved_to_supplement=True,awaits_AP_results=True,
        PDF_marker_successful_invocations=1))
    print('Academic body and complete appendices prepared; AP paragraphs await registered results')

def assemble():
    d=read(OUT/'candidate_decision.json');assert d['study_complete']
    main=(OUT/'paper_body.md').read_text(encoding='utf-8')
    main=main.replace('@@AP_COMPLETE_METHOD@@',d['paper_results_paragraph']).replace('@@AP_CONCLUSION@@',d['paper_conclusion_paragraph'])
    assert '@@' not in main
    (OUT/'manuscript.md').write_text(main+'\n\\clearpage\n\n'+(OUT/'model_and_algorithm_appendices.md').read_text(encoding='utf-8'),encoding='utf-8')
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),
        bibliography_SHA=sha(OUT/'references.bib'),candidate_decision_SHA=sha(OUT/'candidate_decision.json'),
        no_result_placeholders=True,full_maintained_appendices=True))
def pdf():
    assert read(OUT/'candidate_decision.json')['study_complete'] and not budget()['unclosed']
    import round134_documents as old
    code=inspect.getsource(old.pdf)
    needle="m[0].startswith('**Table 1.')"
    assert code.count(needle)==1
    code=code.replace(needle,"m[0].startswith('**Table 2.')")
    def layout_before(value):
        fence=chr(96)*3
        for heading,command in [
            ('### 3.4 Numerical qualification and termination',r'\Needspace{18\baselineskip}'),
            ('## A.6 Cutoff and coverage proof',r'\Needspace{18\baselineskip}'),
            ('## 7. Conclusions and implications',r'\Needspace{14\baselineskip}'),
            ('## 6. State information, relaxation strength and complete search',r'\clearpage')]:
            assert value.count(heading)==1
            value=value.replace(heading,'\n'+fence+'{=latex}\n'+command+'\n'+fence+'\n\n'+heading)
        return value
    needle='    def keep_captions(value):'
    assert code.count(needle)==1
    code=code.replace(needle,needle+'\n        value=layout_before(value)')
    needle="for heading in ('## 7. Conclusions and implications','# References'):"
    assert code.count(needle)==1
    code=code.replace(needle,"for heading in ('# References',):")
    ns=dict(vars(old),OUT=OUT,TEMP=TEMP,layout_before=layout_before)
    exec(compile(code,__file__+'::maintained_pdf_export','exec'),ns)
    ns['pdf']()
if __name__=='__main__':{'prepare':prepare,'assemble':assemble,'pdf':pdf}[sys.argv[1]]()

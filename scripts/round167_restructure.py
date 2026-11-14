"""One-time, source-faithful reorganization of the current English manuscript."""
from round167_common import *
import re
PAPER=ROOT/'results/unified_exact_round137'
old=subprocess.check_output(['git','show',BASE+':results/unified_exact_round137/paper_body.md'],cwd=ROOT).decode('utf-8-sig').replace('\r\n','\n')
def section(start,end): return old[old.index(start):old.index(end)].strip()+'\n\n'
def content(start,end):return section(start,end).split('\n',1)[1].strip()+'\n\n'
def table(n,new):
    match=re.search(r'^\*\*Table '+re.escape(str(n))+r'(?:\.|, panel \(b\)\.).*?(?=^\|)',old,re.M|re.S)
    assert match,n
    start=match.start();end=match.end()
    while end<len(old) and old[end]=='|':end=old.find('\n',end)+1
    text=old[start:end].strip()
    text=re.sub(r'^\*\*Table '+re.escape(str(n))+r'(?:\.|, panel \(b\)\.)','**Table '+str(new)+'.',text,count=1)
    return text+'\n\n'
def narrative(text):return text.strip()+'\n\n'
def main():
    assert '## 6. Conclusions' not in (PAPER/'paper_body.md').read_text(encoding='utf-8-sig'),'one-time edit: do not overwrite later revisions'
    intro=content('## 1. Introduction','## 2. Physical model')
    intro=intro.replace('We further characterize the joint local graph:', 'We characterize the joint local graph:')
    intro=intro.replace('The compact representation is evaluated as the separately named C166 candidate; it does not change B\'s definition.',
        'The compact representation is evaluated as the separately named C166 candidate; the conditional network discussed below remains an offline representation prototype.')
    intro+=narrative(r'''The distinction matters to an operator choosing a fleet plan and to a researcher choosing an exact representation. A stock mixture that supplies a strong root bound may cease to explain the service mixture after some encoding decisions have been fixed. Conversely, a representation that preserves more such information can require more continuous variables and conservation rows on the capacities encountered in practice. We therefore state exactly which information each formulation preserves, then assess its observable computational consequences. The final decision analysis uses the same physical fleets and qualified bounds to answer what can be guaranteed about extra route time or a change in objective weight, including when a complete optimal route plan remains unknown.''')
    physics=content('## 2. Physical model and objective','## 3. Shared inventory')
    shared=content('### 3.1 Discrete states','#### 3.1.1 A compact')
    compact=content('#### 3.1.1 A compact','### 3.2 Ordered supply')
    compact=compact.replace('Exact state penalties, threshold counts, vehicle-state assignment or holed stock domains need additional supports or restrictions.',
        'Exact state penalties, threshold counts and vehicle-state assignments need their own common pieces; holed integer membership must be retained by an explicit code or legal paths.')
    compact=compact.replace('Section 3.1.1','Section 2.3')
    conditional=narrative(r'''### 2.4 Preserving conditional code information

Preserving the physical hull does not preserve its relation to a separately chosen inventory code. Let \(c(y)\) be the absolute base-2 code with \(d=\max\{1,\operatorname{bit\_width}(C)\}\), and augment the joint graph by \(\delta=c(y)\) and \(w=gc(y)\). Denote its convex hull by \(E(D)\), where \(D=[l,u]\cap\mathbb Z\). For \(D=\{0,\ldots,4\}\), \(b=2\), \(g\in[0,1/2]\), fixing \(\delta_0=1\) leaves stocks \(\{1,3\}\), hence movement and visits both equal one. C166 instead permits \(Y=2,M=V=0,g=1/4,Z=1/2\), with \(\delta=(1,1/2,0)\), \(w=(1/4,1/8,0)\). Its stock support chooses only the initial state while its independent code layer uses a different mixture.

**Proposition 1 (conditional joint representation).** A fixed MSB-first interval DAG, separated into donor, initial and receiver pieces, represents \(E(D)\) with \(O(1+\log(C+1))\) columns, rows and nonzeros. On the same edges let

\[
Af=e,\qquad Aq=ge,\qquad f\ge0,\qquad \alpha f\le q\le\beta f.
\]

Here \(e\) is unit source-sink balance. Path costs reconstruct \(Y,M,V\) from \(f\), \(Z\) from the same \(q\), and every code/product digit from the corresponding bit-one edges. Fixing any subset of absolute digits gives exactly \(E(D(F))\), with physical projection \(H(D(F))\).

**Proof sketch.** Tightness to interval bounds uses at most four states per bit layer; each legal stock has a unique complete path. For \(\alpha<\beta\), the nonnegative conserved flows \((\beta f-q)/(\beta-\alpha)\) and \((q-\alpha f)/(\beta-\alpha)\) decompose into legal paths at the two Gini endpoints. At \(\alpha=\beta\), use \(q=\alpha f\) directly. A fixed digit removes inconsistent paths by nonnegativity. Appendix A.11 gives both directions, integer exactness and the embedding condition. \(\square\)

The enumerated same-code reference R_abs retains every continuous stock/product weight and explicitly links its absolute digits; historical LOG uses the offset \(y-l\). D167 matches R_abs's enhanced projection and can strictly strengthen conditioned C166. The unconditioned physical projections coincide. Network-flow and disjunctive convexification are established tools [@behle2007; @balas2005; @muldoon2013]; the contribution here is their joint stock/service/product application and conditional boundary. The guarantee concerns these digit fixes, not arbitrary Native branches, a full routing hull or the historical cause of C166's search cost.''')
    ordered=content('### 3.2 Ordered supply','### 3.3 Complete startup').replace('**Proposition 1 (ordered','**Proposition 2 (ordered')
    startup=content('### 3.3 Complete startup','### 3.4 Numerical').replace('**Proposition 2 (coverage)','**Proposition 3 (coverage)')
    zero=content('### 3.4 Numerical','### 3.5 A separately')
    policy=narrative(r'''The complete clock starts before own startup and includes import, construction, all Native calls, online physical/numerical qualification, cleanup and required output. Required later verification is recorded separately; nested writer, helper, Runtime, Work and node counters explain this work and are not added again. Physical route horizon \(T\) and computational cap are distinct. The registered caps are 600/1200/2400 s by size. An OPEN observation has no certificate time, and its budget never substitutes for convergence. On the intersection where both methods qualify certificates, a paid-time difference is substantive when at least \(\max\{10\text{ s},.1\times\text{faster time}\}\).

All main runs use Gurobi 13.0.2, one thread and fixed processor affinity on an Intel i7-12700KF Windows host. Requested relative and absolute MIP gaps are zero; NodeLimit is unlimited and Native strategies retain their defaults. Solver tolerances are \(10^{-6}\) feasibility/optimality and \(10^{-5}\) integrality, with the separate \(10^{-7}\) project certificate/equivalence policy. A numerical proof source must match the actual input, objective, domain, interval, cutoff and model identity and pass the applicable primal/bound/physical-consistency gates. Raw LP values mean all integer types were relaxed before optimization; MIP-root values after cuts are a different observation. The implementation's qualification and conservative source-rejection fallback are specified in Appendices A.7 and B.4.

Feasible endpoints always come from a complete independently checked fleet evaluated with the original objective, including true Gini, all inventory balances, empty departure, every load prefix, nonzero one-way service, loaded return and unloading. A returned native objective with inflated epigraph auxiliaries cannot replace that evaluation. A bound restricted to one interval or cutoff does not certify the full physical problem until combined with all coverage and complement obligations. Source rejection removes the dependent certificate, while a sufficient independent zero proof remains available. Rounded display values are never reimported as physical witnesses or exact bounds.''')
    enhancement=content('### 3.5 A separately','## 4. Computational design')
    protocol=content('## 4. Computational design','## 5. Complete-method')
    # Keep the prospective input design and cohort definitions; state clocks once.
    protocol=protocol[protocol.index('The fixed-source protocol'):]
    protocol=protocol[:protocol.index('Caps are 600/1200/2400')]+table(1,1)
    protocol=protocol.replace('§5.5','§4.3').replace('24 additional','24')
    comparator=narrative(r'''The comparators isolate different questions. P is the independent cold compact model. PS recomputes and pays complete own H, then supplies only its own fleet to that model. The strengthened root-only control keeps shared states, physical rows and own startup, and solves the unsplit root using Native branch-and-cut; B adds the complete external control package. B/P and B/PS therefore compare integrated methods, whereas full/root tests the additional controller package. E+/B tests a separate paid proof source. C166/B changes the representation within the same complete B lifecycle. R_abs/C166/D167 below compare offline conditional LP expressions and do not supply new complete-method observations. No solution, bound, tree, Start or free helper crosses methods, Seeds, weights or physical configurations. Same solver Seed is a shared setting, not an identical random trajectory.

Tables report each registered panel on its own denominator. Repeated use of a matching baseline in AM, mechanisms, resource or weight analysis refers to the same historical record, counted once. The six later source configurations are new relative to the earlier panels but already exposed for their Seed and representation follow-ups. Different Seeds on them remain repeated within-input observations. The four resource pairs use identical data except route time, and the normalized weight families retain the same physical feasible set. These contracts distinguish wider coverage from replication and from a change in the question asked of an existing run.''')
    mainpanel=content('### 5.1 Current main panel','### 5.2 Positive objectives')
    mainpanel=mainpanel[:mainpanel.index('The complete paired interpretation')]
    cohort_intro=narrative(r'''The later cohort contains six archived-source configurations, selected once from a frozen recipe across three sources and two sizes before all 18 B/E+/P runs. Synthetic stock, targets and weights supply finite configuration coverage. Table 4 retains the complete Seed0 endpoints. The same inputs then receive two additional predeclared solver Seeds for B/P, paying fresh lifecycles and own H with fixed H seed 20260626; the 24 additional runs create twelve paired repetitions, not twelve new physical inputs.''')
    cohort=cohort_intro+table(8,4)
    cohort+=narrative(r'''B and E+ certify 3/6, versus P 1/6. Their physical U coincide on all six inputs; E+ raises X35's qualified L from .3949882559151472 to .42319954961578576 at U=.45747531701601785. The relative gap falls from 13.6591% to 7.49238%, without a new certificate. E+'s lower raw search L=.39492875817006656 identifies the independent proof contribution. Its three joint-CERT B comparisons add 26.10, 1.70 and 6.18 s on C20/B20/X20; only C20 is substantive under §3.4. The helper's paid cost and its remaining inventory-price widths, .0143871/.0229556 on B35/X35, accompany the proof gain. Earlier near-tight inventory prices cannot be assigned to these later domains.

The B/P joint-CERT denominator is only B20 (1/6). B has lower U than P on three inputs, worse U on C35 and equivalent U on two; its L is stronger on five and equivalent on B20. C35 retains P's historical U=.09331934374779818 against B's .12956638965196035. Thus even this favorable certificate panel includes a saved primal reversal and all large inputs OPEN. No best-of-B/E+ method is constructed.''')
    cohort+=table(9,5)
    cohort+=narrative(r'''At every Seed, B certifies 3/6 and P 1/6. B35 and X35 retain better B U and L in all three observations, while every n35 B/P run remains OPEN. C35's within-Seed primal ordering reverses: P is better at Seed0 and B at Seeds1/2, while B's L remains higher. Nevertheless the historical P fleet improves all three saved B incumbents: their U are .129566390/.107429866/.108083936, versus P's .093319344/.157624313/.146764456. This is an incumbent deficit, not evidence for a persistent within-Seed ranking or an isolated causal route operator.

Paid B certificate times at Seeds0/1/2 are 199.779/354.388/341.810 s on C20, 5.05829/4.96364/5.27705 s on B20 and 119.749/136.999/131.829 s on X20. P certifies only B20, in 235.856/303.033/266.801 s. Those three within-Seed B20 comparisons are substantive; they do not yield a full-panel speedup. The independently pre-frozen feasible-target diagnostic also shows B missing C35's known target in all three runs and X35's target in both new Seeds, even when B beats the corresponding P run. The supplement retains availability intervals, censoring, all individual U/L and costs, together with the limited earlier four-role second-Seed check (B 3/4, P and PS 1/4 at each Seed).''')
    cohort+=section('![Three-Seed original-objective','Certificate-status consistency')
    mechanisms=narrative(r'''### 4.4 What the mechanism controls identify

The four selected Seed0 roles compare full B, strengthened root-only, and single deletion of movement/visit links A/B, resource group \(C_R\), or geometry/objective group \(C_G\). Core products, original integer physics, own startup and the configured controller policy remain. Row deletion can change reached states and realized actions, so these are conditional contrasts rather than additive shares of a speedup. Initial matched-scope LPs expose A/B increments on two roles; the other groups show no detected initial-root increments in this panel. Removing a valid group cannot improve the ideal minimization bound, but can improve complete Native search.

On K-15-S, full B certifies in 112.769 s. Deleting \(C_R\) reduces it to 75.2546 s, while deleting A/B or \(C_G\) increases it to 128.246/143.383 s. The \(C_R\) reversal occurs mainly inside MIP: Runtime falls 110.549 to 73.048 s, Work 160.926 to 109.31 and nodes 48701 to 29036; generation differs by .0231363 s. Seed1 reverses all three deletion-time directions: full 115.444 s versus 93.6997/132.475/99.6006 s after A/B, \(C_R\), \(C_G\) removal. Root-only times, 112.649/113.580 s at the two Seeds, differ nonmaterially from full. The complete tables and cost accounting are in Supplement S167.2.

Hard roles retain opposed endpoints. On K-20-S, full and root-only share U=.716807 and finish with L=.705356/.706405. Deleting \(C_R\) weakens full L to .703444. On K-35-U, full U/L=.692854/.565766; A/B deletion improves U to .654639 and weakens L to .564355, while \(C_G\) deletion gives .666262/.550980. Root-only shares full U and has L=.566106. All these runs remain OPEN. Across the four Seed0 roles, full has no substantive certificate-cost advantage over root-only: the two easier roles have nonmaterial differences, and root-only retains slightly better L on both harder roles. The integrated B/P gains therefore do not establish an independent net benefit of external scheduling.

AM thresholds .04/.08/.16 are tested on the same four roles and two preselected Seed1 repeats. Finite observed child scores stay below .04; logical-infeasibility splits are separate. The AM/mechanism ledgers retain every tested role, finite gate, terminal and logical split, plus guards and incomplete eligibility exposure. Unchanged observed actions at these thresholds are not general robustness or proof of low outer cost. They describe the states actually reached under the fixed policy.

Other structural results delimit the interpretation. The complete joint service hull still leaves the inherited four-station fixed-positive-stock original-objective gap of exactly 1/4; the corresponding loaded-return proof checks all legal totals. Local product ideality is therefore weaker than the integer objective or full routing hull. Full-physical shared-G completion excludes saved points, yet free reoptimization gives the same LP value on one domain and only about .00018725 gain on another. A projected row retains about 87% of that gain. Six complete primary-role arms then have worse U than both fresh controls, equal proof L and no certificate; four conditional positions remain unstarted. Those negative outcomes remain alongside the positive scoped LP result.

The independently priced inventory problem gives \(L_I\le f_I^*\le U_I\) and \(f_I^*\le f_P^*\le U_P\). Thus

\[
U_P-L_I=(U_P-f_P^*)+(f_P^*-f_I^*)+(f_I^*-L_I).
\]

Only the final term is bounded by the price width \(U_I-L_I\). A precise necessary inventory value cannot determine the physical realization gap or incumbent quality. The earlier inventory/resource/product studies and their positive, mixed and adverse complete outcomes are retained in the supplement by mathematical object. They supply context for E+ and for the conditional representation, without adding another current main-method cohort.''')
    rep=content('### 6.5 Compact representation','## 7. Conclusions')
    rep=rep.replace('Section 3.1.1','Section 2.3').replace('**Table 16.','**Table 6.')
    rep=rep.replace('The predeclared material-difference scale is max(10 s, 0.1 times the faster\ncertificate time).','The comparison uses the policy in §3.4.')
    rep=rep.replace('from the same new executable','from the same executable').replace('new B/P test','additional B/P test')
    diagnosis=narrative(r'''The conditional network is tested separately on eight frozen canonical frames, with three deterministic bit scopes and R_abs/C166/D167: 72 raw LP positions. Twelve fixed local LPs and four independently enumerable tiny physical MIPs complete the offline diagnostics. All 88 Optimize calls qualify. Across 24 frame/scope triples, D167 and R_abs differ by at most \(2.22\times10^{-16}\); unconditioned objectives also match C166. Among sixteen conditioned triples, strict D167 increments over C166 are .000358489 on X20 root F2 and .00000692904/.0000208111 on B35 root F1/F2. The other thirteen match numerically. D167 has more columns and rows than R_abs on every frame; preparation plus diagnostic execution takes 126.262 s, including the solver-free checks. These modest, local increments retain research value, but the present implementation does not yet motivate complete integration or a speed claim. Full positions, dimensions and costs are in the supplement.''')
    resources=narrative(r'''### 5.1 What more route time certifiably buys

The four input-designed resource pairs fix the physical data, normalized weights and \(\rho=1\), and change only route horizon T. Each base has positive shortage, positive weights and a pre-solve positive objective floor; the design uses no observed difficulty filter. Increasing T enlarges the physical feasible set, but finite-budget bounds and computational time can move in either direction.''')+table(4,7)
    resources+=narrative(r'''GI-TBC certifies the two B20 objectives .480735/.198473 at 3300/5100 s, with certificate costs 784.143/538.603 s. It certifies X20's .645325/.434796 at 4800/7200 s, with costs 20.5065/337.305 s. Thus both pairs have the same resource-value direction and opposite proof-cost directions. On X20's smaller horizon every method attains the same feasible objective, but P/PS remain open at L=.589197/.590359. The distinction is proof-gap closure, not a transferred incumbent or certificate.

All three methods remain OPEN on all four n35 resource configurations. B has lower U and higher L than the compact controls at the registered caps. For X35's larger horizon B gives .403272/.210887, PS .404567/.203817 and P .490517/.201288. These are endpoint improvements with no certificate-time ranking. On B35 the smaller-horizon interval [.455904,.591518] lies above the larger-horizon upper .344643, even though both B runs are open. The same separation can be bounded in both directions on every pair.

If \([L_j,U_j]\) contains the optimum at \(T_j\), feasible-set nesting gives

\[
\max\{0,L_1-U_2\}\le F^*(T_1)-F^*(T_2)\le U_1-L_2.
\]

The computation uses the complete full-precision fleets and qualified global lower sources. Each original lower is reduced by \(10^{-7}\), and recomputed feasible objectives receive \(10^{-12}\) upward protection. These guards and outward display rounding are retained in Table 8; all arithmetic and source ownership are preserved in the decision data.''')+table(5,8)
    resources+=narrative(r'''The n35 intervals prove strict optimal-objective improvement, but leave widths .261271 and .321218; positivity of the lower endpoints does not determine the magnitude precisely. The smaller pairs localize the change to about two parts in ten million in objective units. These are differences in the specified dispersion/deviation objective, not monetary savings or general marginal prices of vehicle time.

All four larger-horizon saved B fleets reduce both Gini and average target deviation and collect more units: pickups change 30 to 43, 16 to 22, 41 to 60 and 29 to 42 on B20/X20/B35/X35. Return loads change 0 to 0, 1 to 0, 2 to 3 and 1 to 0. B35 improves while returning more inventory and reducing total station stock by one; X35 returns less and increases that total by one. X35's normalized stock sum S nevertheless falls from 28.7591 to 28.2238, because target denominators weight allocation differently from mass. The saved route durations are near their limits, but near-full utilization does not prove that an unknown optimum has a binding horizon. The supplement retains every route's travel, handling, unloading, prefix peak and station inventory distribution.''')
    resources+=section('![Original-objective endpoints','### 5.3 Objective weights')
    weights=content('### 5.3 Objective weights','### 5.4 Limited preselected')
    weights=weights.replace('**Table 6.','**Table 9.').replace('**Table 6, panel (b).','**Table 10.').replace('Table 5','Table 8')
    conclusion=narrative(r'''## 6. Conclusions

GI-TBC connects shared inventory states, objective products, movement and nonzero visits within the inherited bicycle redistribution problem. Objective-preserving physical extensions and complete improving-interval coverage supply the exact-method argument; own startup, qualification, continuation and termination make it a complete implementable method. The HGA-TGBC problem and decoder lineage remain explicit. Standard convexification, network and binary-product tools retain their established attribution.

The finite complete comparisons support B as the uniform main method. The breadth panel gives 9/12 certificates versus 7/12 for each compact control, and the positive-resource panel gives 4/8 versus 0/8. In the later six-input cohort B's 3/6 versus P's 1/6 repeats at three solver Seeds. All large cases in that cohort remain open, C35 reverses its within-Seed primal ordering, and its historical P fleet exposes all three B incumbent deficits. E+ supplies a genuine stronger X35 proof endpoint at a separately paid cost, including a substantive C20 increase. The selected full/root controls leave the outer controller's independent net computational benefit unresolved.

Representation strength and complete value also remain distinct. Five legal stock supports preserve the joint physical LP interface, but C166 certifies 2/6 versus B's 3/6 and substantially increases X20 proof cost. Its C35/B35 primal improvements coexist with weaker lowers, and X35 worsens on both sides. The conditional network establishes precisely what its disjoint code layer can lose: one common stock/service/product/code hull survives every partial absolute-bit fix. D167 matches that enumerated hull, with three strict conditioned LP increments in the fixed frames, but costs more rows and columns at these capacities. It remains an offline research prototype; no full-method acceleration or causal Native-branch explanation follows.

The same verified fleets and qualified global bounds support decisions beyond certificate counts. Four continuous-weight archive envelopes give whole-range regret bounds .002356282, .000000100002, .015594269 and .136115162. They distinguish a stable known fleet, supported plan switches and unresolved quality without claiming the complete Pareto frontier. All four route-time pairs have strictly positive optimal-objective improvement bounds; the n35 magnitude intervals remain broad. Better displayed objectives can accompany more loaded return, as on B35, or less, as on X35. These are bounded conclusions about inventory-to-target ratio dispersion and target deviation, not demographic fairness or monetary returns.

Further algorithm comparisons require a representation whose conditional information survives the declared physical interface at an acceptable complete cost, followed by independently paid own-H full-method evidence with qualified endpoints and all adverse cases retained. Better local hulls, fewer binaries and small LP times are insufficient substitutes. The unresolved incumbent deficits, physical realization gaps and separate value of interval scheduling are specific scientific questions; the present study closes neither them nor the general scalability of equitable redistribution.''')
    body=old.splitlines()[0]+'\n\n'+narrative(r'''## Abstract

Static bicycle redistribution couples inventory equity to routes with empty departures, prefix capacity and paid handling, including loaded returns. GI-TBC connects shared inventory states, movement and nonzero visits to objective products, then combines own feasible startup with complete true-Gini interval coverage. The breadth panel gives 9/12 certificates versus 7/12 for each compact control; a positive-resource panel gives 4/8 versus 0/8. Limited within-input Seed evidence retains open and adverse endpoints. Compact and conditional state representations distinguish preserved information from complete computational efficiency. Verified fleet archives and global lower bounds yield continuous-weight guarantees: one fixed fleet stays within an absolute objective tolerance of 1.00002e-7 over its covered range. Two-sided route-time bounds establish strict optimal-objective improvement even where optimal routes remain unproved, while large-instance improvement magnitudes remain uncertain. These finite results support the integrated exact method and bounded transportation decisions; the controls leave the independent speed benefit of external interval scheduling unresolved.''')
    body+='## 1. Introduction and related work\n\n'+intro
    body+='## 2. Problem and shared-state formulation\n\n### 2.1 Physical semantics and objective\n\n'+physics
    body+='### 2.2 A shared inventory, service and product state\n\n'+shared
    body+='### 2.3 What compact supports preserve\n\n'+compact+conditional
    body+='## 3. The complete GI-TBC method\n\n### 3.1 Physical strengthening\n\n'+ordered
    body+='### 3.2 Own startup and complete interval coverage\n\n'+startup
    body+='### 3.3 A separately paid proof enhancement\n\n'+enhancement
    body+='### 3.4 Numerical qualification, costs and termination\n\n'+policy+zero
    body+='## 4. Computational evidence\n\n### 4.1 Comparators and registered evidence\n\n'+comparator+protocol
    body+='### 4.2 Complete main-method panels\n\n'+mainpanel
    body+='### 4.3 Archived-source and within-input Seed evidence\n\n'+cohort+mechanisms
    body+='### 4.5 Representation strength and complete cost\n\n'+rep+diagnosis
    body+='## 5. Certified transportation decisions\n\n'+resources+'### 5.2 Quality between sampled objective weights\n\n'+weights+conclusion
    body=body.replace('§5.5','§4.3').replace('§3.1.1','§2.3').replace('§6','§4')
    body=re.sub(r'\n\\clearpage\n','\n',body)
    (PAPER/'paper_body.md').write_text(body.rstrip()+'\n',encoding='utf-8')
    # The moved narrative remains available without creating a second main paper.
    supplement=(PAPER/'supplement.md').read_text(encoding='utf-8-sig')
    navigation='''\n## S167.1 Navigation after manuscript consolidation\n\nThe main text is now organized by claims. Complete per-role AM and mechanism observations remain under “Seed 0 main mechanism comparison”, “Seed 1 limited mechanism repeat” and the retained detailed interpretation below. Three-Seed individual endpoints, joint-CERT costs and saved-target availability remain under “Round164 completed finite solver-Seed evidence” and “All pre-frozen feasible-target availability intervals”. All twelve B/C166 endpoints, qualification sizes and nested costs remain under “Round166 compact representation and certified decisions”. Appendix A.11 contains the conditional representation proof. The new offline diagnostics below are independent of complete-method performance records.\n\n'''
    moved=section('### 5.4 Limited preselected','### 5.5 Archived-source')+section('### 6.1 AM rule','### 6.3 Mechanism synthesis')
    moved=moved.replace('### 5.4 Limited preselected second Seed','### Earlier four-role second-Seed interpretation').replace('### 6.1 AM rule and experimental interpretation','### AM rule and experimental interpretation').replace('### 6.2 Conditional mechanism results','### Conditional mechanism results')
    moved=re.sub(r'\*\*Table (\d+)([.,])',r'**Retained table M\1\2',moved)
    moved=moved.replace('Table 11','retained table M11').replace('Table 12','retained table M12').replace('Table 13','retained table M13').replace('Table 14','retained table M14')
    supplement+=navigation+'## S167.2 Detailed AM, mechanism and earlier Seed interpretation\n\n'+moved
    (PAPER/'supplement.md').write_text(supplement.rstrip()+'\n',encoding='utf-8')
    sections=re.split(r'(?=^## )',body,flags=re.M)
    write(OUT/'manuscript_word_counts.json',dict(before_whitespace_words=len(old.split()),after_whitespace_words=len(body.split()),
        counting='len(text.split()), same full paper_body.md whitespace convention',sections=[dict(heading=s.splitlines()[0],words=len(s.split())) for s in sections],
        old_main_sections=7,new_main_sections=6,moved_sections=['5.4 detailed second Seed','6.1 detailed AM roles','6.2 conditional mechanism details'],
        single_current_manuscript=True))
    print('Reorganized body:',len(old.split()),'->',len(body.split()),'whitespace words.')
if __name__=='__main__':main()

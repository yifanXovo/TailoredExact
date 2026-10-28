"""Maintain the R135 manuscript lineage; assemble only from complete real results."""
from round137_common import *
import copy, inspect, re, shutil

OLD=ROOT/'results/unified_exact_round135'
LABELS=dict(S2='GI-TBC',P='P',PS='PS',S2R='GI-TBC-R',NO_AB='minus A/B',NO_CR='minus \\(C_R\\)',NO_CG='minus \\(C_G\\)',AM004='AM .04',AM016='AM .16')

def fmt(value):return 'n/a' if value is None else format(value,'.6g') if isinstance(value,(float,int)) and not isinstance(value,bool) else str(value)
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),*['| '+' | '.join(fmt(v) for v in r)+' |' for r in rows]])+'\n\n'

def polish_current_prose(text):
    text=re.sub(r'\b(All|all|the)(\d+)\b',r'\1 \2',text)
    text=re.sub(r'\b(tolerance|depth|width)(?=\d)',r'\1 ',text)
    text=re.sub(r'\b(are|is|at|from|versus|certifies)(?=\d)',r'\1 ',text)
    text=re.sub(r'\bSeed([01])\b',r'Seed \1',text)
    values=[
        ('rho=.5/1/2',r'\(\rho\in\{.5,1,2\}\)'),
        ('rho=.5/2',r'\(\rho\in\{.5,2\}\)'),
        ('rho=1',r'\(\rho=1\)'),('rho1',r'\(\rho=1\)'),
        ('rho.5',r'\(\rho=.5\)'),('rho2',r'\(\rho=2\)'),
        ('lambda=.15',r'\(\lambda=.15\)'),
        ('tau=.08',r'\(\tau_{\mathrm{AM}}=.08\)'),
        ('n15/20/35',r'\(n\in\{15,20,35\}\)'),
        ('n20/35',r'\(n\in\{20,35\}\)'),
        ('n15',r'\(n=15\)'),('n20',r'\(n=20\)'),('n35',r'\(n=35\)'),
        ('G/P_avg',r'\(G/P_{\mathrm{avg}}\)'),
        ('P_avg',r'\(P_{\mathrm{avg}}\)'),
        ('Tcert',r'\(T_{\mathrm{cert}}\)')
    ]
    for raw,value in values:
        text=re.sub(r'(?<![\w\\-])'+re.escape(raw)+r'(?!\w|\.\d)',lambda m,v=value:v,text)
    for raw,value in [('rho',r'\(\rho\)'),('tau',r'\(\tau_{\mathrm{AM}}\)'),('Omega',r'\(\Omega\)'),('n',r'\(n\)')]:
        text=text.replace('| '+raw+' |','| '+value+' |')
    text=re.sub(r'(?<=[A-Za-z]),(?=\d)',', ',text)
    text=re.sub(r' /(?=\d+ (?:methods|observations))',' / ',text)
    return text


def nest_preserved_markdown(text,levels=2):
    result=[];fence=None
    for line in text.splitlines():
        found=re.match(r'^\s*(\x60{3,}|~{3,})',line)
        if found:
            mark=found.group(1)
            if fence is None:fence=(mark[0],len(mark))
            elif mark[0]==fence[0] and len(mark)>=fence[1]:fence=None
            result.append(line);continue
        heading=re.match(r'^(#{1,6}) (.*)$',line) if fence is None else None
        result.append('#'*min(6,len(heading.group(1))+levels)+' '+heading.group(2) if heading else line)
    return '\n'.join(result)+'\n'


def prepare():
    assert not (OUT/'method_and_model_source.md').exists()
    body=(OLD/'paper_body.md').read_text(encoding='utf-8-sig')
    prefix=body[:body.index('## 4. Computational design')]
    prefix=prefix.replace(body.splitlines()[0],'# GI-TBC: a Gini-interval tailored branch-and-cut algorithm for equitable bicycle redistribution')
    prefix=prefix.replace('the S2 algorithm','GI-TBC').replace('implemented as S2','historically called S2, configuration ms2')
    prefix=prefix.replace('Sensitivity in Section 5.4 changes \\(\\lambda\\) within a fixed physical instance.',
        'The breadth panel retains this convention; the resource panel fixes \\(\\rho=1\\), and the weight study varies \\(\\rho\\) within fixed physical configurations.')
    heading='## 3. Shared inventory states and GI-TBC'
    assert heading in prefix
    theory=r'''For positive total shortage \(s=\sum_iD_i-\sum_ib_i>0\), positive weights and \(\lambda>0\) (equivalently \(\rho>0\)), let \(a=\min_i\omega_i/D_i>0\). Nonnegative loaded return yields

\[
P\ge a\sum_i|D_i-Y_i|\ge a\left|\sum_iD_i-\sum_iY_i\right|\ge as,
\qquad F\ge\lambda as=\rho as/\Omega>0.
\]

We use this established stock-shortage construction to guarantee positive objectives in the resource study, without filtering on observed difficulty. It does not guarantee a binding route horizon. With all other physical and objective data fixed, \(T_1\le T_2\) gives \(X(T_1)\subseteq X(T_2)\) and \(F^*(T_2)\le F^*(T_1)\). Finite-budget primal/dual endpoints and runtimes need not be monotone.

'''
    prefix=prefix.replace(heading,theory+heading)
    (OUT/'method_and_model_source.md').write_text(prefix,encoding='utf-8')
    for name in ['model_and_algorithm_appendices.md','references.bib']:
        shutil.copyfile(OLD/name,OUT/name)
    write(OUT/'document_lineage.json',dict(UTC=utc(),base=BASE,
        maintained_R135_sources={n:sha(OLD/n) for n in ['paper_body.md','model_and_algorithm_appendices.md','supplement.md','references.bib']},
        complete_appendix_derivations_retained=True,method_name='GI-TBC - Gini-interval tailored branch-and-cut',
        marker_successful_invocations=1,results_not_yet_assembled=True))
    references()
    print('Maintained method/model source and complete appendices/bibliography prepared; no PDF export')

def references():
    """Update only current names, premises, source pointers and study parameters."""
    path=OUT/'method_and_model_source.md';body=path.read_text(encoding='utf-8')
    body=body.replace('The state-penalty comparison in Section 6 applies Jensen\'s inequality and an elementary projection construction;',
        'The preserved historical state-penalty comparison in Supplement S6 applies Jensen\'s inequality and an elementary projection construction;')
    body=body.replace(r'integer target \(D_i>0\)',r'positive target \(D_i>0\)')
    target_note='The computational text format stores integer targets. All present test targets also satisfy '+r'\(D_i\le C_i\)'+', a data convention rather than an additional physical constraint; the inventory capacity bounds apply to '+r'\(b_i,Y_i\)'+'.'
    if target_note not in body:
        body=body.replace('The depot enters neither target deviation nor dispersion.',
            'The depot enters neither target deviation nor dispersion.\n\n'+target_note)
    body=body.replace('Third, the computational study measures complete-method cost against cold compact and independently paid-start compact controls. Historical breadth and final implementation confirmation retain their own versions and denominators. The study identifies substantial certification and runtime advantages, paid-start reversals and a positive-objective size boundary. A within-instance weight experiment relates the equity-target trade-off to actual vehicle operations. A bounded formulation study explains why retaining more state information can improve an LP without guaranteeing a faster complete algorithm.',
        'Third, we evaluate complete-method cost against independent cold compact and fully paid-start compact controls. A predeclared multi-source breadth panel, shortage-guaranteed positive-objective resource pairs, and within-configuration effective-weight contrasts separate the scientific questions. AM thresholds and four conditional mechanism controls are accompanied by a limited preselected second Gurobi Seed. We report certificates and two-sided endpoints, including paid-start reversals, opposed endpoint trade-offs and unresolved cases; historical evidence retains its own versions and denominators. These comparisons distinguish mathematical strengthening, root behavior and complete-algorithm cost.')
    body=body.replace('For positive total shortage \\(s=\\sum_iD_i-\\sum_ib_i>0\\) and positive weights, let',
        'For positive total shortage \\(s=\\sum_iD_i-\\sum_ib_i>0\\), positive weights and \\(\\lambda>0\\) (equivalently \\(\\rho>0\\)), let')
    start=body.index('## 3. Shared inventory states and GI-TBC')
    body=body[:start]+re.sub(r'\bS2\b','GI-TBC',body[start:])
    body=body.replace('Algorithm 1  GI-TBC / GI-TBC','Algorithm 1  GI-TBC')
    path.write_text(body,encoding='utf-8')
    path=OUT/'model_and_algorithm_appendices.md';appendix=path.read_text(encoding='utf-8-sig')
    appendix=appendix.replace(r'target inventory \(D_i\) is a positive integer no larger than \(C_i\).',
        r'Target inventory satisfies \(D_i>0\). The computational text format stores integer targets, and the present test targets additionally satisfy \(D_i\le C_i\); this describes the data rather than adding a target-capacity constraint to physical feasibility.')
    heading='## A.6 Cutoff and coverage proof'
    if '\\clearpage\n\n'+heading not in appendix:
        appendix=appendix.replace(heading,'\\clearpage\n\n'+heading)
    appendix=appendix.replace('S2 uses uniform pair support','GI-TBC uses uniform pair support').replace('The S2 termination rule','The GI-TBC termination rule')
    appendix=appendix.replace('Current S2 visits vehicles','GI-TBC visits vehicles')
    appendix=appendix.replace('**Current frozen method.** S2/MS2 uses',
        '**Current frozen method.** GI-TBC (historical S2, configuration ms2) uses')
    appendix=appendix.replace('S2R is a diagnostic deletion control, not a second proposed method.',
        'GI-TBC-R (implementation s2-root, historical S2R) is the diagnostic root-only control.')
    appendix=appendix.replace('P, PS and S2 use the same predicate. P obtains no H, while PS and S2 pay their complete own startup.',
        'P, PS and GI-TBC use the same predicate. P obtains no H, while PS and GI-TBC pay their complete own startup.')
    appendix=appendix.replace('The R134 reference identities and the R135 default-off AP recompilation are distinguished in B.1;',
        'The current GI-TBC identity and the separately pinned historical R134/R135 studies are distinguished in B.1;')
    appendix=appendix.replace(r'the baseline panel uses \(\lambda=.15\), with within-instance sensitivity at \(.075,.30\), positive weights and \(t_p=t_d=60\).',
        r'the current breadth panel uses \(\lambda=.15\), the resource panel fixes \(\rho=1\), and the within-configuration weight study uses \(\rho\in\{.5,1,2\}\), with \(\lambda=\rho/\Omega\), positive weights and \(t_p=t_d=60\).')
    appendix=appendix.replace('This supplement defines the controller','This appendix defines the controller').replace('adopted S2/MS2 method','adopted GI-TBC method (historical S2, configuration ms2)').replace('The current S2 row policy','The current GI-TBC row policy')
    a=appendix.index('## B.1 Active entry and parameters');b=appendix.index('## B.2',a);section=appendix[a:b]
    section=section.replace('The current S2 command','The current GI-TBC command')
    a1=section.find('The accepted S2 reference')
    if a1<0:a1=section.index('The current GI-TBC source/PE')
    b1=section.index('~~~text',a1)
    pin='https://github.com/yifanXovo/TailoredExact/blob/25800aa6b51bf7607b51e5df14a10a5ca4571889/results/unified_exact_round135/'
    replacement=('The current GI-TBC source/PE and policy are fixed in [candidate_manifest.json](candidate_manifest.json); '
        'all 120 actual method vectors, inputs, physical horizons, weights, Seeds and caps are in [matrix_frozen.json](matrix_frozen.json), '
        'with the prospectively registered sharing and order in [experiment_plan.json](experiment_plan.json). '
        'The default vector below uses ms2, tau=.08 and AP off. The three AM values are .04/.08/.16; the explicit '
        '`--round137-am-threshold` overrides the actual first-class field after presets. The four research controls are '
        '`--round127-mode s2-root`, `--round137-delete-ab`, `--round137-delete-cr`, and `--round137-delete-cg`; '
        'each changes only the declared comparison. Actual threshold/deletion readback is checked before qualification closes. '
        'The accepted inclusive root is the post-R130 implementation, not the old MD workflow. P and PS use their own complete '
        'vectors in the matrix rather than an abbreviated derivation from the GI-TBC vector.\n\n'
        'Historical R135 is separately pinned: its [candidate manifest]('+pin+'candidate_manifest.json), '
        '[first-stage commands]('+pin+'C_matrix_frozen.json) and [conditional-stage commands]('+pin+'D_matrix_frozen.json) '
        'compare S2/AP at lambda=.15. Those observations remain historical; AP is not enabled in the current stage. '
        'R134 confirmation and weight observations likewise retain their original identities in the preserved supplement.\n\n'
        'INPUT, OUT, physical T, cap B, B_MINUS_6 and SEED take their registered values. H seed 20260626 and native settings '
        'remain fixed. The zero-stop flag does not assert return before the native lifecycle: an own zero U can produce '
        'the degenerate [0,0] root, and the independent proof is finalized after resource release and complete physical '
        'verification. The supervisor starts the production clock before admission and seals required output; native '
        'Runtime alone is not T_cert.\n\n')
    section=section[:a1]+replacement+section[b1:]
    appendix=appendix[:a]+section+appendix[b:];path.write_text(appendix,encoding='utf-8')
    lineage=read(OUT/'document_lineage.json');lineage.pop('exact_appendices_retained',None)
    lineage.update(complete_appendix_derivations_retained=True,current_name_source_links_and_parameters_updated=True,
        derivative_appendix_SHA=sha(path),method_source_SHA=sha(OUT/'method_and_model_source.md'))
    write(OUT/'document_lineage.json',lineage)
    print('Current paper names, positive-weight premise and pinned historical references updated; no PDF export')

def assemble():
    summary=read(OUT/'reports/summary.json');assert summary['completed']==120 and not summary['missing']
    assert not budget()['unclosed']
    arms=read(OUT/'reports/arms.json');pairs=read(OUT/'reports/pairs.json');ops=read(OUT/'reports/operations.json')
    by={r['position']:r for r in arms}
    body=(OUT/'method_and_model_source.md').read_text(encoding='utf-8')
    detail='## Current detailed panel tables\n\nComplete panel observations accompany the compact question-led main text. Shared defaults retain their actual position identities.\n\n'
    main_table_number=0
    def main_caption(caption):
        nonlocal main_table_number
        main_table_number+=1
        return f'**Table {main_table_number}. {caption}**\n\n'
    def main_table(headers,rows):
        captions={
            ('Study','Configurations / observations'):'Registered studies, observations and shared defaults.',
            ('Panel','GI-TBC'):'Qualified certificates in the main Seed0 panels.',
            ('Panel','Other'):'Certificate-time comparisons conditioned on both methods certifying.',
            ('Base / source','n'):'Input-based positive-objective resource design.',
            ('Base','GI-TBC L(T1)'):'Strict resource-value improvements from separated qualified endpoints.',
            ('Physical configuration','rho'):'Within-configuration weights; C denotes an own qualified certificate.',
            ('Method','Selected Seed0 certificates /4'):'Certificates in the four preselected second-Seed configurations.',
            ('Role','Full'):'Observed Seed0 initial LP optima for the conditional mechanism controls.',
            ('K-15-S variant','Canonical generation (s)'):'Conditional Seed0 construction cost and returned solver effort on K-15-S.',
            ('K-35-U variant','Own feasible U'):'Opposed Seed0 open endpoints in the K-35-U mechanism panel.',
            ('Mechanism','Mathematical role'):'Mechanisms, mathematical roles, supporting evidence and boundaries.'}
        return main_caption(captions[tuple(headers[:2])])+table(headers,rows)
    def counts(stage,method):return sum(r['stage']==stage and r['method']==method and r['certificate'] and r['performance_eligible'] for r in arms)
    abstract=('Static bicycle redistribution couples integer station stocks with routes, prefix loads and handling time. '
        'We develop GI-TBC (Gini-interval tailored branch-and-cut), sharing finite inventory states between service and objective information, retaining valid supply/support inequalities and complete objective-interval coverage. '
        'The formulation preserves empty departure, loaded return and unique nonzero one-way service; we establish implicit service integrality and the physical embedding and termination conditions. '
        f'In a prospectively registered twelve-input Seed0 breadth panel, GI-TBC obtains {counts("B1","S2")}/12 qualified certificates, versus {counts("B1","P")}/12 cold compact and {counts("B1","PS")}/12 independently paid-start compact. '
        'A separately designed four-base/eight-configuration positive-objective resource panel, within-configuration weights, three AM thresholds, four mechanism contrasts and a limited second Seed distinguish complete-method performance from mathematical strengthening. '
        'All adverse and open outcomes are retained. Earlier multi-source validation and fixed-denominator objective-gap evidence remain separately identified. The evidence supports a finite stage conclusion, while positive-objective scale and conditional mechanism effects delimit generalization.')
    a=body.index('## Abstract');b=body.index('## 1. Introduction')
    body=body[:a]+'## Abstract\n\n'+abstract+'\n\n'+body[b:]
    body+='''## 4. Computational design

The main comparisons use the same physical problem and original objective. P is the independent cold compact model; PS pays its complete own H and maps only its own fleet into the original compact model; GI-TBC pays its complete own H, model construction, verification, interval search and proof/output. No solution, bound, tree or Start crosses methods, Seeds, objective weights or physical configurations. Gurobi 13.0.2 uses one thread and fixed processor affinity on an Intel i7-12700KF Windows host. H seed 20260626 is distinct from Gurobi Seed0/1. Same Seed does not mean different models follow the same random trajectory.

The fixed-source protocol was committed before once-only generation. Six known roles and six new draws form a twelve-input breadth panel (four each at n15/20/35); CITI, CABI and Divvy supply archived station geometry/capacity. Ten new draws in total include four additional shortage bases at n20/35, each paired at two transparently designed route horizons. Targets, initial stock, weights and depot are synthetic or transformed; this is not observed demand, a new source, or independent population sampling. Every selected source row and serialized input is disclosed.

Breadth retains lambda=.15. Resource pairs fix rho=1 and alter only T; the two extra weight levels rho=.5/2 reuse the matching rho1 baseline at two preselected physical configurations. AM and mechanism defaults share only exactly matching input/T/weight/Seed/cap/configuration runs. Main results use Seed0; four preselected full-method triplets and small overlapping AM/mechanism blocks use Seed1. They are finite repeated observations, not independent new inputs or an estimated runtime distribution.

For each new resource base, let \\(d_{\\max}\\) be its maximum serialized station-to-depot distance and \\(M\\) its vehicle count. Before optimization, the route horizons were fixed by

\\[
\\begin{aligned}
T_{\\rm base}&=2d_{\\max}/1.5+120\\sum_{i\\in N}\\max(b_i-D_i,0)/M,\\\\
T_1&=300\\left\\lceil\\frac{\\max(1800,.75T_{\\rm base})}{300}\\right\\rceil,\\\\
T_2&=300\\left\\lceil\\frac{1.5T_1}{300}\\right\\rceil.
\\end{aligned}
\\]

This input-based rule uses geometry, initial stock, targets and fleet size; it supplies neither a binding-horizon guarantee nor an outcome-dependent difficulty filter. The weight study preselects R-B20-S-T1 and R-X35-S-T2. Within each T pair, every datum except T is identical.

Caps are 600/1200/2400 s by size; every open certificate time remains null. Actual production, postverification and total clocks are retained separately. Native proof qualification and physical original-objective endpoints follow the accepted R134/R135 policy. Rejected native sources cannot support a bound. A current run can still qualify its own independently finalized exact-zero certificate under that policy; this basis and any rejected source are reported separately. Both-certified time differences are substantive when at least max(10s,10% of the faster time); numerical values and the conditioned intersection denominator accompany the classification.

'''
    body+=main_table(['Study','Configurations / observations','Purpose'],[
        ['Breadth','12 physical inputs /36 methods','Sources, stock regimes and scales'],
        ['Positive-resource pairs','4 bases,8 physical configurations /24 methods','rho1, guaranteed positive objective'],
        ['Weights','2 physical configurations,2 extra rho levels /12 methods','Relative method dependence on objective weight'],
        ['AM','4 roles,2 extra thresholds /8 methods','Observed gates/actions and complete cost'],
        ['Mechanisms','4 roles,4 contrasts /16 methods','Conditional formulation/control effects'],
        ['Second Seed','12 main+4 AM+8 mechanism methods','Preselected limited repeat check']])
    body+='## 5. Complete-method, resource and weight results\n\n'
    body+='### 5.1 Current main panel and historical context\n\n'
    body+=main_table(['Panel','GI-TBC','P','PS'],[['Breadth' if stage=='B1' else 'Resource pairs',f'{counts(stage,"S2")}/{12 if stage=="B1" else 8}',f'{counts(stage,"P")}/{12 if stage=="B1" else 8}',f'{counts(stage,"PS")}/{12 if stage=="B1" else 8}'] for stage in ['B1','B2']])
    body+='Certificates in this table require formal performance eligibility. Historical S2 retains its actual source and policy: R132 obtains 17/24 versus P 9/24 and PS 4/12; R134 final confirmation obtains 12/14 versus P 9/14 and PS 2/4. These are separate panels and repeated observations, and are not pooled with the current denominators. R132 also retains its disclosed source-reduced own-zero observation outside formal timing counts.\n\n'
    runtime_rows=[]
    for stage in ['B1','B2']:
        for other in ['P','PS']:
            both=[p for p in pairs if p['comparison_kind']==stage and p['left']=='S2' and p['right']==other and p['class']=='BOTH_CERTIFIED']
            stats=summary['stages'][stage]['comparisons'][f'S2/{other}']
            runtime_rows.append(['Breadth' if stage=='B1' else 'Resource pairs',other,len(both),
                f'{sum(p.get("material") is True and p["direction"]=="Win" for p in both)} / {sum(p.get("material") is True and p["direction"]=="Lose" for p in both)}',
                stats['both_certified_geomean']])
    body+=main_table(['Panel','Other','Both certified','GI-TBC W / L','Geo Other / GI-TBC'],runtime_rows)
    body+='Time ratios and substantive time wins/losses in this table condition on both methods qualifying a certificate; their intersection sizes are shown explicitly. A ratio above 1 means a lower GI-TBC certificate time on this conditioned subset. An open cap supplies no certificate time and enters neither the ratio nor these time-win counts. Certificate-only differences and open endpoints remain in the complete panel.\n\n'
    breadth={(r['role'],r['method']):r for r in arms if r['stage']=='B1'}
    breadth_roles={role for role,method in breadth}
    assert all(breadth[role,'PS']['H_complete'] and breadth[role,'S2']['H_complete'] and
        breadth[role,'PS']['H_semantic_SHA']==breadth[role,'S2']['H_semantic_SHA'] and
        breadth[role,'PS']['H_fleet_SHA']==breadth[role,'S2']['H_fleet_SHA'] for role in breadth_roles)
    assert {role for role in breadth_roles if not breadth[role,'S2']['certificate']}=={'K-20-S','K-35-U','N-B35-S'}
    def bv(role,method,key):return fmt(breadth[role,method][key])
    body+=(f'The new positive-objective certificate cases include N-B15-B, N-X15-S and N-C20-U. '
        f'On N-B15-B, GI-TBC takes {bv("N-B15-B","S2","T_cert")} s versus P {bv("N-B15-B","P","T_cert")} s and PS {bv("N-B15-B","PS","T_cert")} s. '
        f'On N-X15-S the corresponding times are {bv("N-X15-S","S2","T_cert")}/{bv("N-X15-S","P","T_cert")}/{bv("N-X15-S","PS","T_cert")} s. '
        f'GI-TBC certifies N-C20-U in {bv("N-C20-U","S2","T_cert")}s while P and PS remain open. These observations retain the independent cost of each complete method.\n\n')
    body+=(f'Paid startup and the subsequent method have distinct effects. On X-35-B, PS certifies in {bv("X-35-B","PS","T_cert")} s versus GI-TBC {bv("X-35-B","S2","T_cert")} s, a substantive PS reversal under the declared rule. '
        f'On N-X20-B, PS {bv("N-X20-B","PS","T_cert")} s and GI-TBC {bv("N-X20-B","S2","T_cert")}s differ by less than 10 s, so the nominal ordering is not substantive. '
        'All twelve breadth PS/GI-TBC pairs independently complete H with matching semantic and fleet hashes; the complete post-startup packages can still behave differently.\n\n')
    body+=(f'GI-TBC remains open on K-20-S, K-35-U and N-B35-S. K-35-U exposes an opposed-endpoint result: P has the lower U, '
        f'{bv("K-35-U","P","U")} versus GI-TBC {bv("K-35-U","S2","U")}, while GI-TBC has the higher L, '
        f'{bv("K-35-U","S2","L")} versus P {bv("K-35-U","P","L")}. '
        'No single endpoint-dominance or certificate-time claim follows. On N-B35-S, GI-TBC improves both endpoints over P and PS but still leaves a positive proof gap. These qualified limits accompany the certification gains.\n\n')
    detail+='## Breadth: complete two-sided endpoints\n\n'
    detail+=table(['Input','P: U / L','PS: U / L','GI-TBC: U / L'],[[role,*[f'{fmt(next(r for r in arms if r["role"]==role and r["stage"]=="B1" and r["method"]==m)["U"])} / {fmt(next(r for r in arms if r["role"]==role and r["stage"]=="B1" and r["method"]==m)["L"])}' for m in ['P','PS','S2']]] for role in dict.fromkeys(r['role'] for r in arms if r['stage']=='B1')])
    zero_p=breadth['N-X20-B','P']
    assert zero_p['source_rejected'] and zero_p['independent_proof'] and not zero_p['native_proof_qualified']
    assert zero_p['certificate'] and zero_p['performance_eligible'] and zero_p['U']==zero_p['L']==0
    body+=(f'N-X20-B cold P has a rejected native bound source and an own zero feasible objective. Its {fmt(zero_p["T_cert"])} s qualified certificate uses the separately finalized nonnegative full-domain floor, '
        'not the rejected native proof. The complete cost and rejection records remain. This current-policy independent-zero certificate does not retroactively change the separately preserved historical exclusion above.\n\n')
    body+='The complete paired interpretation, including substantive reversals and conditioned runtime statistics, is given in the stage decision and the full supplement. Smaller signed gap alone does not establish endpoint dominance: U and L are compared separately. No cap is substituted for a certificate time.\n\n'
    body+='### 5.2 Positive objectives and physical resource pairs\n\n'
    body+='All four serialized shortage bases have positive weights, a strictly positive analytic floor, and both local donor and receiver stations before movement. Relaxing T enlarges the feasible set; the observed feasible plans, qualified bounds and proof progress test how the methods use that resource, not a causal effect of n alone. The physical operation records distinguish travel, handling, returned stock, prefix peaks and route-duration utilization.\n\n'
    resource_inputs=[p for p in read(OUT/'input_manifest.json')['roles'] if p['module']=='B2']
    design=[]
    for base in dict.fromkeys(p['base_id'] for p in resource_inputs):
        pp=sorted([p for p in resource_inputs if p['base_id']==base],key=lambda p:p['T_seconds'])
        assert len(pp)==2 and pp[0]['input_sha256']==pp[1]['input_sha256']
        p=pp[0];design.append([f'{base} /{p["source"]}',p['V'],f'{pp[0]["T_seconds"]} /{pp[1]["T_seconds"]}',p['shortage'],p['Omega'],p['positive_objective_floor']])
    body+=main_table(['Base / source','n','T1 / T2 (s)','Shortage s','Omega','Floor lambda a s'],design)
    body+='The floor is a pre-solve guarantee at rho1, shared by the two physical horizons. It is not the reported solver L, and a larger T need not improve a finite-budget U or L monotonically.\n\n'
    resource_results={(r['role'],r['method']):r for r in arms if r['stage']=='B2'}
    rb1=resource_results['R-B20-S-T1','S2'];rb2=resource_results['R-B20-S-T2','S2']
    assert all(r['certificate'] and r['performance_eligible'] for r in [rb1,rb2])
    assert rb2['U']<rb1['L']-1e-7
    body+=(f'On R-B20-S, GI-TBC qualifies certificates at F={fmt(rb1["U"])} with T=3300 s and F={fmt(rb2["U"])} with T=5100 s. '
        f'The two qualified intervals establish a strict value improvement under the controlled resource change. '
        f'Certificate times are {fmt(rb1["T_cert"])}/{fmt(rb2["T_cert"])} s respectively. '
        'The lower proof cost on this pair is an observed result; feasible-set inclusion supplies no runtime ordering for other inputs.\n\n')
    rx={method:resource_results['R-X20-S-T1',method] for method in ['P','PS','S2']}
    assert rx['S2']['certificate'] and all(r['performance_eligible'] for r in rx.values())
    assert all(not rx[method]['certificate'] and abs(rx[method]['U']-rx['S2']['U'])<=1e-7 for method in ['P','PS'])
    body+=(f'R-X20-S-T1 isolates a proof-gap difference. All three verified feasible objectives coincide at {fmt(rx["S2"]["U"])}, '
        f'while GI-TBC forms its own qualified certificate in {fmt(rx["S2"]["T_cert"])} s. '
        f'P and PS retain L={fmt(rx["P"]["L"])}/{fmt(rx["PS"]["L"])}, respectively, and remain open under their own evidence. '
        'The complete-method comparison concerns closure of the dual gap on this witness; the conditional controls delimit attribution to individual mechanisms. No other method inherits the GI-TBC proof or certificate time.\n\n')
    rx2=resource_results['R-X20-S-T2','S2']
    assert rx2['certificate'] and rx2['performance_eligible'] and rx2['U']<rx['S2']['L']-1e-7
    body+=(f'On R-X20-S, the larger horizon reduces the certified objective from {fmt(rx["S2"]["U"])} to {fmt(rx2["U"])}, '
        f'while the GI-TBC certificate cost increases from {fmt(rx["S2"]["T_cert"])} to {fmt(rx2["T_cert"])} s. '
        'Together with R-B20-S, these two n20 pairs show the same resource-value direction and opposite observed proof-cost directions. '
        'They remain finite Seed0 observations; the input differences across bases prevent a pure source or scale attribution.\n\n')
    rb35a=resource_results['R-B35-S-T1','S2'];rb35b=resource_results['R-B35-S-T2','S2']
    assert all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in [rb35a,rb35b])
    assert rb35b['U']<rb35a['L']-1e-7
    body+=(f'Value improvement can also be demonstrated while both GI-TBC runs remain open. On R-B35-S, '
        f'the qualified T1 lower endpoint {fmt(rb35a["L"])} exceeds the verified T2 feasible upper endpoint {fmt(rb35b["U"])}. '
        f'The separated intervals [{fmt(rb35a["L"])},{fmt(rb35a["U"])}] and [{fmt(rb35b["L"])},{fmt(rb35b["U"])}] '
        'support a strict resource-value improvement under the stated numerical policy. Each optimum remains inside its own interval, and no certificate-time comparison is reported.\n\n')
    separations=[]
    for base in dict.fromkeys(p['base_id'] for p in resource_inputs):
        tight=resource_results[base+'-T1','S2']
        loose=min((resource_results[base+'-T2',method] for method in ['P','PS','S2'] if resource_results[base+'-T2',method]['performance_eligible']),key=lambda r:r['U'])
        assert tight['performance_eligible'] and loose['U']<tight['L']-1e-7
        separations.append((base,tight,loose))
    assert len(separations)==4
    body+='All four resource bases admit this type of strict endpoint separation: an eligible T2 feasible upper endpoint lies below the qualified GI-TBC T1 lower endpoint. This offline value comparison preserves every method\'s own certificate/open status and clocks; no bound or feasible plan is transferred into another production run. It establishes strict improvement for these four designed pairs without claiming that every increase in T must improve the optimum strictly.\n\n'
    body+=main_table(['Base','GI-TBC L(T1)','Feasible U(T2) / owner','L(T1) - U(T2)','Source status T1 / T2'],
        [[base,tight['L'],f'{fmt(loose["U"])} /{LABELS[loose["method"]]}',tight['L']-loose['U'],
          f'{"C" if tight["certificate"] else "open"} /{"C" if loose["certificate"] else "open"}']
         for base,tight,loose in separations])
    body+='The T2 column identifies the owner of the lowest verified feasible upper endpoint among the three completed methods. A cross-method separation concerns the common problem value and does not certify either open source run.\n\n'
    op_by_position={o['position']:o for o in ops}
    detail+='## Positive-resource GI-TBC operating points\n\n'
    detail+=table(['Configuration','G / P_avg / S','Returned units','Max duration / T','Status'],
        [[r['role'],f'{fmt(r["G"])} /{fmt(r["P_avg"])} /{fmt(r["S"])}',op_by_position[r['position']]['returns'],
          op_by_position[r['position']]['maximum_duration']/r['T'],
          'UEV' if not r['performance_eligible'] else 'C' if r['certificate'] else 'open']
         for r in arms if r['stage']=='B2' and r['method']=='S2'])
    body+='The supplement reports operations of each verified own incumbent, including open configurations. The components and S distinguish changes in dispersion, target deviation and the inventory denominator. Duration utilization describes the displayed routes; a near-unit ratio alone does not establish a binding optimum. Full per-vehicle travel/handling, pickups/drops/returns and prefix peaks are retained in the [operations data supplement](reports/operations.json).\n\n'
    resource_GI=[r for r in arms if r['stage']=='B2' and r['method']=='S2']
    for base in dict.fromkeys(p['base_id'] for p in resource_inputs):
        tight=resource_results[base+'-T1','S2'];loose=resource_results[base+'-T2','S2']
        assert tight['G']>loose['G']+1e-7 and tight['P_avg']>loose['P_avg']+1e-7
    utilizations=[op_by_position[r['position']]['maximum_duration']/r['T'] for r in resource_GI]
    assert min(utilizations)>.994
    rx35tight=resource_results['R-X35-S-T1','S2'];rx35loose=resource_results['R-X35-S-T2','S2']
    returns_tight=op_by_position[rx35tight['position']]['returns'];returns_loose=op_by_position[rx35loose['position']]['returns']
    assert rx35tight['S']>rx35loose['S']+1e-7 and returns_tight==1 and returns_loose==0
    body+=(f'Both G and P_avg decrease between the saved GI-TBC plans in every resource pair. The longest route uses at least {fmt(100*min(utilizations))}% of its horizon in each displayed plan. '
        'The separate strict endpoint separations establish resource-value relevance; near-full route use alone does not establish exact binding. '
        f'R-X35-S also illustrates why S must be distinguished from inventory mass: loaded returns fall from {fmt(returns_tight)} to {fmt(returns_loose)}, so total station inventory increases by one, '
        f'while S falls from {fmt(rx35tight["S"])} to {fmt(rx35loose["S"])}. '
        'The different target denominators make S depend on the allocation of units, not only their total. These are verified feasible-plan comparisons; the n35 optima remain unresolved.\n\n')
    n35_resource=[r for r in arms if r['stage']=='B2' and r['n']==35]
    assert len(n35_resource)==12 and all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in n35_resource)
    for role in dict.fromkeys(r['role'] for r in n35_resource):
        full=resource_results[role,'S2']
        assert all(full['U']<resource_results[role,method]['U']-1e-7 and full['L']>resource_results[role,method]['L']+1e-7 for method in ['P','PS'])
    rx35={method:resource_results['R-X35-S-T2',method] for method in ['P','PS','S2']}
    body+=(f'All three methods remain open on all four n35 resource configurations. GI-TBC has lower U and higher L than both controls at the registered complete caps, '
        f'but none of these endpoint improvements is a certificate-time gain. On R-X35-S-T2, GI-TBC reports U/L={fmt(rx35["S2"]["U"])}/{fmt(rx35["S2"]["L"])}, '
        f'versus PS {fmt(rx35["PS"]["U"])}/{fmt(rx35["PS"]["L"])} and P {fmt(rx35["P"]["U"])}/{fmt(rx35["P"]["L"])}. '
        f'The feasible-objective advantage over PS is only {fmt(rx35["PS"]["U"]-rx35["S2"]["U"])}; primal and dual differences remain visible separately. '
        'These persistent open outcomes delimit the positive-objective scale reached by this finite panel.\n\n')
    for role,better,worse in [('R-B35-S-T1','P','PS'),('R-B35-S-T2','PS','P'),('R-X20-S-T2','P','PS')]:
        first=resource_results[role,better];second=resource_results[role,worse]
        assert first['U']<second['U']-1e-7 and first['L']>second['L']+1e-7
    body+='Paid-start effects are conditional on the resource configuration. On R-B35-S-T1, cold P has lower U and higher L than PS; this two-endpoint direction reverses at T2. P also has both better endpoints on R-X20-S-T2. All of these compact runs remain open. These fixed-budget comparisons retain the complete cost of startup and do not establish an eventual proof-time ordering or a universal startup benefit.\n\n'
    body+='![Original-objective endpoints at the two physical horizons. Solid lines join feasible U circles; dashed lines join qualified L triangles. Filled U circles denote qualified certificates, and grey dotted lines show the pre-solve positive floor. Connecting lines describe finite-budget observations, not an exact optimal-value curve.](figures/resource_endpoints.png)\n\n'
    body+='\\clearpage\n\n### 5.3 Objective weights\n\n'
    weighted=[r for r in arms if r['stage']=='B3' or r['stage']=='B2' and r['role'] in ['R-B20-S-T1','R-X35-S-T2']]
    assert len(weighted)==18
    detail+='## Objective weights: all methods and decompositions\n\n'
    detail+=table(['Configuration','rho','Method','G / P_avg','U / L','Certificate'],[[r['physical_configuration_id'],r['rho'],LABELS[r['method']],f'{fmt(r["G"])} / {fmt(r["P_avg"])}',f'{fmt(r["U"])} / {fmt(r["L"])}','UEV' if not r['performance_eligible'] else 'C' if r['certificate'] else 'open'] for r in weighted])
    weight_groups={}
    for r in weighted:weight_groups.setdefault((r['physical_configuration_id'],r['rho']),{})[r['method']]=r
    assert len(weight_groups)==6 and all(set(rr)=={'P','PS','S2'} for rr in weight_groups.values())
    def endpoint_cell(r):return f'{fmt(r["U"])} /{fmt(r["L"])}'+(' (C)' if r['performance_eligible'] and r['certificate'] else ' (open)' if r['performance_eligible'] else ' (UEV)')
    body+=main_table(['Physical configuration','rho','P: U / L','PS: U / L','GI-TBC: U / L'],
        [[physical,rho,*[endpoint_cell(rr[m]) for m in ['P','PS','S2']]] for (physical,rho),rr in sorted(weight_groups.items())])
    wlow={m:next(r for r in weighted if r['role']=='R-B20-S-T1-rho0.5' and r['method']==m) for m in ['P','PS','S2']}
    assert all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in wlow.values())
    assert abs(wlow['PS']['U']-wlow['S2']['U'])<=1e-7 and wlow['S2']['L']>wlow['PS']['L']+1e-7
    body+=(f'Certification depends on the weight even within the preselected n20 physical configuration. GI-TBC certifies R-B20-S-T1 at rho1, '
        f'whereas all three methods remain open at rho.5. At rho.5, GI-TBC and PS have the same verified U={fmt(wlow["S2"]["U"])}, '
        f'but their qualified L values are{fmt(wlow["S2"]["L"])}/{fmt(wlow["PS"]["L"])}. '
        'This retains a finite-budget dual-progress advantage without a certificate-time claim at that weight.\n\n')
    whigh={m:next(r for r in weighted if r['role']=='R-B20-S-T1-rho2' and r['method']==m) for m in ['P','PS','S2']}
    assert all(r['performance_eligible'] for r in whigh.values()) and whigh['S2']['certificate']
    assert all(not whigh[m]['certificate'] and whigh[m]['T_cert'] is None for m in ['P','PS'])
    assert abs(whigh['PS']['U']-whigh['S2']['U'])<=1e-7
    body+=(f'At rho2, GI-TBC certifies F={fmt(whigh["S2"]["U"])} in {fmt(whigh["S2"]["T_cert"])} s, '
        f'while P and PS remain open. PS attains the same verified feasible objective but has L={fmt(whigh["PS"]["L"])} '
        f'instead of the GI-TBC lower endpoint {fmt(whigh["S2"]["L"])}. '
        'Thus the n20 complete-proof advantage is observed at two tested weights, and the third retains a dual-endpoint advantage without closure. Each method retains its own proof status.\n\n')
    w35low={m:next(r for r in weighted if r['role']=='R-X35-S-T2-rho0.5' and r['method']==m) for m in ['P','PS','S2']}
    assert all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in w35low.values())
    assert all(w35low['S2']['U']<w35low[m]['U']-1e-7 and w35low['S2']['L']>w35low[m]['L']+1e-7 for m in ['P','PS'])
    assert w35low['PS']['U']<w35low['P']['U']-1e-7 and w35low['P']['L']>w35low['PS']['L']+1e-7
    body+=(f'At the fixed n35 horizon T=6300 s, all three methods remain open at rho.5. GI-TBC reports '
        f'U/L={fmt(w35low["S2"]["U"])}/{fmt(w35low["S2"]["L"])}, with lower U and higher L than both controls. '
        'PS has the better feasible objective than cold P, while P has the higher qualified lower endpoint. '
        'This preserves an opposed-endpoint startup result alongside the finite GI-TBC endpoint advantages; no certificate-time ordering is assigned.\n\n')
    w35rows=[r for r in weighted if r['n']==35]
    assert len(w35rows)==9 and all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in w35rows)
    for role in dict.fromkeys(r['role'] for r in w35rows):
        rr={r['method']:r for r in w35rows if r['role']==role}
        assert all(rr['S2']['U']<rr[m]['U']-1e-7 and rr['S2']['L']>rr[m]['L']+1e-7 for m in ['P','PS'])
    w35high={m:next(r for r in w35rows if r['role']=='R-X35-S-T2-rho2' and r['method']==m) for m in ['P','PS','S2']}
    w35base={m:next(r for r in w35rows if r['role']=='R-X35-S-T2' and r['method']==m) for m in ['P','PS','S2']}
    body+=(f'The n35 configuration remains open for every method at all three tested weights. GI-TBC has lower U and higher L than both controls within each weight. '
        f'At rho2, its U/L={fmt(w35high["S2"]["U"])}/{fmt(w35high["S2"]["L"])} compares with PS '
        f'{fmt(w35high["PS"]["U"])}/{fmt(w35high["PS"]["L"])} and P {fmt(w35high["P"]["U"])}/{fmt(w35high["P"]["L"])}. '
        f'The feasible-objective advantage over PS is {fmt(w35high["PS"]["U"]-w35high["S2"]["U"])} at rho2, '
        f'compared with {fmt(w35base["PS"]["U"]-w35base["S2"]["U"])} at rho1. '
        'Thus the magnitude of the finite primal advantage varies with the weight, while the unresolved proof gap persists. These observations do not imply a monotone weight effect or complete-proof-time robustness.\n\n')
    w20_GI=[next(r for r in weighted if r['physical_configuration_id']=='R-B20-S-T1' and r['method']=='S2' and abs(r['rho']-rho)<1e-10) for rho in [.5,1,2]]
    assert all(w20_GI[i]['G']<w20_GI[i+1]['G'] and w20_GI[i]['P_avg']>w20_GI[i+1]['P_avg'] for i in [0,1])
    assert w35high['S2']['G']<w35base['S2']['G']-1e-7 and w35high['S2']['P_avg']<w35base['S2']['P_avg']-1e-7
    assert w35high['S2']['input_SHA']==w35base['S2']['input_SHA'] and w35high['S2']['T']==w35base['S2']['T']
    body+=(f'The saved n20 GI-TBC operating points show G increasing and P_avg decreasing across rho=.5/1/2; the low-weight run remains open. '
        f'The n35 points expose a stronger finite-search limitation: at the same physical input and T, the rho2 saved plan has G/P_avg='
        f'{fmt(w35high["S2"]["G"])}/{fmt(w35high["S2"]["P_avg"])}, both below the rho1 saved plan values '
        f'{fmt(w35base["S2"]["G"])}/{fmt(w35base["S2"]["P_avg"])}. '
        'Thus the rho1 saved incumbent is dominated in the two objective components by another saved feasible plan. '
        'This is an offline comparison of completed observations that exposes a primal deficit in the retained rho1 incumbent. Each run keeps its own U/L and proof status; no plan, Start or bound was transferred during production. '
        'It provides no exact optimal weight frontier and does not establish monotonic search behavior.\n\n')
    body+='Cross-weight values refer to different objectives, while method comparisons are made within each weight. Uncertified weights report feasible operating points and qualified bounds; they do not define an exact optimal trade-off curve.\n\n'
    body+='\\clearpage\n\n### 5.4 Limited preselected second Seed\n\n'
    main_order={'P':0,'PS':1,'S2':2}
    repeat=sorted([r for r in arms if r['stage']=='D2-main'],key=lambda r:(r['n'],r['role'],main_order[r['method']]))
    assert len(repeat)==12 and len({r['role'] for r in repeat})==4
    detail+='## Limited Seed1: complete main triplets\n\n'
    detail+=table(['Role','Method','Status','Own Tcert (s)','U / L','Production (s)'],
        [[r['role'],LABELS[r['method']],'UEV' if not r['performance_eligible'] else 'C' if r['certificate'] else 'open',r['T_cert'],
          f'{fmt(r["U"])} /{fmt(r["L"])}',r['T_produce']] for r in repeat])
    repeat_roles={r['role'] for r in repeat}
    def repeat_cert(seed,method):return sum(r['certificate'] and r['performance_eligible'] for r in arms if r['role'] in repeat_roles and r['seed']==seed and r['method']==method and r['stage'] in ['B1','B2','D2-main'])
    body+=main_table(['Method','Selected Seed0 certificates /4','Seed1 certificates /4'],
        [[LABELS[m],repeat_cert(0,m),repeat_cert(1,m)] for m in ['P','PS','S2']])
    body+='These four configurations were selected before the current results. Their Seed1 observations remain distinct from the full main Seed0 panel and do not replace an unfavorable first observation. Same Seed is a common setting for different models, not a shared random trajectory, and two Seeds do not estimate a runtime distribution. Complete H remains part of the defined algorithm configuration with its own fixed seed; the AM/mechanism repeat blocks use the corresponding actual Seed1 baselines.\n\n'
    k15_repeat={(r['seed'],r['method']):r for r in arms if r['role']=='K-15-S' and r['method'] in ['P','PS','S2'] and r['stage'] in ['B1','D2-main']}
    assert len(k15_repeat)==6 and all(r['performance_eligible'] for r in k15_repeat.values())
    assert all(r['certificate']==(method=='S2') for (seed,method),r in k15_repeat.items())
    assert max(r['U'] for r in k15_repeat.values())-min(r['U'] for r in k15_repeat.values())<1e-7
    t0=k15_repeat[0,'S2']['T_cert'];t1=k15_repeat[1,'S2']['T_cert']
    assert abs(t0-t1)<max(10,.1*min(t0,t1))
    assert k15_repeat[0,'P']['L']>k15_repeat[0,'PS']['L']+1e-7 and k15_repeat[1,'PS']['L']>k15_repeat[1,'P']['L']+1e-7
    body+=(f'K-15-S retains the same certificate pattern in the limited repeat: only GI-TBC certifies, in {fmt(t0)} / {fmt(t1)} s at Seed0 / Seed1, '
        'a nonmaterial complete-cost difference under the declared rule. All six runs attain the same verified feasible objective, but each compact run retains its own open proof status. '
        f'Finite dual progress is less stable in direction: Seed0 cold P / paid-start PS end at L={fmt(k15_repeat[0,"P"]["L"])}/{fmt(k15_repeat[0,"PS"]["L"])}, '
        f'whereas Seed1 ends at {fmt(k15_repeat[1,"P"]["L"])}/{fmt(k15_repeat[1,"PS"]["L"])}. '
        'Thus the compact dual ordering reverses even while feasible objectives and this role-specific certificate pattern agree. This finite observation does not establish a distribution or an eventual proof-time ranking.\n\n')
    uc_repeat={(r['seed'],r['method']):r for r in arms if r['role']=='UC-B20-B' and r['method'] in ['P','PS','S2'] and r['stage'] in ['B1','D2-main']}
    assert len(uc_repeat)==6 and all(r['performance_eligible'] and r['certificate'] for r in uc_repeat.values())
    assert max(r['U'] for r in uc_repeat.values())-min(r['U'] for r in uc_repeat.values())<1e-7
    for method in ['P','S2']:
        a=uc_repeat[0,method]['T_cert'];b=uc_repeat[1,method]['T_cert']
        assert abs(a-b)<max(10,.1*min(a,b))
    a=uc_repeat[0,'PS']['T_cert'];b=uc_repeat[1,'PS']['T_cert']
    assert abs(a-b)>=max(10,.1*min(a,b))
    body+=(f'UC-B20-B also retains its certificate pattern, with all three methods certifying at both Seeds. GI-TBC takes '
        f'{fmt(uc_repeat[0,"S2"]["T_cert"])}/{fmt(uc_repeat[1,"S2"]["T_cert"])} s and cold P '
        f'{fmt(uc_repeat[0,"P"]["T_cert"])}/{fmt(uc_repeat[1,"P"]["T_cert"])} s, respectively; their cross-Seed differences are below the substantive rule. '
        f'Paid-start PS changes from {fmt(a)} to {fmt(b)} s. This descriptive change exceeds that rule while the GI-TBC advantage over both compact controls persists in this role. '
        'Complete own H and matched within-Seed trace/fleet identities are retained; unchanged certification status does not make every complete runtime stable. Two Seeds still supply finite checks rather than a distribution or a best-Seed selection.\n\n')
    rb_repeat={(r['seed'],r['method']):r for r in arms if r['role']=='R-B20-S-T1' and r['method'] in ['P','PS','S2'] and r['stage'] in ['B2','D2-main']}
    assert len(rb_repeat)==6 and all(r['performance_eligible'] and r['certificate']==(method=='S2') for (seed,method),r in rb_repeat.items())
    a=rb_repeat[0,'S2']['T_cert'];b=rb_repeat[1,'S2']['T_cert']
    assert abs(a-b)>=max(10,.1*min(a,b))
    assert abs(rb_repeat[1,'PS']['U']-rb_repeat[1,'S2']['U'])<=1e-7 and rb_repeat[1,'PS']['T_cert'] is None
    assert rb_repeat[1,'P']['U']<rb_repeat[0,'P']['U']-1e-7 and rb_repeat[1,'P']['L']<rb_repeat[0,'P']['L']-1e-7
    body+=(f'R-B20-S-T1 preserves own certification only for GI-TBC, whose certificate cost changes from {fmt(a)} to {fmt(b)} s, a substantive descriptive shift under the stated rule. '
        f'At Seed1, paid-start PS reaches the same feasible U={fmt(rb_repeat[1,"S2"]["U"])}, but retains its own lower endpoint {fmt(rb_repeat[1,"PS"]["L"])} and remains open. '
        f'Cold P improves its feasible objective from {fmt(rb_repeat[0,"P"]["U"])} to {fmt(rb_repeat[1,"P"]["U"])} while its lower bound falls from '
        f'{fmt(rb_repeat[0,"P"]["L"])} to {fmt(rb_repeat[1,"P"]["L"])}. The complete-method certificate pattern therefore coexists with material time variation and opposed cross-Seed endpoint changes. '
        'These are finite matched observations; the Seed0 panel remains the primary evidence, and no certificate is transferred to a compact run.\n\n')
    k35_repeat={(r['seed'],r['method']):r for r in arms if r['role']=='K-35-U' and r['method'] in ['P','PS','S2'] and r['stage'] in ['B1','D2-main']}
    assert len(k35_repeat)==6 and all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in k35_repeat.values())
    assert k35_repeat[0,'P']['U']<k35_repeat[0,'PS']['U']-1e-7 and k35_repeat[0,'P']['L']>k35_repeat[0,'PS']['L']+1e-7
    assert k35_repeat[1,'PS']['U']<k35_repeat[1,'P']['U']-1e-7 and k35_repeat[1,'PS']['L']>k35_repeat[1,'P']['L']+1e-7
    assert all(k35_repeat[1,'S2']['U']<k35_repeat[1,m]['U']-1e-7 and k35_repeat[1,'S2']['L']>k35_repeat[1,m]['L']+1e-7 for m in ['P','PS'])
    assert k35_repeat[1,'S2']['U']<k35_repeat[0,'S2']['U']-1e-7 and k35_repeat[1,'S2']['L']<k35_repeat[0,'S2']['L']-1e-7
    body+=(f'K-35-U remains open for every method at both Seeds. At Seed1, GI-TBC has U/L={fmt(k35_repeat[1,"S2"]["U"])}/{fmt(k35_repeat[1,"S2"]["L"])}, '
        f'compared with P {fmt(k35_repeat[1,"P"]["U"])}/{fmt(k35_repeat[1,"P"]["L"])} and PS {fmt(k35_repeat[1,"PS"]["U"])}/{fmt(k35_repeat[1,"PS"]["L"])}. '
        'GI-TBC improves both endpoints over both controls within Seed1, whereas Seed0 retains the better P feasible objective and stronger GI-TBC lower bound. '
        f'GI-TBC also improves its own U from {fmt(k35_repeat[0,"S2"]["U"])} to {fmt(k35_repeat[1,"S2"]["U"])} across Seeds while L falls from '
        f'{fmt(k35_repeat[0,"S2"]["L"])} to {fmt(k35_repeat[1,"S2"]["L"])}. A smaller signed gap therefore does not make both of its own endpoints better. '
        'The compact comparison reverses in both endpoints: P is better than PS at Seed0, while PS is better than P at Seed1. No open certificate time is supplied, and the adverse Seed0 observations are retained.\n\n')
    assert all(repeat_cert(seed,m)==({'P':1,'PS':1,'S2':3}[m]) for seed in [0,1] for m in ['P','PS','S2'])
    body+='## 6. Mechanisms, AM and stage interpretation\n\n'
    note=(OUT/'mathematical_analysis.md').read_text(encoding='utf-8')
    a=note.index('## AM rule and experimental interpretation');b=note.index('## Scope of prior evidence')
    body+=note[a:b].replace('## AM rule and experimental interpretation','### 6.1 AM rule and experimental interpretation').replace('The prior R47/R52 decision supports the default .08','The preserved AM construction and threshold-validation evidence in the supplement supports the default .08').replace('The new explicit research CLI sets the first-class `split_threshold` after presets. The historical `round47_c6_adaptive_mass_tau` field is not substituted for that control.', 'The experimental threshold is applied to the actual controller parameter after presets.')
    am_keys={(r['role'],r['seed']) for r in arms if r['stage'] in ['C1','D2-AM']}
    am_rows=[r for r in arms if (r['role'],r['seed']) in am_keys and r['method'] in ['S2','AM004','AM016']]
    role_order={'K-15-S':0,'UC-B20-B':1,'K-20-S':2,'K-35-U':3}
    am_rows.sort(key=lambda r:(r['seed'],role_order[r['role']],r['AM_threshold']))
    def max_score(r):
        decisions=read(OUT/f'reports/AM/position_{r["position"]:03}.json')
        values=[float(x['S_AM']) for x in decisions if x.get('S_AM') is not None and math.isfinite(float(x['S_AM'])) and x['finite_score_gate']]
        return max(values) if values else None
    body+='The Seed0 AM comparison contains eight additional positions and twelve views after sharing the four matching default runs. The Seed1 AM block contains four additional positions and six views, using its two independently measured Seed1 defaults.\n\n'
    for seed,heading in [(0,'Seed0 main AM comparison'),(1,'Seed1 limited AM repeat')]:
        selected=[r for r in am_rows if r['seed']==seed]
        assert len(selected)==(12 if seed==0 else 6)
        panel='**'+heading+'**\n\n'+table(['Role','tau','Max gate score','Actions','Production (s)'],
            [[r['role'],r['AM_threshold'],max_score(r),', '.join(f'{k}:{v}' for k,v in r['AM_actions'].items()),r['T_produce']] for r in selected])
        if seed==0:body+=main_caption('Observed Seed0 AM score gates, actions and complete production cost.')+panel
        else:detail+='## Limited Seed1 AM observations\n\n'+panel
    body+='Scores in this table summarize finite score gates only; all-child and finite-score ledgers are joined by decision sequence. Separate classes retain no-strict-improvement terminal, logical one/both-child infeasibility and other actions, including runs without a child decision exposure. Logical infeasibility has no finite score/margin and is independent of tau. Different thresholds need not create different actions, and no split was forced for table coverage.\n\n'
    k15_am=sorted([r for r in am_rows if r['role']=='K-15-S' and r['seed']==0],key=lambda r:r['AM_threshold'])
    assert len(k15_am)==3 and all(r['performance_eligible'] and r['certificate'] for r in k15_am)
    k15_gates=[]
    for r in k15_am:
        observed=read(OUT/f'reports/AM/position_{r["position"]:03}.json')
        gates=[d for d in observed if d['finite_score_gate']]
        terminals=[d for d in observed if d['exposure_class']=='FINITE_TERMINAL_NO_STRICT']
        assert len(gates)==len(terminals)==1 and gates[0]['selected_action']=='native-target' and terminals[0]['selected_action']=='exact-close'
        assert gates[0]['margin_at_actual_tau']<0
        k15_gates.append(gates[0])
    assert max(float(d['S_AM']) for d in k15_gates)-min(float(d['S_AM']) for d in k15_gates)<1e-12
    spread=max(r['T_cert'] for r in k15_am)-min(r['T_cert'] for r in k15_am)
    assert spread<max(10,.1*min(r['T_cert'] for r in k15_am))
    body+=(f'K-15-S illustrates finite threshold exposure with a wide negative margin. Each Seed0 run has one finite gate with '
        f'normalized score {fmt(float(k15_gates[0]["S_AM"]))}; tolerance-adjusted margins at tau=.04/.08/.16 are '
        f'{" / ".join(fmt(d["margin_at_actual_tau"]) for d in k15_gates)}. All select native-target, followed by a separately classified no-strict-improvement exact-close terminal. '
        f'All three qualify certificates in {" / ".join(fmt(r["T_cert"]) for r in k15_am)} s, respectively; their {fmt(spread)} s spread is below the declared substantive-difference rule. '
        'This finite comparison reports the three actual complete runs and their observed gates; it does not establish sensitivity on other configurations.\n\n')
    uc_am=sorted([r for r in am_rows if r['role']=='UC-B20-B' and r['seed']==0],key=lambda r:r['AM_threshold'])
    assert len(uc_am)==3 and all(r['performance_eligible'] and r['certificate'] for r in uc_am)
    uc_gates=[]
    for r in uc_am:
        observed=read(OUT/f'reports/AM/position_{r["position"]:03}.json')
        logical=[d for d in observed if d['exposure_class']=='LOGICAL_ONE_INFEASIBLE']
        gates=[d for d in observed if d['finite_score_gate']]
        assert len(logical)==3 and len(gates)==1 and gates[0]['selected_action']=='native-target'
        assert all(d['S_AM'] is None and d['margin_at_actual_tau'] is None and d['selected_action']=='split' and not d['tau_controls_logical_infeasibility'] for d in logical)
        assert gates[0]['margin_at_actual_tau']<0
        uc_gates.append(gates[0])
    assert max(float(d['S_AM']) for d in uc_gates)-min(float(d['S_AM']) for d in uc_gates)<1e-12
    uc_spread=max(r['T_cert'] for r in uc_am)-min(r['T_cert'] for r in uc_am)
    assert uc_spread<max(10,.1*min(r['T_cert'] for r in uc_am))
    body+=(f'UC-B20-B separates logical splitting from the finite score test. Each threshold run records three one-child-infeasible splits with no finite score or margin; those actions are independent of tau. '
        f'The subsequent finite gate has score {fmt(float(uc_gates[0]["S_AM"]))} and selects native-target at all three thresholds. '
        f'Qualified certificate times are {" / ".join(fmt(r["T_cert"]) for r in uc_am)} s in the same threshold order, with no substantive time difference. '
        'The split counts therefore do not establish that a finite AM score crossed a threshold.\n\n')
    k20_am=sorted([r for r in am_rows if r['role']=='K-20-S' and r['seed']==0],key=lambda r:r['AM_threshold'])
    assert len(k20_am)==3 and all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in k20_am)
    assert max(r['U'] for r in k20_am)-min(r['U'] for r in k20_am)<1e-7
    k20_gates=[]
    for r in k20_am:
        observed=read(OUT/f'reports/AM/position_{r["position"]:03}.json')
        gates=[d for d in observed if d['finite_score_gate']]
        assert len(gates)==1 and gates[0]['selected_action']=='native-target' and gates[0]['margin_at_actual_tau']<0
        assert any(d['selected_action']=='exact-close' and d['exposure_class']=='FINITE_TERMINAL_NO_STRICT' for d in observed)
        k20_gates.append(gates[0])
    assert max(float(d['S_AM']) for d in k20_gates)-min(float(d['S_AM']) for d in k20_gates)<1e-12
    body+=(f'All three K-20-S runs remain open at U={fmt(k20_am[0]["U"])}, with qualified L in '
        f'[{fmt(min(r["L"] for r in k20_am))},{fmt(max(r["L"] for r in k20_am))}]. '
        f'The observed finite gate score is {fmt(float(k20_gates[0]["S_AM"]))}, below the tested thresholds. '
        'The later exact-close label names a scheduled exact solve; it does not mean that a qualified certificate was completed. '
        'These capped endpoints and unchanged finite-gate choices do not establish a general threshold ranking.\n\n')
    k35_am=sorted([r for r in am_rows if r['role']=='K-35-U' and r['seed']==0],key=lambda r:r['AM_threshold'])
    assert len(k35_am)==3 and all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in k35_am)
    assert max(r['U'] for r in k35_am)-min(r['U'] for r in k35_am)<1e-7
    for r in k35_am:
        observed=read(OUT/f'reports/AM/position_{r["position"]:03}.json')
        assert len(observed)==1 and observed[0]['exposure_class']=='FINITE_TERMINAL_NO_STRICT' and not observed[0]['finite_score_gate']
        assert observed[0]['selected_action']=='exact-close' and abs(float(observed[0]['S_AM']))<1e-10
    body+=(f'K-35-U reaches a finite no-strict-child-improvement terminal before a threshold comparison in each run. '
        f'The paired child observations are present, but no finite score gate is exposed; the near-zero terminal score is not counted as a threshold test. '
        f'All three remain open at U={fmt(k35_am[0]["U"])}, with L in '
        f'[{fmt(min(r["L"] for r in k35_am))},{fmt(max(r["L"] for r in k35_am))}]. '
        'This is distinct from both a logical-infeasibility split and a run with no recorded child decision.\n\n')
    seed0_am=[r for r in am_rows if r['seed']==0]
    assert len(seed0_am)==12
    for tau in [.04,.08,.16]:
        rr=[r for r in seed0_am if r['AM_threshold']==tau]
        assert len(rr)==4 and sum(r['certificate'] and r['performance_eligible'] for r in rr)==2
    body+='Each tested threshold therefore yields two qualified certificates among the same four Seed0 roles. The observed finite gates of K-15-S, K-20-S and UC-B20-B remain well below the smallest tested threshold; K-35-U stops at the separate no-strict-improvement test. These finite observations provide no basis for replacing the accepted tau=.08, while leaving sensitivity at unvisited states outside the claim. The limited Seed1 checks remain separately identified.\n\n'
    am_repeat_rows=[r for r in am_rows if r['seed']==1]
    assert len(am_repeat_rows)==6
    repeat_gate_records=[]
    for role in ['K-15-S','UC-B20-B']:
        rr=sorted([r for r in am_repeat_rows if r['role']==role],key=lambda r:r['AM_threshold'])
        assert len(rr)==3 and all(r['performance_eligible'] and r['certificate'] for r in rr)
        assert all(r['AM_class_counts']==rr[0]['AM_class_counts'] and r['AM_actions']==rr[0]['AM_actions'] for r in rr)
        assert max(r['T_cert'] for r in rr)-min(r['T_cert'] for r in rr)<max(10,.1*min(r['T_cert'] for r in rr))
        for r in rr:
            gates=[d for d in read(OUT/f'reports/AM/position_{r["position"]:03}.json') if d['finite_score_gate']]
            assert len(gates)==1 and gates[0]['margin_at_actual_tau']<0 and float(gates[0]['S_AM'])<.04
            repeat_gate_records.extend(gates)
    body+='The limited Seed1 AM repeat preserves these reached action classes on both selected roles: one finite native-target gate and one no-strict terminal, plus three logical splits on UC-B20-B. All six observations certify, with no substantive within-role time difference across the three thresholds. Their finite scores remain below .04 with negative margins; the repeat does not test unvisited near-threshold states.\n\n'
    assert sum(r['AM_limit_eligibility_evaluations'] for r in am_rows)==51
    assert all(r['AM_depth_limit_rejections']==r['AM_width_limit_rejections']==r['AM_limit_audit_unknown']==0 for r in am_rows)
    body+='Across the eighteen AM views, all51 recorded eligibility evaluations are reconstructible and none rejects depth8 or width1e-4. Across all58 current outer-controller runs, the125 recorded evaluations likewise contain no such rejection. These are checks of recorded guards, not proof that no unrecorded attempt occurred or that the limits are irrelevant elsewhere.\n\n'
    body+='### 6.2 Conditional mechanism results\n\n'
    mech_keys={(r['role'],r['seed']) for r in arms if r['stage'] in ['C2','D2-mechanism']}
    mech_rows=[r for r in arms if (r['role'],r['seed']) in mech_keys and r['method'] in ['S2','S2R','NO_AB','NO_CR','NO_CG']]
    mechanism_order={'S2':0,'S2R':1,'NO_AB':2,'NO_CR':3,'NO_CG':4}
    mech_rows.sort(key=lambda r:(r['seed'],role_order[r['role']],mechanism_order[r['method']]))
    body+='The Seed0 mechanism comparison adds sixteen positions to four shared defaults, giving twenty views. The separately reported Seed1 block adds eight positions to its two actual Seed1 defaults, giving ten views. Root values below are observed complete LP optima, while the final search bounds discussed in the text are different quantities.\n\n'
    for seed,heading in [(0,'Seed0 main mechanism comparison'),(1,'Seed1 limited mechanism repeat')]:
        detail+='## '+heading+'\n\n'
        selected=[r for r in mech_rows if r['seed']==seed]
        assert len(selected)==(20 if seed==0 else 10)
        detail+=table(['Contrast','Role','Root LP optimum','Production (s)','Status'],
            [[LABELS.get(r['method'],r['method']),r['role'],r.get('observed_root_LP_optimum'),r['T_produce'],
              'UEV' if not r['performance_eligible'] else 'C' if r['certificate'] else 'open'] for r in selected])
    root_rows=[r for r in mech_rows if r['seed']==0]
    body+=main_table(['Role','Full','Root only','Minus A/B','Minus \\(C_R\\)','Minus \\(C_G\\)'],
        [[role,*[next(r for r in root_rows if r['role']==role and r['method']==m).get('observed_root_LP_optimum') for m in ['S2','S2R','NO_AB','NO_CR','NO_CG']]] for role in role_order])
    body+='The entries are observed initial LP optima, with n/a for an unexposed complete point. Numerical deletion attribution also requires the paired domain, objective, cutoff and own-H checks in the supplement. Full per-variant complete clocks, returned effort counters and limited Seed1 observations are retained there.\n\n'
    root_pairs=[p for p in pairs if p['comparison_kind'] in ['C2','D2-mechanism']]
    assert len(root_pairs)==24 and all(p['root_LP_attribution_exposed'] for p in root_pairs)
    for p in root_pairs:
        if p['left'] in ['NO_CR','NO_CG','S2R']:
            assert abs(p['root_LP_left_minus_right'])<=1e-7
    ab_root={p['role']:p for p in root_pairs if p['seed']==0 and p['left']=='NO_AB'}
    assert ab_root['K-15-S']['root_LP_left_minus_right']<-1e-7 and ab_root['K-20-S']['root_LP_left_minus_right']<-1e-7
    assert all(abs(ab_root[role]['root_LP_left_minus_right'])<=1e-7 for role in ['UC-B20-B','K-35-U'])
    body+=(f'All24 paired root comparisons meet the saved common-domain/objective/cutoff and complete-own-H conditions. A/B deletion lowers the initial optimum by '
        f'{fmt(-ab_root["K-15-S"]["root_LP_left_minus_right"])} on K-15-S and {fmt(-ab_root["K-20-S"]["root_LP_left_minus_right"])} on K-20-S. '
        'No initial objective increment above tolerance1e-7 is observed for either resource-group or geometry/objective-group retention on the four Seed0 roles; the selected Seed1 roots reproduce these patterns. '
        'Equal initial optimal objective values do not establish that retained rows are slack, inactive or redundant; the optimal face and later search can change. Final lower-bound changes cannot be relabelled as initial-root increments.\n\n')
    k15_mech={r['method']:r for r in mech_rows if r['role']=='K-15-S' and r['seed']==0}
    uc_mech={r['method']:r for r in mech_rows if r['role']=='UC-B20-B' and r['seed']==0}
    expected_mechanisms={'S2','S2R','NO_AB','NO_CR','NO_CG'}
    assert set(k15_mech)==set(uc_mech)==expected_mechanisms
    assert all(r['performance_eligible'] and r['certificate'] for r in [*k15_mech.values(),*uc_mech.values()])
    def substantive_time(a,b):return abs(a-b)>=max(10,.1*min(a,b))
    full=k15_mech['S2']['T_cert']
    assert k15_mech['NO_CR']['T_cert']<full and substantive_time(k15_mech['NO_CR']['T_cert'],full)
    assert all(k15_mech[m]['T_cert']>full and substantive_time(k15_mech[m]['T_cert'],full) for m in ['NO_AB','NO_CG'])
    assert not substantive_time(k15_mech['S2R']['T_cert'],full)
    body+=(f'K-15-S exposes mixed conditional complete-method effects. All five methods qualify their own certificates at the same objective. '
        f'The full method takes {fmt(full)} s; deleting A/B or \\(C_G\\) takes {fmt(k15_mech["NO_AB"]["T_cert"])} / {fmt(k15_mech["NO_CG"]["T_cert"])} s, respectively, '
        f'while deleting \\(C_R\\) takes {fmt(k15_mech["NO_CR"]["T_cert"])} s. Those three differences are substantive under the declared rule, including the deletion advantage for \\(C_R\\). '
        f'GI-TBC-R takes {fmt(k15_mech["S2R"]["T_cert"])} s, a nonmaterial difference from the full method. '
        'These contrasts retain the rest of the representation and complete own H, so their directions are conditional rather than additive component shares.\n\n')
    cost_order=['S2','S2R','NO_AB','NO_CR','NO_CG']
    body+=main_table(['K-15-S variant','Canonical generation (s)','Explicit LP Runtime (s)','MIP Runtime sum (s)','Work sum','Native B&B nodes sum'],
        [[LABELS.get(m,m),k15_mech[m]['model_build_seconds'],k15_mech[m]['root_lp_seconds']+k15_mech[m]['child_lp_seconds'],
          k15_mech[m]['native_MIP_seconds'],k15_mech[m]['Work'],k15_mech[m]['nodes']] for m in cost_order])
    cf=k15_mech['S2'];cr=k15_mech['NO_CR'];cg=k15_mech['NO_CG']
    assert abs(cf['model_build_seconds']-cr['model_build_seconds'])<.1
    assert cf['native_MIP_seconds']-cr['native_MIP_seconds']>30 and cf['Work']>cr['Work'] and cf['nodes']>cr['nodes']
    assert cg['model_build_seconds']<cf['model_build_seconds'] and cg['native_MIP_seconds']>cf['native_MIP_seconds']
    body+=(f'The K-15-S \\(C_R\\) deletion reversal is accompanied by a change mainly inside native MIP search: summed returned MIP Runtime falls from '
        f'{fmt(cf["native_MIP_seconds"])} to {fmt(cr["native_MIP_seconds"])} s, Work from {fmt(cf["Work"])} to {fmt(cr["Work"])}, '
        f'and summed native B&B nodes from {fmt(cf["nodes"])} to {fmt(cr["nodes"])}. '
        f'The cumulative canonical-generation timer differs by only {fmt(cf["model_build_seconds"]-cr["model_build_seconds"])} s. '
        f'Conversely, \\(C_G\\) deletion reduces timed canonical generation to {fmt(cg["model_build_seconds"])} s but increases returned MIP Runtime to {fmt(cg["native_MIP_seconds"])} s and the complete certificate cost. '
        'These matched conditional observations separate artifact-generation cost from the native search that follows. They do not identify an additive causal share or a net controller overhead. '
        'The diagnostics are nested inside production; explicit LP counts omit internal MIP relaxations, target-MIP families are included in the MIP sum, Work is not seconds, and node sums are per-call native counters rather than unique nodes of the outer interval tree. '
        'The full cost tables and actual phase statuses are retained in the supplement.\n\n')
    k15_seed1={r['method']:r for r in mech_rows if r['role']=='K-15-S' and r['seed']==1}
    assert set(k15_seed1)==expected_mechanisms and all(r['performance_eligible'] and r['certificate'] for r in k15_seed1.values())
    f1=k15_seed1['S2']
    for m in ['NO_AB','NO_CR','NO_CG']:
        assert substantive_time(k15_seed1[m]['T_cert'],f1['T_cert'])
        assert (k15_seed1[m]['T_cert']<f1['T_cert']) != (k15_mech[m]['T_cert']<full)
    assert not substantive_time(k15_seed1['S2R']['T_cert'],f1['T_cert'])
    body+=(f'The preselected Seed1 mechanism repeat reverses all three K-15-S row-deletion time directions. Full GI-TBC certifies in {fmt(f1["T_cert"])} s, '
        f'versus {fmt(k15_seed1["NO_AB"]["T_cert"])}/{fmt(k15_seed1["NO_CR"]["T_cert"])}/{fmt(k15_seed1["NO_CG"]["T_cert"])} s after A/B, resource-group and geometry/objective-group deletion. '
        'Each difference is substantive: A/B and geometry/objective deletion are now faster, while resource-group deletion is slower. '
        f'The corresponding returned MIP Runtime sums are {fmt(f1["native_MIP_seconds"])} s for full and '
        f'{fmt(k15_seed1["NO_AB"]["native_MIP_seconds"])}/{fmt(k15_seed1["NO_CR"]["native_MIP_seconds"])}/{fmt(k15_seed1["NO_CG"]["native_MIP_seconds"])} s after deletion. '
        'The same initial-root pattern, independently paid H and recorded action classes coexist with these reversed native search costs. '
        f'Root-only takes {fmt(k15_seed1["S2R"]["T_cert"])} s, a nonmaterial difference. The two Seeds therefore support conditional mixed effects, not a stable runtime ranking or an additive component share.\n\n')
    uc_seed1=[r for r in mech_rows if r['role']=='UC-B20-B' and r['seed']==1]
    assert len(uc_seed1)==5 and all(r['performance_eligible'] and r['certificate'] for r in uc_seed1)
    assert max(r['T_cert'] for r in uc_seed1)-min(r['T_cert'] for r in uc_seed1)<10
    uc_times=[r['T_cert'] for r in uc_mech.values()]
    assert max(uc_times)-min(uc_times)<10
    body+=(f'All five UC-B20-B methods qualify certificates between {fmt(min(uc_times))} and {fmt(max(uc_times))} s. '
        'Every pairwise difference is below the ten-second absolute floor, so this tiny case supplies no substantive complete-cost ranking. '
        'The logical split activity reported above and the net benefit of the whole outer package are assessed separately; visible outer actions alone do not determine a full-method speed advantage.\n\n')
    k20_mech={r['method']:r for r in mech_rows if r['role']=='K-20-S' and r['seed']==0}
    kr_full=k20_mech['S2'];kr_deleted=k20_mech['NO_CR']
    assert all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in [kr_full,kr_deleted])
    assert abs(kr_full['U']-kr_deleted['U'])<1e-7 and kr_full['L']>kr_deleted['L']+1e-7
    body+=(f'The \\(C_R\\) result differs on K-20-S. Both runs remain open at the same verified U={fmt(kr_full["U"])}, '
        f'while the full method has qualified L={fmt(kr_full["L"])} versus {fmt(kr_deleted["L"])} after deletion. '
        'Thus the deletion advantage in K-15-S certificate cost coexists with better finite-budget dual progress for the full method on K-20-S. '
        'These are final-endpoint observations at matched complete caps; root-LP attribution additionally requires its own matched-scope evidence.\n\n')
    assert set(k20_mech)==expected_mechanisms
    assert all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in k20_mech.values())
    assert max(r['U'] for r in k20_mech.values())-min(r['U'] for r in k20_mech.values())<1e-7
    assert k20_mech['S2R']['L']>kr_full['L']+1e-7
    assert all(kr_full['L']>k20_mech[m]['L']+1e-7 for m in ['NO_AB','NO_CG'])
    body+=(f'The whole K-20-S contrast also retains an adverse endpoint for the full controller: GI-TBC-R has the same U and final qualified L='
        f'{fmt(k20_mech["S2R"]["L"])}, above the full method\'s {fmt(kr_full["L"])}. '
        f'A/B and \\(C_G\\) deletion end at L={fmt(k20_mech["NO_AB"]["L"])}/{fmt(k20_mech["NO_CG"]["L"])}. '
        'All five runs remain open. These are final qualified bounds from search under the registered budget; numerical root-LP optima require their separate matched-scope evidence. No certificate-time ranking follows. '
        'Row strengthening and outer scheduling therefore have distinct conditional interpretations.\n\n')
    k35_mech={r['method']:r for r in mech_rows if r['role']=='K-35-U' and r['seed']==0}
    kg_full=k35_mech['S2'];kg_deleted=k35_mech['NO_CG']
    assert set(k35_mech)==expected_mechanisms
    assert all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in k35_mech.values())
    body+=main_table(['K-35-U variant','Own feasible U','Qualified final L','Status'],
        [[LABELS.get(m,m),k35_mech[m]['U'],k35_mech[m]['L'],'open'] for m in cost_order])
    assert all(r['performance_eligible'] and not r['certificate'] and r['T_cert'] is None for r in [kg_full,kg_deleted])
    assert kg_deleted['U']<kg_full['U']-1e-7 and kg_full['L']>kg_deleted['L']+1e-7
    assert kg_deleted['U']-kg_deleted['L']<kg_full['U']-kg_full['L']
    assert all(r['AM_class_counts']=={'FINITE_TERMINAL_NO_STRICT':1} and r['AM_actions']=={'exact-close':1} for r in [kg_full,kg_deleted])
    body+=(f'K-35-U exposes an opposed-endpoint result for \\(C_G\\) deletion. The full method reports U/L='
        f'{fmt(kg_full["U"])}/{fmt(kg_full["L"])}, versus {fmt(kg_deleted["U"])}/{fmt(kg_deleted["L"])} after deletion. '
        'The deleted model finds a better feasible objective, while the full method retains the stronger qualified final lower bound. '
        'A smaller signed gap after deletion therefore does not establish endpoint dominance. Both ledgers record one no-strict-improvement exact-close action under the same outer policy; the native searches remain separate and both runs remain open. No certificate-time comparison is assigned.\n\n')
    kg_ab=k35_mech['NO_AB']
    assert kg_ab['performance_eligible'] and not kg_ab['certificate'] and kg_ab['T_cert'] is None
    assert kg_ab['U']<kg_full['U']-1e-7 and kg_full['L']>kg_ab['L']+1e-7
    body+=(f'A/B deletion also has opposed endpoints on K-35-U: its verified own U/L='
        f'{fmt(kg_ab["U"])}/{fmt(kg_ab["L"])} improves the feasible objective by {fmt(kg_full["U"]-kg_ab["U"])}, '
        f'while the full method retains L higher by {fmt(kg_full["L"]-kg_ab["L"])}. '
        'Both runs remain open. Thus the full-method certificate advantage of A/B on K-15-S and its higher final bound on K-20-S coexist with a better K-35-U feasible objective after deletion. '
        'A smaller deletion gap does not combine these distinct endpoint directions into dominance, and no instance-specific setting is selected.\n\n')
    kg_cr=k35_mech['NO_CR']
    assert kg_cr['U']<kg_full['U']-1e-7 and kg_full['L']>kg_cr['L']+1e-7
    assert all(k35_mech[m]['U']<kg_full['U']-1e-7 and kg_full['L']>k35_mech[m]['L']+1e-7 for m in ['NO_AB','NO_CR','NO_CG'])
    body+=(f'\\(C_R\\) deletion has U/L={fmt(kg_cr["U"])}/{fmt(kg_cr["L"])} on this larger role. '
        'All three row-group deletions therefore improve the saved feasible objective while weakening the qualified final lower endpoint relative to the full formulation. '
        'This repeated within-role primal/dual opposition is retained alongside the easier certificate-cost advantages and the K-15-S \\(C_R\\) reversal. '
        'It does not justify an instance-specific setting or a complete-proof-time ordering.\n\n')
    kg_root=k35_mech['S2R']
    assert kg_root['performance_eligible'] and not kg_root['certificate'] and kg_root['T_cert'] is None
    assert abs(kg_root['U']-kg_full['U'])<1e-7 and kg_root['L']>kg_full['L']+1e-7
    body+=(f'The legal root-only comparison also retains a higher final lower endpoint on K-35-U: GI-TBC-R reports U/L='
        f'{fmt(kg_root["U"])}/{fmt(kg_root["L"])}, at the same U as the full method and a final L higher by {fmt(kg_root["L"]-kg_full["L"])}. '
        'Both runs remain open under the matched complete cap. Together with K-20-S, these selected hard-role observations show no full-controller endpoint advantage over root-only at the saved Seed0 endpoints. '
        'They do not compare initial root-LP optima or establish an eventual proof-time ordering; the remaining mechanism and limited Seed1 findings retain their separate scopes.\n\n')
    assert not substantive_time(k15_mech['S2']['T_cert'],k15_mech['S2R']['T_cert'])
    assert not substantive_time(uc_mech['S2']['T_cert'],uc_mech['S2R']['T_cert'])
    body+='Across these four preselected Seed0 roles, no substantive full-over-root certificate-cost advantage is observed: the two easier roles certify with nonmaterial differences, while both harder roles remain open and root-only has the same U with slightly higher final L. The strengthened root already suffices for the two easier certificates in this panel. Thus visible outer activity and the strong integrated GI-TBC results relative to compact controls do not assign a separate incremental speed advantage to the outer package here. The accepted post-R130 attribution history remains relevant with its own version and cases; the current limited Seed1 repeats are reported separately.\n\n'
    for selected in [k15_mech,k20_mech]:
        assert selected['NO_AB']['AM_class_counts']=={'FINITE_TERMINAL_NO_STRICT':1}
        for method in ['S2','NO_CR','NO_CG']:
            assert selected[method]['AM_class_counts']=={'FINITE_SCORE_GATE':1,'FINITE_TERMINAL_NO_STRICT':1}
    for method in ['S2','NO_AB','NO_CR','NO_CG']:
        assert uc_mech[method]['AM_class_counts']=={'LOGICAL_ONE_INFEASIBLE':3,'FINITE_SCORE_GATE':1,'FINITE_TERMINAL_NO_STRICT':1}
        assert k35_mech[method]['AM_class_counts']=={'FINITE_TERMINAL_NO_STRICT':1}
    assert all(not selected['S2R']['AM_class_counts'] for selected in [k15_mech,uc_mech,k20_mech,k35_mech])
    body+='The row-deletion controls keep the configured outer policy fixed, but can change its reached states and realized actions. On K-15-S and K-20-S, A/B deletion records only a no-strict-improvement terminal, while full, \\(C_R\\)-deleted and \\(C_G\\)-deleted runs each also record one finite native-target gate. On UC-B20-B, each of the four outer variants records three logical-infeasibility splits, one finite gate and one terminal. On K-35-U, each records only the no-strict terminal; root-only has no child-AM record on any role. The complete Seed0 mechanism observations therefore contain ten finite gates, sixteen terminals and twelve logical splits. These counts describe reached decisions, not independent instances. Conditional formulation effects include any induced control-path change; identical configured policy is not identical realized scheduling or native search.\n\n'
    body+='The saved initial domain/objective/cutoff and independently paid H determine which numerical roots may be compared; the full paired report flags their actual matches. Root values require an observed OPTIMAL LP; n/a means no complete applicable point was exposed. The ideal deletion relation is not a runtime theorem. Work/nodes, LP/MIP time, model-construction cost, complete own H and outer actions accompany these conditional contrasts; no additive allocation of total speed-up is made. Depth 8 / minimum width 1e-4 remain fixed. Recorded eligibility rows are joined to retained scheduler-epoch geometry; a source-rejection reset or missing leaf makes the reconstruction unknown. Eligible child work may stop before its ledger row, so missing records do not prove no attempted test. The depth guard short-circuits the width check; a width that would also reject after depth failure is not counted as another causal trigger. Zero-width proofs without recorded guard evaluations are not counted as width-limit triggers. Final materialized-leaf and decision-parent/probed-child depths are distinct observations. The full-versus-variant results and exposure limits are interpreted in the stage decision and supplement.\n\n'
    body+='\\clearpage\n\n### 6.3 Mechanism synthesis and boundaries\n\n'
    body+=main_table(['Mechanism','Mathematical role','Corresponding experiment','Supported conclusion','Boundary'],[
        ['Complete own H','Constructs and checks its own feasible Start; supplies no lower-bound proof',
         'P/PS across main panels and four Seed1 triplets',
         'PS materially wins X-35-B; P improves both endpoints on K-20-S and R-X20-S-T2',
         'Startup package only; no operator or H-seed attribution'],
        ['Outer interval controller','Preserves improving-interval coverage through probing, targeting and exact continuation',
         'Full/GI-TBC-R: four Seed0 roles, two Seed1 repeats',
         'No substantive certificate-cost gain here; both hard Seed0 roles have higher root-only final L',
         'Reached actions do not establish net benefit; prior versioned evidence remains separate'],
        ['Shared-state A/B links','Valid movement/visit equalities connect service to inventory mixtures',
         'A/B deletion: four Seed0 roles, two Seed1 repeats',
         'Two initial LP increments; K-15-S time direction reverses across Seeds; full K-20-S has higher final L',
         'Core products retained; unique one-way service preserves implicit quantity integrality'],
        ['Resource group \\(C_R\\)','Ordered-supply and pair-cover/handling inequalities strengthen necessary resource conditions',
         'Single-group deletion: four Seed0 roles, two Seed1 repeats; pair-only unchanged',
         'K-15-S deletion wins Seed0 and loses Seed1; full K-20-S has higher final L; initial increments undetected',
         'Valid LP tightening need not accelerate search; no additive shares'],
        ['Geometry/objective group \\(C_G\\)','Spread, centering and objective estimators use dedicated auxiliaries',
         'Single-group deletion: four Seed0 roles, two Seed1 repeats; original domains/products retained',
         'K-15-S time direction reverses; K-35-U deletion improves U and weakens L; initial increments undetected',
         'This group does not contain all fairness structure; endpoint opposition persists'],
        ['AM score and logic','Normalized child-bound score applies after eligibility, validity and terminal tests',
         'Three thresholds: four Seed0 roles, two Seed1 repeats',
         'Finite scores stay below .04; logical splits hold separately; K-35-U stops before its threshold test',
         'Observed unchanged actions do not prove global robustness or small proof cost']])
    body+='These rows summarize the observed conditional findings. The full Seed0 and separately identified Seed1 tables retain every selected role, and the accompanying paired/root and cost reports determine where numerical root attribution is actually exposed. Shared inventory-state/core products are retained throughout the current mechanism study, so they have no isolated runtime effect assigned here.\n\n'
    body+='## 7. Conclusions and implications\n\n'+read(OUT/'candidate_decision.json')['paper_conclusion']+'\n\n'
    stage_report=(OUT/'final_report.md').read_text(encoding='utf-8')
    a=stage_report.index('1. **Positive-objective primal/dual bottlenecks under physical resources.**')
    b=stage_report.index('## Budget, manuscript and remaining facts',a)
    agenda=stage_report[a:b]
    agenda=agenda.replace('R133 J2/J3','The fixed-denominator four-station reference, preserved in the supplement,')
    agenda=agenda.replace('R134 threshold-count (TC) strengthening','The previously tested threshold-count (TC) extension of that reference')
    agenda=agenda.replace('prior R47/R52 examples','prior AM construction and threshold-validation evidence, preserved in the supplement')
    body+='### 7.1 Research priorities\n\n'+agenda
    author_note='The direct HGA-TGBC antecedent is the project manuscript *Equity-aware Bike Repositioning in Station-based Bike-sharing Systems*. Its current author order, affiliations and publication status, this paper\'s author list/affiliations, and the original capture URL/date and selection provenance of the old CITI443 table still require author confirmation. These facts are not invented and do not prevent scientific discussion of this draft.\n'
    body=polish_current_prose(body)
    detail=polish_current_prose(detail)
    (OUT/'paper_body.md').write_text(body,encoding='utf-8')
    appendix=(OUT/'model_and_algorithm_appendices.md').read_text(encoding='utf-8-sig')
    (OUT/'manuscript.md').write_text(body+'\n\\clearpage\n\n'+appendix,encoding='utf-8')
    supplement='# Supplement: Round137 complete observations and preserved historical evidence\n\n'
    supplement+='The current tables contain every registered position. C means a performance-eligible qualified certificate; O means open; UEV means evidence outside formal performance eligibility. Open times are null, not the cap. Detailed full-precision arrays, physical operations, raw lifecycle/model evidence and source identities accompany the CSV/JSON authorities. Prior evidence below keeps its original version and denominators.\n\n'
    supplement+='## Author and source metadata awaiting confirmation\n\n'+author_note+'\n'
    supplement+=detail+'\n'
    supplement+=table(['Position / study','Input / Seed','Method','Status','U','L','Production / verification / total s'],[[f'{r["position"]} /{r["stage"]}',f'{r["role"]} /{r["seed"]}',LABELS.get(r['method'],r['method']),'UEV' if not r['performance_eligible'] else 'C' if r['certificate'] else 'O',r['U'],r['L'],f'{fmt(r["T_produce"])} /{fmt(r["T_verify"])} /{fmt(r["T_total"])}'] for r in arms])
    supplement+='## Current stage analysis\n\n'+nest_preserved_markdown((OUT/'final_report.md').read_text(encoding='utf-8'))
    historical=(OLD/'supplement.md').read_text(encoding='utf-8-sig')
    historical=re.sub(r'\(figures/([^)]*)\)',r'(https://raw.githubusercontent.com/yifanXovo/TailoredExact/25800aa6b51bf7607b51e5df14a10a5ca4571889/results/unified_exact_round135/figures/\1)',historical)
    supplement+='\n\n## Preserved historical supplement (R135 observations retained; headings nested and figure links pinned)\n\n'+nest_preserved_markdown(historical)
    (OUT/'supplement.md').write_text(supplement,encoding='utf-8')
    assert '@@' not in body
    write(OUT/'document_assembly.json',dict(UTC=utc(),manuscript_SHA=sha(OUT/'manuscript.md'),
        bibliography_SHA=sha(OUT/'references.bib'),summary_SHA=sha(OUT/'reports/summary.json'),
        decision_SHA=sha(OUT/'candidate_decision.json'),complete_appendices=True,no_result_placeholders=True,
        original_R135_evidence_not_relabelled=True))

    lineage=read(OUT/'document_lineage.json')
    lineage.update(last_assembly_UTC=utc(),results_not_yet_assembled=False,
        derivative_appendix_SHA=sha(OUT/'model_and_algorithm_appendices.md'),
        method_source_SHA=sha(OUT/'method_and_model_source.md'),
        current_assembled_manuscript_SHA=sha(OUT/'manuscript.md'))
    write(OUT/'document_lineage.json',lineage)

def pdf():
    assert read(OUT/'candidate_decision.json')['study_complete'] and not budget()['unclosed']
    import datetime as document_clock
    import round134_documents as old
    local_date=document_clock.datetime.now(document_clock.timezone(document_clock.timedelta(hours=8),'Asia/Shanghai'))
    months='January February March April May June July August September October November December'.split()
    stamp=f'{local_date.day} {months[local_date.month-1]} {local_date.year}'
    source=inspect.getsource(old.pdf)
    assert source.count('date=26 October 2026')==1
    code=source.replace('date=26 October 2026',f'date={stamp}')
    ns=dict(vars(old),OUT=OUT,TEMP=TEMP)
    exec(compile(code,__file__+'::maintained_pdf_export','exec'),ns);ns['pdf']()
    receipt=read(OUT/'pdf_export.json')
    receipt.update(document_date_requested=stamp,document_date_timezone='Asia/Shanghai')
    write(OUT/'pdf_export.json',receipt)

if __name__=='__main__':
    globals()[sys.argv[1]]()

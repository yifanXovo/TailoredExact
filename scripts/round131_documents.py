"""Local manuscript migration, stratified assessment and evidence registry."""
from round131_benchmark import *
from round131_analysis import table as csv_table
import csv, re, io

def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)
def fmt(x):return 'null' if x is None else f'{x:.3f}'
def role(q):return f"{q['id']} / S{q['seed']}"+(f" / R{q['repeat']}" if q['layer']=='B' else '')
def timecell(q,m):return 'unevaluable' if q['classification']=='UNEVALUABLE' else fmt(q[m+'_T_cert']) if q[m+'_T_cert'] is not None else 'open'

def registry():
    o=read(OUT/'observations.json');rows=[];source_tables={}
    inherited=list(csv.DictReader((PRIOR/'evidence_migration.csv').open(encoding='utf-8-sig')))
    for n,a in enumerate(inherited,1):
        a=dict(a);authority=a['source_authority'];rnd=int(a['round'])
        source=ROOT/authority
        if authority not in source_tables:
            b=git('show',BASE+':'+authority) if not source.exists() else source.read_bytes()
            source_tables[authority]=(hashlib.sha256(b).hexdigest(),list(csv.DictReader(io.StringIO(b.decode('utf-8-sig')))))
        source_sha,original_rows=source_tables[authority]
        matches=[r for r in original_rows if r['id']==a['id'] and (r.get('method') or r.get('arm'))==a['method']
            and (not r.get('seed') or str(r['seed'])==str(a['seed']))]
        assert len(matches)==1,(authority,a['id'],a['method'],a['seed'],len(matches))
        original=matches[0]
        # Preserve each original observation; do not select a fastest record.
        a.update(repeat=original.get('repeat') or a.get('repeat') or '1',source_table_SHA=source_sha,
            run_identity=original.get('producer_receipt_SHA') or original.get('destination') or 'record-sha256:'+hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),
            historical_run_identity_scope='original producer receipt/destination where recorded, otherwise exact original endpoint record hash (no inferred missing process identity)',
            dedup_scope='round + source authority + actual original row identity; no cross-round best-of',
            current_main_panel=False,current_overhead_panel=False,current_V35_scope=False)
        if rnd==129:a['evidence_role']='known protection' if a['id']=='PB-C20-B' else 'prospective at R129 selection; exposed in later research'
        for k in ['input_SHA','PE_SHA','DLL_SHA','cap_seconds','V','M','Q_vector','T_seconds']:
            if a.get(k) in [None,'','unknown'] and original.get(k) not in [None,'']:a[k]=original[k]
        rows.append(a)
    # R130's registry did not include the predecessor tiny repetitions or
    # bounded training table. Their exact source rows remain separate.
    m127=read(ROOT/'results/unified_exact_round127/input_manifest.json')
    for filename,purpose in [('tiny_arms.csv','predecessor full-MB tiny overhead'),('training_arms.csv','bounded P parameter selection; development, not benchmark')]:
        path=ROOT/'results/unified_exact_round127'/filename
        for n,a in enumerate(csv.DictReader(path.open(encoding='utf-8-sig')),1):
            pool=m127['tiny_roles'] if filename.startswith('tiny') else m127['training_roles']
            p=next(p for p in pool if p['id']==a['id'])
            method=a.get('method') or ('P_'+a['configuration'] if filename.startswith('training') else a['arm'])
            repeat=a.get('repeat') or '1';authority=path.relative_to(ROOT).as_posix()
            rows.append(dict(round=127,id=a['id'],seed=a['seed'],repeat=repeat,method=method,
                actual_configuration='full three-station M-B' if method=='MB' else a.get('configuration') or 'original cold P',
                evidence_role=purpose,PE_SHA=a.get('PE_SHA') or read(ROOT/'results/unified_exact_round127/E1_frozen.json')['PE_SHA'],DLL_SHA=DLL_SHA,
                input_SHA=a.get('input_SHA') or p['input_sha256'],source_recorded_commit=a.get('source_commit','unknown'),
                cap_seconds=a.get('cap_seconds') or p['cap_seconds'],V=p['V'],M=p['M'],Q_vector=p['Q_vector'],T_seconds=p['T_seconds'],
                numerical_policy='original recorded policy; no new historical qualification',clock='original complete T_produce/T_verify/T_total; training admission-prefix repair is retained in its source',
                T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total'],certificate=a['certificate'],T_cert=a['T_cert'],
                source_authority=authority,source_table_SHA=sha(path),run_identity=a.get('destination') or a.get('identity_SHA') or str(n),
                direct_current_method_performance=False,current_main_panel=False,current_overhead_panel=False,current_V35_scope=False,
                predecessor_numbers_relabelled=False))
    for a in o['arms']:
        rows.append(dict(round=131,id=a['id'],seed=a['seed'],repeat=a['repeat'],method=a['method'],
            actual_configuration='uniform pair-support MS2' if a['method']=='S2' else 'original cold P',
            evidence_role=dict(A='known SC final-version main benchmark',B='known tiny final-version overhead',C='known V35 final-version scope')[a['layer']],
            PE_SHA=a['PE_SHA'],DLL_SHA=a['DLL_SHA'],input_SHA=a['input_SHA'],source_recorded_commit=SOURCE,
            cap_seconds=a['cap_seconds'],V=a['V'],M=a['M'],Q_vector=a['Q_vector'],T_seconds=a['T_seconds'],
            numerical_policy='unchanged source/return/coverage and signed numerical policy',clock='complete T_produce; T_cert=T_produce only after qualification; T_verify/T_total separate',
            T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total'],certificate=a['certificate'],T_cert=a['T_cert'],
            source_authority='results/unified_exact_round131/arms.csv',source_table_SHA=sha(OUT/'arms.csv'),run_identity=a['run_identity'],
            direct_current_method_performance=a['method']=='S2',current_main_panel=a['layer']=='A',current_overhead_panel=a['layer']=='B',current_V35_scope=a['layer']=='C',predecessor_numbers_relabelled=False))
    keys=[]
    for a in rows:
        key=[a.get(k,'unknown') for k in ['round','source_authority','run_identity','id','method','PE_SHA','input_SHA','seed','repeat','cap_seconds']]
        a['registry_key']=hashlib.sha256(json.dumps(key,sort_keys=True).encode()).hexdigest();keys.append(a['registry_key'])
    assert len(keys)==len(set(keys))
    csv_table(OUT/'evidence_registry.csv',rows)
    write(OUT/'evidence_registry_scope.json',dict(rows=len(rows),by_round=dict(collections.Counter(str(a['round']) for a in rows)),
        direct_new_formal_records=52,distinct_new_known_inputs=10,no_cross_round_best_time=True,no_pooled_win_or_speedup=True,
        true_run_identity_key_includes_repeat=True,historical_unavailable_fields_remain_unknown=True,
        registry_is_not_a_performance_selection_table=True))

def documents():
    o=read(OUT/'observations.json');s=read(OUT/'stratified_summary.json');ts=read(OUT/'tiny_summary.json')['roles']
    pairs=o['pairs'];layers=s['layers'];tables={}
    for layer in ['A','B','C']:
        pp=[q for q in pairs if q['layer']==layer]
        tables[layer]=table(['Known problem / Seed'+(' / repeat' if layer=='B' else ''),'P T_cert (s)','S2 T_cert (s)','Class','S2/P direction','S2 - P (s)','P / S2'],
            [[role(q),timecell(q,'P'),timecell(q,'S2'),q['classification'],q['direction'],fmt(q['S2_minus_P_seconds']),fmt(q['P_over_S2_certification_ratio'])] for q in pp])
        (OUT/'tables').mkdir(exist_ok=True)
        (OUT/'tables'/f'layer_{layer}.md').write_text(tables[layer],encoding='utf-8')
        csv_table(OUT/'tables'/f'layer_{layer}.csv',pp)
    label='DIRECT_CERTIFICATION_SUPPORT_WITH_FINITE_LIMITS'
    repeated=[]
    for id in [p['id'] for p in read(OUT/'input_manifest.json')['roles'] if p['layer']=='A']:
        qq=[q for q in pairs if q['id']==id and (q['classification']=='P_ONLY_CERTIFIED' or q['materiality']=='P_MATERIALLY_FASTER')]
        if len(qq)==2:repeated.append(id)
    if repeated:label='MIXED_WITH_REPEATED_MATERIAL_REVERSE_RISK'
    elif layers['A']['directions'].get('Win',0)==0:label='MAINLY_OPEN_OR_INSUFFICIENT_DIRECT_SUPPORT'
    def listed(condition):
        rr=[q for q in pairs if q['layer']=='A' and condition(q)]
        return ', '.join(role(q) for q in rr) or 'none'
    actual_faster=listed(lambda q:q['classification']=='BOTH_CERTIFIED' and q['direction']=='Win')
    only=listed(lambda q:q['classification']=='S2_ONLY_CERTIFIED')
    losses=listed(lambda q:q['direction']=='Lose')
    opens=listed(lambda q:q['classification']=='BOTH_OPEN')
    warning=sum(x['warnings_10_seconds'] for x in ts);p_risk=sum(x['P_only_risks'] for x in ts)
    repeated_tiny=[f"{x['id']} / S{z['seed']}" for x in ts for z in x['by_seed'] if z['repeatable_10_second_warning']]
    repeated_among_six=[x['id'] for x in ts if x['at_least_two_10_second_warnings_among_six']]
    repeated_tiny_P_only=[x['id'] for x in ts if x['P_only_risks']>=2]
    if not repeated and (layers['A']['directions'].get('Lose',0) or layers['C']['directions'].get('Lose',0) or warning or p_risk):label='MIXED_WITH_RECORDED_REVERSE_RESULTS'
    if s['issues']:label='PROOF_OR_IDENTITY_ISSUE_REQUIRES_DECISION'
    c_nonzero=layers['C']['nonzero_certification_counts']['S2']
    c_reverse=[q for q in pairs if q['layer']=='C' and (q['classification']=='P_ONLY_CERTIFIED' or q['materiality']=='P_MATERIALLY_FASTER')]
    repeat_risk=bool(repeated or repeated_among_six or repeated_tiny_P_only or len(c_reverse)>=2)
    decision=('Decision for substantive paper review: determine whether the claim narrowed to these case-dependent gains and the explicitly located repeated reverse observations is sufficient. Tiny repetitions narrow only the tiny-overhead statement; C has one Seed and is not within-input replicated evidence. S2 adoption stays fixed. This round makes no algorithm change and authorizes no follow-up experiment.' if repeat_risk else
        'The final-version evidence gap is closed within this finite design. Deliver the limited paper statement for substantive review and end this round; no extra ablation or selection cycle follows.')
    dd=layers['A']['directions']
    synopsis=(f"On the six known SC problems at two Seeds (12 matched observations), S2 and P certify {layers['A']['certification_counts']['S2']} and {layers['A']['certification_counts']['P']} observations, respectively; "
        f"the strict S2/P directions are {dd.get('Win',0)} Win, {dd.get('Lose',0)} Lose, {dd.get('Tie',0)} Tie and {dd.get('UNDETERMINED',0)} undetermined"
        +(f", with {dd['UNEVALUABLE']} unevaluable" if dd.get('UNEVALUABLE') else '')
        +f". The tiny layer records {layers['B']['directions'].get('Win',0)} strict Win, {layers['B']['directions'].get('Lose',0)} strict Lose and {layers['B']['directions'].get('Tie',0)} Tie across twelve matched observations, with {warning} observed >=10-second delays and {p_risk} P-only certification risks. "
        f"At V35, S2 and P have {c_nonzero} and {layers['C']['nonzero_certification_counts']['P']} nonzero certificates across two Seed0 observations, with {layers['C']['classes'].get('P_ONLY_CERTIFIED',0)} P-only cases; both-open cases have unknown final certification-time ordering.")
    open_table=table(['Layer / problem / Seed','S2 U','S2 L','P U','P L','Observed endpoint relation'],
        [[q['layer']+' / '+role(q),f"{q['S2_U']:.12g}",f"{q['S2_L']:.12g}",f"{q['P_U']:.12g}",f"{q['P_L']:.12g}",
          ('S2 lower U' if q['S2_U']<q['P_U'] else 'P lower U' if q['P_U']<q['S2_U'] else 'equal U')+'; '+('S2 higher L' if q['S2_L']>q['P_L'] else 'P higher L' if q['P_L']>q['S2_L'] else 'equal L')]
         for q in pairs if q['classification']=='BOTH_OPEN'])
    assessment=f'''# Round131 benchmark assessment

Execution: **{s['execution']}**. Stage exit: **`{s['stage_exit']}`**. Scientific assessment: **`{label}`**.

{synopsis}

The adopted method remains the frozen S2/MS2. R129 selection and R130 adoption are settled. This study compares only full S2 and original cold P, using the same frozen E3/DLL, complete independently paid workflows and unchanged numerical/time policies. All ten inputs were already exposed. There is no fresh, blind or unseen validation claim, tuning, production compilation, algorithm change or instance-wise dispatch.

## A: primary final-version certification panel

Six original SC problems, two Seeds, 24 arms and 12 S2/P comparisons. The full six-problem set includes SC-C20-S. S2 truly certifies faster in the both-certified intersection on: **{actual_faster}**. S2 alone certifies on: **{only}**. Actual strict losses: **{losses}**. Both-open observations: **{opens}**. Every both-open pair is UNDETERMINED, regardless of its U/L advantage. The full endpoint/clock table in Supplement S and arms.csv gives the actual values.

{tables['A']}
Only the {layers['A']['both_certified_intersection_n']} explicitly both-certified observations enter the conditional geometric mean P/S2={fmt(layers['A']['conditional_geometric_mean_P_over_S2'])}. It does not summarize the entire panel. Absolute seconds and ratios use the unrounded authorities; the table display is rounded. A/C materiality is symmetric, slower minus faster >= max(10 seconds, .1*faster), and does not change strict Win/Lose. Repeated material reverse roles: **{', '.join(repeated) or 'none'}**. Single-sided certificates are never excused by a time threshold.

## B: final-S2 absolute tiny overhead

Two known problems, three Seeds and two opposite-order matched repeats per Seed: 24 arms, twelve observations. This layer is not pooled with A/C. Observed >=10-second S2 delays: **{warning}**; P-only certification risks: **{p_risk}**. At least two of six observations meet the delay threshold on: **{', '.join(repeated_among_six) or 'none'}**. Within the same Seed, both valid repeats meet it at: **{', '.join(repeated_tiny) or 'none'}**. These are observed repetitions, not a statistical noise theorem. A 0.1-second loss remains Lose. Fewer than two valid repeats never yield an estimated fluctuation range. SM-B10-B is a legal empty-fleet/structurally easy role and does not represent all tiny difficulty.

{tables['B']}
'''
    tiny_stats=[]
    for x in ts:
        z=x['S2_minus_P_seconds'];pt=x['certification_seconds']['P'];st=x['certification_seconds']['S2']
        tiny_stats.append([x['id'],str(z['n']),fmt(z['median']),f"{fmt(z['minimum'])} .. {fmt(z['maximum'])}",f"{fmt(pt['median'])} [{fmt(pt['minimum'])}, {fmt(pt['maximum'])}]",f"{fmt(st['median'])} [{fmt(st['minimum'])}, {fmt(st['maximum'])}]"])
    tiny_table=table(['Problem','Both-cert n / 6','Median S2-P (s)','S2-P range (s)','P median [range] (s)','S2 median [range] (s)'],tiny_stats)
    assessment+=tiny_table+f'''
tiny_summary.json retains all six directions and each Seed's two repeats, with valid counts and exact ranges. These are six actual observations per known input, not six new inputs.

## C: finite V35 scope boundary

The two complete original R122 V35 roles use Seed0 only and fresh full 2400-second contracts. They are not continuations of old trees or merged short-window development clocks. Final S2 nonzero certifications: **{c_nonzero}/2**. This {'expands the observed nonzero certification size to V35 on the named certified roles only' if c_nonzero else 'does not expand the observed nonzero certification size to V35'}. For any both-open pair, **final certification-time ordering is unknown**. U/L/gap may describe the observed endpoints only. One Seed supplies no two-Seed robustness statement.

{tables['C']}
## Open endpoints, without certification ordering

The following are the actual both-open endpoints. The relation is descriptive only: no certification Win, Tie, cap-based speedup or extrapolated final solve time is assigned.

{open_table}
## Version migration and limits

A is the principal final-version SC table. R126/R127 full three-station M-B tables remain historical and are not relabelled S2. B fills the final-S2 tiny-version gap. R129's four inputs retain their prospective-at-selection role and are now known; its protection input is separate. R130's complete PS and S2R attribution directions, including reversals/open cases, remain separate. R127/R128 MS2 development uses its original build and clocks. Earlier R122/R123 V50 and longer-window MB/ENS results remain predecessor evidence. This round measures a maximum V35 with one Seed in C and validates neither final S2 at V50/V60 nor universal dominance or statistical significance.

The ten known inputs come from two existing safe station tables. Inventories, targets, weights and fleets are constructed; geography retains original compact/regional Euclidean rules. Scenario means service-station total shortage/balance/surplus, excluding depot. A has four shortage, one balanced and one surplus role; B has one shortage and one easy balanced role; C has one surplus and one balanced role. Source, geography, size, fleet and physical T vary together, with station overlap. These are not a factorial design, IID city samples or independent unseen validation. Only lambda=.15 is tested. The finite denominators are A=6 inputs/12 observations, B=2/12, C=2/2; no weighted total Win or cross-round average speedup is supplied.

There is no new component or causal test. The paper may describe a tailored branch-and-cut framework with Gini-interval decomposition while distinguishing the custom representation/valid rows/H/controller from Gurobi's native branching and cuts. Decomposition exists; R130 did not show repeated material net outer-package gains. R127 tuned-P negative holdout, earlier mixed same-H outcomes, and R128/R129 reverse/open observations remain visible.

{decision}
'''
    (OUT/'benchmark_assessment.md').write_text(assessment,encoding='utf-8')
    write(OUT/'scientific_assessment.json',dict(execution=s['execution'],stage_exit=s['stage_exit'],scientific_assessment=label,
        synopsis=synopsis,repeated_material_reverse_A=repeated,tiny_warning_count=warning,tiny_P_only_risks=p_risk,
        tiny_repeated_warning_roles=repeated_tiny,tiny_repeated_warnings_among_six=repeated_among_six,tiny_repeated_P_only_roles=repeated_tiny_P_only,
        V35_S2_nonzero_certifications=c_nonzero,V35_material_reverse_observations=[{k:q[k] for k in ['id','seed','classification','materiality']} for q in c_reverse],decision=decision))
    # Preserve the prior complete paper and mathematical/H/controller sources;
    # update only version, evidence entry points, experiment sections and scope.
    main=(PRIOR/'manuscript.md').read_text(encoding='utf-8')
    main=main.replace('Round130 uniform pair-support paper reading draft, 22 October 2026. R126/R127 results below retain their historical scope.',
        'Round131 frozen S2 benchmark reading draft, 23 October 2026. Section 6.11 is the primary final-version SC benchmark; Sections 6.12-6.13 report separate tiny overhead and V35 scope. Historical observations retain their original versions.')
    abstract=main[main.index('## Abstract'):main.index('## 1. Introduction')]
    first=abstract.split('\n\n')[1]
    main=main.replace(abstract,'## Abstract\n\n'+first+'\n\n'+synopsis+' All ten inputs are already-known constructed problems from two station tables; the three evidence layers are not pooled. The method and full workflow are fixed across sizes. R129 selection and R130 adoption remain settled, while prior same-H/outer-control evidence supports only scoped attribution. There is no final-version V50/V60 claim, universal dominance claim or new single-component causal claim.\n\n')
    old=next(line for line in main.splitlines() if line.startswith('3. It reports actual MS2 evidence'))
    main=main.replace(old,'3. It supplies a frozen E3 S2/P main certification table on all six known SC problems at both Seeds (24 arms), a separate two-input tiny overhead layer (24 arms, three Seeds by two repeats), and two Seed0 V35 scope observations (four arms). R129 selection, R130 attribution and older full-M-B/ENS measurements retain their original protocols and roles; no aggregate cross-layer success rate or average speedup is reported.')
    gateway=next(line for line in main.splitlines() if line.startswith('The current sole method is S2/MS2. Its direct performance'))
    main=main.replace(gateway,'The current sole method is S2/MS2. The principal final-version benchmark is Section 6.11 (A); Sections 6.12 (B) and 6.13 (C) separately report absolute tiny overhead and finite V35 scope. Section 6.9 preserves R129 selection-time evidence and Section 6.10 preserves R130 known-role attribution. Sections 6.1-6.8 retain predecessor/development identities. Old full-M-B/ENS times are never relabelled S2 or mixed into a common final-version clock cohort.')
    main=main.replace('The actual MS2 observations in Section 6.9 and the known-role attribution in Section 6.10 provide current-version evidence.',
        'The complete frozen-version main panel is Section 6.11; tiny overhead and finite V35 scope are reported separately in Sections 6.12 and 6.13. Sections 6.9 and 6.10 retain the earlier selection-time and known-role attribution evidence.')
    main=main.replace('The current direct statements concern the actual MS2 R129 observations and the complete fixed R130 attribution panel, with conditional both-certified time ratios.',
        'The principal final-version statement concerns the complete fixed Round131 A panel; B and C separately delimit tiny overhead and V35 scope. The earlier MS2 R129 selection observations and fixed R130 attribution panel retain their own roles. Time ratios condition on each explicitly both-certified intersection.')
    main=main.replace('Supplement S retains all 32 arms and 48 pairs, all three clocks, the three long endpoints and checkpoint unknowns.',
        'Supplement S retains the historical R122 32 arms and 48 pairs, all three clocks, the three long endpoints and checkpoint unknowns, and adds the separately labelled 52 Round131 arms. The 26 current comparisons are shown in Tables R131.A-C.')
    main=main.replace('### 6.5 Tiny cases, repeated Seeds and absolute delay risk','### 6.5 Historical full-M-B tiny cases, repeated Seeds and absolute delay risk')
    main=main.replace('The Round130 fixed attribution study ends here. Its final report narrows claims to the observed method, version and domain; no further solving, tuning, input or Seed is authorized.',
        'The separately completed Round130 attribution study retains its scoped conclusion. Round131 closes the fixed final-version benchmark gap with the finite A/B/C evidence in Sections 6.11-6.13; this round ends without further solving, tuning, input, Seed or component selection.')
    new_sections='''### 6.11 Primary frozen-S2 certification benchmark (Round131 A)

The algorithm adopted in R130 is fixed. This measures the entire original six-problem SC set at Seeds 0 and 1 with the same frozen E3 S2 and cold P: 24 fresh independently paid arms and twelve matched observations. These are exposed known inputs, not new or unseen validation. No old M-B time is used as an S2 measurement. Each method pays admission, its own H if applicable, modeling, every LP/MIP/Start check and required outputs under one complete deadline. Full argv, native readbacks, physical/source-return-cover checks and three clocks remain in the reproducibility package. Caps are 600 seconds for V15 and 1200 for V20, with the original 30-second reserve and 6/2-second native/hard-stop offsets. Both-open results are UNDETERMINED; unqualified evidence is UNEVALUABLE; unknown certification times stay null.

**Table R131.A. All twelve main S2/P observations.** Time is complete qualified certification time in seconds. Delta and ratio exist only for both-certified pairs; exact authorities and all U/L/three-clock fields are in Supplement S.

'''+tables['A']+'\n'+synopsis+f''' The main conditional P/S2 geometric mean is {fmt(layers['A']['conditional_geometric_mean_P_over_S2'])} on the explicitly listed {layers['A']['both_certified_intersection_n']} both-certified observations only. Materiality describes magnitude, not direction or a method-selection gate. All losses remain in the table.

### 6.12 Absolute final-S2 tiny overhead (Round131 B)

The two original V8/V10 inputs each use three Seeds and two opposite-order repeats, for 24 arms and twelve comparisons under complete 90-second contracts. No free warm-up, shared H/Start/tree or extra Seed is used. The six repeated observations per problem measure absolute overhead and are not weighted into A. A strict subsecond loss is still Lose; the 10-second warning is practical, not a theorem about noise. The legal empty-fleet/structurally easy SM-B10-B remains in the table and does not stand for all small-instance difficulty.

**Table R131.B. All twelve tiny matched observations.** R denotes a full independent repeat at the same Seed. Missing certification times are null in the authority.

'''+tables['B']+f'\nThere are {warning} observed >=10-second delays and {p_risk} P-only certification risks. Two-repeat warning roles: {", ".join(repeated_tiny) or "none"}.\n\n'+tiny_table+'''
The exact per-Seed two-repeat direction/range records and six-observation medians/ranges are in tiny_summary.json. A range is not estimated when fewer than two valid repeats exist.

### 6.13 Finite V35 scope (Round131 C)

Both original R122 V35 roles use their original Q, physical T and complete 2400-second contract, at Seed0 only, with opposite order across the two roles. These are fresh complete final-version runs, not continuations or pooled short-window clocks.

**Table R131.C. Both V35 Seed0 observations.** Both-open means final certification-time ordering is unknown. Endpoint U/L/gap is supplemental and supplies no certification-speed Win.

'''+tables['C']+f'\nFinal S2 has {c_nonzero}/2 nonzero V35 certificates. This '+('extends observed nonzero certification to the named V35 roles only' if c_nonzero else 'does not extend observed nonzero certification to V35')+'''. C has one Seed, and there is no final-version V50/V60 validation. The source and scenario coverage remains finite and coupled: two station tables, constructed inventories/targets/weights, service-station total scenario labels, fixed lambda=.15, compact/regional Euclidean geography, and overlapping station selections. A=6 inputs/12 observations, B=2/12 and C=2/2 remain separate denominators. No new H, C_G or outer-controller causal claim is inferred. The R130 outer-package result and all predecessor negative/open findings are retained.

'''
    main=main.replace('## 7. Extended endpoint evidence and the known long-window proof boundary',new_sections+'## 7. Extended endpoint evidence and the known long-window proof boundary')
    begin=main.index('GI-TBC in its uniform pair-support implementation, MS2 (S2), is the sole proposed method.',main.index('## 9. Conclusion'))
    end=main.index('\n\n',begin)
    main=main[:begin]+'GI-TBC in its uniform pair-support implementation, MS2 (S2), remains the sole proposed method. '+synopsis+' The main SC measurements close a version-to-evidence gap while all unfavorable directions and finite scope limits remain explicit. R130 provides scoped same-H backend support without repeated material outer-package runtime gains. Empirical observations are separate from the ideal representation/coverage propositions and the unchanged floating-point evidence policy. The resulting certification statement is finite and case-dependent on these known inputs; it does not establish population-wide dominance.'+main[end:]
    main=main.replace('[current claim decision](claim_decision.md)','[current benchmark assessment](benchmark_assessment.md)')
    main=main.replace('adds the separately labelled Round129 and Round130 clocks','adds the separately labelled Round129, Round130 and Round131 clocks')
    (OUT/'manuscript.md').write_text(main,encoding='utf-8')
    for n in ['model_appendix.md','algorithm_appendix.md','references.bib','literature_evidence.csv','literature_scope.md','method_spec_matrix.csv']:
        shutil.copyfile(PRIOR/n,OUT/n)
    full=table(['Layer / problem','Seed / repeat','Method','Certified','T_cert','T_produce','T_verify','T_total','U','L','signed U-L'],
        [[a['layer']+' / '+a['id'],f"{a['seed']} / {a['repeat']}",a['method'],a['certificate'],fmt(a['T_cert']),fmt(a['T_produce']),fmt(a['T_verify']),fmt(a['T_total']),f"{a['U']:.6g}",f"{a['L']:.6g}",f"{a['signed_gap']:.3g}"] for a in o['arms']])
    complete=(PRIOR/'tables/complete_results.md').read_text(encoding='utf-8')+'\n\n## S.131 Fixed final-version benchmark\n\n'+assessment+'\n\n**Table R131.S. All 52 formal arms and three clocks.** Display rounded only; CSV/JSON authorities retain full precision and nulls.\n\n'+full
    (OUT/'tables/complete_results.md').write_text(complete,encoding='utf-8')
    display=(PRIOR/'tables/historical_display.md').read_text(encoding='utf-8')+'\n\n## S.131 Final-version full endpoint and clock authority\n\n**Table R131.S. All 52 formal arms and three clocks.** Layer, Seed and repeat preserve denominators. Open certification time is null.\n\n'+full
    (OUT/'tables/historical_display.md').write_text(display,encoding='utf-8')
    write(OUT/'manuscript_lineage.json',dict(parent='results/unified_exact_round130/manuscript.md',parent_SHA=sha(PRIOR/'manuscript.md'),current_SHA=sha(OUT/'manuscript.md'),
        local_changes=['version/date','abstract','contribution','evidence gateway','6.11 A','6.12 B','6.13 C','discussion stop boundary','conclusion','supplement'],
        exact_unchanged_appendix_SHAs={n:sha(OUT/n) for n in ['model_appendix.md','algorithm_appendix.md','references.bib']},
        R125_formula_cuts_H_controller_retained=True,layout_pipeline_reused=True))
    v=read(OUT/'paper_version_manifest.json');v['formal_results_pending']=False;write(OUT/'paper_version_manifest.json',v)
    (OUT/'reproducibility.md').write_text('''# Round131 reproducibility scope

Run scripts/round131_portable_check.py from the supplied recovered root after restoring the current finite carriers. The checker performs read-only fixed-input/argv/physical/model/Start/source-return-cover and arithmetic checks; it never starts Optimize, compiles or falls back to an old checkout. Native PE/DLL and licenses are excluded. Re-running performance requires separately available exact E3/DLL bytes; this round does not rebuild them. The full exact commands are in argv_freeze.json and paper_method_config.json.

The raw signed gaps, Seed0-only historical flags, actual returned settings, producer seals and qualified endpoints stay separate. T_cert is null unless own complete evidence qualifies. No cap is substituted. Empty departure, loaded return, unique nonzero service, inventories/load prefixes and travel plus 120 times cumulative pickup determine physical validity. Objective uses original true Gini and weighted relative deviation, excluding depot. The original numerical policy is unchanged. Zero certificates and absence of backend exposure are reported explicitly.

The primary finite panel is A. B and C have separate roles and denominators. All inputs were exposed before this round; no generator is called. evidence_registry.csv preserves the original round/build/clock/cap/Seed/repeat and role of each cited measurement, without choosing a cross-round best time. Original R130 full attribution and adverse/open predecessor observations remain authoritative in their original files.
''',encoding='utf-8')
    registry()
    print(json.dumps(dict(stage_exit=s['stage_exit'],scientific_assessment=label,synopsis=synopsis)))

def pdf():
    # The existing full-paper export remains the typography engine.
    import round126_export as old
    os.environ['ROUND131_PDF_DEST']=str(OUT/'manuscript.pdf')
    os.environ['ROUND131_PDF_RECEIPT']=str(OUT/'pdf_export.json')
    ns=dict(vars(old),OUT=OUT,TEMP_PARENT=TEMP/'pdf')
    code=inspect.getsource(old.export).replace('date=19 October 2026','date=23 October 2026').replace('ROUND126_PDF_','ROUND131_PDF_')
    exec(compile(code,__file__+'::maintained_export','exec'),ns);ns['export']()

if __name__=='__main__':{'documents':documents,'pdf':pdf}[sys.argv[1]]()

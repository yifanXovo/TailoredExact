"""Certification-first typed comparisons; no solver imports or starts."""
from round127_common import *
import collections,csv,copy,math,statistics
from decimal import Decimal,localcontext
from round127_pipeline import table
import round108_reader as core
from round127_qualify import row_family,compare as model_deletion_check
from compare_round112_startup import reconstruct as H,fleet_key

def qualified(a):return a is not None and all(a.get(k) for k in ['formal_protocol_qualified','numbers_qualified','certificate_qualified']) and not a.get('source_reduced')
def pair(id,left,right,*,kind,seed=1,repeat=None,alias=False):
    a,b=left,right
    out=dict(id=id,panel=kind,seed=seed,repeat=repeat,left=a['method'] if a else 'MB',right=b['method'] if b else 'MD',
        classification='UNEVALUABLE',direction='UNEVALUABLE',left_certified=bool(a and a.get('certificate')),right_certified=bool(b and b.get('certificate')),
        left_T_cert=a.get('T_cert') if a else None,right_T_cert=b.get('T_cert') if b else None,
        left_T_produce=a.get('T_produce') if a else None,right_T_produce=b.get('T_produce') if b else None,
        right_over_left_certification_ratio=None,left_minus_right_seconds=None,legacy_materiality=None,
        alias=alias,independent_comparison=not alias,binary_layer=a.get('binary_layer') if a else b.get('binary_layer') if b else None)
    if not qualified(a) or not qualified(b):return dict(out,basis='missing, blocked, or unqualified evidence; not ordinary censoring')
    assert a['PE_SHA']==b['PE_SHA'] and a['DLL_SHA']==b['DLL_SHA'] and a['input_SHA']==b['input_SHA'] and a['seed']==b['seed']
    ac,bc=bool(a['certificate']),bool(b['certificate'])
    if ac and bc:
        if abs(a['U']-b['U'])>1e-7:return dict(out,basis='certified own physical objectives disagree; investigate')
        dt=a['T_cert']-b['T_cert'];material=max(30,.1*b['T_cert'])
        out.update(classification='BOTH_CERTIFIED',direction='Win' if dt<0 else 'Lose' if dt>0 else 'Tie',
            left_minus_right_seconds=dt,right_over_left_certification_ratio=b['T_cert']/a['T_cert'],
            legacy_materiality='LEFT_MATERIALLY_FASTER' if dt<=-material else 'RIGHT_MATERIALLY_FASTER' if dt>=material else 'TIME_CLOSE')
    elif ac:out.update(classification='LEFT_ONLY_CERTIFIED',direction='Win')
    elif bc:out.update(classification='RIGHT_ONLY_CERTIFIED',direction='Lose')
    else:out.update(classification='BOTH_OPEN',direction='UNDETERMINED')
    return dict(out,basis='qualified complete own certification and unrounded production cost; no cap imputation')
def load_stage(stage):
    out=[]
    for path in sorted((OUT/stage).glob('*/reconstructed.json')):
        out.extend(read(path)['arms'])
    return out
def statistics_pairs(rows):
    independent=[r for r in rows if r['independent_comparison']]
    both=[r for r in independent if r['classification']=='BOTH_CERTIFIED'];ratios=[r['right_over_left_certification_ratio'] for r in both]
    return dict(rows=len(rows),independent_typed_comparisons=len(independent),classes=dict(collections.Counter(r['classification'] for r in independent)),
        directions=dict(collections.Counter(r['direction'] for r in independent)),
        both_certified_intersection_n=len(both),both_certified_ids=[r['id'] for r in both],
        conditional_geometric_mean=math.exp(statistics.fmean(math.log(x) for x in ratios)) if ratios else None,
        denominator_warning='shared arms and builds; no independence, population, or open-run time-to-certification inference')
def root(d):
    calls=[r['payload'] for r in read(d/'observations.json') if r['payload']['kind']=='call' and r['payload']['leaf']=='L0']
    if not calls:return None,None
    c=calls[0];path=core.portable(ROOT,c['model_path']);assert sha(path)==c['model_sha256']
    return core.lp_model(path),c
def explanatory_point(base,deleted,point):
    """Actual serialized rows, exact binary64-point arithmetic; no Optimize."""
    removed=collections.Counter(base['rows'])-collections.Counter(deleted['rows'])
    regular=[];W=[]
    with localcontext() as ctx:
        ctx.prec=80;D=Decimal.from_float
        for (terms,sense,rhs),count in removed.items():
            coefficients=dict(terms);aw=coefficients.pop('W_SP',0.)
            if set(coefficients)-set(point):return dict(status='UNKNOWN_MISSING_ORIGINAL_COLUMNS',missing=sorted(set(coefficients)-set(point)))
            lhs=sum((D(c)*D(point[n]) for n,c in coefficients.items()),Decimal(0));rhs=D(rhs)
            senses=[(lhs,rhs,aw)] if sense=='<=' else [(-lhs,-rhs,-aw)] if sense=='>=' else [(lhs,rhs,aw),(-lhs,-rhs,-aw)]
            for x,b,aW in senses:
                if aW:W.append((D(aW),b-x))
                else:regular.append(dict(residual=float(max(Decimal(0),x-b)),multiplicity=count))
        maximum=max([r['residual'] for r in regular],default=0.)
        result=dict(removed_rows=sum(removed.values()),ordinary_rows_max_residual=maximum,
            ordinary_violated_rows=sum(r['multiplicity'] for r in regular if r['residual']>1e-6),
            ordinary_status='VIOLATED_AT_SAVED_POINT' if maximum>1e-6 else 'NUMERICALLY_UNCERTAIN' if maximum>1e-7 else 'NO_VIOLATION_AT_SAVED_POINT')
        if W:
            lo,hi=map(D,base['bounds']['W_SP']);sources=[]
            for aw,residual in W:
                value=residual/aw
                if aw>0:hi=min(hi,value);sources.append('upper')
                else:lo=max(lo,value);sources.append('lower')
            separation=lo-hi;tolerance=Decimal('0.000001')
            result.update(W_lower=str(lo),W_upper=str(hi),W_empty_exact_serialized_intersection=lo>hi,
                W_status='NO_EXTENSION_AT_SAVED_POINT' if separation>tolerance else 'NUMERICALLY_UNCERTAIN' if separation>0 else 'EXTENSION_INTERVAL_NONEMPTY_AT_SAVED_POINT',
                W_note='Existence checked by eliminating only W with its actual bounds/rows; no arbitrary W assignment. A nonempty interval does not imply global redundancy.')
        return result
def mechanism():
    rows=[];diagnostics=[]
    for path in sorted((OUT/'core').glob('*/identity.json')):
        i=read(path);launches={l['method']:l for l in i['launches']};p=i['launches'][0]['panel'];hs={};models={};calls={}
        for method,l in launches.items():
            d=core.portable(ROOT,l['destination']);r=read(d/'result.json');a=next(a for a in read(path.parent/'reconstructed.json')['arms'] if a['method']==method)
            ledger=core.rows(d/'external/paper_optimize_ledger.csv') if (d/'external/paper_optimize_ledger.csv').exists() else []
            lp_status=core.rows(d/'external/lp_status_ledger.csv') if (d/'external/lp_status_ledger.csv').exists() else []
            root_status=next((q for q in lp_status if q['leaf_id']=='L0'),None)
            m,c=root(d) if method!='P' and method!='PT' else (core.lp_model(d/'compact.lp'),None)
            models[method]=m;calls[method]=c
            if method not in ['P','PT']:hs[method]=H(ROOT,p,d)
            families=collections.Counter()
            if m:
                for rr in m['rows']:
                    fam=row_family(rr)
                    if fam.startswith(('cover_','conditional_')):
                        terms=dict(rr[0]);vehicles={n.split('_')[1] for n in terms if n.startswith(('p_','z_'))}
                        if len(vehicles)==1:families[fam]+=1
                    elif fam=='ordered_supply':families[fam]+=1
            h=hs.get(method);ind=read(d/'independent_evidence.json')
            best=[w for w in ind.get('witnesses',[]) if abs(w['F']-a['U'])<=1e-7 and 'available' in w]
            LP=sum(float(q['solver_runtime']) for q in ledger if q['solve_kind']=='LP');MIP=sum(float(q['solver_runtime']) for q in ledger if q['solve_kind']!='LP')
            rows.append(dict(id=p['id'],method=method,binary_layer='E1',H_complete=h['complete'] if h else None,
                initial_own_U=h['physical']['F'] if h else None,
                initial_fleet_SHA=hashlib.sha256(json.dumps(h['fleet'],sort_keys=True).encode()).hexdigest() if h else None,
                root_rows=len(m['rows']) if m else 0,root_columns=len(m['order']) if m else 0,
                root_nonzeros=sum(len(q[0]) for q in m['rows']) if m else 0,
                target_row_families=dict(families),root_LP_bound=float(root_status['lower_bound']) if root_status and root_status['bound_available']=='1' else None,
                root_LP_native_seconds=float(ledger[0]['solver_runtime']) if ledger and ledger[0]['solve_kind']=='LP' else None,
                actual_native_calls=a['native_Optimize'],native_nodes=sum(float(q['nodes']) for q in ledger) if ledger else r.get('gurobi_node_count'),
                LP_native_seconds=LP,MIP_native_seconds=MIP,H_plus_admission_seconds=r.get('process_elapsed_at_exact_phase_start_seconds') if h else 0,
                split_count=r.get('external_gini_tree_split_count'),partial_target_calls=r.get('external_gini_tree_partial_mip_optimize_count'),
                target_reached_events=r.get('external_gini_tree_partial_mip_target_reached_count'),
                best_own_witness_first_logged_available=min(w['available'] for w in best) if best else None,
                witness_time_scope='first retained physical witness matching final own U; logged availability, not exact native discovery time',
                root_cutoff=c['cutoff'] if c else None,certificate=a['certificate'],T_cert=a['T_cert'],
                point_status=read(d/'external/round127_root_lp_status.json') if (d/'external/round127_root_lp_status.json').exists() else 'unknown/no optimal root LP point',
                root_LP_bound_source='actual L0 LP status/optimize ledger; no extra diagnostic solve' if root_status else 'unknown/no original root LP'))
        for method in ['MR','MG','MS2']:
            if method not in launches:continue
            d=core.portable(ROOT,launches[method]['destination']);status=d/'external/round127_root_lp_status.json';point_path=d/'external/round127_root_lp.csv'
            matched=hs['MB']['complete'] and hs[method]['complete'] and hs['MB']['fleet']==hs[method]['fleet'] and calls['MB'] and calls[method] and all(calls['MB'][k]==calls[method][k] for k in ['cutoff','lower_g','upper_g'])
            record=dict(id=p['id'],method=method,matched_complete_H_and_scope=bool(matched),extra_Optimize=0,
                scope='explanatory actual saved root point only; not a certification/performance proof')
            if matched:
                check=model_deletion_check(core.portable(ROOT,calls['MB']['model_path']),core.portable(ROOT,calls[method]['model_path']),method.lower(),p['V'],p['M'])
                record['actual_formal_root_deletion_check']=check
                for item in rows:
                    if item['id']==p['id'] and item['method']==method:item['removed_target_families_vs_MB']=check['families']
                if method=='MG':
                    for item in rows:
                        if item['id']==p['id'] and item['method']=='MB':item['target_row_families'].update(check['families'])
                mb=next(q for q in rows if q['id']==p['id'] and q['method']=='MB');weak=next(q for q in rows if q['id']==p['id'] and q['method']==method)
                if mb['root_LP_bound'] is not None and weak['root_LP_bound'] is not None:
                    record['deleted_minus_full_root_LP_bound']=weak['root_LP_bound']-mb['root_LP_bound']
                    record['LP_deletion_monotonic_within_1e6']=weak['root_LP_bound']<=mb['root_LP_bound']+1e-6
                    assert record['LP_deletion_monotonic_within_1e6'],('investigate LP/domain discrepancy',record)
            if not matched or not status.exists() or not read(status).get('complete'):
                diagnostics.append(dict(record,status='UNKNOWN_MISSING_POINT_OR_INCONSISTENT_DOMAIN'));continue
            with point_path.open(newline='') as f:point={r['name']:float(r['value']) for r in csv.DictReader(f)}
            assert set(point)==set(models[method]['order'])
            diagnostics.append(dict(record,**explanatory_point(models['MB'],models[method],point)))
    table(OUT/'mechanism_costs.csv',rows);write(OUT/'root_LP_deleted_row_explanations.json',diagnostics)
    return rows,diagnostics
def analyze():
    main,tiny,corearms=map(load_stage,['main','tiny','core']);manifest=read(OUT/'experiment_manifest.json');sel=read(OUT/'tuning_selection.json')
    mp=[];tp=[];cp=[]
    for p in manifest['E0_main']:
        by={a['method']:a for a in main if a['id']==p['id']}
        mp.append(pair(p['id'],by.get('MB'),by.get('P'),kind='E0_main'))
    tiny_stats=[]
    for g in manifest['E0_tiny']:
        id=g['role']['id'];by={a['method']:a for a in tiny if a['id']==id and a['seed']==g['seed'] and a['repeat']==g['repeat']}
        row=pair(id,by.get('MB'),by.get('P'),kind='E0_tiny',seed=g['seed'],repeat=g['repeat'])
        row['dt_ge_10_warning']=row['left_minus_right_seconds']>=10 if row['classification']=='BOTH_CERTIFIED' else None
        row['P_only_risk']=row['classification']=='RIGHT_ONLY_CERTIFIED';tp.append(row)
    for id in dict.fromkeys(r['id'] for r in tp):
        rr=[r for r in tp if r['id']==id];both=[r for r in rr if r['classification']=='BOTH_CERTIFIED'];warn=[r for r in both if r['dt_ge_10_warning']]
        tiny_stats.append(dict(id=id,problem_count=1,observations=6,both_certified_pairs=len(both),median_dt=statistics.median(r['left_minus_right_seconds'] for r in both) if both else None,
            median_scope='all six pairs' if len(both)==6 else 'explicit both-certified subset only',
            P_only_count=sum(r['P_only_risk'] for r in rr),dt_ge10_count=len(warn),at_least_one_ge10=bool(warn),repeated_ge10=len(warn)>=2,
            typical_median_ge10=statistics.median(r['left_minus_right_seconds'] for r in both)>=10 if len(both)==6 else None,
            by_seed={s:[r['left_minus_right_seconds'] for r in rr if r['seed']==s] for s in range(3)},not_statistical_significance=True))
    for g in manifest['E1_core']:
        id=g['role']['id'];by={a['method']:a for a in corearms if a['id']==id}
        if sel['selected']['id']=='q0':by['PT']=dict(by['P'],method='PT',alias_of='P',independent_observation=False)
        for left,right in g['prespecified_pairs']:
            row=pair(id,by.get(left),by.get(right),kind='E1_core',alias=sel['selected']['id']=='q0' and 'PT' in [left,right])
            row.update(left=left,right=right)
            if right=='MD':row.update(basis='BLOCKED_BEFORE_FORMAL: inclusive-root/U0-Start obligation incompatible with retained equality closure',direction='UNEVALUABLE',classification='UNEVALUABLE')
            if sel['selected']['id']=='q0' and [left,right]==['PT','P']:
                row.update(classification='ALIAS_SAME_METHOD',direction='NOT_INDEPENDENT',right_over_left_certification_ratio=None,left_minus_right_seconds=None,basis='PT points to P; no independent observation')
            cp.append(row)
    for name,rows in [('main_arms',main),('tiny_arms',tiny),('core_arms',corearms),('main_pairs',mp),('tiny_pairs',tp),('core_pairs',cp),('tiny_statistics',tiny_stats)]:table(OUT/(name+'.csv'),rows)
    old={r['id']:r for r in read(ROOT/'results/unified_exact_round126/certification_summary.json').get('physical_optima',[])}
    with (ROOT/'results/unified_exact_round126/arms.csv').open(newline='',encoding='utf-8-sig') as f:oldarms=list(csv.DictReader(f))
    transitions=[]
    for p in mp:
        aa={r['arm']:r for r in oldarms if r['id']==p['id']}
        def converted(a,method):
            return dict(method=method,certificate=a['certificate']=='True',formal_protocol_qualified=a['formal_protocol_qualified']=='True',numbers_qualified=a['numbers_qualified']=='True',certificate_qualified=a['certificate_qualified']=='True',source_reduced=a.get('source_reduced')=='True',
                PE_SHA=a['PE_SHA'],DLL_SHA=a['DLL_SHA'],input_SHA=a.get('input_SHA',a.get('input_identity')),seed=0,U=float(a['U']),T_cert=float(a['T_cert']) if a['T_cert'] else None,T_produce=float(a['T_produce']),binary_layer='E0')
        prior=pair(p['id'],converted(aa['M-B'],'MB'),converted(aa['P-GRB'],'P'),kind='R126_E0_seed0',seed=0)
        transitions.append(dict(id=p['id'],Seed0_category=prior['classification'],Seed0_direction_new_symmetric_rule=prior['direction'],Seed1_category=p['classification'],Seed1_direction=p['direction'],same_problem_not_two=True,historical_materiality_labels_unchanged=True))
    table(OUT/'seed_transitions.csv',transitions)
    mechanisms,explanations=mechanism()
    summary=dict(execution='PARTIAL',reason='Three MD formal arms blocked by mandatory mathematical qualification; all other fixed positions retained',
        scientific_judgment='FOUNDATIONAL_ISSUE_REQUIRES_DECISION',foundation_scope='MD inclusive-root/own-U0-Start specification versus retained documented no-strict-improver closure; no blanket revocation of frozen MB proof policy',
        main=statistics_pairs(mp),tiny=statistics_pairs(tp),core_by_comparison={f'{a}/{b}':statistics_pairs([r for r in cp if r['left']==a and r['right']==b]) for a,b in manifest['E1_core'][0]['prespecified_pairs']},
        tiny_risks=tiny_stats,tuning_selected=sel['selected'],training_status=sel['status'],
        observed_formal_arms=len(main)+len(tiny)+len(corearms),main_observed=len(main),tiny_observed=len(tiny),core_observed=len(corearms),
        blocked_core_arms=3,PT_aliases=3 if sel['selected']['id']=='q0' else 0,distinct_evaluation_inputs=9,distinct_training_inputs=3,
        per_layer_certifications={stage:{m:sum(bool(a.get('certificate')) for a in arms if a['method']==m) for m in dict.fromkeys(a['method'] for a in arms)} for stage,arms in [('E0_main',main),('E0_tiny',tiny),('E1_core',corearms)]},
        all_observed_arms_qualified=all(qualified(a) for a in main+tiny+corearms),fees=budget(),
        next_priority='Resolve the single MD equality-closure versus inclusive-root specification issue with substantive user review; execute no new algorithm or experiment')
    expected_core=18-(3 if sel['selected']['id']=='q0' else 0)
    assert (len(main),len(tiny),len(corearms))==(12,24,expected_core),'fixed formal positions incomplete; do not write final report yet'
    summary['mechanism_axis']={}
    for comparison in ['MB/MD','MB/MR','MB/MG','MB/MS2']:
        pp=summary['core_by_comparison'][comparison];directions=pp['directions']
        label='BLOCKED_BEFORE_FORMAL' if comparison=='MB/MD' else 'MIXED_OBSERVED_DIRECTIONS' if directions.get('Win') and directions.get('Lose') else 'REVERSE_CERTIFICATION_OBSERVATIONS' if directions.get('Lose') else 'DIRECT_CERTIFICATION_INCREMENT_IN_THIS_PANEL' if directions.get('Win') else 'ONLY_OPEN_OR_UNEXPOSED_INFORMATION'
        summary['mechanism_axis'][comparison]=dict(label=label,classes=pp['classes'],directions=directions,scope='three known roles, one Seed, shared MB arms; no universal necessity or MIP monotonicity claim')
    write(OUT/'stratified_summary.json',summary);return summary
if __name__=='__main__':print(json.dumps(analyze()))

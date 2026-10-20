"""Finite, solver-free recovery checks. Never imports a native solver API.

Checks every training/evaluation sealed endpoint/clock and recomputes the bounded
selection and typed comparisons. Representative physical/model audits remain
separately identified; this is not an exact rational audit of every matrix.
"""
from pathlib import Path
import ast,collections,csv,hashlib,json,math,statistics,time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round127'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def portable(value):
    value=str(value).replace('\\','/')
    for prefix in ['results/','reference/','scripts/','src/','include/']:
        where=value.find('/'+prefix)
        if where>=0:return ROOT/value[where+1:]
    p=Path(value)
    return p if p.is_absolute() else ROOT/p
def rows(p):
    with Path(p).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def qualified(a):return all(a.get(k) for k in ['formal_protocol_qualified','numbers_qualified','certificate_qualified']) and not a.get('source_reduced')
def same(x,y,tol=1e-8):assert abs(x-y)<=tol,(x,y)

def pair(a,b):
    if a is None or b is None or not qualified(a) or not qualified(b):return 'UNEVALUABLE','UNEVALUABLE',None,None
    assert a['PE_SHA']==b['PE_SHA'] and a['DLL_SHA']==b['DLL_SHA'] and a['input_SHA']==b['input_SHA'] and a['seed']==b['seed']
    if a['certificate'] and b['certificate']:
        same(a['U'],b['U'],1e-7);dt=a['T_cert']-b['T_cert']
        return 'BOTH_CERTIFIED','Win' if dt<0 else 'Lose' if dt>0 else 'Tie',dt,b['T_cert']/a['T_cert']
    if a['certificate']:return 'LEFT_ONLY_CERTIFIED','Win',None,None
    if b['certificate']:return 'RIGHT_ONLY_CERTIFIED','Lose',None,None
    return 'BOTH_OPEN','UNDETERMINED',None,None

def check():
    tick=time.perf_counter();manifest=read(OUT/'experiment_manifest.json');inputs=read(OUT/'input_manifest.json')
    for p in inputs['main_roles']+inputs['tiny_roles']+inputs['training_roles']+inputs['core_roles']:
        assert sha(ROOT/p['input_path'])==p['input_sha256']
    for n,h in read(OUT/'tiny_recipe.json')['dependencies'].items():assert sha(ROOT/n)==h
    e1_sources=read(OUT/'E1_frozen.json')['source_bindings'];e0_sources=read(OUT/'E0_identity.json')['source_bindings']
    for n,h in e1_sources.items():assert sha(ROOT/n)==h
    for n,h in e0_sources.items():
        p=ROOT/n
        if sha(p)!=h:p=OUT/'source_E0'/n
        assert sha(p)==h
    for n,binding in read(OUT/'manuscript_lineage.json')['appendices'].items():assert sha(OUT/n)==binding['parent_SHA']==binding['active_SHA']
    allarms={};seals=0;model_hashes=0;selection=read(OUT/'tuning_selection.json');training=[];training_keys=[];cold_models={}
    for stage in ['training','main','tiny','core']:
        allarms[stage]=[]
        for path in sorted((OUT/stage).glob('*/identity.json')):
            identity=read(path);arms=read(path.parent/'reconstructed.json')['arms']
            assert len(identity['launches'])==len(arms)
            for l,a in zip(identity['launches'],arms):
                d=portable(l['destination']);assert d==portable(a['destination'])
                seal=read(d/'producer_seal.json');producer=read(d/'producer_receipt.json');total=read(d/'arm_total_receipt.json')
                assert producer['producer_seal_SHA']==sha(d/'producer_seal.json')
                assert seal['native_stopped_no_reentry'] and seal['required_outputs_closed']
                for name,h in seal['required_SHA'].items():assert sha(d/name)==h,(d,name)
                same(a['T_produce'],producer['t_produce_perf']-producer['t0_perf'])
                same(a['T_verify'],total['t_verified_perf']-producer['t_produce_perf'])
                same(a['T_total'],a['T_produce']+a['T_verify'])
                assert a['T_cert']==(a['T_produce'] if a['certificate'] and a['formal_protocol_qualified'] else None)
                endpoint=read(d/'audit.json')['endpoint'];assert endpoint['certificate']==a['certificate']
                same(endpoint['U'],a['U'],1e-7);same(endpoint['L'],a['L'],1e-7);same(a['gap'],a['U']-a['L'],1e-15)
                if a['certificate'] and not a['own_exact_zero']:assert -1e-7<=a['gap']<=1e-7
                assert a['PE_SHA']==identity['candidate_binary_sha256'] and a['DLL_SHA']==manifest['DLL_SHA']
                assert a['binary_layer']==('E0' if stage in ['main','tiny'] else 'E1')
                if stage!='training':assert a['T_produce']<=l['cap_seconds']
                if a['binary_layer']=='E1' and l['method'] in ['P','PT']:
                    parameters=read(d/'round127_parameters.json');wanted=l['configuration']
                    assert (parameters['MIPFocus'],parameters['Cuts'],parameters['NumStart_before_optimize'])==(wanted['MIPFocus'],wanted['Cuts'],0)
                    assert parameters['loaded_after_presets'] and parameters['authoritative_model_environment']
                    cold_models.setdefault((stage,a['input_SHA']),set()).add(sha(d/'compact.lp'))
                    if l['method']=='PT':assert wanted['id']==selection['selected']['id']
                for observation in read(d/'observations.json'):
                    call=observation['payload']
                    if call['kind']=='call':assert sha(portable(call['model_path']))==call['model_sha256'];model_hashes+=1
                if stage=='training':
                    clock=read(path.parent/'complete_training_clock.json');fee=OUT/'fees'/path.parent.relative_to(OUT).as_posix().replace('/','_')
                    marker=read(fee/'PID.json')['launched_unix'];full=producer['t_produce_unix']-marker
                    same(clock['T_produce'],full);same(clock['T_verify'],a['T_verify']);same(clock['T_total'],full+a['T_verify'])
                    assert clock['producer_receipt_SHA']==sha(d/'producer_receipt.json') and clock['marker_receipt_SHA']==sha(fee/'PID.json')
                    assert clock['all_gates_qualified']==bool(qualified(a) and full<=l['cap_seconds'])
                    assert clock['T_cert']==(full if clock['all_gates_qualified'] and a['certificate'] else None)
                    p=read(d/'round127_parameters.json');q=l['configuration']
                    assert (p['MIPFocus'],p['Cuts'],p['NumStart_before_optimize'])==(q['MIPFocus'],q['Cuts'],0)
                    training_keys.append((a['id'],a['seed'],q['id']))
                    training.append(dict(config=q['id'],seed=a['seed'],certificate=a['certificate'],qualified=clock['all_gates_qualified'],q_score=full/l['cap_seconds'] if a['certificate'] and clock['all_gates_qualified'] else 1 if clock['all_gates_qualified'] else None))
                seals+=1;allarms[stage].append(a)
    assert len(training)==36
    expected_training=[(p['role']['id'],p['seed'],p['configuration']['id']) for p in manifest['E1_training']]
    assert training_keys==expected_training and len(set(training_keys))==36
    for q in manifest['configurations']:
        assert [(p['role']['id'],p['seed']) for p in manifest['E1_training'] if p['configuration']==q]==[(p['id'],s) for p in inputs['training_roles'] for s in [2,3]]
    scores=[]
    for q in manifest['configurations']:
        rr=[r for r in training if r['config']==q['id']];assert len(rr)==6
        seedN={str(s):sum(r['certificate'] and r['qualified'] for r in rr if r['seed']==s) for s in [2,3]}
        scores.append(dict(q,complete_qualified=all(r['qualified'] for r in rr),N=sum(r['certificate'] and r['qualified'] for r in rr),N_by_seed=seedN,N_min=min(seedN.values()),S_q=sum(r['q_score'] for r in rr)/6 if all(r['qualified'] for r in rr) else None))
    assert scores==selection['scores'];q0=scores[0];assert q0['complete_qualified']
    eligible=[q for q in scores[1:] if q['complete_qualified'] and q['N']>=q0['N'] and q['N_min']>=q0['N_min'] and (q['N']>q0['N'] or q['N']==q0['N']>0 and q['S_q']<q0['S_q'] and q['S_q']<=.9*q0['S_q'])]
    selected=min(eligible,key=lambda q:(-q['N'],-q['N_min'],q['S_q'],q['nondefault_parameters'],int(q['id'][1:]))) if eligible else q0
    assert selected==selection['selected'] and sha(OUT/'selected_P.prm')==selection['selected_prm_SHA']
    assert sha(OUT/'tuning_manifest'/(selected['id']+'.prm'))==selection['selected_prm_SHA']
    assert all(len(values)==1 for values in cold_models.values()),'cold configurations changed actual compact model bytes'
    assert selection['evaluation_results_consulted']==0
    pair_counts={};warnings={};pair_records={}
    for stage in ['main','tiny','core']:
        published=rows(OUT/(stage+'_pairs.csv'));rebuilt=[]
        expected=[(p['id'],1,None,'MB','P') for p in manifest['E0_main']] if stage=='main' else [(g['role']['id'],g['seed'],g['repeat'],'MB','P') for g in manifest['E0_tiny']] if stage=='tiny' else [(g['role']['id'],1,None,a,b) for g in manifest['E1_core'] for a,b in g['prespecified_pairs']]
        keys=[(r['id'],int(r['seed']),int(r['repeat']) if r['repeat'] else None,r['left'],r['right']) for r in published]
        assert keys==expected and len(set(keys))==len(expected)
        for row in published:
            aa=[a for a in allarms[stage] if a['id']==row['id'] and a['seed']==int(row['seed']) and (not row['repeat'] or a['repeat']==int(row['repeat']))]
            by={a['method']:a for a in aa};alias=stage=='core' and selected['id']=='q0' and 'PT' in [row['left'],row['right']]
            if alias:by['PT']=dict(by['P'],method='PT')
            actual=pair(by.get(row['left']),by.get(row['right']))
            if row['right']=='MD':actual=('UNEVALUABLE','UNEVALUABLE',None,None)
            if alias and row['left']=='PT':actual=('ALIAS_SAME_METHOD','NOT_INDEPENDENT',None,None)
            assert actual[:2]==(row['classification'],row['direction']),(row,actual)
            for key,value in zip(['left_minus_right_seconds','right_over_left_certification_ratio'],actual[2:]):
                assert (float(row[key]) if row[key] else None)==value
            assert (row['nonalias_entry']=='True')==(not alias)
            if stage=='tiny':
                warning=actual[2]>=10 if actual[0]=='BOTH_CERTIFIED' else None
                assert row['dt_ge_10_warning']==('' if warning is None else str(warning))
                warnings.setdefault(row['id'],[]).append(warning)
            rebuilt.append(actual[0])
        pair_counts[stage]=dict(collections.Counter(rebuilt))
        pair_records[stage]=published
    assert len(allarms['main'])==12 and len(allarms['tiny'])==24
    assert len(allarms['core'])==18-(3 if selected['id']=='q0' else 0)
    assert len(read(OUT/'blocked_core_arms.json'))==3
    aliases=read(OUT/'PT_aliases.json');assert len(aliases)==(3 if selected['id']=='q0' else 0)
    for alias in aliases:
        assert alias['target_method']=='P' and portable(alias['target_destination']).is_dir()
        targets=[a for a in allarms['core'] if a['id']==alias['id'] and a['method']=='P'];assert len(targets)==1
        assert portable(targets[0]['destination'])==portable(alias['target_destination'])
        assert sha(portable(alias['target_destination']).parents[1]/'reconstructed.json')==alias['target_result_SHA']
    summary=read(OUT/'stratified_summary.json');assert summary['distinct_evaluation_inputs']==9 and summary['distinct_training_inputs']==3
    assert summary['observed_formal_arms']==sum(len(allarms[s]) for s in ['main','tiny','core'])
    assert len({a['input_SHA'] for s in ['main','tiny','core'] for a in allarms[s]})==9
    def summary_check(published,reported):
        nonalias=[r for r in published if r['nonalias_entry']=='True'];both=[r for r in nonalias if r['classification']=='BOTH_CERTIFIED']
        assert reported['rows']==len(published) and reported['nonalias_typed_entries']==len(nonalias)
        assert reported['evaluable_nonalias_entries']==sum(r['classification']!='UNEVALUABLE' for r in nonalias)
        assert reported['unevaluable_nonalias_entries']==sum(r['classification']=='UNEVALUABLE' for r in nonalias)
        assert reported['alias_entries']==len(published)-len(nonalias)
        assert reported['classes']==dict(collections.Counter(r['classification'] for r in nonalias))
        assert reported['directions']==dict(collections.Counter(r['direction'] for r in nonalias))
        assert reported['both_certified_intersection_n']==len(both) and reported['both_certified_ids']==[r['id'] for r in both]
        gm=math.exp(statistics.fmean(math.log(float(r['right_over_left_certification_ratio'])) for r in both)) if both else None
        assert reported['conditional_geometric_mean']==gm
    for stage in ['main','tiny']:summary_check(pair_records[stage],summary[stage])
    for key,reported in summary['core_by_comparison'].items():
        a,b=key.split('/');summary_check([r for r in pair_records['core'] if r['left']==a and r['right']==b],reported)
    for item in summary['tiny_risks']:
        rr=[r for r in pair_records['tiny'] if r['id']==item['id']];both=[r for r in rr if r['classification']=='BOTH_CERTIFIED'];dts=[float(r['left_minus_right_seconds']) for r in both]
        assert len(rr)==item['observations']==6 and item['both_certified_pairs']==len(both)
        assert item['median_dt']==(statistics.median(dts) if both else None)
        assert item['median_scope']==('all six pairs' if len(both)==6 else 'explicit both-certified subset only')
        count=sum(dt>=10 for dt in dts)
        assert (item['dt_ge10_count'],item['at_least_one_ge10'],item['repeated_ge10'])==(count,count>0,count>=2)
        assert item['typical_median_ge10']==(statistics.median(dts)>=10 if len(both)==6 else None)
        assert item['P_only_count']==sum(r['classification']=='RIGHT_ONLY_CERTIFIED' for r in rr)
        assert item['by_seed']=={str(s):[float(r['left_minus_right_seconds']) if r['left_minus_right_seconds'] else None for r in rr if int(r['seed'])==s] for s in range(3)}
    return dict(status='PASS',producer_seals_verified=seals,actual_call_model_hashes_verified=model_hashes,
        training_positions=36,selection_recomputed=selected,pair_classes=pair_counts,tiny_threshold_flags=warnings,source_bindings_verified=dict(E0=len(e0_sources),E1=len(e1_sources)),
        formal_arms=summary['observed_formal_arms'],blocked_MD=3,aliases=len(aliases),cold_model_groups_with_identical_bytes=len(cold_models),
        native_starts=0,Optimize=0,production_compilations=0,seconds=time.perf_counter()-tick,
        scope='Every training/evaluation sealed endpoint/clock, actual model bytes, independent finite selection/pair/alias arithmetic. Physical and matrix qualification are separately documented finite checks; no new optimization or universal rational proof.')
if __name__=='__main__':
    receipt=check();(ROOT/'portable_check_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))

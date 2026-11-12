"""Post-panel physical/identity readback and within-input Seed comparisons.

This module is analysis only: it imports no Gurobi binding and launches no
producer, restricted MIP, route oracle or old campaign.
"""
from round164_common import *
import collections,csv,io,math,statistics,zipfile

TOL=1e-7

def rows(path):
    if not path.exists():return []
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def csv_write(path,records,fields=None):
    if not records:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields or list(records[0]),extrasaction='ignore')
        writer.writeheader();writer.writerows(records)

def fee_label(position):
    dispositions=read(OUT/'execution_dispositions.json') if (OUT/'execution_dispositions.json').exists() else {}
    return dispositions.get('qualified_fee_by_position',{}).get(str(position),f'arm_{position:03}')

def collect(group):
    from round108_reader import full_fleet
    from round164_campaign import seed_readback
    launch=group['launch'];d=Path(launch['destination']);method=group['arm']['method'];seed=group['arm']['gurobi_seed']
    a=read(d/'round164_endpoint.json');result=read(d/'result.json');close=read(d/'verification_closeout.json')
    fee=read(OUT/'fees'/fee_label(group['position'])/'receipt.json');clock=read(d/'arm_total_receipt.json')
    assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
    assert all(a[k] and close[k] for k in ['implementation_qualified','evidence_complete','performance_eligible'])
    physical=full_fleet(ROOT,launch['panel'],result);assert abs(physical['F']-a['U'])<=TOL
    assert a['PE_SHA']==PE_SHA and a['DLL_SHA']==DLL_SHA and a['input_SHA']==launch['panel']['input_sha256']
    assert a['seed']==seed and seed_readback(launch)['expected_seed']==seed
    trailer=fee['end_unix']-clock['t_verified_unix'];assert trailer>=0
    a=dict(a,position=group['position'],method=method,gurobi_seed=seed,repeat=1,
        # Distinguish the producer's raw reported search endpoint from the
        # original qualified-reader search endpoint. B uses no E+ floor.
        raw_search_L=result['lower_bound'],qualified_search_L=a['L'],final_proof_L=a['L'],
        raw_search_field='result.json.lower_bound',qualified_search_field='original post-seal reader endpoint',
        inherited_T_verify=a['T_verify'],inherited_T_total=a['T_total'],reader_trailer_seconds=trailer,
        T_verify=a['T_verify']+trailer,T_total=a['T_total']+trailer,scientific_outer_seconds=fee['outer_seconds'],
        state='CERT' if a['certificate'] else 'OPEN',physical_G=physical['G'],physical_P=physical['P'],
        physical_weighted_penalty=launch['panel']['lambda']*physical['P'],
        H_seconds=result.get('incumbent_generation_time_seconds',0) if method=='B' else 0,
        H_decoder_seconds=result.get('hga_wall_time_seconds',0) if method=='B' else 0,H_seed=20260626 if method=='B' else None,
        raw_legacy_formal_performance=a.get('formal_performance'),Round164_formal_frozen_panel=True,
        mathematical_input_id=launch['id'],exposed=True,panel_kind='R163 cohort finite solver-seed confirmation',
        historical=False,study_round=164,fee_label=fee_label(group['position']),source_commit=None,
        no_cross_seed_endpoint_composition=True)
    assert abs(a['T_total']-a['T_produce']-a['T_verify'])<1e-6
    assert (a['T_cert'] is not None)==bool(a['certificate'])
    observations=read(d/'observations.json');calls=[o['payload'] for o in observations if o['payload']['kind']=='call']
    if method=='P':
        parameters=read(d/'round127_parameters.json')
        assert parameters==dict(MIPFocus=0,Cuts=-1,NumStart_before_optimize=0,
            loaded_after_presets=True,authoritative_model_environment=True)
        a['cold_NumStart_before_optimize']=0;assert not a.get('H_complete',False)
    optimize=rows(d/'external/paper_optimize_ledger.csv')
    a.update(Native_Work=result['gurobi_work'] if method=='P' else result['external_gini_tree_work'],
        Native_nodes=result['gurobi_node_count'] if method=='P' else result['external_gini_tree_nodes'],
        Native_Runtime=sum(float(v['solver_runtime']) for v in optimize) if optimize else result.get('gurobi_runtime',0.),
        Native_ledger_reported_Work_sum=sum(float(v['work']) for v in optimize) if optimize else None,
        Native_ledger_reported_nodes_sum=sum(float(v['nodes']) for v in optimize) if optimize else None,
        Native_calls=len(calls),Native_diagnostic_policy='inherited result counters; individual Optimize ledger retained, never added to paid wall time',
        failed_or_rejected_sources=len(read(d/'audit.json').get('source_rejections',[])),
        signed_gap=a['U']-a['L'],original_relative_gap=a['relative_gap'])
    a['source_links']=dict(endpoint=(d/'round164_endpoint.json').relative_to(ROOT).as_posix(),
        physical_evidence=(d/'independent_evidence.json').relative_to(ROOT).as_posix(),
        fee=(OUT/'fees'/fee_label(group['position'])/'receipt.json').relative_to(ROOT).as_posix())
    return a

class History:
    def __init__(self):
        self.path=ROOT/'results/unified_exact_round163/artifacts/new_evidence_01.zip'
        assert sha(self.path)=='365d892c8d3593ddcf8c98f88fa220d96f7afb889b0b6f47ba86f09006aa3512'
        self.zip=zipfile.ZipFile(self.path);self.access=[]
    def read(self,member):
        info=self.zip.getinfo(member);assert info.file_size<15000000,('bounded historical member',member,info.file_size)
        raw=self.zip.read(member)
        self.access.append(dict(commit=R163_SCIENCE,archive=self.path.relative_to(ROOT).as_posix(),
            member=member,SHA256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
        return json.loads(raw)
    def close(self):
        self.zip.close();write(OUT/'historical_member_access.json',dict(UTC=utc(),
            accesses=self.access,full_archive_expanded=False,old_producers_or_Optimize=0))

def history_arms(history,new_arms):
    from round108_reader import full_fleet
    old=read(ROOT/'results/unified_exact_round163/reports/complete_arms.json')
    matrix=read(ROOT/'results/unified_exact_round163/matrix_frozen.json')
    science=read(ROOT/'results/unified_exact_round163/science_identity.json')
    assert science['PASS'] and science['measured_CPP_commit']==MEASURED_CPP
    assert science['measured_PE_SHA256']==PE_SHA and science['DLL_SHA256']==DLL_SHA
    assert sha(INPUT_MANIFEST)==INPUT_MANIFEST_SHA
    new_by={(a['id'],a['method'],a['seed']):a for a in new_arms}
    result=[];facts=[]
    for group in matrix['groups']:
        launch=group['launch'];method=launch['R163_method']
        if method not in ('B','P'):continue
        a=next(v for v in old if v['id']==launch['id'] and v['method']==method)
        assert a['performance_eligible'] and a['implementation_qualified'] and a['evidence_complete']
        assert a['PE_SHA']==PE_SHA and a['DLL_SHA']==DLL_SHA and a['seed']==0
        member=f"results/unified_exact_round163/{group['group']}/raw/{launch['arm_id']}"
        raw=history.read(member+'/result.json');observations=history.read(member+'/observations.json')
        physical=full_fleet(ROOT,launch['panel'],raw);assert abs(physical['F']-a['U'])<=TOL
        calls=[o['payload'] for o in observations if o['payload']['kind']=='call']
        assert calls and all(c['settings']['Seed']==0 and c['settings']['expected']['Seed']==0 for c in calls)
        comparisons=[]
        for seed in (1,2):
            other=new_by[(a['id'],method,seed)]
            assert other['input_SHA']==a['input_SHA']
            fresh=next(g['launch'] for g in read(OUT/'matrix_frozen.json')['groups']
                if g['launch']['id']==a['id'] and g['launch']['R164_method']==method and g['launch']['seed']==seed)
            assert all(fresh['panel'][k]==launch['panel'][k] for k in
                ['input_path','input_sha256','lambda','T_seconds','pickup_seconds','drop_seconds','Q_vector','cap_seconds'])
            oldc=launch['command'];newc=fresh['command']
            for flag in ['--process-shutdown-margin','--threads','--mip-threads','--gurobi-presolve',
                '--method','--round127-mode','--time-limit','--process-wall-time-limit']:
                assert oldc[oldc.index(flag)+1]==newc[newc.index(flag)+1]
            comparisons.append(seed)
        result.append(dict(a,historical=True,study_round=163,source_commit=R163_SCIENCE,
            gurobi_seed=0,repeat=1,raw_search_L=raw['lower_bound'],qualified_search_L=a['L'],
            final_proof_L=a['L'],source_archive_prefix=member,
            exposed=True,panel_kind='R163 cohort finite solver-seed confirmation',
            mathematical_input_id=a['id'],no_cross_seed_endpoint_composition=True))
        facts.append(dict(id=a['id'],method=method,seed=0,input_SHA256=a['input_SHA'],
            source_commit=R163_SCIENCE,source_report='results/unified_exact_round163/reports/complete_arms.json',
            source_science_identity_SHA256=sha(ROOT/'results/unified_exact_round163/science_identity.json'),
            physical_endpoint_replayed=True,all_Seed0_calls_checked=len(calls),same_PE_DLL=True,
            same_physical_parameters_and_caps=True,same_deadline_shutdown_and_paid_clock_policy=True,
            comparison_new_Seeds=comparisons,eligible_for_descriptive_three_Seed_contract=True))
    assert len(result)==12
    write(OUT/'Seed0_reuse_qualification.json',dict(PASS=True,UTC=utc(),historical_arms=12,facts=facts,
        environment_basis='same retained PE/DLL/Windows host, i7-12700KF 20 logical CPUs and mask4; original runtime paths and live module bindings agree',
        system_environment_frozen='environment_freeze.json',statistical_exchangeability_claim=False,
        original_environment_not_rebuilt=True,old_logical_sample_not_new_performance=True,Seed0_repeated=False,
        grouping='six mathematical inputs, three within-input Seed observations each; no IID or population claim'))
    return result

def sign(value):return -1 if value < -TOL else 1 if value > TOL else 0

def pair(b,p):
    assert (b['id'],b['seed'],b['repeat'])==(p['id'],p['seed'],p['repeat'])
    assert b['input_SHA']==p['input_SHA'] and b['method']=='B' and p['method']=='P'
    both=b['certificate'] and p['certificate']
    delta_t=b['T_cert']-p['T_cert'] if both else None
    threshold=max(10.,.1*min(b['T_cert'],p['T_cert'])) if both else None
    return dict(id=b['id'],gurobi_seed=b['seed'],repeat=b['repeat'],historical=b['historical'],
        B_state=b['state'],P_state=p['state'],B_U=b['U'],P_U=p['U'],B_L=b['L'],P_L=p['L'],
        delta_U=b['U']-p['U'],delta_L=b['L']-p['L'],
        delta_raw_search_L=b['raw_search_L']-p['raw_search_L'],
        delta_U_sign=sign(b['U']-p['U']),delta_L_sign=sign(b['L']-p['L']),
        B_T_cert=b['T_cert'],P_T_cert=p['T_cert'],joint_CERT=bool(both),
        paid_cert_absolute_difference=delta_t,paid_cert_B_over_P=b['T_cert']/p['T_cert'] if both else None,
        material_time_scale_seconds=threshold,
        material_time_difference=abs(delta_t)>=threshold if both else None,
        T_cert_intersection_only=True,B_T_total=b['T_total'],P_T_total=p['T_total'],
        delta_T_total=b['T_total']-p['T_total'],endpoint_tolerance=TOL)

def target_arrival(arm,launch,observations,result,producer,completion,target):
    from round108_reader import full_fleet
    events=[]
    # The inherited producer did not isolate all startup/trailer overhead on
    # the journal's relative clock. Conservatively add its entire excluded
    # nonnegative duration, as the accepted R108 policy does. A zero lower
    # bound avoids converting an availability observation into exact discovery.
    excluded=producer['T_produce']-completion['fully_observed_end_to_end_seconds']
    assert excluded>=-1e-6;excluded=max(0.,excluded)
    for record in observations:
        witness=record['payload']
        if witness['kind']!='witness':continue
        physical=full_fleet(ROOT,launch['panel'],witness)
        if physical['F']<=target+TOL:
            upper=min(producer['T_produce'],record['effective_available_seconds']+excluded)
            events.append(dict(sequence=record['sequence'],source=witness['source'],F=physical['F'],
                event_data_close_seconds=record['data_close_seconds'],
                supervisor_first_observed_seconds=record['first_observed_seconds'],
                paid_clock_interval_lower_seconds=0.,paid_clock_interval_upper_seconds=upper,
                exact_first_find=False,full_fleet_replayed=True))
    final=full_fleet(ROOT,launch['panel'],result);endpoint_hit=final['F']<=target+TOL
    first=min(events,key=lambda e:e['sequence']) if events else None
    upper=first['paid_clock_interval_upper_seconds'] if first else producer['T_produce'] if endpoint_hit else None
    return dict(id=arm['id'],gurobi_seed=arm['seed'],method=arm['method'],repeat=1,historical=arm['historical'],
        u_ref=target,known_feasible_target_not_optimum=True,reached_observed=bool(first or endpoint_hit),
        disposition='saved_journal_witness_interval' if first else 'final_witness_only_upper_bound' if endpoint_hit else 'not_observed_in_window_right_censored',
        first_saved_qualified_event=first,paid_clock_lower_seconds=0. if upper is not None else None,
        paid_clock_upper_seconds=upper,window_end_T_produce=producer['T_produce'],
        unseparated_wrapper_offset_upper_seconds=excluded,qualifying_saved_events=len(events),
        final_F=final['F'],final_witness_hits=endpoint_hit,exact_first_discovery_time_known=False,
        clocks='inherited committed journal availability plus conservative paid wrapper bound; no interpolation or verification-clock backfill',
        production_target_used=False)

def arrival_analysis(arms,history):
    targets={v['id']:v['u_ref'] for v in read(OUT/'primal_targets_frozen.json')['targets']}
    new={(g['launch']['id'],g['launch']['seed'],g['arm']['method']):g['launch'] for g in read(OUT/'matrix_frozen.json')['groups']}
    old={(g['launch']['id'],0,g['launch']['R163_method']):g['launch'] for g in read(ROOT/'results/unified_exact_round163/matrix_frozen.json')['groups']}
    output=[]
    for arm in arms:
        key=(arm['id'],arm['seed'],arm['method']);launch=(old if arm['historical'] else new)[key]
        if arm['historical']:
            prefix=arm['source_archive_prefix']
            obs=history.read(prefix+'/observations.json');result=history.read(prefix+'/result.json')
            producer=history.read(prefix+'/producer_receipt.json');completion=history.read(prefix+'/completion.json')
        else:
            d=Path(launch['destination']);obs=read(d/'observations.json');result=read(d/'result.json')
            producer=read(d/'producer_receipt.json');completion=read(d/'completion.json')
        output.append(target_arrival(arm,launch,obs,result,producer,completion,targets[arm['id']]))
    write(OUT/'reports/primal_target_arrival.json',output)
    csv_write(OUT/'reports/primal_target_arrival.csv',output,[
        'id','gurobi_seed','method','historical','u_ref','reached_observed','disposition',
        'paid_clock_lower_seconds','paid_clock_upper_seconds','window_end_T_produce','final_F',
        'qualifying_saved_events','exact_first_discovery_time_known'])

def run():
    assert read(OUT/'panel_complete.json')['arms']==24
    matrix=read(OUT/'matrix_frozen.json');new=[collect(g) for g in matrix['groups']]
    assert len(new)==24 and len({(a['id'],a['seed'],a['method'],a['repeat']) for a in new})==24
    history=History()
    try:
        old=history_arms(history,new);arms=old+new;by=collections.defaultdict(dict)
        for a in arms:
            key=(a['id'],a['seed']);assert a['method'] not in by[key];by[key][a['method']]=a
        assert len(by)==18 and all(set(v)=={'B','P'} for v in by.values())
        pairs=[pair(by[key]['B'],by[key]['P']) for key in sorted(by)]
        summaries={}
        for seed in (0,1,2):
            methods={}
            for method in ('B','P'):
                current=[a for a in arms if a['seed']==seed and a['method']==method]
                methods[method]=dict(n=6,CERT=sum(a['certificate'] for a in current),OPEN=sum(not a['certificate'] for a in current),
                    T_produce=sum(a['T_produce'] for a in current),T_verify=sum(a['T_verify'] for a in current),
                    T_total=sum(a['T_total'] for a in current),Native_Work=sum(a['Native_Work'] for a in current),
                    Native_nodes=sum(a['Native_nodes'] for a in current),H_seconds=sum(a['H_seconds'] for a in current))
            current=[p for p in pairs if p['gurobi_seed']==seed]
            summaries[seed]=dict(methods=methods,joint_CERT=sum(p['joint_CERT'] for p in current),
                joint_CERT_pairs=[p for p in current if p['joint_CERT']],
                lower_B_U=sum(p['delta_U_sign']<0 for p in current),higher_B_U=sum(p['delta_U_sign']>0 for p in current),
                higher_B_L=sum(p['delta_L_sign']>0 for p in current),lower_B_L=sum(p['delta_L_sign']<0 for p in current),
                historical=seed==0)
        config=[]
        for p in read(OUT/'input_references.json')['roles']:
            current=sorted([v for v in pairs if v['id']==p['id']],key=lambda v:v['gurobi_seed'])
            assert [v['gurobi_seed'] for v in current]==[0,1,2]
            entry=dict(id=p['id'],seeds=[0,1,2],B_CERT=sum(v['B_state']=='CERT' for v in current),
                P_CERT=sum(v['P_state']=='CERT' for v in current),pairs=current)
            for endpoint in ('U','L'):
                values=[v['delta_'+endpoint] for v in current];signs=[sign(v) for v in values]
                entry['delta_'+endpoint]=dict(values=values,signs=signs,median=statistics.median(values),
                    minimum=min(values),maximum=max(values),all_same_qualified_sign=len(set(signs))==1,
                    opposite_nonzero_signs_observed=(-1 in signs and 1 in signs))
            config.append(entry)
        write(OUT/'reports/complete_arms.json',new);write(OUT/'reports/three_seed_arms.json',arms)
        write(OUT/'reports/comparisons.json',[p for p in pairs if p['gurobi_seed'] in (1,2)])
        write(OUT/'reports/three_seed_comparisons.json',pairs);write(OUT/'reports/within_configuration.json',config)
        write(OUT/'reports/summary.json',dict(complete_new_arms=24,new_pairs=12,mathematical_inputs=6,
            total_within_input_pairs=18,Seed0_historical=True,Seed0_reuse_eligible=True,seeds=summaries,
            independent_new_inputs=0,IID_sample_count=None,significance_or_success_probability_claim=False,
            best_seed_selection=False,Eplus_retested=False,no_extra_study=True))
        fields=['position','id','method','gurobi_seed','repeat','historical','state','physical_G','physical_P','U',
            'raw_search_L','qualified_search_L','final_proof_L','signed_gap','original_relative_gap',
            'T_cert','T_produce','T_verify','T_total','scientific_outer_seconds','Native_Work','Native_nodes',
            'Native_Runtime','Native_calls','H_seconds','H_seed','failed_or_rejected_sources','input_SHA','PE_SHA','DLL_SHA','destination']
        csv_write(OUT/'reports/complete.csv',new,fields);csv_write(OUT/'reports/three_seed_arms.csv',arms,fields)
        csv_write(OUT/'reports/comparisons.csv',[p for p in pairs if p['gurobi_seed'] in (1,2)])
        csv_write(OUT/'reports/three_seed_comparisons.csv',pairs)
        arrival_analysis(arms,history)
    finally:history.close()
    print(json.dumps(dict(PASS=True,new_arms=24,new_pairs=12,total_pairs=18,mathematical_inputs=6,seeds=summaries),indent=2))

if __name__=='__main__':run()

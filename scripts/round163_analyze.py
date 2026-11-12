"""Post-panel original-objective readback and all-pair analysis; no producer."""
from round163_common import *
import collections,csv,io,statistics

TOL=1e-7
METHODS=['B','Eplus','P']

def rows(path):
    if not path.exists():return []
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def csv_write(path,records,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(records)

def collect(group):
    from round108_reader import full_fleet
    l=group['launch'];d=Path(l['destination']);position=group['position'];method=l['R163_method']
    a=read(d/'round163_endpoint.json');r=read(d/'result.json');close=read(d/'verification_closeout.json')
    producer=read(d/'producer_receipt.json');clock=read(d/'arm_total_receipt.json')
    fee=read(OUT/'fees'/f'arm_{position:03}'/'receipt.json')
    assert fee['exit_code']==0 and fee['exit_observed'] and not fee['timeout']
    assert all(a[k] and close[k] for k in ['implementation_qualified','evidence_complete','performance_eligible'])
    physical=full_fleet(ROOT,l['panel'],r)
    assert abs(physical['F']-a['U'])<=TOL
    assert a['PE_SHA']==PE_SHA and a['DLL_SHA']==DLL_SHA and a['input_SHA']==l['panel']['input_sha256']
    # Include the current runner's required post-reader controls and endpoint
    # serialization through the observed outer exit. Keep inherited timings,
    # so the small reader trailer is visible instead of silently omitted.
    trailer=fee['end_unix']-clock['t_verified_unix'];assert trailer>=0
    a=dict(a,position=position,method=method,raw_search_L=a.get('raw_search_L',a['L']),final_proof_L=a['L'],
        inherited_T_verify=a['T_verify'],inherited_T_total=a['T_total'],reader_trailer_seconds=trailer,
        T_verify=a['T_verify']+trailer,T_total=a['T_total']+trailer,scientific_outer_seconds=fee['outer_seconds'],
        state='CERT' if a['certificate'] else 'OPEN',physical_G=physical['G'],physical_P=physical['P'],
        helper_seconds=0.,helper_floor=None,helper_qualified=False,helper_first_return_cpp_seconds=None,
        helper_raw_lookup_seconds=a.get('helper_seconds'),helper_native_work=0.,helper_native_nodes=0,
        H_seconds=r.get('incumbent_generation_time_seconds',0) if method!='P' else 0,
        H_decoder_seconds=r.get('hga_wall_time_seconds',0) if method!='P' else 0,
        raw_legacy_formal_performance=a.get('formal_performance'),raw_legacy_not_holdout=a.get('not_holdout'),
        Round163_formal_frozen_panel=True,
        prospective_at_recipe_and_matrix_freeze=True,exposed_after_this_study=True,
        prospective_scope='new configurations on archived sources; no new city or IID/observed-demand claim')
    assert abs(a['T_total']-a['T_produce']-a['T_verify'])<1e-6
    assert a['T_cert'] is not None if a['certificate'] else a['T_cert'] is None
    obs=read(d/'observations.json');calls=[o['payload'] for o in obs if o['payload']['kind']=='call']
    for c in calls:
        settings=c['settings']
        for k,v in dict(Threads=1,Seed=0,Presolve=-1,MIPFocus=0,Cuts=-1,MIPGap=0,MIPGapAbs=0).items():assert settings[k]==v,(position,k)
    if method=='P':
        actual=read(d/'round127_parameters.json')
        assert actual==dict(MIPFocus=0,Cuts=-1,NumStart_before_optimize=0,loaded_after_presets=True,authoritative_model_environment=True)
        a['cold_NumStart_before_optimize']=actual['NumStart_before_optimize']
        assert not a.get('H_complete',False)
    optimize=rows(d/'external/paper_optimize_ledger.csv')
    a.update(Native_Work=r['gurobi_work'] if method=='P' else r['external_gini_tree_work'],
        Native_nodes=r['gurobi_node_count'] if method=='P' else r['external_gini_tree_nodes'],
        Native_Runtime=sum(float(v['solver_runtime']) for v in optimize) if optimize else r.get('gurobi_runtime',0.),
        Native_ledger_reported_Work_sum=sum(float(v['work']) for v in optimize) if optimize else None,
        Native_ledger_reported_nodes_sum=sum(float(v['nodes']) for v in optimize) if optimize else None,
        Native_diagnostic_policy='inherited result counters; individual Optimize ledger values retained separately, never added to paid outer seconds',
        Native_calls=len(calls),failed_or_rejected_sources=len(read(d/'audit.json').get('source_rejections',[])))
    root=d/'external/models/round153_root.json'
    if method=='Eplus' and root.exists():
        meta=read(root);a.update(helper_seconds=meta['helper_process_seconds'],helper_floor=meta['lower'] if meta['qualified'] else None,
            helper_qualified=meta['qualified'],helper_exit=meta['helper_exit'],helper_node_limit=meta['node_limit'],
            helper_remaining_at_launch=meta['whole_method_remaining_at_launch'],helper_global_stop=meta['global_deadline_stop'])
        # The old generic endpoint looked for helper_seconds instead of the
        # actual meta field helper_process_seconds. This is a pure reporting
        # correction. All original records, producer costs and SHA stay intact.
        phases=rows(d/'phases.csv')
        anchors=[float(v['process_seconds'])+float(v['work_deadline_remaining_seconds']) for v in phases
                 if float(v['process_seconds'])>0 and v['work_deadline_remaining_seconds']!='']
        if anchors:
            a['helper_first_return_cpp_seconds']=statistics.median(anchors)-meta['whole_method_remaining_at_launch']+meta['helper_process_seconds']
        lp_launches=[float(v['process_seconds']) for v in phases if v['event']=='first_lp_optimize_launch']
        a['first_lp_optimize_cpp_seconds']=lp_launches[0] if lp_launches else None
        a['helper_phase']='own first canonical root construction; before formal first LP Optimize'
        a['helper_phase_inference']='phase ledger and unchanged construction/checkpoint code; return clock reconstructed, no independent first-application timestamp'
        result=d/'external/round153_floor/result.json';hr=read(result) if result.exists() else {}
        pricing=d/'external/round153_floor/pricing/result.json'
        price=read(pricing) if pricing.exists() else {}
        native=price.get('calls',[])
        a.update(helper_inventory_upper=hr.get('upper'),helper_price_complete_domain=price.get('complete_domain'),
            helper_price_decision=price.get('decision'),helper_price_reason=price.get('reason'),
            helper_native_work=sum(v.get('Work',v.get('work',0)) for v in native),
            helper_native_nodes=sum(v.get('NodeCount',v.get('nodes',0)) for v in native),
            helper_native_statuses=[v.get('Status') for v in native])
        audit=read(d/'round154_control_audit.json')
        assert all(v['floor_rows']==0 for v in audit['models'])
        ledger=audit.get('proof_ledger')
        if ledger:
            assert ledger['native_floor_rows']==0 and ledger['AM_uses_search_bounds']
            a['raw_search_L']=ledger['raw_search_L'];assert ledger['proof_L']==a['L']
            a['helper_proof_stopped']=ledger['proof_stopped']
            a['proof_checkpoint_policy']='qualified floor checked at outer checkpoints before selection/after solveLp and final closeout; no claim of continuous Native callback adoption'
        if a.get('own_exact_zero') and a['certificate']:
            a['helper_effect']='own independently qualified exact-zero proof; no extra endpoint certificate'
        elif not meta['qualified']:a['helper_effect']='no qualified floor; retained B information'
        elif meta['lower']==0 and hr.get('upper')==0:
            a['helper_effect']='inventory optimum is zero on this scope; no positive floor is available'
        elif hr.get('upper') is not None and max(abs(meta['lower']),abs(hr['upper']))<=TOL:
            a['helper_effect']='inventory value is numerically near zero at the inherited qualification scale; not an exact-zero physical proof'
        elif hr.get('upper') is not None and a['raw_search_L']>=hr['upper']-TOL:
            a['helper_effect']='final search lower dominates the inventory value upper at the inherited qualification scale'
        elif a['raw_search_L']>=meta['lower']-TOL:a['helper_effect']='final qualified search lower dominates returned floor'
        else:a['helper_effect']='floor supports final proof lower'
        a['helper_zero_floor']=meta['qualified'] and meta['lower']==0
        a['helper_near_zero_at_qualification_scale']=bool(meta['qualified'] and hr.get('upper') is not None and
            max(abs(meta['lower']),abs(hr['upper']))<=TOL)
        a['inventory_upper_strictly_below_final_search']=bool(hr.get('upper') is not None and hr['upper']<=a['raw_search_L'])
        if price.get('lower') is not None and price.get('upper') is not None:
            a['helper_inventory_width']=price['upper']-price['lower']
        trace=rows(d/'external/global_bound_trace.csv')
        available=[v for v in trace if a['helper_first_return_cpp_seconds'] is not None and
                   float(v['process_elapsed_seconds'])>=a['helper_first_return_cpp_seconds']]
        live=meta['qualified'] and ledger and ledger['root_complete'] and ledger['sources_live']
        increments=[max(0.,min(meta['own_cutoff'],meta['lower'])-float(v['valid_global_lower_bound'])) for v in available] if live else []
        a['max_available_mid_proof_increment_over_logged_raw_search']=max(increments,default=0.)
        a['logged_states_with_available_floor_gain']=sum(v>TOL for v in increments)
        a['mid_bound_interpretation']='qualified available proof information at logged raw-search states; not an altered raw AM input or a backdated certificate'
    elif method=='Eplus':a['helper_effect']='legal termination before canonical root/helper'
    else:a['helper_effect']='method has no helper'
    # Preserve original signed/zero-gap policy from the qualified reader.
    a['signed_gap']=a['U']-a['L']
    a['original_relative_gap']=a['relative_gap']
    a['source_links']=dict(endpoint=(d/'round163_endpoint.json').relative_to(ROOT).as_posix(),
        physical_evidence=(d/'independent_evidence.json').relative_to(ROOT).as_posix(),
        fee=(OUT/'fees'/f'arm_{position:03}'/'receipt.json').relative_to(ROOT).as_posix())
    return a

def pair(a,b):
    both=a['certificate'] and b['certificate']
    return dict(id=a['id'],candidate=a['method'],control=b['method'],candidate_state=a['state'],control_state=b['state'],
        delta_U=a['U']-b['U'],delta_search_L=a['raw_search_L']-b['raw_search_L'],delta_proof_L=a['L']-b['L'],
        delta_signed_gap=a['signed_gap']-b['signed_gap'],delta_T_produce=a['T_produce']-b['T_produce'],
        delta_T_verify=a['T_verify']-b['T_verify'],delta_T_total=a['T_total']-b['T_total'],
        candidate_U=a['U'],control_U=b['U'],candidate_L=a['L'],control_L=b['L'],
        candidate_T_cert=a['T_cert'],control_T_cert=b['T_cert'],
        joint_CERT=both,paid_cert_ratio=a['T_cert']/b['T_cert'] if both and b['T_cert'] else None,
        helper_seconds=a['helper_seconds'],helper_floor=a['helper_floor'],helper_effect=a['helper_effect'],
        endpoint_qualification_tolerance=TOL,single_Seed_runtime_distribution_claim=False)

def run():
    assert read(OUT/'panel_complete.json')['arms']==18
    matrix=read(OUT/'matrix_frozen.json');arms=[collect(g) for g in matrix['groups']]
    assert len(arms)==18
    by=collections.defaultdict(dict)
    for a in arms:
        assert a['method'] not in by[a['id']];by[a['id']][a['method']]=a
    assert len(by)==6 and all(set(v)==set(METHODS) for v in by.values())
    comparisons=[]
    for role,v in by.items():
        assert len({a['input_SHA'] for a in v.values()})==1
        if v['B'].get('H_semantic_SHA') is not None:
            assert v['B']['H_semantic_SHA']==v['Eplus']['H_semantic_SHA'],('own-H differs; investigate',role)
        for x,y in [('B','P'),('Eplus','B'),('Eplus','P')]:comparisons.append(pair(v[x],v[y]))
    summary={}
    for method in METHODS:
        current=[a for a in arms if a['method']==method]
        summary[method]=dict(n=6,CERT=sum(a['certificate'] for a in current),OPEN=sum(not a['certificate'] for a in current),
            T_produce=sum(a['T_produce'] for a in current),T_verify=sum(a['T_verify'] for a in current),T_total=sum(a['T_total'] for a in current),
            H_seconds=sum(a['H_seconds'] for a in current),helper_seconds=sum(a['helper_seconds'] for a in current),
            Native_Work=sum(a['Native_Work'] for a in current),Native_nodes=sum(a['Native_nodes'] for a in current))
    pairs={}
    for x,y in [('B','P'),('Eplus','B'),('Eplus','P')]:
        vv=[v for v in comparisons if (v['candidate'],v['control'])==(x,y)]
        pairs[x+'_vs_'+y]=dict(n=6,candidate_CERT=summary[x]['CERT'],control_CERT=summary[y]['CERT'],
            joint_CERT=sum(v['joint_CERT'] for v in vv),paid_cert_ratios=[v['paid_cert_ratio'] for v in vv if v['joint_CERT']],
            lower_U=sum(v['delta_U']<-TOL for v in vv),higher_U=sum(v['delta_U']>TOL for v in vv),
            higher_proof_L=sum(v['delta_proof_L']>TOL for v in vv),lower_proof_L=sum(v['delta_proof_L']<-TOL for v in vv),
            total_cost_delta=sum(v['delta_T_total'] for v in vv),original_gap_policy_retained=True)
    write(OUT/'reports/complete_arms.json',arms)
    write(OUT/'reports/comparisons.json',comparisons)
    write(OUT/'reports/summary.json',dict(methods=summary,pairs=pairs,complete_arms=18,configurations=6,Seed=0,
        archived_source_prospective_confirmation=True,independent_cities_or_IID=False,
        no_OPEN_dropped_for_global_time_claim=True,raw_runner_reporting_corrections=['actual helper_process_seconds field','post-reader trailer included through outer exit']))
    fields=['position','id','method','state','physical_G','physical_P','U','raw_search_L','final_proof_L','signed_gap','original_relative_gap',
        'T_cert','T_produce','T_verify','T_total','scientific_outer_seconds','Native_Work','Native_nodes','Native_Runtime','Native_calls',
        'H_seconds','helper_seconds','helper_floor','helper_qualified','helper_first_return_cpp_seconds','helper_effect','helper_inventory_upper',
        'helper_inventory_width','helper_native_work','helper_native_nodes','failed_or_rejected_sources','input_SHA','PE_SHA','DLL_SHA','destination']
    csv_write(OUT/'reports/complete.csv',arms,fields)
    csv_write(OUT/'reports/comparisons.csv',comparisons,list(comparisons[0]))
    print(json.dumps(dict(methods=summary,pairs=pairs),indent=2))

if __name__=='__main__':run()

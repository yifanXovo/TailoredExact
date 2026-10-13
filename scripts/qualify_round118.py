"""One finite billed zero-Optimize batch; fixtures never become observations."""
from round118_common import *
import copy,csv,re,shutil,traceback
import round118_campaign as campaign
import round118_call_logs as logs
import round114_audit as audit
import round114_ps as ps
import round108_reader as core
import round111_seed_audit as models
import read_round116 as reader
from round114_claims import reconcile,qualify_endpoint,missing_return_gate
from round118_math import enumerations

def expect_rejection(cases,name,fn):
    try:fn()
    except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:cases.append(dict(case=name,rejected=True,error_class=type(e).__name__))
    else:raise AssertionError('invalid evidence accepted: '+name)

def log_cases(q,cases):
    old=ROOT/'results/unified_exact_round116/campaign/group01'
    i=read(old/'identity.json');l=next(x for x in i['launches'] if x['arm']=='M-B')
    d=core.portable(ROOT,l['destination']);r=read(d/'result.json');j=audit.journal(ROOT,l,d,read(d/'observations.json'))
    view=logs.build(ROOT,l,d,j,r)
    with logs.activate(view):
        chain=audit.return_chain(ROOT,l,d,j,r,read(d/'completion.json'));claims=audit.claims_for(l,j,chain,r)
        original=read(d/'native_claims.json');assert claims==original
        proofs=core.returned_native_proofs(ROOT,j,core.evidence.controller_tables(d,r))
    cases.append(dict(case='safe_V20_actual_single_segments_old_claim_fields_equal',calls=len(view['actual']),claims=len(claims),returned_proofs=len(proofs),passed=True))
    context=models.ArmModels()
    try:
        for c in j['calls'].values():
            contract,m=context.model_contract(ROOT,l['panel'],core.portable(ROOT,c['model_path']),'M-B')
            assert contract['quantity_type']=='C' and contract['frozen_A_B_rows_checked']==40
    finally:context.clear()
    cases.append(dict(case='actual_MB_continuous_quantities_integer_inventory_binary_structure_AB',passed=True))
    f=q/'double';(f/'external').mkdir(parents=True)
    chosen=[j['calls'][1],j['calls'][2]];data=[core.portable(ROOT,c['native_log_path']).read_bytes() for c in chosen]
    target=f/'double.log';target.write_bytes(b''.join(data));jl=copy.deepcopy(j)
    jl.update(calls={n:dict(c,call=n,native_log_path=str(target)) for n,c in enumerate(chosen,1)},
        not_started_ids=set(),actual_started_ids={1,2},returned_ids={1,2},unreturned_ids=set(),failure=None,
        started=2,returned=2,declared=2,not_started=0,bounds=[])
    ledger=[dict(row,native_log=str(target)) for row in chain['ledger'][:2]]
    def save_ledger(rows):
        with (f/'external/paper_optimize_ledger.csv').open('w',encoding='utf-8',newline='') as file:
            w=csv.DictWriter(file,list(rows[0]));w.writeheader();w.writerows(rows)
    save_ledger(ledger);vl=logs.build(ROOT,l,f,jl,r)
    cl=dict(logs=[dict(call=cid,text=v['text']) for cid,v in vl['views'].items()],ledger=ledger,phase=chain['phase'])
    ownclaims=audit.claims_for(l,jl,cl,r)
    expected=[float(re.findall(r'Optimal objective\s+([-+0-9.eE]+)',x.decode())[-1]) for x in data]
    assert [c['value'] for c in ownclaims]==expected
    with logs.activate(vl):
        downstream=core.returned_native_proofs(ROOT,jl,dict(controller_native=ledger))
        # The shared file's leading blank separator belongs to the preceding
        # byte span; semantic text and every span hash remain checked separately.
        for cid,c in jl['calls'].items():assert logs.call_text(ROOT,c,cid).strip()==data[cid-1].decode().strip()
    cases.append(dict(case='two_calls_one_file_per_call_terminal_values_and_headers',values=expected,
        bindings=vl['bindings'],passed=True,synthetic_reuse_of_safe_actual_segments=True))
    bad=copy.deepcopy(jl);bad['calls'][1]['model_sha256']='0'*64
    expect_rejection(cases,'wrong_complete_model_SHA',lambda:logs.build(ROOT,l,f,bad,r))
    bad=copy.deepcopy(jl);bad['calls'][1]['lower_g']+=.01
    expect_rejection(cases,'wrong_true_G_domain_same_log',lambda:logs.build(ROOT,l,f,bad,r))
    bad=copy.deepcopy(jl);bad['calls'][1]['cutoff']+=.01
    expect_rejection(cases,'wrong_cutoff_epoch_domain',lambda:logs.build(ROOT,l,f,bad,r))
    target.write_bytes(b''.join(data)+data[0]);expect_rejection(cases,'duplicate_Optimize_segment',lambda:logs.build(ROOT,l,f,jl,r))
    target.write_bytes(data[0]);expect_rejection(cases,'missing_second_Optimize_segment',lambda:logs.build(ROOT,l,f,jl,r))
    target.write_bytes(b''.join(data));save_ledger(list(reversed(ledger)))
    expect_rejection(cases,'wrong_serial_ledger_mapping',lambda:logs.build(ROOT,l,f,jl,r));save_ledger(ledger)
    bad=copy.deepcopy(jl);bad['returned_ids']={1};bad['unreturned_ids']={2}
    expect_rejection(cases,'real_started_without_return_not_floor0_pass',lambda:logs.build(ROOT,l,f,bad,r))
    bad=copy.deepcopy(jl);bad['actual_started_ids']={1}
    expect_rejection(cases,'declaration_not_inferred_as_Optimize',lambda:logs.build(ROOT,l,f,bad,r))
    expect_rejection(cases,'whole_file_fallback_rejects_two_calls',lambda:logs.call_text(ROOT,jl['calls'][1],1))
    identical=copy.deepcopy(jl);identical['calls'][2]=dict(identical['calls'][1],call=2)
    sameledger=[ledger[0].copy(),ledger[0].copy()];save_ledger(sameledger);target.write_bytes(data[0]+data[0])
    iv=logs.build(ROOT,l,f,identical,r);assert set(iv['views'])=={1,2}
    assert iv['views'][1]['binding']['byte_end']<=iv['views'][2]['binding']['byte_begin']
    cases.append(dict(case='different_calls_identical_values_models_scopes_keep_distinct_identity',passed=True))
    # Restore the explicitly synthetic two-segment fixture for publication.
    target.write_bytes(b''.join(data));save_ledger(ledger)
    write(f/'provenance.json',dict(synthetic=True,no_Optimize=True,not_a_performance_observation=True,bindings=vl['bindings']))

def lifecycle_cases(q,cases):
    source=ROOT/'results/unified_exact_round116/qualification/cli01/raw/02_H100_S0_P-S'
    p=copy.deepcopy(read(OUT/'qualification/input_manifest.json')['roles'][0]);p['reference']=read(OUT/'qualification/reference/H100/build.json')
    positive=read(source/'result.json');own=read(source/'result.json.round112.startup.json');sourceobs=read(source/'observations.json')
    for branch in ['premodel_deadline','mapped_not_started']:
        d=q/branch;d.mkdir();r=copy.deepcopy(positive)
        for key in ['routes','objective','G','P']:r[key]=own[key]
        r.update(status='startup_deadline',strict_certified_original_problem=False,lower_bound=0.,upper_bound=own['objective'],
            final_UB=own['objective'],initial_heuristic_UB=own['objective'],process_shutdown_margin_seconds=30,process_return_code=0,
            gurobi_optimize_count=0,gurobi_solution_count=0,gurobi_solver_finalization_reached=False)
        for key in ['gurobi_obj_bound_available','gurobi_obj_bound_c_available','native_mip_best_bound_available','native_mip_objective_available']:r[key]=False
        events=[copy.deepcopy(sourceobs[0]['payload']),copy.deepcopy(sourceobs[1]['payload'])];times=[.8,.9]
        if branch=='mapped_not_started':
            for src in source.glob('native.log.round112.start*'):shutil.copyfile(src,d/src.name)
            shutil.copyfile(source/'compact.lp',d/'compact.lp')
            c=copy.deepcopy(next(q['payload'] for q in sourceobs if q['payload']['kind']=='call'))
            c['model_path']=str(d/'compact.lp');c['native_log_path']=str(d/'native.log')
            events+=[c,dict(schema=1,kind='not_started',call=1,reason='no_remaining_original_work_window',actual_Optimize=False)]
            times+=[89.999,90.001]
        write(d/'result.json',r);write(d/'result.json.round112.startup.json',own)
        l=dict(number=1,id='H100',arm='P-S',destination=str(d),panel=p,cap_seconds=120,
            command=['NONREAL_LIFECYCLE_FIXTURE','--plain-baseline','--round112-ens-start-compact'])
        write(d/'launch.json',l);comp=dict(returncode=0,stop_reason='normal_return',within_cap=True);write(d/'completion.json',comp)
        phases=[('process_entry','start',0.),('round112_ENS_H','start',.01),('round112_ENS_H','complete',.7)]
        if branch=='mapped_not_started':phases+=[('round112_compact_start','start',.75),('round112_compact_start','complete',89.998)]
        phases+=[('final_result_serialization_start','start',90.002),('final_result_serialization_complete','complete',90.003),('process_exit','complete',90.004)]
        with (d/'phases.csv').open('x',encoding='utf-8',newline='') as file:
            w=csv.writer(file);w.writerow(['sequence','process_seconds','event','status','nominal_deadline_remaining_seconds','work_deadline_remaining_seconds','detail'])
            for seq,(event,status,t) in enumerate(phases):w.writerow([seq,t,event,status,120-t,90-t,'rc=0' if event=='process_exit' else ''])
        observations=[];(d/'journal').mkdir()
        for seq,(e,t) in enumerate(zip(events,times),1):
            e['sequence']=seq;raw=d/'journal'/f'event_{seq}.json';write(raw,e);h=sha(raw)
            (d/'journal'/f'event_{seq}.commit').write_text(f'NEJ1 {seq} {t} {raw.stat().st_size} {h}\n',encoding='ascii')
            observations.append(dict(sequence=seq,data_close_seconds=t,first_observed_seconds=t,effective_available_seconds=t,sha256=h,payload=e))
        write(d/'observations.json',observations)
        life=ps.ps_journal(ROOT,p,d,observations);result=ps.validate_ps_lifecycle(ROOT,l,d,life,r,comp,core.full_fleet(ROOT,p,own))
        assert life['started']==0 and bool(result['Start'])==(branch=='mapped_not_started')
        view=logs.build(ROOT,l,d,life,r);assert not view['actual']
        cases.append(dict(case=branch,passed=True,synthetic_fixture=True,actual_Optimize=0,full_Start_verified=bool(result['Start'])))
        if branch=='mapped_not_started':
            bad=copy.deepcopy(observations);bad[-1]['payload']['actual_Optimize']=True
            expect_rejection(cases,'cancel_after_actual_Optimize_rejected',lambda:ps.event_lifecycle(bad))
            declared=ps.event_lifecycle(observations[:-1]);assert declared['pending_declaration_ids']=={1} and declared['started']==0
            cases.append(dict(case='pending_declaration_is_unresolved_not_not_started',passed=True))

def classification_cases(cases):
    good=dict(identity_verified=True,input_verified=True,model_domain_verified=True,journal_verified=True,return_verified=True,files_verified=True,
        own_physical_verified=True,independent_floor0=True,clock_valid=True,necessary_closeout_complete=True,own_U=1.,own_exact_zero=False)
    v=qualify_endpoint(good,[dict(arm='M-B',call=1)]);assert v['L']==0 and not v['certificate'] and reader.proof_class(v)=='SOURCE_REDUCED_OPEN'
    cases.append(dict(case='isolated_bad_claim_does_not_supply_nonzero_certificate',passed=True))
    for k in ['model_domain_verified','return_verified','clock_valid']:
        assert not qualify_endpoint(dict(good,**{k:False}),[],dict(U=1,L=0,gap=1,certificate=False))['formal_protocol_qualified']
        cases.append(dict(case='unresolved_'+k,passed=True))
    claim=dict(arm='M-B',call=1,sequence=2,model_SHA='NONREAL-model',input_SHA='NONREAL-input',scope=dict(full_original=False,lower_g=.3,upper_g=.5,cutoff=1.),
        value=.7,source='NONREAL-scope',available=1.,domain_verified=True,dependencies=[1])
    outside=dict(arm='P-S',F=.4,G=.2,input_SHA='NONREAL-input',source='NONREAL-fleet',available=2.,physical_verified=True)
    assert not reconcile([claim],[outside])['rejections']
    assert reconcile([claim],[dict(outside,G=.4)])['damaged_calls']==[dict(arm='M-B',call=1)]
    assert all(not c['native_proof_qualified'] for c in reconcile([claim,dict(claim,sequence=3,value=.1)],[dict(outside,G=.4)])['all_claims'])
    cases.append(dict(case='scope_excludes_other_domain_and_later_small_value_never_restores_bad_call',passed=True))
    parent=dict(gamma_L=0.,gamma_U=1.,lower_bound=.6)
    siblings=[dict(lo=0.,hi=.5,L=.6,cutoff=2.),dict(lo=.5,hi=1.,L=.8,cutoff=2.)]
    assert core.supported_leaf_bound(parent,siblings)==.6
    expect_rejection(cases,'sibling_max_is_not_global_lower_bound',lambda:core.supported_leaf_bound(dict(parent,lower_bound=.8),siblings))
    expect_rejection(cases,'new_smaller_domain_bound_not_old_parent',lambda:core.supported_leaf_bound(dict(parent,lower_bound=.8),siblings[1:]))
    cases.append(dict(case='full_parent_coverage_uses_min_over_regions',passed=True))
    # The inherited extremely narrow exception remains zero-witness-only.
    f=dict(prefix_continuous=True,failure_terminal=True,failure_reason='full_bound_witness_inconsistency',damaged_call=1,
        actual_call_ids=[1],journal_returned_ids=[],explicit_not_started_ids=[],terminal_MIP=True,all_actual_calls_bound=True,normal_return=True,
        API_or_ledger_return_verified=True,logs_parameters_models_cleanup_verified=True,serialization_process_exit_verified=True,
        own_committed_exact_zero=True,same_domain_counterexample_verified=True,independent_floor0=True,clock_valid=True)
    assert missing_return_gate(f)['missing_returned_preserved']==[1]
    expect_rejection(cases,'positive_V40_cannot_use_old_own_zero_missing_return_exception',lambda:missing_return_gate(dict(f,own_committed_exact_zero=False)))
    a=dict(arm='M-B',U=1.,L=1.+1e-15,gap=-1e-15,certificate=True,certificate_qualified=True,numbers_qualified=True,formal_protocol_qualified=True,complete_seconds=100.)
    pair=reader.pair(a,dict(a,arm='P-GRB',gap=0,L=1));assert pair['candidate_gap']<0 and not pair['percentage_gap_path_applicable']
    cases.append(dict(case='tiny_signed_gap_not_clamped_or_percentage_inflated',passed=True))
    for cap in [120,5400]:
        p=copy.deepcopy(read(OUT/'qualification/input_manifest.json')['roles'][0]);p['cap_seconds']=cap;p['reference']=read(OUT/'qualification/reference/H100/build.json')
        for arm in ['P-GRB','M-B','P-S','ENS-C']:
            cmd=campaign.argv(p,arm,Path('NONREAL_ARGV_ONLY'))
            assert cmd[cmd.index('--time-limit')+1]==str(cap-6) and cmd[cmd.index('--process-shutdown-margin')+1]=='30'
            assert '--round100-continuous-quantities' not in cmd
    cases.append(dict(case='real_command_generator_same_deadline_and_no_ENS_Q_at_both_caps',passed=True))
    assert len(enumerations())==8;cases.append(dict(case='n2_n3_decimal_binary64_exact_rational_penalty_relaxation',passed=True))

def clock_cases(q,cases):
    from round115_common import clock_evidence
    d=q/'clock';d.mkdir();c=dict(returncode=0,stop_reason='normal_return',within_cap=True)
    write(d/'completion.json',c);write(d/'verification_closeout.json',dict(necessary_verification_complete=True))
    write(d/'producer_seal.json',dict(required_SHA={'completion.json':sha(d/'completion.json')}))
    p=dict(state='PRODUCED_PENDING_VERIFICATION',verification_passed=None,producer_seal_SHA=sha(d/'producer_seal.json'),
        t0_perf=10.,t_produce_perf=129.,T_produce=119.,cap_seconds=120,required_outputs_closed=True,native_stopped_no_reentry=True,
        t0_unix=1000.,t_produce_unix=1119.)
    write(d/'producer_receipt.json',p)
    v=dict(producer_receipt_SHA=sha(d/'producer_receipt.json'),verification_closeout_SHA=sha(d/'verification_closeout.json'),necessary_verification_complete=True,
        t_verified_perf=239.,T_verify=110.,T_total=229.,t_verified_unix=1229.)
    write(d/'arm_total_receipt.json',v)
    result=clock_evidence(d,dict(cap_seconds=120));assert result['within_cap'] and result['T_total']>120 and result['T_verify']>30
    cases.append(dict(case='v2_same_origin_producer119_verify110_total229_is_eligible',passed=True,synthetic_clock=True))
    p['T_produce']=118.;(d/'producer_receipt.json').write_text(json.dumps(p),encoding='utf-8')
    v['producer_receipt_SHA']=sha(d/'producer_receipt.json');(d/'arm_total_receipt.json').write_text(json.dumps(v),encoding='utf-8')
    expect_rejection(cases,'inconsistent_producer_clock_not_backfilled',lambda:clock_evidence(d,dict(cap_seconds=120)))
    p['T_produce']=119.;(d/'producer_receipt.json').write_text(json.dumps(p),encoding='utf-8')
    v['producer_receipt_SHA']=sha(d/'producer_receipt.json');(d/'arm_total_receipt.json').write_text(json.dumps(v),encoding='utf-8')

def qualify_in_process(label):
    tick=time.perf_counter();q=OUT/'qualification'/label;q.mkdir();cases=[]
    check_identity();log_cases(q,cases);lifecycle_cases(q,cases);classification_cases(cases);clock_cases(q,cases)
    assert time.perf_counter()-tick<180
    summary=dict(passed=True,cases=cases,Optimize=0,OS_children=0,driver_processes=0,
        holder='already charged H100 wrapper',helpers=helpers(),test_SHA=sha(__file__),known_reused_log_risk_resolved_for_qualified_views=True,
        no_V100_restore_or_execution=True,no_formal_input_H_or_oracle=True,seconds=time.perf_counter()-tick)
    write(q/'summary.json',summary);return summary

def run(label):
    fee,tick=fee_begin(label,0,180,True);code=1
    try:
        qualify_in_process(label)
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])

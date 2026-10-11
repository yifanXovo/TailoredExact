"""One explicitly billed finite driver; in-process fixtures, no native calls."""
from round114_common import *
import copy, csv, inspect, shutil, traceback, types
import round114_campaign as campaign
import round114_audit as audit
import round114_ps as ps
import qualify_round113 as old_tests
from round114_claims import reconcile,qualify_endpoint,missing_return_gate,ClaimRejection,in_domain
import round111_decisions as decisions

def frozen_evidence(U=1.,zero=False):
    return dict(identity_verified=True,input_verified=True,model_domain_verified=True,journal_verified=True,
        return_verified=True,files_verified=True,own_physical_verified=True,independent_floor0=True,clock_valid=True,
        necessary_closeout_complete=True,own_U=U,own_exact_zero=zero)

def claim_cases(out):
    out.mkdir();cases=[]
    call=dict(full_original=True,lower_g=0.,upper_g=.98,cutoff=0.)
    claim=dict(arm='P-GRB',call=1,sequence=52,model_SHA='actual-fixture-model-sha',input_SHA='shared-fixture-input',
        scope=call,value=2.28e-6,source='synthetic_bound_claim',available=136.5,domain_verified=True,dependencies=[1])
    witness=dict(arm='ENS-C',F=0.,G=0.,source='synthetic_verified_own_zero',input_SHA=claim['input_SHA'],available=320.,physical_verified=True)
    forward=reconcile([claim],[witness]);reverse=reconcile(list(reversed([claim])),list(reversed([witness])))
    assert forward==reverse and forward['damaged_calls']==[dict(arm='P-GRB',call=1)]
    assert not reconcile([claim],[])['rejections'] and not reconcile([],[witness])['rejections']
    assert forward['rejections'][0]['counterexample']['arm']=='ENS-C'
    cases.append(dict(case='before_after_witness_order_source_attribution',passed=True,reconciliation=forward))
    local=dict(claim,scope=dict(full_original=False,lower_g=.1,upper_g=.2,cutoff=.3),value=.01)
    assert not reconcile([local],[witness])['rejections']
    same=dict(witness,G=.15,F=.001);assert reconcile([local],[same])['damaged_calls']==[dict(arm='P-GRB',call=1)]
    cases.append(dict(case='same_domain_and_outside_domain',passed=True))
    later=dict(claim,sequence=82,value=0.)
    allclaims=reconcile([claim,later],[witness])['all_claims'];assert all(q['native_proof_qualified'] is False for q in allclaims)
    second=dict(witness,arm='M-B',source='second_distinguishable_own_witness',F=.1,available=200.)
    assert reconcile([claim,later],[witness,second])==reconcile([later,claim],[second,witness])
    rejected=forward['damaged_calls'];open_ep=qualify_endpoint(frozen_evidence(),rejected)
    assert open_ep['endpoint_source']=='SOURCE_REDUCED_OPEN' and open_ep['L']==0 and not open_ep['certificate']
    zero=qualify_endpoint(frozen_evidence(0.,True),rejected);assert zero['endpoint_source']=='OWN_ZERO_CERTIFICATE' and zero['certificate']
    for field in ['identity_verified','model_domain_verified','journal_verified','return_verified','files_verified','clock_valid','independent_floor0']:
        e=frozen_evidence();e[field]=False;assert not qualify_endpoint(e,rejected)['formal_protocol_qualified']
    e=frozen_evidence();e['own_U']=None;assert not qualify_endpoint(e,rejected)['formal_protocol_qualified']
    normal=dict(U=1.,L=.1,gap=.9,certificate=False)
    unchanged=qualify_endpoint(frozen_evidence(),[],normal);assert all(unchanged[k]==normal[k] for k in normal)
    cases.append(dict(case='whole_call_dependencies_independent_endpoint_and_mandatory_evidence',passed=True,
        affected_kinds=forward['rejections'][0]['rejected_native_kinds'],open_endpoint=open_ep,own_zero=zero,
        smaller_final_bound_does_not_restore_call=True,no_own_UB_or_clock_rejected=True))
    # Actual journal code must fail closed for identity/required files/unknown event.
    for kind in ['unknown_failure','unknown_event']:
        try:missing_return_gate(dict(failure_reason=kind))
        except AssertionError:cases.append(dict(case=kind,rejected=True))
        else:raise AssertionError('unknown evidence recovered')
    write(out/'receipt.json',dict(cases=cases,actual_qualification_functions=True,synthetic_values_not_solver_returns=True,
        qualifier_SHA=sha(ROOT/'scripts/round114_claims.py')))

def zero_call_cases(out):
    out.mkdir();namespace=dict(vars(old_tests),ROOT=ROOT,OUT=OUT,OLD_ROOT=Path('E:/codes/ExactEBRP-round112'))
    exec(compile(inspect.getsource(old_tests.fixture),__file__+'::source_supported_fixture','exec'),namespace)
    cases=[];identity=read(OUT/'qualification/cli01/identity.json')
    for branch in ['premodel_deadline','mapped_not_started','startup_zero']:
        l,observations=namespace['fixture'](out,branch);d=Path(l['destination'])
        assert (ROOT/l['panel']['input_path']).is_file(),'frozen zero-call fixture input missing'
        j=ps.ps_journal(ROOT,l['panel'],d);r=read(d/'result.json');c=read(d/'completion.json')
        own=ps.core.full_fleet(ROOT,l['panel'],read(d/'result.json.round112.startup.json'))
        good=ps.validate_ps_lifecycle(ROOT,l,d,j,r,c,own)
        assert good['actual_Optimize']==0 and good['branch'] in ['PREMODEL_STARTUP_DEADLINE','MAPPED_EXPLICIT_NOT_STARTED','OWN_STARTUP_ZERO']
        cases.append(dict(branch=branch,passed=True,lifecycle=good))
        for key,value in [('gurobi_status',2),('native_mip_status_code',2),('gurobi_obj_val_available',True),('gurobi_lifecycle_valid',True)]:
            try:ps.validate_ps_lifecycle(ROOT,l,d,j,dict(r,**{key:value}),c,own)
            except AssertionError:cases.append(dict(branch=branch,field=key,synthetic_change=value,rejected=True))
            else:raise AssertionError(('contradictory zero-Optimize native claim accepted',branch,key))
    write(out/'receipt.json',dict(cases=cases,zero_Optimize_fixtures=True,actual_native_cancellation_executed=False,
        inherited_Start_gate_preserved=True,only_four_new_field_mutations_per_supported_branch=True))

def journal_cases(out,source):
    out.mkdir();l=read(source/'launch.json');observations=read(source/'observations.json');cases=[]
    for name in ['unknown_event','unknown_failure','identity_mismatch']:
        d=out/name;d.mkdir();(d/'journal').mkdir();events=[copy.deepcopy(q['payload']) for q in observations]
        if name=='identity_mismatch':events[0]['input_sha256']='unbound-input'
        else:events.append(dict(schema=1,kind='failure' if name=='unknown_failure' else 'unrecognized_event',reason='unknown_failure'))
        rows=[]
        for seq,e in enumerate(events,1):
            e['sequence']=seq;p=d/'journal'/f'event_{seq}.json';write(p,e);h=sha(p);t=float(seq)
            (d/'journal'/f'event_{seq}.commit').write_text(f'NEJ1 {seq} {t} {p.stat().st_size} {h}\n',encoding='ascii')
            rows.append(dict(sequence=seq,data_close_seconds=t,first_observed_seconds=t,effective_available_seconds=t,sha256=h,payload=e))
        try:audit.journal(ROOT,l,d,rows)
        except AssertionError as exc:cases.append(dict(case=name,rejected=True,exception=repr(exc),actual_journal_entry=True))
        else:raise AssertionError(('unknown mandatory journal evidence accepted',name))
    write(out/'receipt.json',dict(cases=cases,OS_children=0,actual_native_fault_injected=False))

def supervisor_cases(out):
    namespace=dict(vars(old_tests),ROOT=ROOT,OUT=OUT,campaign=campaign)
    source=inspect.getsource(old_tests.supervisor_cases)
    source=source.replace("['normal','display_failure','disk_stop_after_display_failure','memory_stop_after_display_failure',", "['normal','typed_claim_rejection','unknown_audit_failure','disk_stop_after_display_failure','memory_stop_after_display_failure',")
    marker="            audit_launch=lambda *args:dict(passed=True,endpoint=dict(U=1.,L=0.,gap=1.,certificate=False)))"
    assert source.count(marker)==1
    replacement=marker+"\n        namespace['ClaimRejection']=ClaimRejection\n        if case=='typed_claim_rejection':\n            def rejected(*args):raise ClaimRejection(dict(passed=False,independent_evidence_audit_passed=True,endpoint=dict(U=1.,L=0.,gap=1.,certificate=False)))\n            namespace['audit_launch']=rejected\n        elif case=='unknown_audit_failure':\n            namespace['audit_launch']=lambda *args:(_ for _ in ()).throw(AssertionError('unknown mandatory failure'))"
    source=source.replace(marker,replacement)
    source=source.replace("        elif case=='display_failure':assert not error and pub.attempts==1 and len(samples)==3 and len(memories)==4 and len(disks)==4", "        elif case=='typed_claim_rejection':\n            assert not error and child_state['kill']==0 and child_state['wait']==1\n            d=directory/'raw';write(d/'progress_publication_receipt.json',pub.receipt())\n            write(d/'independent_evidence.json',dict(witnesses=[]))\n            write(d/'native_claims.json',[]);write(d/'claim_rejections.json',dict(rejections=[]))\n            fee=directory/'fee';fee.mkdir()\n            rec=json.loads((directory/'summary.jsonl').read_text().splitlines()[-1])\n            local=dict(vars(campaign),time=clock)\n            exec(compile(inspect.getsource(campaign.finish_arm),__file__+'::actual_finish_arm','exec'),local)\n            local['finish_arm'](dict(l,seed=0),{},0.,rec,fee)\n            assert (d/'audit_execution_metrics.json').is_file() and (d/'whole_arm_receipt.json').is_file()\n            assert read(d/'audit.json')['passed'] is False\n            write(directory/'next_fixed_arm_eligible.json',dict(typed_rejection_fully_closed=True,whole_SHA=sha(d/'whole_arm_receipt.json')))\n            next_l=dict(l,number=2,destination=str(directory/'next_raw'))\n            namespace['audit_launch']=lambda *args:dict(passed=True,endpoint=dict(U=1.,L=0.,gap=1.,certificate=False))\n            campaign.supervisor_function(namespace)(next_l,dict(common=dict(affinity_mask=4)),dict(prereg_sha256='mock',runner_sha256='mock'))\n            assert (directory/'next_raw/completion.json').is_file()")
    namespace['ClaimRejection']=ClaimRejection
    exec(compile(source,__file__+'::bounded_source_extracted_supervision','exec'),namespace)
    namespace['supervisor_cases'](out)

def inherited_contracts(out):
    out.mkdir();root=OUT/'inherited_return_authority';manifest=read(root/'dependency_manifest.json')
    for name,h in manifest['files'].items():assert sha(root/name)==h
    records=[]
    for n in [15,17,25,26]:
        authority=root/'results/unified_exact_round111/review/inherited_main03/authority'
        side=read(authority/f'recovery_{n}.json');signed=read(authority/f'recovery_{n}_signed_audit.json')
        assert side['independent_audit_SHA']==sha(authority/f'recovery_{n}_signed_audit.json')
        raw=next((root/'results/unified_exact_round110/campaign/raw').glob(f'{n:02d}_*'))
        l=read(raw/'launch.json');p=l['panel'];r=read(raw/'result.json');obs=read(raw/'observations.json')
        assert (root/p['input_path']).is_file(),'frozen inherited fixture input missing'
        own=audit.core.full_fleet(root,p,r);instance=audit.core.evidence.instance(root,p)
        exactzero=all(x==y for x,y in zip(own['Y'][1:],instance['D'][1:]))
        assert exactzero==(n in [17,25])
        for seq,q in enumerate(obs,1):assert journal_check(raw,seq,q,p['cap_seconds'])
        calls={q['payload']['call']:q['payload'] for q in obs if q['payload']['kind']=='call'}
        returned={q['payload']['call'] for q in obs if q['payload']['kind']=='returned'}
        j=dict(calls=calls,returned_ids=returned,not_started_ids=set(),actual_started_ids=set(calls),
            unreturned_ids=set(calls)-returned,failure=obs[-1]['payload'] if obs[-1]['payload']['kind']=='failure' else None)
        chain=audit.return_chain(root,l,raw,j,r,read(raw/'completion.json'))
        e=frozen_evidence(own['F'],exactzero)
        interval=side['time']['interval'];assert side['time']['exact_seconds'] is None and 0<interval[0]<=interval[1]<l['cap_seconds']
        e.update(original_clock_interval=interval,exact_old_clock_not_created=True)
        if n in [17,25]:
            failure=j['failure'];assert failure['reason'] in ['full_bound_witness_inconsistency','local_bound_witness_inconsistency']
            last=max(calls);claims=[q['payload'] for q in obs if q['payload']['kind']=='bound' and q['payload']['call']==last]
            zero_payloads=[q for q in obs if q['payload']['kind']=='witness' and audit.core.full_fleet(root,p,q['payload'])['F']==0.]
            assert zero_payloads and any(q['native_bound']>1e-7 for q in claims)
            witness=dict(audit.core.full_fleet(root,p,zero_payloads[-1]['payload']),arm=l['arm'],source='inherited_committed_own_zero',
                input_SHA=p['input_sha256'],available=zero_payloads[-1]['effective_available_seconds'],physical_verified=True)
            native_claim=dict(arm=l['arm'],call=last,sequence=claims[0]['sequence'],model_SHA=calls[last]['model_sha256'],
                input_SHA=p['input_sha256'],scope=calls[last],value=max(q['native_bound'] for q in claims),
                source='actual_inherited_terminal_call_bound',available=0.,domain_verified=True,dependencies=[last])
            assert in_domain(calls[last],witness) and reconcile([native_claim],[witness])['rejections']
            outside=dict(calls[last],full_original=False,lower_g=.1,upper_g=.2,cutoff=1.)
            assert not in_domain(outside,witness) and not reconcile([dict(native_claim,scope=outside)],[witness])['rejections']
            f=dict(prefix_continuous=True,failure_terminal=True,failure_reason=failure['reason'],damaged_call=last,
                actual_call_ids=chain['actual'],journal_returned_ids=sorted(returned),explicit_not_started_ids=[],terminal_MIP=True,
                all_actual_calls_bound=True,normal_return=True,API_or_ledger_return_verified=True,logs_parameters_models_cleanup_verified=True,
                serialization_process_exit_verified=True,own_committed_exact_zero=True,same_domain_counterexample_verified=True,
                independent_floor0=True,clock_valid=True)
            assert missing_return_gate(f)['independently_verified_returned']==len(calls)
            for name,change in [('missing_field',lambda q:q.pop('logs_parameters_models_cleanup_verified')),
                ('unknown_failure',lambda q:q.update(failure_reason='unknown')),
                ('domain_mismatch',lambda q:q.update(same_domain_counterexample_verified=False)),
                ('own_zero_missing',lambda q:q.update(own_committed_exact_zero=False)),
                ('extra_unbound_call',lambda q:q.update(actual_call_ids=q['actual_call_ids']+[last+1]))]:
                changed=copy.deepcopy(f);change(changed)
                try:missing_return_gate(changed)
                except AssertionError:records.append(dict(original_fixture=n,case=name,rejected=True))
                else:raise AssertionError(('invalid narrow fixture accepted',n,name))
        q=qualify_endpoint(e,[dict(arm=l['arm'],call=max(calls))]);assert q['L']==0 and q['certificate']==exactzero
        records.append(dict(original_fixture=n,qualified_endpoint=q,own_U=own['F'],signed_own_U=side['own_U'],original_clock_interval=interval,
            original_raw_audit_passed=read(raw/'audit.json')['passed'],declared=len(calls),actual_Optimize=len(chain['actual']),journal_returned=len(returned),
            independently_verified_returned=len(chain['actual']),explicit_not_started=0,model_contract_inherited_from_signed_authority=True,
            old_matrix_runtime_repeated=False,normal_return_chain_replayed=True))
    write(out/'receipt.json',dict(cases=records,fixture_numbers_not_runtime_routing_conditions=True,Optimize=0,old_times_unchanged=True))

def journal_check(d,seq,q,cap):
    return audit.journal_receipts.receipt(d/'journal'/f'event_{seq}.commit',q['first_observed_seconds'],cap)==q

def compatibility(out):
    out.mkdir();old=OUT/'inherited_r113';manifest=read(old/'dependency_manifest.json')
    for name,h in manifest['files'].items():assert sha(old/name)==h
    rows=audit.core.rows(old/'reports_final/arms.csv');pairs=audit.core.rows(old/'reports_final/pairs.csv')
    valid=[r for r in rows if r['formal_protocol_qualified']=='True'];assert len(valid)==15
    goodpairs=[p for p in pairs if p['evaluable']=='True'];assert len(goodpairs)==21
    lookup={(r['id'],r['arm']):r for r in valid}
    for row in goodpairs:
        def endpoint(method):
            r=lookup[row['id'],method]
            return dict(r,U=float(r['U']),L=float(r['L']),gap=float(r['gap']),complete_seconds=float(r['complete_seconds']),
                certificate=r['certificate']=='True',certificate_qualified=True,numbers_qualified=True,formal_protocol_qualified=True)
        v=decisions.pair(endpoint(row['candidate']),endpoint(row['control']))
        assert v['classification']==row['classification'] and v['severe_regression']==(row['severe_regression']=='True')
    cold=next(r for r in rows if r['id']=='G50-C1' and r['arm']=='P-GRB')
    assert cold['U']==cold['L']==cold['complete_seconds']=='' and cold['formal_protocol_qualified']=='False'
    write(out/'receipt.json',dict(passed=True,old15_qualified=15,old21_pairs_unchanged=21,missing_pairs_retained=9,
        signed_L48_PS_gap=next(float(r['gap']) for r in valid if r['id']=='R108-L48' and r['arm']=='P-S'),
        old_cold_P_no_whole_still_unqualified=True,old_clocks_from_bound_original_sources=True,old_LP_matrix_reparse=False))
    csv.field_size_limit(64*1024*1024);small=out/'empty_root';small.mkdir()
    shutil.copyfile(old/'reports_final/same_H_fleets.csv',small/'same_H_fleets.csv')
    assert audit.core.rows(small/'same_H_fleets.csv')
    write(out/'small_dependency_restore.json',dict(CSV_field_limit=csv.field_size_limit(),empty_root=True,original_root_fallback=False,
        SHA=sha(small/'same_H_fleets.csv')))

def run(label):
    fee,tick=campaign.fee_begin(label,0,180,True);code=1;q=OUT/'qualification'/label;q.mkdir()
    try:
        import round114_counterexample
        round114_counterexample.run(ROOT,q/'counterexample')
        claim_cases(q/'claims');zero_call_cases(q/'zero_calls');journal_cases(q/'journal',q/'zero_calls/premodel_deadline');supervisor_cases(q/'supervisor')
        inherited_contracts(q/'inherited_returns');compatibility(q/'compatibility')
        write(q/'summary.json',dict(passed=True,driver_processes=1,OS_children=0,Optimize=0,native_environment=0,
            synthetic_audit_values_separate_from_actual_CLI=True,performance_helpers=campaign.helpers(),test_SHA=sha(__file__)))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])

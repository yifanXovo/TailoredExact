"""One billed driver, in-process mocks and source-derived fixtures; no Optimize."""
from round113_common import *
import collections, copy, csv, hashlib, inspect, platform, shutil, types, traceback
import round113_campaign as campaign
import round113_audit as audit
import round90_lp_g_g3 as original
from round113_progress import OptionalPublisher, DenyDeleteHandle, original_atomic_status
from round111_decisions import pair

def controlled_sharing(out):
    out.mkdir();path=out/'runtime_status.json';launch=dict(number=1,id='mock',arm='P-S')
    value=dict(process_seconds=0.,message='controlled Windows contract')
    original_atomic_status(path,value);old_failure=None
    with DenyDeleteHandle(path):
        try:original_atomic_status(path,value)
        except OSError as e:old_failure=dict(errno=e.errno,winerror=e.winerror,error=repr(e))
        assert old_failure
        pub=OptionalPublisher(launch);pub(path,value);pub(path,dict(value,process_seconds=60.))
        assert pub.disabled and pub.attempts==1 and pub.skipped==1
    next_arm=OptionalPublisher(dict(launch,number=2));next_arm(path,value)
    assert not next_arm.disabled and next_arm.successes==1
    for error in [ValueError('serialization'),TypeError('logic')]:
        def fail(*args,error=error):raise error
        bad=OptionalPublisher(launch,fail)
        try:bad(path,value)
        except type(error):pass
        else:raise AssertionError('non-OSError swallowed')
    write(out/'receipt.json',dict(platform=platform.platform(),os_name=os.name,
        actual_CreateFileW=True,desired_access='GENERIC_READ',share_READ=True,share_WRITE=True,share_DELETE=False,
        old_replace_failure=old_failure,new_current_arm=pub.receipt(),next_arm=next_arm.receipt(),
        no_unique_historical_handle_holder_claim=True,non_filesystem_errors_propagate=True))

class Clock:
    def __init__(self):self.now=0.
    def monotonic(self):return self.now
    def perf_counter(self):return self.now
    def time(self):return 1791696000.+self.now
    def sleep(self,n):self.now+=n

def supervisor_cases(out):
    out.mkdir();results=[]
    for case in ['normal','display_failure','disk_stop_after_display_failure','memory_stop_after_display_failure',
        'deadline','necessary_sample_failure','necessary_final_write_failure']:
        directory=out/case;directory.mkdir();clock=Clock();child_state=dict(kill=0,wait=0,affinity_restored=False)
        duration=125 if case not in ['deadline','necessary_sample_failure','necessary_final_write_failure'] else 500 if case!='necessary_final_write_failure' else 1
        class Child:
            pid=123;returncode=None
            def poll(self):
                if self.returncode is None and clock.now>=duration:self.returncode=0
                return self.returncode
            def kill(self):child_state['kill']+=1;self.returncode=-9
            def wait(self,timeout=None):child_state['wait']+=1;assert self.poll() is not None;return self.returncode
        child=Child()
        class Affinity:
            def inherited_core(self,mask):return self
            def __enter__(self):return dict(before=dict(process_mask=4))
            def __exit__(self,*args):child_state['affinity_restored']=True
            def read_masks(self,pid=None):return dict(process_mask=4)
        memories=[];disks=[]
        def memory():
            memories.append(clock.now)
            return (4 if len(memories)==1 or case!='memory_stop_after_display_failure' else 1)*1024**3
        def disk(path):
            disks.append(clock.now)
            return types.SimpleNamespace(free=(4 if len(disks)>1 and case=='disk_stop_after_display_failure' else 20)*1024**3)
        pub=OptionalPublisher(dict(number=1,id=case,arm='P-S'),lambda *args:(_ for _ in ()).throw(OSError(13,'controlled optional failure')))
        if case in ['normal','deadline','necessary_sample_failure','necessary_final_write_failure']:
            pub=OptionalPublisher(dict(number=1,id=case,arm='P-S'))
        def append(path,value):
            if case=='necessary_sample_failure' and path.name=='samples.jsonl':raise OSError(13,'necessary sample failure')
            original.append_jsonl(path,value)
        def necessary(path,value):
            if case=='necessary_final_write_failure' and path.name=='postexit_audit_receipt.json':raise OSError(13,'necessary final receipt failure')
            original.write_new(path,value)
        namespace=dict(vars(original),ROOT=ROOT,CAMPAIGN=directory,time=clock,
            foreign_heavy_processes=lambda:[],memory_available=memory,
            shutil=types.SimpleNamespace(disk_usage=disk),subprocess=types.SimpleNamespace(Popen=lambda *a,**k:child),
            affinity=Affinity(),atomic_status=pub,append_jsonl=append,write_new=necessary,_arm_tick=0.,
            audit_launch=lambda *args:dict(passed=True,endpoint=dict(U=1.,L=0.,gap=1.,certificate=False)))
        l=dict(number=1,id=case,arm='P-S',destination=str(directory/'raw'),cap_seconds=180,hard_stop_seconds=178,command=['IN_PROCESS_MOCK'])
        error=None
        try:campaign.supervisor_function(namespace)(l,dict(common=dict(affinity_mask=4)),dict(prereg_sha256='mock',runner_sha256='mock'))
        except (OSError,RuntimeError) as e:error=repr(e)
        samples=[json.loads(s) for s in (directory/'raw/samples.jsonl').read_text().splitlines()] if (directory/'raw/samples.jsonl').exists() else []
        times=[s['process_seconds'] for s in samples]
        assert all(b-a>=60 for a,b in zip(times,times[1:])) and child_state['affinity_restored']
        if case=='normal':assert not error and child_state['kill']==0 and child_state['wait']==1
        elif case=='display_failure':assert not error and pub.attempts==1 and len(samples)==3 and len(memories)==4 and len(disks)==4
        elif case in ['disk_stop_after_display_failure','memory_stop_after_display_failure']:
            assert error and child_state['kill']==1 and child_state['wait']==1 and pub.disabled
        elif case=='deadline':assert not error and child_state['kill']==1 and child_state['wait']==1
        elif case=='necessary_sample_failure':assert error and child_state['kill']==1 and child_state['wait']==1
        else:assert error and child_state['kill']==0 and child_state['wait']==1
        results.append(dict(case=case,passed=True,error=error,sample_seconds=times,memory_check_seconds=memories,
            disk_check_seconds=disks,child=child_state,publication=pub.receipt(),coverage='actual source-extracted supervisor; in-process fake clock/child only',OS_child_starts=0))
    write(out/'receipt.json',dict(cases=results,supervisor_source_SHA=sha(original.__file__),extractor_SHA=sha(campaign.__file__),
        actual_OS_child_execution=False,native_execution=False,global_namespace_restored=True))

def fixture(out,branch):
    """Synthetic raw explicitly labelled; actual native matrix/vector retained."""
    source=OLD_ROOT/'results/unified_exact_round112/qualification/cli02/raw/02_H100_S0_P-S'
    zero=OLD_ROOT/'results/unified_exact_round112/qualification/zero01/raw/01_ownzero_S0_P-S'
    d=out/branch;d.mkdir();p=copy.deepcopy(read(OUT/'input_manifest.json')['qualification_roles'][0])
    p['reference']=read(OUT/'qualification/reference/H100/build.json');p['instance_path']=p['input_path']
    own=read(source/'result.json.round112.startup.json');r=read(zero/'result.json')
    positive=read(source/'result.json')
    for key in ['routes','objective','G','P']:
        r[key]=own[key]
    r.update(status='startup_deadline',strict_certified_original_problem=False,lower_bound=0.,upper_bound=own['objective'],
        final_UB=own['objective'],initial_heuristic_UB=own['objective'],process_shutdown_margin_seconds=30,
        process_return_code=0,gurobi_optimize_count=0)
    records=read(source/'observations.json');events=[copy.deepcopy(records[0]['payload']),copy.deepcopy(records[1]['payload'])]
    times=[.8,.9]
    if branch=='mapped_not_started':
        for path in source.glob('native.log.round112.start*'):shutil.copyfile(path,d/path.name)
        shutil.copyfile(source/'compact.lp',d/'compact.lp')
        for key,value in positive.items():
            if key.startswith(('gurobi_threads_','gurobi_seed_','gurobi_presolve_','gurobi_mip_gap_','gurobi_mip_gap_abs_')):
                r[key]=value
        for key in ['gurobi_version','gurobi_model_fingerprint','gurobi_num_vars','gurobi_num_constrs','gurobi_native_domain_audit_passed']:
            r[key]=positive[key]
        call=copy.deepcopy(records[2]['payload']);call['model_path']=str(d/'compact.lp');call['native_log_path']=str(d/'native.log')
        events += [call,dict(schema=1,sequence=4,kind='not_started',call=1,reason='no_remaining_original_work_window',actual_Optimize=False)]
        times += [89.999,90.001]
    elif branch=='startup_zero':
        p=copy.deepcopy(read(OLD_ROOT/'results/unified_exact_round112/input_manifest.json')['qualification_roles'][2])
        p['reference']=read(OLD_ROOT/'results/unified_exact_round112/qualification/reference/ownzero/build.json');p['instance_path']=p['input_path']
        own=read(zero/'result.json.round112.startup.json');r=read(zero/'result.json')
        records=read(zero/'observations.json');events=[copy.deepcopy(q['payload']) for q in records];times=[q['data_close_seconds'] for q in records]
    write(d/'result.json',r);write(d/'result.json.round112.startup.json',own)
    command=['SOURCE_DERIVED_FIXTURE','--plain-baseline','--round112-ens-start-compact']
    l=dict(number=1,id=p['id'],arm='P-S',destination=str(d),panel=p,cap_seconds=p['cap_seconds'],command=command)
    write(d/'launch.json',l);write(d/'completion.json',dict(returncode=0,stop_reason='normal_return',within_cap=True))
    phases=[('process_entry','start',0.),('round112_ENS_H','start',.01),('round112_ENS_H','complete',.7)]
    if branch=='mapped_not_started':phases += [('round112_compact_start','start',.75),('round112_compact_start','complete',89.998)]
    final=.03 if branch=='startup_zero' else 90.002
    if branch=='startup_zero':phases[2]=('round112_ENS_H','complete',.02)
    phases += [('final_result_serialization_start','start',final),('final_result_serialization_complete','complete',final+.001),('process_exit','complete',final+.002)]
    with (d/'phases.csv').open('x',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['sequence','process_seconds','event','status','nominal_deadline_remaining_seconds','work_deadline_remaining_seconds','detail'])
        for seq,(event,status,t) in enumerate(phases):writer.writerow([seq,t,event,status,p['cap_seconds']-t,p['cap_seconds']-30-t,'rc=0' if event=='process_exit' else ''])
    observations=[];(d/'journal').mkdir()
    for seq,(event,t) in enumerate(zip(events,times),1):
        event['sequence']=seq;raw=d/'journal'/f'event_{seq}.json';write(raw,event);h=sha(raw)
        (d/'journal'/f'event_{seq}.commit').write_text(f'NEJ1 {seq} {t} {raw.stat().st_size} {h}\n',encoding='ascii')
        observations.append(dict(sequence=seq,data_close_seconds=t,first_observed_seconds=t,effective_available_seconds=t,sha256=h,payload=event))
    write(d/'observations.json',observations)
    write(d/'fixture_provenance.json',dict(synthetic=True,production_schema_source_SHA=sha(ROOT/'src/NativeEvidenceJournal.cpp'),
        actual_preserved_Start_source=str(source) if branch=='mapped_not_started' else None,
        native_execution=False,Optimize=0,performance_observation=False,branch=branch))
    return l,observations

def lifecycle_cases(out):
    out.mkdir();results=[];identity=read(OUT/'qualification/cli01/identity.json')
    for branch in ['premodel_deadline','mapped_not_started','startup_zero']:
        l,observations=fixture(out,branch);d=Path(l['destination']);c=read(d/'completion.json')
        necessary=audit.adapter(l,observations,c,identity);assert necessary['passed']
        j=audit.ps_journal(ROOT,l['panel'],d);offline=audit.paid_endpoint(ROOT,l,identity,d,j)
        assert necessary['endpoint']['U']==offline['arm']['U'] and necessary['endpoint']['L']==offline['arm']['L']
        assert j['started']==0 and offline['lifecycle']['backend_exposure']=='BACKEND_NOT_EXPOSED'
        assert bool(offline['Start'])==(branch=='mapped_not_started')
        results.append(dict(branch=branch,passed=True,necessary_endpoint=necessary['endpoint'],offline_endpoint=offline['arm'],
            lifecycle=offline['lifecycle'],synthetic_fixture=True))
    l=read(out/'mapped_not_started/launch.json');events=read(out/'mapped_not_started/observations.json')
    mutators={
        'duplicate_cancel':lambda e:e+[copy.deepcopy(e[-1])],
        'unknown_cancel_ID':lambda e:[*e[:-1],dict(e[-1],payload=dict(e[-1]['payload'],call=2))],
        'wrong_cancel_reason':lambda e:[*e[:-1],dict(e[-1],payload=dict(e[-1]['payload'],reason='not_a_production_reason'))],
        'actual_optimize_cancel':lambda e:[*e[:-1],dict(e[-1],payload=dict(e[-1]['payload'],actual_Optimize=True))],
        'cancel_before_call':lambda e:[*e[:2],e[3],e[2]],
        'returned_after_cancel':lambda e:e+[dict(payload=dict(schema=1,sequence=5,kind='returned',call=1,return_code=0))],
        'native_witness_before_cancel':lambda e:[*e[:-1],dict(payload=dict(e[1]['payload'],sequence=4,call=1,source='native_MIPSOL_verified_original_routes')),e[-1]],
        'native_bound_after_cancel':lambda e:e+[dict(payload=dict(schema=1,sequence=5,kind='bound',call=1))],
        'duplicate_call':lambda e:[*e[:-1],copy.deepcopy(e[-2])],
    }
    for name,mutate in mutators.items():
        changed=mutate(copy.deepcopy(events))
        for seq,row in enumerate(changed,1):row['payload']['sequence']=seq
        errors={}
        for entry,call in [('necessary_audit',lambda:audit.adapter(l,changed,read(Path(l['destination'])/'completion.json'),identity)),
                           ('offline_boundary',lambda:audit.ps_journal(ROOT,l['panel'],Path(l['destination']),changed))]:
            try:call()
            except (AssertionError,KeyError) as error:errors[entry]=repr(error)
            else:raise AssertionError('invalid event flow accepted: '+name+' '+entry)
        results.append(dict(case=name,rejected=True,errors=errors))
    started=copy.deepcopy(events[:-1]);life=audit.event_lifecycle(started)
    assert life['started']==0 and life['not_started']==0 and life['unreturned_ids']==life['pending_declaration_ids']=={1}
    results.append(dict(case='declaration_without_cancel_and_return',actual_Optimize='UNKNOWN_PENDING_DECLARATION',
        unreturned_ids=sorted(life['unreturned_ids']),normal_no_Optimize_eligible=False))
    started.append(dict(payload=dict(events[1]['payload'],sequence=4,call=1,source='native_MIPSOL_verified_original_routes')))
    life=audit.event_lifecycle(started)
    assert life['started']==1 and life['returned']==life['not_started']==0 and life['unreturned_ids']=={1}
    results.append(dict(case='actual_native_activity_without_return',actual_Optimize=1,
        unreturned_ids=[1],normal_no_Optimize_eligible=False))
    # Gate mutations use the same real files; immutable snapshots preserve each rejection.
    base=out/'mapped_not_started';r=read(base/'result.json');c=read(base/'completion.json');j=audit.ps_journal(ROOT,l['panel'],base)
    own=audit.core.full_fleet(ROOT,l['panel'],read(base/'result.json.round112.startup.json'))
    for name,changes in [('started_result_with_cancel',dict(gurobi_optimize_count=1)),('native_bound_with_cancel',dict(gurobi_obj_bound_c_available=True)),
        ('optimal_with_cancel',dict(strict_certified_original_problem=True)),('error_return',dict(process_return_code=1))]:
        try:audit.validate_ps_lifecycle(ROOT,l,base,j,dict(r,**changes),c,own)
        except AssertionError as e:results.append(dict(case=name,rejected=True,error=repr(e)))
        else:raise AssertionError('invalid result accepted: '+name)
    write(out/'receipt.json',dict(cases=results,no_extra_Optimize=True,actual_deadline_cancellation_executed=False,
        necessary_audit_and_offline_boundary_shared=True))

def compatibility(out):
    """Changed event/control boundary only; original signed Start/matrix audit inherited."""
    out.mkdir();old=OLD_ROOT/'results/unified_exact_round112';reports=old/'reports_final'
    armrows=audit.core.evidence.rows(reports/'arms.csv');pairs=audit.core.evidence.rows(reports/'pairs.csv')
    complete=[a for a in armrows if a['formal_protocol_qualified']=='True'];assert len(complete)==12
    identity=read(old/'campaign/identity.json');records=[]
    for l in identity['launches'][:12]:
        d=Path(l['destination']);a=read(d/'audit.json');r=read(d/'result.json');w=read(d/'whole_arm_receipt.json')
        row=next(v for v in complete if int(v['number'])==l['number'])
        differences={key:float(row[key])-a['endpoint'][key] for key in ['U','L','gap']}
        assert all(abs(v)<=1e-7 for v in differences.values()),'retained numerical policy mismatch'
        assert float(row['complete_seconds'])==w['complete_seconds'] and a['passed'] and w['complete_seconds']<=l['cap_seconds']
        if l['arm']=='P-S':
            events=read(d/'observations.json');j=audit.event_lifecycle(events)
            assert j['declared']==j['started']==j['returned']==r['gurobi_optimize_count']==1 and not j['not_started']
            # Compile the same gate against a retained, SHA-checked old Start audit.
            old_start=a['Start'];assert sha(str(d/'native.log.round112.start')+'.before.matrix.json')==old_start['before_SHA']
            assert sha(str(d/'native.log.round112.start')+'.after.matrix.json')==old_start['after_SHA']
            assert sha(str(d/'native.log.round112.start')+'.values.csv')==old_start['vector_SHA']
            namespace=dict(vars(audit));namespace['inherited']=types.SimpleNamespace(start_audit=lambda *args:dict(old_start))
            exec(compile(inspect.getsource(audit.validate_ps_lifecycle),__file__+'::targeted_inherited_Start','exec'),namespace)
            own=audit.core.full_fleet(ROOT,l['panel'],read(d/'result.json.round112.startup.json'))
            result=namespace['validate_ps_lifecycle'](ROOT,l,d,j,r,read(d/'completion.json'),own)
            assert result['actual_Optimize']==1 and result['branch']=='ONE_STARTED_RETURNED_ORIGINAL_COMPACT_MIP'
        records.append(dict(number=l['number'],id=l['id'],arm=l['arm'],U=float(row['U']),L=float(row['L']),
            gap=float(row['gap']),certificate=a['endpoint']['certificate'],original_whole=w['complete_seconds'],
            original_necessary_audit_to_signed_final_reader_differences=differences,
            original_audit_SHA=sha(d/'audit.json'),original_whole_SHA=sha(d/'whole_arm_receipt.json'),
            new_replay_seconds_not_performance=True))
    evaluable=[p for p in pairs if p['evaluable']=='True'];assert len(evaluable)==18
    lookup={(a['id'],a['arm']):a for a in complete}
    for original_pair in evaluable:
        def endpoint(s):
            a=lookup[(original_pair['id'],s)]
            return dict(a,U=float(a['U']),L=float(a['L']),gap=float(a['gap']),complete_seconds=float(a['complete_seconds']),
                certificate=a['certificate']=='True',certificate_qualified=True,numbers_qualified=True,formal_protocol_qualified=True)
        v=pair(endpoint(original_pair['candidate']),endpoint(original_pair['control']))
        assert v['classification']==original_pair['classification'] and v['evaluable']
    partial=Path(identity['launches'][12]['destination'])
    missing=[name for name in ['result.json','completion.json','audit.json','whole_arm_receipt.json'] if not (partial/name).exists()]
    assert len(missing)==4
    conclusion=read(reports/'backend_conclusions.json')
    assert all(v['status']=='INCOMPLETE_ATTRIBUTION' and [q['classification'] for q in v['five_role_vector']]==
        ['WIN','WIN','LOSS','UNEVALUABLE','UNEVALUABLE'] for v in conclusion.values())
    write(out/'receipt.json',dict(qualified12=records,evaluable_old_pairs=18,missing_old_pairs=12,
        signed_L48_PS_gap=next(a['gap'] for a in records if a['id']=='R108-L48' and a['arm']=='P-S'),
        inherited_backend_conclusions=conclusion,partial13_endpoint_rejected=True,partial13_missing=missing,
        old_LP_matrices_reparsed=0,old_Start_audit_inherited_and_raw_SHAs_checked=True,
        same_H_authority_SHA=sha(reports/'same_H.csv'),performance_times_from_original_receipts_only=True))
    # Early small empty-root restore/CSV-width check, no native and no fallback.
    restored=out/'empty_restore';restored.mkdir();shutil.copyfile(reports/'same_H_fleets.csv',restored/'same_H_fleets.csv')
    csv.field_size_limit(64*1024*1024)
    a=audit.core.evidence.rows(restored/'same_H_fleets.csv');assert a
    assert sha(restored/'same_H_fleets.csv')==sha(reports/'same_H_fleets.csv')
    write(out/'small_restore_receipt.json',dict(empty_root_created=True,CSV_field_limit=csv.field_size_limit(),
        rows=len(a),source_SHA=sha(reports/'same_H_fleets.csv'),restored_SHA=sha(restored/'same_H_fleets.csv'),
        no_original_root_fallback_while_parsing_restored_file=True,Optimize=0))

def run(label):
    fee,tick=campaign.fee_begin(label,0,120,True);code=1
    q=OUT/'qualification'/label;q.mkdir()
    try:
        only_compatibility='--compatibility-only' in sys.argv[2:]
        only_lifecycle='--lifecycle-only' in sys.argv[2:]
        if only_lifecycle:
            lifecycle_cases(q/'lifecycle')
        elif not only_compatibility:
            controlled_sharing(q/'sharing');supervisor_cases(q/'supervisor');lifecycle_cases(q/'lifecycle')
        if not only_lifecycle:compatibility(q/'compatibility')
        write(q/'summary.json',dict(passed=True,driver_processes=1,OS_children=0,holder_in_driver=True,
            Optimize=0,actual_Win32_replace_covered=True,supervisor_coverage='source extracted with fake clock and child',
            synthetic_lifecycle_fixtures=True,targeted_old12_replay=True,no_old_LP_matrix_reparse=True,
            helper_SHA=sha(__file__),performance_helpers=campaign.helpers(),compatibility_only=only_compatibility,lifecycle_only=only_lifecycle,
            inherited_successful_finite_cases='finite01' if only_compatibility else None))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,0)

if __name__=='__main__':run(sys.argv[1])

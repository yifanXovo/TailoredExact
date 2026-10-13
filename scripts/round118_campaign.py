"""One fixed four-arm campaign and two once-only H100 qualification children."""
from round118_common import *
import copy,csv,inspect,shutil,traceback,types
import round115_campaign as inherited
import round90_lp_g_g3 as supervisor
from round109_prepare import COMMON
from round100_idle import ensure_idle
from round118_verify import verify
csv.field_size_limit(64*1024*1024)

def producer(name):
    namespace=dict(vars(inherited),ROOT=ROOT,OUT=OUT)
    return types.FunctionType(getattr(inherited,name).__code__,namespace,name)
production_check=producer('production_check')
finish_producer=producer('finish_producer')

def supervised(l,i,tick):
    publisher=inherited.OptionalPublisher(l);d=Path(l['destination'])
    namespace=dict(vars(supervisor),ROOT=ROOT,CAMPAIGN=d.parents[1],atomic_status=publisher,_arm_tick=tick,production_check=production_check)
    try:return inherited.supervisor_function(namespace)(l,i['prereg'],i)
    finally:
        if d.is_dir():write(d/'progress_publication_receipt.json',dict(publisher.receipt(),necessary_write_before_production=True,
            global_namespace_modified=False,qualification_fault_injected=False))

def argv(p,arm,d):
    prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=PE_SHA)
    cmd=supervisor.audited_runner_utilities.command_for(prereg,p,'P-GRB',d) if arm in ['P-GRB','P-S'] else supervisor.command_for(prereg,p,'ENS-C',d)
    if arm=='P-S':cmd+=['--round112-ens-start-compact']
    if arm=='M-B':cmd+=['--round98-state-service','m-binary']
    assert '--round100-continuous-quantities' not in cmd
    assert cmd[cmd.index('--time-limit')+1]==str(p['cap_seconds']-6)
    return cmd

def freeze_argv():
    check_identity();p=read(OUT/'input_manifest.json')['roles'][0]
    h=copy.deepcopy(read(ROOT/'results/unified_exact_round116/input_manifest.json')['qualification_roles'][0]);h['method_order']=['P-S','M-B']
    if not (OUT/'qualification/input_manifest.json').exists():write(OUT/'qualification/input_manifest.json',dict(roles=[h]))
    plans=[]
    for name,role in [('campaign',p),('qualification/cli01',h)]:
        role=copy.deepcopy(role)
        role['reference']=read(OUT/'qualification/reference/H100/build.json') if role['id']=='H100' else dict(fingerprint='REFERENCE_FINGERPRINT',rows='REFERENCE_ROWS',columns='REFERENCE_COLUMNS')
        launches=[]
        for n,arm in enumerate(role['method_order'],1):
            d=OUT/name/'raw'/f'{n:02d}_{role["id"]}_S0_{arm}'
            launches.append(dict(number=n,group_number=1,global_launch_number=n,id=role['id'],arm=arm,seed=0,panel=role,
                panel_kind=role['panel_kind'],destination=str(d),cap_seconds=role['cap_seconds'],hard_stop_seconds=role['cap_seconds']-2,command=argv(role,arm,d)))
        plans.append(dict(name=name,launches=launches))
    write(OUT/'argv_freeze.json',dict(frozen_UTC=utc(),input_SHA=p['input_sha256'],production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        recipe_SHA=sha(OUT/'source_recipe.json'),plans=plans,precedes_any_round118_native_qualification=True,
        reference_only_readback_slots=['REFERENCE_FINGERPRINT','REFERENCE_ROWS','REFERENCE_COLUMNS'],
        slot_rule='filled once by frozen zero-Optimize cold exporter; all algorithm arguments already literal; no discretionary change'))
    print('four formal argv and P-S then M-B H100 argv frozen; no native start')

def prepare():
    frozen=read(OUT/'argv_freeze.json');check_identity()
    for plan in frozen['plans']:
        camp=OUT/plan['name'];camp.mkdir(parents=True,exist_ok=True);launches=copy.deepcopy(plan['launches'])
        for l in launches:
            ref=OUT/'qualification/reference'/l['id'];l['panel']['reference']=read(ref/'build.json')
            assert sha(ref/'original.lp')==l['panel']['reference']['canonical_sha256']
            assert l['panel']['reference']['optimizer_calls']==0
            l['command']=argv(l['panel'],l['arm'],Path(l['destination']))
        p=launches[0]['panel'];dst=camp/'reference'/p['id'];dst.mkdir(parents=True,exist_ok=False)
        for n in ['original.lp','build.json']:shutil.copyfile(OUT/'qualification/reference'/p['id']/n,dst/n)
        i=dict(prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=PE_SHA),
            prereg_sha256=sha(OUT/'protocol.json'),protocol_path=(OUT/'protocol.json').relative_to(ROOT).as_posix(),
            runner_sha256=sha(__file__),helpers=helpers(),source_hashes=bindings(),candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,
            measured_source_commit=SOURCE,delivery_base_commit=BASE,references={p['id']:p['reference']},launches=launches,
            measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),original_native_window_unchanged=True)
        write(camp/'identity.json',i)
    i=read(OUT/'campaign/identity.json')
    write(OUT/'fixed_manifest.json',dict(groups=[dict(group_number=1,id='N40-R1-S',campaign='campaign',identity_SHA=sha(OUT/'campaign/identity.json'),
        fee_label='formal01',nominal_seconds=21600,administration_reserve=120)],launches=i['launches']))
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),
        argv_freeze_SHA=sha(OUT/'argv_freeze.json'),protocol_SHA=sha(OUT/'protocol.json'),measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),
        fixed_manifest_SHA=sha(OUT/'fixed_manifest.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        qualification_campaign_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),default_ENS_changed=False))
    print('new helpers and actual reference identities bound; no optimizer start')

def billed(name,label,qualification=False):
    camp=OUT/name;i=read(camp/'identity.json');count=len(i['launches']);assert count==(2 if qualification else 4)
    cap=600 if qualification else 26680
    fee,tick=fee_begin(label,count,cap,qualification);code=1
    try:
        ensure_idle();check_identity();assert i['helpers']==helpers() and i['runner_sha256']==sha(__file__)
        assert not (camp/'summary.jsonl').exists()
        if qualification:
            from qualify_round118 import qualify_in_process
            qualify_in_process('finite05')
        if not qualification:
            gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
            assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['helpers']==helpers()
            assert gate['campaign_identity_SHA']==sha(camp/'identity.json') and gate['fixed_manifest_SHA']==sha(OUT/'fixed_manifest.json')
            hfee=OUT/'fees'/gate['H100_fee_label'];closed=read(hfee/'receipt.json')
            assert closed['actual_exit_observed'] and closed['exit_code']==0
            if gate.get('qualification_campaign')=='qualification/final':
                assert closed['actual_native_children']==1 and gate['H100_fee_label']=='cli03'
                assert gate['explicit_postverifier_identity_exception_authorization_SHA']==sha(OUT/'budget_authorization_13.json')
                assert read(OUT/'budget_authorization_13.json')['reuse_sealed_PS_with_corrected_readonly_verifier'] is True
                old=read(OUT/'fees/cli02/receipt.json')
                assert old['actual_exit_observed'] and old['actual_native_children']==1 and old['exit_code']==1
                final=read(OUT/'qualification/final/identity.json');ps=final['launches'][0]
                assert ps['arm']=='P-S' and gate['reused_PS_producer_receipt_SHA']==sha(Path(ps['destination'])/'producer_receipt.json')
                assert gate['original_PS_actual_launch_identity_SHA']==sha(OUT/'qualification/cli02/identity.json')
                assert read(Path(ps['destination'])/'completion.json')['returncode']==0
                assert gate['H100_actual_Optimize_by_arm']['P-S']==1 and gate['H100_actual_Optimize_by_arm']['M-B']>0
            else:assert closed['actual_native_children']==2
        for n,l in enumerate(i['launches'],1):
            arm_tick=tick if n==1 else time.perf_counter();armunix=read(fee/'launch.json')['wrapper_creation_unix'] if n==1 else time.time()
            check_identity();assert not Path(l['destination']).exists() and sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
            write(fee/f'{n:02d}_before.json',dict(number=n,id=l['id'],arm=l['arm'],t0_perf=arm_tick,t0_unix=armunix))
            supervised(l,i,arm_tick);finish_producer(l,arm_tick,armunix);verify(l,i)
            write(fee/f'{n:02d}_after.json',dict(producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),
                total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json'),verification_complete=True))
            remaining=(count-n)*l['cap_seconds']
            assert time.perf_counter()-tick+budget()['paid_outer_seconds']+remaining+120<=28000
            if qualification:assert time.perf_counter()-tick<=cap
        if qualification:write(camp/'qualification_trailer.json',dict(passed=True,normal_returns=count,production_PE_SHA=PE_SHA,
            helpers=helpers(),inside_outer_clock=True,not_performance=True))
        if qualification:
            from qualify_round118_post import admit_in_process
            admit_in_process(name,label,'post02')
            assert time.perf_counter()-tick<=cap
        else:
            # All children have exited. Cross-arm revocation and the six pairs
            # are a paid group phase, never assigned to the following method.
            from read_round118 import rebuild
            group_tick=time.perf_counter()
            value=rebuild(ROOT,OUT/'reconstruction01')
            assert value['decision']['execution_stage']=='COMPLETE'
            assert len(value['arms'])==4 and len(value['pairs'])==6
            write(OUT/'group_verification_receipt.json',dict(seconds=time.perf_counter()-group_tick,
                inside_formal_wrapper_outer_clock=True,after_all_native_children_exit=True,
                no_solution_bound_Start_or_cache_transfer=True,not_assigned_to_an_individual_arm=True,
                current_core_SHA=sha(OUT/'reconstruction01/current_core.json'),Optimize=0,native_starts=0))
            assert time.perf_counter()-tick<=cap
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,qualification,code,sum((Path(l['destination'])/'launch.json').exists() for l in i['launches']))

if __name__=='__main__':
    if sys.argv[1]=='freeze-argv':freeze_argv()
    elif sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='billed':billed(sys.argv[2],sys.argv[3],'--qualification' in sys.argv[4:])
    else:raise ValueError(sys.argv[1])

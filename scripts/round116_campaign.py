"""Explicit manifest adapter, exactly six once-only groups; R115 producer unchanged."""
from round116_common import *
import copy,inspect,shutil,subprocess,traceback,types,csv
import round115_campaign as inherited
from round109_prepare import COMMON
from round100_idle import ensure_idle
from round115_verify import verify
csv.field_size_limit(64*1024*1024)

def helpers():
    names=set(inherited.helpers())
    names.update('scripts/'+n for n in ['round116_common.py','round116_campaign.py','round116_data.py','round116_prepare.py',
        'round116_reference_batch.cpp','read_round116.py','qualify_round116.py','qualify_round116_post.py'])
    return {p:sha(ROOT/p) for p in sorted(names)}

records=inherited.records
production_check=inherited.production_check
supervisor_function=inherited.supervisor_function
supervised=inherited.supervised
finish_producer=inherited.finish_producer
fee_pending=inherited.fee_pending

def outstanding_formal(exclude_group=None):
    fixed=read(OUT/'fixed_manifest.json') if (OUT/'fixed_manifest.json').exists() else None
    if not fixed:return dict(groups=6,children=24,nominal=50400,administration=720)
    groups=[g for g in fixed['groups'] if g['group_number']!=exclude_group and not (OUT/'fees'/g['fee_label']/'launch.json').exists()]
    return dict(groups=len(groups),children=4*len(groups),nominal=sum(g['nominal_seconds'] for g in groups),administration=120*len(groups))

def fee_begin(label,children,cap,qualification=False,group_number=None):
    tick,creation=process_origin();b=budget();d=OUT/'fees'/label;future=outstanding_formal(group_number)
    assert not b['unclosed'] and b['remaining_starts']>=children+1 and b['remaining_outer_seconds']>=cap
    assert b['remaining_starts']>=children+1+future['children']+future['groups']
    assert b['remaining_outer_seconds']>=cap+future['nominal']+future['administration']
    if qualification:
        assert b['qualification_starts']+children+1<=16 and b['qualification_seconds']+cap<=1800
    d.mkdir(parents=True,exist_ok=False)
    write(d/'launch.json',dict(command=sys.argv,cwd=str(ROOT),conservative_process_starts=children+1,qualification=qualification,
        declared_native_children=children,wrapper_pid=os.getpid(),wrapper_creation_unix=creation,outer_cap=cap,
        budget_before=b,helpers=helpers(),unstarted_formal_reservation=future,group_number=group_number))
    return d,tick

def prepare():
    check_identity();manifest=read(OUT/'input_manifest.json');protocol=read(OUT/'protocol.json');groups=[];all_launches=[]
    for p0 in manifest['roles']+manifest['qualification_roles']:
        qual=p0['panel_kind']=='qualification';group=0 if qual else p0['number']
        name='qualification/cli01' if qual else f'campaign/group{group:02d}'
        camp=OUT/name;camp.mkdir(parents=True,exist_ok=False);p=copy.deepcopy(p0)
        ref=OUT/'qualification/reference'/p['id'];p['reference']=read(ref/'build.json')
        assert sha(ref/'original.lp')==p['reference']['canonical_sha256'] and p['reference']['optimizer_calls']==0
        dst=camp/'reference'/p['id'];dst.mkdir(parents=True)
        for n in ['original.lp','build.json']:shutil.copyfile(ref/n,dst/n)
        prereg=dict(common=COMMON,candidate_binary=PE.relative_to(ROOT).as_posix(),candidate_binary_sha256=PE_SHA)
        launches=[]
        for n,arm in enumerate(p['method_order'],1):
            d=camp/'raw'/f'{n:02d}_{p["id"]}_S0_{arm}'
            cmd=inherited.supervisor.audited_runner_utilities.command_for(prereg,p,'P-GRB',d) if arm in ['P-GRB','P-S'] else inherited.supervisor.command_for(prereg,p,'ENS-C',d)
            if arm=='P-S':cmd+=['--round112-ens-start-compact']
            if arm=='M-B':cmd+=['--round98-state-service','m-binary']
            launches.append(dict(number=n,global_launch_number=None if qual else (group-1)*4+n,group_number=group,id=p['id'],arm=arm,
                seed=0,panel=p,panel_kind=p['panel_kind'],destination=str(d),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=cmd))
        identity=dict(prereg=prereg,prereg_sha256=sha(OUT/'protocol.json'),protocol_path=(OUT/'protocol.json').relative_to(ROOT).as_posix(),
            runner_sha256=sha(__file__),helpers=helpers(),source_hashes=bindings(),candidate_binary_sha256=PE_SHA,dll_sha256=DLL_SHA,
            measured_source_commit=SOURCE,delivery_base_commit=BASE,references={p['id']:p['reference']},launches=launches,
            measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),dependency_graph_SHA=sha(OUT/'producer_dependency_graph.json'),
            original_native_window_unchanged=True,group_number=group)
        write(camp/'identity.json',identity)
        if not qual:
            groups.append(dict(group_number=group,id=p['id'],campaign=name,identity_SHA=sha(camp/'identity.json'),fee_label=f'formal{group:02d}',nominal_seconds=4*p['cap_seconds'],administration_reserve=120))
            all_launches+=launches
    assert len(all_launches)==24 and sum(l['cap_seconds'] for l in all_launches)==50400
    write(OUT/'fixed_manifest.json',dict(groups=groups,launches=all_launches,protocol_SHA=sha(OUT/'protocol.json'),input_manifest_SHA=sha(OUT/'input_manifest.json')))
    write(OUT/'candidate_identity.json',dict(production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        source_bindings=bindings(),helpers=helpers(),input_manifest_SHA=sha(OUT/'input_manifest.json'),protocol_SHA=sha(OUT/'protocol.json'),
        measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),dependency_graph_SHA=sha(OUT/'producer_dependency_graph.json'),
        fixed_manifest_SHA=sha(OUT/'fixed_manifest.json'),full_argv=[l['command'] for l in all_launches],
        qualification_campaign_identity_SHA=sha(OUT/'qualification/cli01/identity.json'),source_recipe_SHA=sha(OUT/'source_recipe.json'),
        source_snapshot_SHA=sha(OUT/'source/snapshot.json'),raw_source_SHA=manifest['raw_station_response_SHA'],
        license_SHA=read(OUT/'source/snapshot.json')['license_SHA'],projection_contract_SHA=sha(OUT/'projection_contract.json'),
        reference_receipt_SHA=sha(OUT/'fees/reference01/receipt.json'),default_ENS_changed=False,
        offline_reader_SHA=sha(ROOT/'scripts/read_round116.py'),qualification_test_SHA=sha(ROOT/'scripts/qualify_round116.py'),
        qualification_post_driver_SHA=sha(ROOT/'scripts/qualify_round116_post.py')))
    print('24 formal argv and4 qualification argv frozen; no solver starts')

def billed(name,label,qualification=False):
    camp=OUT/name;i=read(camp/'identity.json');count=len(i['launches']);assert count==4
    group=None if qualification else i['group_number'];cap=540 if qualification else 4*i['launches'][0]['cap_seconds']+120
    fee,tick=fee_begin(label,count,cap,qualification,group);code=1
    try:
        ensure_idle();check_identity();assert i['source_hashes']==bindings() and i['helpers']==helpers() and i['runner_sha256']==sha(__file__)
        assert not records(camp)
        if not qualification:
            gate=read(OUT/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
            assert gate['candidate_identity_SHA']==sha(OUT/'candidate_identity.json') and gate['helpers']==helpers()
            assert gate['fixed_manifest_SHA']==sha(OUT/'fixed_manifest.json')
        for n,l in enumerate(i['launches'],1):
            arm_tick=tick if n==1 else time.perf_counter();armunix=read(fee/'launch.json')['wrapper_creation_unix'] if n==1 else time.time()
            check_identity();assert not Path(l['destination']).exists() and sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
            write(fee/f'{n:02d}_before.json',dict(number=n,id=l['id'],arm=l['arm'],t0_perf=arm_tick,t0_unix=armunix))
            supervised(l,i,arm_tick);finish_producer(l,arm_tick,armunix);verify(l,i)
            write(fee/f'{n:02d}_after.json',dict(producer_receipt_SHA=sha(Path(l['destination'])/'producer_receipt.json'),
                total_receipt_SHA=sha(Path(l['destination'])/'arm_total_receipt.json'),verification_complete=True))
            # Native windows remain per-arm fixed. Required verification is never
            # cancelled merely for exceeding30s or the planned120s group reserve.
            future=outstanding_formal(group);elapsed=time.perf_counter()-tick
            assert elapsed+budget()['paid_outer_seconds']+future['nominal']+future['administration']<=65000
            if qualification:assert elapsed<=cap
        if qualification:write(camp/'qualification_trailer.json',dict(passed=True,normal_returns=count,production_PE_SHA=PE_SHA,
            helpers=helpers(),inside_outer_clock=True,not_performance=True))
        code=0
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:fee_pending(fee,tick,qualification,code,sum((Path(l['destination'])/'launch.json').exists() for l in i['launches']))

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='billed':billed(sys.argv[2],sys.argv[3],'--qualification' in sys.argv[4:])
    else:raise ValueError(sys.argv[1])

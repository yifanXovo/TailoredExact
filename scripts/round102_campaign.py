"""Serial frozen full-production experiment entry point. Import launches nothing.

prepare <name> <roles.json> pins the current source, runtime and fresh P matrix.
run <name> <number> admits exactly the next never-started arm, no automatic retry.
The inherited R90 supervisor accounts for the whole process and durable journal.
"""
import argparse,json,math,subprocess,time,shutil
import round90_lp_g_g3 as r90
import round94_lpg_formal_recovery_v3 as scope
import round96_external as ext
from round100_idle import ensure_idle
from pathlib import Path
from round102_common import *

def helpers():
    names=['round102_campaign.py','round102_common.py','round101_common.py','round90_lp_g_g3.py','round88_a1_g3.py',
        'round94_lpg_formal_recovery_v3.py','round94_lpg_contemporary.py','round86_native_evidence.py',
        'analyze_round61.py','round70_affinity.py','round83_audit_v2.py','round75_startup.py',
        'round96_external.py','round96_prepare.py']
    return {'scripts/'+n:sha(ROOT/'scripts'/n) for n in names}|{
        'results/unified_exact_round94/preregistration.json':sha(ROOT/'results/unified_exact_round94/preregistration.json')}

def adapter(launch,observations,completion,identity):
    dest=Path(launch['destination']);arm=launch['arm'];reason=completion['stop_reason']
    native_scope=scope.scope_receipt(launch,observations)
    result=read(dest/'result.json') if reason=='normal_return' else None
    if result is not None:
        if arm!='P-GRB':
            ledger=dest/'external/paper_optimize_ledger.csv'
            ledger_count=len(scope.ledger_rows(dest)[1]) if ledger.exists() else 0
            assert native_scope['native_calls']==ledger_count,'Optimize ledger/journal call count differs'
        expected={'P-GRB':'custom','ENS-C':'research-round83-vds-equal-net-exchange',
            'R1':'research-round98-ensc-state-service-aggregate',
            'R2':'research-round98-ensc-state-service-projected',
            'R3':'research-round98-ensc-state-service-vehicle-state',
            'Q-I':'research-round99-ensc-discrete-structure-q-integer',
            'M-B':'research-round99-ensc-discrete-structure-m-binary',
            'M-BL':'research-round99-ensc-discrete-structure-m-binary-linked',
            'ENS-Q':'research-round100-ensc-continuous-quantities',
            'FLEET-SHELL':'research-round101-ensc-fleet-shell-tree',
            'FLEET-SHADOW':'research-round101-ensc-fleet-shadow-tree',
            'FLEET-SUBMIT':'research-round101-ensc-fleet-submit-tree',
            'FLEET-ROOT':'research-round101-ensc-fleet-submit-root','J-SHELL':'research-round102-ensc-service-shell-root','J-SHADOW':'research-round102-ensc-service-shadow-root','J-SUBMIT':'research-round102-ensc-service-submit-root'}[arm]
        assert result['algorithm_preset']==expected
    audited=r90.evidence.audit(ROOT,launch['panel'],observations,identity['candidate_binary_sha256'])
    r90.evidence.finalize_endpoint(ROOT,launch['panel'],arm,audited,observations,result,reason,launch['panel']['reference'])
    if arm=='P-GRB':
        assert sha(dest/'compact.lp')==launch['panel']['reference']['canonical_sha256']
        if result is not None:
            assert result['gurobi_hga_start_requested'] is False and result['gurobi_optimize_count']==1
            for key,field in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:
                assert result[field]==launch['panel']['reference'][key]
    elif result is not None:
        folder=dest/'hga.csv.exchange';assert folder.is_dir()
        initial=r90.normalize(read(folder/'initial.json'))
        audited['neutral_exchange']=r90.replay_exchange(launch['panel'],folder,initial)
        assert not read(folder/'result.json')['verification_failed']
        final=r90.normalize(read(folder/'final.json'))
        startup=[r['payload'] for r in observations if r['payload']['kind']=='witness' and r['payload']['call']==0]
        assert len(startup)==1
        assert r90.route_hash(r90.normalize(startup[0])) in {r90.route_hash(initial),r90.route_hash(final)}
    if result is not None:
        audited['parameter_readback']=scope.v2.parameter_readback(result,require_call=native_scope['native_calls']>0,
            arm='P-GRB' if arm=='P-GRB' else 'ENS-C')
    audited['native_scope_adapter']=native_scope;audited['passed']=True
    return audited

def prepare(name,roles_path):
    ensure_idle();camp=OUT/name;assert not camp.exists();camp.mkdir()
    protocol=read(roles_path);roles=protocol['roles'];binary=BUILD/'ExactEBRP.exe'
    grouped=protocol.get('reference_billing')=='one_finite_batch'
    if grouped:
        assert 1<=len(roles)<=3 and protocol['phase'] in ['fleet qualification','fleet isolation','fleet development','fleet confirmation','fleet long','service qualification','service isolation','service development','service confirmation','service long']
        write(camp/'reference_batch_launch.json',dict(planned_children=len(roles),planned_optimizer_calls=0,
            ids=[r['id'] for r in roles],maximum_child_seconds=60,source_sha256=sha(__file__)))
    reference_batch_tick=time.perf_counter()
    prereg=dict(common=ext.COMMON,candidate_binary=binary.relative_to(ROOT).as_posix(),candidate_binary_sha256=sha(binary))
    references={};launches=[]
    for original in roles:
        p=dict(original);assert sha(ROOT/p['input_path'])==p['input_sha256']
        dest=camp/'reference'/p['id'];dest.mkdir(parents=True)
        if 'prepaid_reference' in p:
            # An explicitly declared earlier finite qualification already paid
            # for this SAME frozen builder/input. Copy exact bytes, no process.
            parent=OUT/'diagnostics'/p['prepaid_reference'];paid=read(parent/'summary.json')
            assert paid['passed'] and paid['production_binary_sha256']==sha(binary)
            assert paid['reference_binary_sha256']==sha(BUILD/'Round65ReferenceBuild.exe')
            assert paid['source_bindings']==bindings() and paid['role']['input_sha256']==p['input_sha256']
            source=parent/'plain_reference';fresh=read(source/'build.json')
            for filename in ['build.json','original.lp']:shutil.copy2(source/filename,dest/filename)
            write(dest/'completion.json',dict(returncode=0,outer_seconds=0,optimizer_calls=0,
                already_billed_parent='qualification/'+p['prepaid_reference'],copy_only=True,
                source_summary_sha256=sha(parent/'summary.json')))
            write(dest/'launch.json',dict(copy_only=True,optimizer_calls=0,source=str(source)))
        else:
            fresh=build_reference(p,dest)
        assert fresh['optimizer_calls']==0
        if 'reference' in p:assert fresh==p['reference'],'fresh plain matrix drift'
        p['reference']=references[p['id']]=fresh;p['instance_path']=p['input_path']
        for arm in p['method_order']:
            assert arm in ['P-GRB','ENS-C','FLEET-SHELL','FLEET-SHADOW','FLEET-SUBMIT','FLEET-ROOT','J-SHELL','J-SHADOW','J-SUBMIT']
            number=len(launches)+1;dest=camp/'raw'/f'{number:02d}_{p["id"]}_{arm}'
            command=(r90.audited_runner_utilities.command_for(prereg,p,arm,dest) if arm=='P-GRB'
                     else r90.command_for(prereg,p,'ENS-C',dest))
            if arm in ['R1','R2','R3','Q-I','M-B','M-BL']:command+=['--round98-state-service',
                {'R1':'aggregate','R2':'projected','R3':'vehicle-state','Q-I':'q-integer','M-B':'m-binary','M-BL':'m-binary-linked'}[arm]]
            if arm.startswith('J-'):
                command+=['--round102-service-cuts',{'J-SHELL':'shell','J-SHADOW':'shadow','J-SUBMIT':'submit'}[arm]]
            if arm.startswith('FLEET-'):
                mode={'FLEET-SHELL':'shell','FLEET-SHADOW':'shadow','FLEET-SUBMIT':'submit','FLEET-ROOT':'submit'}[arm]
                command+=['--round101-fleet-cuts',mode,'--round101-fleet-range','root' if arm=='FLEET-ROOT' else 'tree']
            launches.append(dict(number=number,id=p['id'],arm=arm,panel=p,stage=name,destination=str(dest),
                cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=command))
    if grouped:
        completions=[read(camp/'reference'/p['id']/'completion.json') for p in roles]
        assert all(c['returncode']==0 and c['optimizer_calls']==0 for c in completions)
        write(camp/'reference_batch_receipt.json',dict(actual_children=len(roles),optimizer_calls=0,
            outer_seconds=time.perf_counter()-reference_batch_tick,
            child_seconds=sum(c['outer_seconds'] for c in completions),
            completion_sha256={p['id']:sha(camp/'reference'/p['id']/'completion.json') for p in roles},
            experimental_starts=1,stop_reason='normal_return',passed=True))
    write(camp/'identity.json',dict(prereg=prereg,prereg_sha256=sha(roles_path),runner_sha256=sha(__file__),
        candidate_binary_sha256=prereg['candidate_binary_sha256'],source_hashes=bindings(),helpers=helpers(),
        dll_sha256=sha('D:/gurobi1302/win64/bin/gurobi130.dll'),input_manifest=str(Path(roles_path).resolve()),
        reference_binary_sha256=sha(BUILD/'Round65ReferenceBuild.exe'),
        references=references,launches=launches,planned_starts=len(launches),
        maximum_process_seconds=sum(x['cap_seconds'] for x in launches),optimizer_calls=0,
        no_algorithm_component_time_slices=True,prepared_unix=time.time()))
    print(json.dumps(dict(prepared=name,planned_starts=len(launches),maximum_process_seconds=sum(x['cap_seconds'] for x in launches))))

def build_reference(p,dest):
        cmd=list(map(str,[BUILD/'Round65ReferenceBuild.exe',p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],dest]))
        write(dest/'launch.json',dict(command=cmd,optimizer_calls=0,binary_sha256=sha(BUILD/'Round65ReferenceBuild.exe')))
        tick=time.perf_counter()
        with (dest/'stdout.log').open('x') as so,(dest/'stderr.log').open('x') as se:
            ret=subprocess.run(cmd,cwd=ROOT,env=env(),stdout=so,stderr=se,timeout=60)
        write(dest/'completion.json',dict(returncode=ret.returncode,outer_seconds=time.perf_counter()-tick,optimizer_calls=0))
        assert ret.returncode==0
        fresh=read(dest/'build.json');assert fresh['optimizer_calls']==0
        if 'reference' in p:assert fresh==p['reference'],'fresh plain matrix drift'
        return fresh

def run(name,number):
    ensure_idle();camp=OUT/name;q=read(camp/'identity.json')
    assert sha(__file__)==q['runner_sha256'],'frozen runner changed'
    assert q['source_hashes']==bindings() and q['helpers']==helpers()
    assert sha(ROOT/q['prereg']['candidate_binary'])==q['candidate_binary_sha256']
    assert sha(q['input_manifest'])==q['prereg_sha256']
    assert sha('D:/gurobi1302/win64/bin/gurobi130.dll')==q['dll_sha256']
    assert sha(BUILD/'Round65ReferenceBuild.exe')==q['reference_binary_sha256']
    records=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()] if (camp/'summary.jsonl').exists() else []
    assert len(records)==number-1 and all(r['audit_passed'] for r in records),'only a never-started valid prefix can continue'
    launch=q['launches'][number-1];assert not Path(launch['destination']).exists()
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    r90.CAMPAIGN=camp;r90.audit_launch=adapter
    record=r90.run_one(launch,q['prereg'],q)
    same=[r for r in records+[record] if r['id']==launch['id']]
    lowers=[r['endpoint']['L'] for r in same];uppers=[r['endpoint']['U'] for r in same if r['endpoint']['U'] is not None]
    assert not uppers or max(lowers)<=min(uppers)+1e-7,'cross-arm contradiction; offline check only'
    write(camp/f'cross_arm_{launch["id"]}_{len(same)}.json',dict(strongest_L=max(lowers),
        best_physical_U=min(uppers) if uppers else None,passed=True,scope='no combined certificate'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);parser.add_argument('name')
    parser.add_argument('value');a=parser.parse_args()
    prepare(a.name,a.value) if a.action=='prepare' else run(a.name,int(a.value))

"""Isolated R96 primal OFF/ON/P campaign, one never-started arm per invocation.

Uses the qualified common R95+R96 build, not the frozen R90 LP-G executable.
All native supervision and original-problem evidence promotion reuse R90/R94.
"""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path
import round90_lp_g_g3 as r90
import round94_lpg_formal_recovery_v3 as scope
import round96_external as external
from round96_prepare import ROOT,OUT,read,write,sha,evidence,citi
from round96_order_analyze import operations,duration

CAMP=OUT/'primal'

def bindings():
    paths=['scripts/round96_primal.py','scripts/round96_order_analyze.py','scripts/round96_primal_inputs.py',
           'scripts/round96_order_oracle.py','scripts/round96_primal_audit_fixture.py',
           'scripts/round96_external.py','scripts/round90_lp_g_g3.py','scripts/round88_a1_g3.py',
           'scripts/round94_lpg_formal_recovery_v3.py','scripts/round94_lpg_contemporary.py',
           'scripts/round86_native_evidence.py','scripts/analyze_round61.py','scripts/round70_affinity.py',
           'scripts/round83_audit_v2.py','scripts/round75_startup.py',
           'scripts/round76_startup.py','scripts/round78_audit.py','scripts/round76_qualify.py',
           'scripts/round96_prepare.py','scripts/generate_citibike443_regional_v1.py',
           'results/unified_exact_round96/production_build_identity.json',
           'results/unified_exact_round96/primal_validation_inputs.json',
           'results/unified_exact_round96/fixed_route_cases.json',
           'results/unified_exact_round96/route_order_oracle.json',
           'results/unified_exact_round96/primal_auditor_fixture.json',
           'results/unified_exact_round96/route_order_admission.md',
           'results/unified_exact_round96/primal_followup_plan.md']
    return {path:sha(ROOT/path) for path in paths}

def build_identity():
    build=read(OUT/'production_build_identity.json')
    assert sha(ROOT/build['binary_path'])==build['binary_sha256']
    for path,expected in build['source_hashes'].items():assert sha(ROOT/path)==expected,path
    assert sha(build['gurobi_dll_path'])==build['gurobi_dll_sha256']
    return build

def idle():
    external.ensure_idle()
    raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match 'round96_reorder|round96_order_diagnostic|round96_multi_diagnostic' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    assert not raw,raw

def prepare():
    idle();build=build_identity();assert not CAMP.exists()
    oracle_gate=read(OUT/'route_order_oracle.json');fixture_gate=read(OUT/'primal_auditor_fixture.json')
    assert oracle_gate['passed'] and fixture_gate['passed']
    assert oracle_gate['source_sha256']==sha(ROOT/'scripts/round96_order_oracle.py')
    assert fixture_gate['reader_sha256']==sha(__file__)
    assert fixture_gate['fixture_sha256']==sha(ROOT/'scripts/round96_primal_audit_fixture.py')
    assert oracle_gate['completed_sha256']==fixture_gate['completed_sha256']==sha(OUT/'route_order/completed.json')
    validation=read(OUT/'primal_validation_inputs.json')
    f5=dict(next(c['panel'] for c in read(OUT/'fixed_route_cases.json')['cases'] if c['id']=='F5_final'))
    f2=dict(next(p for p in read(ROOT/'results/unified_exact_round94/preregistration.json')['roles'] if p['id']=='F2'))
    f5.update(cap_seconds=3600,method_order=['ENS-C','P-GRB','ORDER-ON'],input_path=f5['instance_path'])
    f2.update(cap_seconds=900,method_order=['ORDER-ON','P-GRB','ENS-C'])
    panels=[f5,f2]+validation['roles'];assert [p['id'] for p in panels]==['F5','F2','V1','V2']
    prereg=dict(candidate_binary=build['binary_path'],candidate_binary_sha256=build['binary_sha256'],common=external.COMMON)
    assert sha(external.REFERENCE)==read(OUT/'external/identity.json')['reference_binary_sha256']
    CAMP.mkdir();launches=[];references={}
    env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    for item in panels:
        p=dict(item,instance_path=item['input_path']);assert sha(ROOT/p['input_path'])==p['input_sha256']
        parsed=citi.parse_instance_mirror(ROOT/p['input_path']);p['M']=parsed['M'];p['V']=parsed['V']
        dest=CAMP/'reference'/p['id'];dest.mkdir(parents=True)
        command=list(map(str,[external.REFERENCE,p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],dest]))
        write(dest/'launch.json',dict(command=command,optimizer_calls=0,binary_sha256=sha(external.REFERENCE)))
        tick=time.perf_counter()
        with (dest/'stdout.log').open('x') as so,(dest/'stderr.log').open('x') as se:
            ret=subprocess.run(command,cwd=ROOT,env=env,stdout=so,stderr=se,timeout=30)
        write(dest/'completion.json',dict(returncode=ret.returncode,wall_seconds=time.perf_counter()-tick,optimizer_calls=0))
        assert ret.returncode==0;p['reference']=read(dest/'build.json');references[p['id']]=p['reference']
        assert p['reference']['optimizer_calls']==0
        for arm in p['method_order']:
            number=len(launches)+1;dest=CAMP/'raw'/f'{number:02d}_{p["id"]}_{arm}'
            command=(r90.audited_runner_utilities.command_for(prereg,p,arm,dest) if arm=='P-GRB'
                     else r90.command_for(prereg,p,'ENS-C',dest)+['--round96-route-order','true' if arm=='ORDER-ON' else 'false'])
            launches.append(dict(number=number,id=p['id'],arm=arm,stage='primal',panel=p,destination=str(dest),
                cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=command))
    for role in references:
        pair=[r['command'].copy() for r in launches if r['id']==role and r['arm']!='P-GRB']
        for command in pair:
            for flag in ['--round96-route-order','--out','--log','--process-phase-ledger','--external-gini-artifact-dir',
                         '--primal-heuristic-generation-log','--progress-log','--native-evidence-dir']:
                command[command.index(flag)+1]='<permitted-difference>'
        assert pair[0]==pair[1]
    assert len(launches)==12 and sum(r['cap_seconds'] for r in launches)==24300
    write(CAMP/'identity.json',dict(candidate_binary_sha256=build['binary_sha256'],source_ref=build['source_ref'],
        prereg_sha256=sha(OUT/'primal_followup_plan.md'),runner_sha256=sha(__file__),bindings=bindings(),
        build_identity_sha256=sha(OUT/'production_build_identity.json'),launches=launches,references=references,
        prereg=prereg,optimizer_calls=0,reference_exports=4))

def order_trace(launch,observations,result,fixture_root=None):
    root=Path(launch['destination'])/'hga.csv.route_order' if fixture_root is None else fixture_root
    p=launch['panel']
    if not root.is_dir():
        assert not result.get('external_gini_tree_root_coverage_valid');return dict(triggered=False)
    initial=read(root/'initial.json');final=read(root/'final.json')
    verified=0;closures=[]
    for path in sorted(root.rglob('*.json')):
        obj=read(path)
        if not isinstance(obj,dict) or 'routes' not in obj:continue
        obj['F']=obj.get('F',obj.get('objective'))
        assert evidence.physical_module.physical(p,obj)['original_T_feasible'];verified+=1
    folders=sorted(root.glob('old_*'),key=lambda path:int(path.name.split('_')[-1]))
    for folder in folders:
        state=read(folder/'result.json');assert not state['verification_failed']
        if state['deadline']:
            assert folder==folders[-1]
            closures.append(dict(deadline=True,exhaustion_not_claimed=True,physical_snapshots_verified=True))
        else:closures.append(r90.replay_exchange(p,folder,r90.normalize(read(folder/'initial.json'))))
    moves=sorted(root.glob('order_*.json'),key=lambda path:int(path.stem.split('_')[-1]))
    for k,path in enumerate(moves,1):
        assert path.name==f'order_{k}.json'
        before=read(root/f'old_{k-1}'/'final.json');after=read(path)
        assert operations(before)==operations(after) and before['inventory']==after['inventory'] and before['F']==after['F']
        distances=read(root/f'old_{k-1}'/'actual_distances.json')
        assert duration(after,p,distances,p['M'])<duration(before,p,distances,p['M'])
    startup=[r['payload'] for r in observations if r['payload']['kind']=='witness' and r['payload']['call']==0]
    assert len(startup)==1
    handed=r90.route_hash(r90.normalize(startup[0]));first=r90.route_hash(r90.normalize(initial));last=r90.route_hash(r90.normalize(final))
    assert handed in {first,last}
    assert final['F']<=initial['F']+1e-12
    return dict(triggered=True,physical_witnesses_replayed=verified,order_moves=len(moves),old_closures=closures,
        initial_F=initial['F'],final_F=final['F'],handoff_initial=handed==first,handoff_final=handed==last)

def auditor():
    old=scope.audit_adapter(r90)
    def audit(launch,observations,completion,identity):
        if launch['arm']!='ORDER-ON':return old(launch,observations,completion,identity)
        checked_scope=scope.scope_receipt(launch,observations)
        normal=completion['stop_reason']=='normal_return'
        result=read(Path(launch['destination'])/'result.json') if normal else None
        if normal:assert result['algorithm_preset']=='research-round96-ensc-route-order'
        audited=evidence.audit(ROOT,launch['panel'],observations,identity['candidate_binary_sha256'])
        evidence.finalize_endpoint(ROOT,launch['panel'],launch['arm'],audited,observations,result,completion['stop_reason'],{})
        if normal:
            audited['five_native_parameter_readback']=scope.v2.parameter_readback(result,
                require_call=checked_scope['native_calls']>0,arm=launch['arm'])
            audited['route_order']=order_trace(launch,observations,result)
        audited.update(native_scope_adapter=checked_scope,passed=True,lp_g_split_evidence=None)
        return audited
    return audit

def run(number):
    idle();build_identity();identity=read(CAMP/'identity.json');assert bindings()==identity['bindings']
    path=CAMP/'summary.jsonl';records=[json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    assert len(records)==number-1 and all(r['audit_passed'] for r in records)
    launch=identity['launches'][number-1];assert not Path(launch['destination']).exists()
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    r90.CAMPAIGN=CAMP;r90.audit_launch=auditor()
    result=r90.run_one(launch,identity['prereg'],identity);records.append(result)
    same=[r for r in records if r['id']==launch['id']];lower=[];upper=[]
    for row in same:
        audit=read(Path(row['destination'])/'audit.json');assert audit['passed']
        lower.append(max(audit['LB'],row['endpoint']['L']))
        upper.extend(w['F'] for w in audit['witnesses'])
        if audit.get('final_physical_verification'):upper.append(audit['final_physical_verification']['F'])
    offline=[];known=read(OUT/'fixed_route_cases.json');panel=launch['panel']
    for ref in known['offline_references']:
        old_panel=next(c['panel'] for c in known['cases'] if c['role']==ref['role'])
        if all(old_panel[key]==panel[key] for key in ['input_sha256','T_seconds','pickup_seconds','drop_seconds','lambda']):
            path=ROOT/ref['witness_path'];assert sha(path)==ref['witness_sha256']
            checked=evidence.physical_module.physical(panel,read(path));assert checked['original_T_feasible']
            offline.append(dict(path=ref['witness_path'],F=checked['F']));upper.append(checked['F'])
    assert not upper or max(lower)<=min(upper)+1e-7
    write(CAMP/f'cross_arm_{launch["id"]}_{len(same)}.json',dict(passed=True,strongest_L=max(lower),
        best_physical_U=min(upper) if upper else None,offline_known_witnesses=offline,
        scope='Offline consistency only; never merged certificate or production Start'))
    if len(same)==3:
        # Reuse the frozen materiality rules by substituting the candidate label,
        # not by altering the stored arm identity or any endpoint evidence.
        adapted=[dict(r,arm='LP-G' if r['arm']=='ORDER-ON' else r['arm']) for r in same]
        write(CAMP/f'decision_signals_{launch["id"]}.json',dict(candidate='ORDER-ON',
            signals=external.r94.severe_signals(adapted,launch['id']),
            action='Retain all planned outcomes; signal is not instance-specific fallback'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);parser.add_argument('--number',type=int)
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:
        assert args.number and 1<=args.number<=12;run(args.number)

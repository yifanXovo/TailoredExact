"""Bounded real-risk qualification: six parses, cold references and contracts."""
from round163_common import *
import collections, copy, math
from fractions import Fraction as F

EXPORTER=WORK/'build-cache/round137/Round137Export.exe'
EXPORTER_SHA='ee5ea33f96e3ae38c005bd75cbe3abb8eaefb483d2760cac7e4168728ac6c4d1'

def reference(p):
    dest=OUT/'qualification/references'/p['id']
    if dest.exists():
        b=read(dest/'build.json');receipt=read(OUT/'qualification/export_logs'/p['id']/'receipt.json')
        assert receipt['exit_code']==0 and receipt['Optimize']==0 and b['optimizer_calls']==0
        assert sha(dest/'original.lp')==b['canonical_sha256']
        return b
    args=[EXPORTER,ROOT/p['input_path'],p['T_seconds'],0,0,0,'p',dest,format(p['lambda'],'.17g'),'off']
    folder=OUT/'qualification/export_logs'/p['id'];folder.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    with (folder/'stdout.log').open('xb') as so,(folder/'stderr.log').open('xb') as se:
        result=subprocess.run(list(map(str,args)),cwd=ROOT,env=meter.environment(),stdout=so,stderr=se,timeout=60)
    write(folder/'receipt.json',dict(command=list(map(str,args)),exit_code=result.returncode,seconds=time.perf_counter()-start,
        exporter_SHA256=sha(EXPORTER),Optimize=0,source='R137 original compact zero-Optimize reference exporter; actual P must match canonical bytes/fingerprint'))
    assert result.returncode==0
    b=read(dest/'build.json');assert b['optimizer_calls']==0 and sha(dest/'original.lp')==b['canonical_sha256']
    assert read(dest/'native_version.json')==dict(major=13,minor=0,technical=2)
    return b

def run():
    from round107_reader import instance
    from round108_reader import lp_model
    from round163_campaign import command,tokens,OFF
    import generate_citibike443_regional_v1 as old
    assert sha(EXPORTER)==EXPORTER_SHA and sha(PE)==PE_SHA and sha(DLL)==DLL_SHA
    rows=[]
    for p in read(OUT/'input_manifest.json')['roles']:
        assert sha(ROOT/p['input_path'])==p['input_sha256']
        data=instance(ROOT,p);parsed=old.parse_instance_mirror(ROOT/p['input_path'])
        for a,b in [('b','initial'),('D','target'),('c','capacities'),('xy','points'),('w','weights')]:
            assert (list(data[a])==parsed[b] if a!='xy' else [list(v) for v in data[a]]==[list(v) for v in parsed[b]]), (p['id'],a)
        assert data['Q']==parsed['Q'] and sum(data['w'][1:])==p['Omega'] and p['lambda']==1/p['Omega']
        b=reference(p);model=lp_model(OUT/'qualification/references'/p['id']/'original.lp')
        objective,constant=model['objective'];objective=dict(objective)
        assert constant==0 and objective['G']==1
        assert all(objective[f'e_{i}']==p['lambda']*data['w'][i] for i in range(1,p['V']+1))
        assert all(model['types'][f'Y_{i}']=='I' for i in range(1,p['V']+1))
        assert not any(v.startswith(('state_','rn_','r162_')) for v in model['order'])
        prepared=dict(p,reference=b);commands={}
        for method in ('B','Eplus','P'):
            cmd=command(prepared,method,OUT/'qualification/no_execution'/p['id']/method);actual=tokens(cmd)
            assert all(actual[f]==v for f,v in OFF.items() if f not in ('--round153-root-floor','--round154-proof-floor','--round156-rn-refinement') or method!='Eplus')
            commands[method]=cmd
        rows.append(dict(id=p['id'],input_SHA256=p['input_sha256'],independent_parses_equal=True,reference=b,
            actual_original_compact_types_and_objective=True,commands=commands))
    # Tiny synthetic fixture is separate from the prospective six and unchanged.
    path=ROOT/'tests/data/round61_transfer.txt';d=old.parse_instance_mirror(path)
    p=dict(id='qualification-tiny-transfer',V=d['V'],M=d['M'],Q_vector=d['Q'],T_seconds=5400,
        cap_seconds=120,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},input_path=path.relative_to(ROOT).as_posix(),
        instance_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),gurobi_seed=0,total_initial=sum(d['initial'][1:]),
        total_target=sum(d['target'][1:]),total_capacity=sum(d['capacities'][1:]),Omega=sum(d['weights'][1:]),
        round137_delete_ab=False,panel_kind='qualification',source='synthetic',inventory='shortage',geometry='tiny',replicate=1)
    p['reference']=reference(p);write(OUT/'qualification/smoke_panel.json',p)
    # Existing pure oracle semantics: epigraph interval is not a lower bound on true G.
    from round153_pricing import stock_value
    from round152_math import h_exact,unary_dp
    scope=dict(Bminus=0,B=2,gamma_L=.25,gamma_U=.5,cutoff=10.,stations=[
        dict(i=i,lo=0,hi=1,c=1.,omega=.5,support=[0,1]) for i in (1,2)])
    costs={(s['i'],y):h_exact(s,y) for s in scope['stations'] for y in s['support']}
    zero=stock_value(scope,[0,0],1.,costs);equal=stock_value(scope,[1,1],1.,costs)
    assert zero['feasible'] and zero['G']==0 and zero['f']==F(.25) and zero['phi']==F(1.25)
    assert equal['feasible'] and equal['G']==0 and equal['f']==F(.25) and equal['phi']==F(.25)
    assert F(unary_dp(scope,costs)['exact'])==0
    # Record actual default definitions rather than infer OFF from config names.
    definitions={}
    for n in range(138,163):
        candidates=list((ROOT/'include').glob(f'Round{n}*.hpp'))
        definitions.update({q.relative_to(ROOT).as_posix():dict(SHA256=sha(q),default_lines=[dict(line=i+1,text=line.strip())
            for i,line in enumerate(q.read_text().splitlines()) if ('false' in line or '"off"' in line or 'NodeLimit' in line)]) for q in candidates})
    helpers=read(OUT/'helper_manifest_Eplus.json')
    assert helpers['NodeLimit']==16384 and helpers['original_price_MIPGapAbs']==1e-4
    assert all(sha(ROOT/n)==h for n,h in helpers['helper_dependencies'].items())
    write(OUT/'qualification/result.json',dict(PASS=True,UTC=utc(),six_inputs=rows,exporter_SHA256=EXPORTER_SHA,
        original_compact_Optimize=0,independent_parser='round107_reader.instance vs frozen R57 generator mirror',
        helper_dependencies_equal=True,helper_scope='own canonical root LP/B/Bminus/legal support; never instance text or old role',
        zero_and_epigraph_semantics_checked=True,source_default_definitions=definitions,
        actual_P_runtime_readbacks_required_in_each_formal_arm=True,actual_full_parameter_readback_in_tiny_Eplus_smoke=True,
        one_end_to_end_smoke_pending=True,Native_NodeLimit_source_guard='R162 production defaults -1; no development CLI NodeLimit supplied'))
    print('Six independent parses and six cold compact references, plus tiny reference, pass. Optimize=0')

if __name__=='__main__':run()

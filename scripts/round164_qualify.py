"""Finite changed-risk qualification; no large/old production replay."""
from round164_common import *
import collections, copy, subprocess

def static():
    from round107_reader import instance
    from round108_reader import lp_model
    from round163_setup import canonical
    from round164_campaign import Arm,command,tokens,OFF
    import generate_citibike443_regional_v1 as parser
    facts=[]
    for p in read(OUT/'input_references.json')['roles']:
        path=ROOT/p['input_path'];assert sha(path)==p['input_sha256']
        data=instance(ROOT,p);parsed=parser.parse_instance_mirror(path)
        for a,b in [('b','initial'),('D','target'),('c','capacities'),('w','weights')]:
            assert list(data[a])==parsed[b],(p['id'],a)
        assert [list(v) for v in data['xy']]==[list(v) for v in parsed['points']]
        assert data['Q']==parsed['Q']==p['Q_vector']
        assert p['lambda']==1/p['Omega'] and p['Omega']==sum(data['w'][1:])
        assert p['lambda'].hex()==p['lambda_binary64'] and format(p['lambda'],'.17g')==p['lambda_decimal17']
        base,full=canonical(parsed,p)
        assert base==p['normalized_base_key'] and full==p['normalized_full_key']
        ref=read(OUT/'qualification/references'/p['id']/'build.json')
        lp=OUT/'qualification/references'/p['id']/'original.lp';assert sha(lp)==ref['canonical_sha256']
        model=lp_model(lp);objective,constant=model['objective'];objective=dict(objective)
        assert constant==0 and objective['G']==1
        assert all(objective[f'e_{i}']==p['lambda']*data['w'][i] for i in range(1,p['V']+1))
        commands=[]
        for seed in (1,2):
            for method in ('B','P'):
                c=command(dict(p,reference=ref),Arm(p['id'],method,seed),OUT/'qualification/not_executed'/p['id']/str(seed)/method)
                values=tokens(c);assert values['--gurobi-seed']==str(seed)
                assert all(values[f]==v for f,v in OFF.items())
                commands.append(dict(seed=seed,method=method,argv=c))
        facts.append(dict(id=p['id'],input_SHA256=sha(path),normalized_base_key=base,normalized_full_key=full,
            lambda_binary64=p['lambda'].hex(),lambda_decimal17=p['lambda_decimal17'],T_seconds=p['T_seconds'],
            independent_parses_equal=True,original_compact_reference=ref,commands=commands))
    # Inspect defaults of all research controls, rather than infer them from names.
    definitions={}
    for n in range(138,163):
        for path in sorted((ROOT/'include').glob(f'Round{n}*.hpp')):
            definitions[path.relative_to(ROOT).as_posix()]=dict(SHA256=sha(path),default_lines=[
                dict(line=i+1,text=line.strip()) for i,line in enumerate(path.read_text().splitlines())
                if ('false' in line or '"off"' in line or 'NodeLimit' in line)])
    write(OUT/'qualification/static.json',dict(PASS=True,UTC=utc(),six_inputs=facts,
        source_default_definitions=definitions,Optimize=0,original_references_reused=True,
        no_input_regeneration_or_old_mathematical_requalification=True))

def smoke(seed,method,fixture='transfer'):
    from round164_campaign import Arm,make,execute
    p=read(OUT/'qualification/tiny_panel.json' if fixture=='transfer' else OUT/'qualification/native_tiny_panel.json')
    camp=OUT/'qualification/smokes'/f'{fixture}_S{seed}_{method}'
    if (camp/'identity.json').exists():
        identity=read(camp/'identity.json');launch=identity['launches'][0]
        d=Path(launch['destination'])
        if (d/'round164_endpoint.json').exists():return read(d/'round164_endpoint.json')
    else:launch,identity=make(p,Arm(p['id'],method,int(seed)),camp,0)
    value=execute(launch,identity)
    return value['arm']

def native_fixture():
    # An existing qualification input, used only if the transfer toy closes at
    # its first Native call. No change to the B algorithm or production knobs.
    import generate_citibike443_regional_v1 as parser
    name='results/unified_exact_round133/qualification/small_native01/input.txt'
    path=materialize(name);data=parser.parse_instance_mirror(path)
    p=dict(id='qualification-existing-native-tiny',V=data['V'],M=data['M'],Q_vector=data['Q'],
        T_seconds=5400,cap_seconds=120,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},
        input_path=name,instance_path=name,input_sha256=sha(path),total_initial=sum(data['initial'][1:]),
        total_target=sum(data['target'][1:]),total_capacity=sum(data['capacities'][1:]),Omega=sum(data['weights'][1:]),
        round137_delete_ab=False,panel_kind='qualification',source='synthetic',inventory='shortage',
        geometry='tiny',replicate=1,exposed=True,known=True)
    dest=OUT/'qualification/references'/p['id']
    exporter=WORK/'build-cache/round137/Round137Export.exe'
    assert sha(exporter)=='ee5ea33f96e3ae38c005bd75cbe3abb8eaefb483d2760cac7e4168728ac6c4d1'
    args=[exporter,path,p['T_seconds'],0,0,0,'p',dest,format(p['lambda'],'.17g'),'off']
    logs=OUT/'qualification/native_fixture_export';logs.mkdir(parents=True,exist_ok=False)
    tick=time.perf_counter()
    with (logs/'stdout.log').open('xb') as out,(logs/'stderr.log').open('xb') as err:
        result=subprocess.run(list(map(str,args)),cwd=ROOT,env=meter.environment(),stdout=out,stderr=err,timeout=60)
    write(logs/'receipt.json',dict(command=list(map(str,args)),exit_code=result.returncode,
        seconds=time.perf_counter()-tick,Optimize=0,exporter_SHA256=sha(exporter)))
    assert result.returncode==0
    p['reference']=read(dest/'build.json');assert p['reference']['optimizer_calls']==0
    assert sha(dest/'original.lp')==p['reference']['canonical_sha256']
    write(OUT/'qualification/native_tiny_panel.json',p)

def run():
    static();arms=[]
    for seed in (1,2):
        for method in ('B','P'):arms.append(smoke(seed,method))
    followon={a['seed']:a['declared_calls']>1 for a in arms if a['R164_method']=='B'}
    if not all(followon.values()):
        if not (OUT/'qualification/native_tiny_panel.json').exists():native_fixture()
        for seed in (1,2):
            if not followon[seed]:
                a=smoke(seed,'B','native');arms.append(a);followon[seed]=a['declared_calls']>1
    assert all(followon.values()),('B successor Native calls still need genuine readback',followon)
    write(OUT/'qualification/result.json',dict(PASS=True,UTC=utc(),static_SHA256=sha(OUT/'qualification/static.json'),
        real_B_P_Seeds_1_2=True,B_successor_Native_readbacks=followon,arms=arms,
        performance_samples=0,measured_PE_SHA256=PE_SHA,DLL_SHA256=DLL_SHA,H_seed=20260626,
        unchanged_producer_and_reader_contracts=True,independent_agent_review=False,
        qualification='implementing-agent changed-risk check; separate final agent review is still required'))
    print(json.dumps(dict(PASS=True,qualification_arms=len(arms),B_successor_readbacks=followon)))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='smoke':smoke(int(sys.argv[2]),sys.argv[3],sys.argv[4] if len(sys.argv)>4 else 'transfer')
    else:run()

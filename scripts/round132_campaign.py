"""D uses unchanged E3 and inherited producer/physical/certificate checks."""
from round132_common import *
import collections, copy, inspect, types
import round130_campaign as inherited

def api():
    ns=dict(vars(inherited),ROOT=ROOT,OUT=OUT,BASE=BASE,SOURCE=SOURCE,E3=E3,EXPORTER=EXPORTER,
            metered=metered,environment=environment)
    text=inspect.getsource(inherited.prepare_group).replace("OUT/'experiment_manifest.json'","OUT/'experiment_plan.json'")
    exec(compile(text,__file__+'::prepare_group','exec'),ns)
    prepare=ns['prepare_group']
    supervised=types.FunctionType(inherited.supervised.__code__,ns,'round132_supervised')
    reconstruct=types.FunctionType(inherited.reconstruct.__code__,ns,'round132_reconstruct')
    ns.update(supervised=supervised,reconstruct=reconstruct)
    return prepare,supervised,reconstruct

def qualify():
    frozen_identity();records=[]
    for p in read(OUT/'input_manifest.json')['roles']:
        d=OUT/'qualification/references'/p['id']
        if (d/'build.json').exists():
            assert sha(d/'original.lp')==read(d/'build.json')['canonical_sha256'];continue
        cmd=[EXPORTER,ROOT/p['input_path'],p['T_seconds'],0,0,0,'p',d]
        assert metered('D_reference_'+p['id'],'qualification',cmd,timeout=120)==0
        b=read(d/'build.json');assert b['optimizer_calls']==0 and sha(d/'original.lp')==b['canonical_sha256']
        assert read(d/'native_metadata.json')['Optimize']==0
        assert read(d/'native_version.json')==dict(major=13,minor=0,technical=2)
        records.append(dict(id=p['id'],input_SHA=p['input_sha256'],reference=b))
    write(OUT/'qualification/D_qualification.json',dict(UTC=utc(),assets=frozen_identity(),records=records,
        Optimize=0,H=0,production_compile=0,source_unchanged=True,
        inherited_native_qualification='results/unified_exact_round130/qualification/native_qualification.json',
        own_full_H_and_PS_Start_qualification_inherited_by_exact_byte_identity=True))

def prepare():
    frozen_identity();assert (OUT/'qualification/D_qualification.json').exists()
    make,_,_=api();plans=[]
    for g in read(OUT/'experiment_plan.json')['D']:
        path=OUT/g['name']/'identity.json'
        if not path.exists():make(g['name'],'E3',g['role'],g['methods'],g['seed'],1)
        i=read(path);i['measured_source_commit']=SOURCE;i['runner_sha256']=sha(__file__)
        for l in i['launches']:
            l.update(group_number=g['number'],evidence_layer=g['role']['layer'])
            cmd=l['command'];cap=l['panel']['cap_seconds'];m=l['method']
            assert cmd[0]==str(E3)
            if m=='PS':assert '--round112-ens-start-compact' in cmd and '--round127-mode' not in cmd
            else:assert cmd.count('--round127-mode')==1 and cmd[cmd.index('--round127-mode')+1]==dict(P='p',S2='ms2')[m]
            for flag,v in [('--time-limit',cap-6),('--process-wall-time-limit',cap),('--process-shutdown-margin',30),
                           ('--gurobi-seed',g['seed']),('--threads',1),('--mip-threads',1),('--gurobi-presolve',-1)]:
                assert cmd[cmd.index(flag)+1]==str(v),(flag,v)
            assert not any(x in cmd for x in ['--round128-mode','--round132-expression','s2-root'])
        write(path,i);plans.append(i)
    adapters=sorted({Path(m.__file__).resolve().relative_to(ROOT).as_posix() for m in list(sys.modules.values())
        if getattr(m,'__file__',None) and Path(m.__file__).resolve().parent==ROOT/'scripts' and str(m.__file__).endswith('.py')})
    # Binding excludes authoring/research scripts that cannot influence D.
    write(OUT/'D_argv_freeze.json',dict(UTC=utc(),plans=plans,formal_arms=60,PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,
        Optimize=0,each_own_H=True,cold_P=True,no_performance_screening=True))
    write(OUT/'D_execution_binding.json',dict(UTC=utc(),plan_SHA=sha(OUT/'experiment_plan.json'),
        inputs_SHA=sha(OUT/'input_manifest.json'),argv_SHA=sha(OUT/'D_argv_freeze.json'),
        groups={g['name']:sha(OUT/g['name']/'identity.json') for g in read(OUT/'experiment_plan.json')['D']},
        adapters={n:sha(ROOT/n) for n in adapters},serial=True,formal_arms=60))
    version=read(ROOT/'results/unified_exact_round131/paper_version_manifest.json')
    version.update(version='Round132',production_method_unchanged=True,D_frozen_PE=PE_SHA,research_default='off')
    write(OUT/'current_method_manifest.json',dict(paper=version,D=frozen_identity(),
        research=dict(status='qualification pending',not_used_for_D=True),repository_default='ENS-C',paper_method='GI-TBC uniform pair-support S2 / MS2'))
    print('All D input bytes and 60 full command positions frozen; no H/Optimize started.')

def separate(label,name,seconds,kind):
    write(OUT/'cost_segments'/label/(name+'.json'),dict(kind=kind,seconds=seconds,native_Optimize=0))

def execute(name,label):
    frozen_identity();_,supervised,reconstruct=api()
    tick,creation=inherited.process_origin();camp=OUT/name;i=read(camp/'identity.json')
    assert not (camp/'reconstructed.json').exists(),'sealed group must not be rerun'
    for l in i['launches']:
        d=Path(l['destination'])
        if not d.exists():
            t=tick if l['number']==1 else time.perf_counter();unix=creation if l['number']==1 else time.time()
            assert sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
            supervised(l,i,t);inherited.finish_producer(l,t,unix)
        else:assert (d/'producer_receipt.json').exists() and (d/'producer_seal.json').exists(),'inspect interrupted arm; never overwrite'
        if not (d/'verification_closeout.json').exists():
            start=time.perf_counter();inherited.verify(l,i)
            separate(label,f'verify_{l["number"]}',time.perf_counter()-start,'non-native postproduction physical/model/certificate audit')
        write(OUT/'runtime_status.json',dict(UTC=utc(),line='D',last_sealed=l['destination'],group=name,next_method=l['number']+1))
        (OUT/'RESUME.md').write_text(f'Round132 D active. Last sealed `{l["destination"]}`. Inspect current fees PID/creation/argv before any resume. Own frozen E3 only. C/E never supply information to D.\n',encoding='utf-8')
    start=time.perf_counter();arms=reconstruct(camp)
    separate(label,'reconstruct',time.perf_counter()-start,'non-native postproduction endpoint reconstruction')
    assert len(arms)==len(i['launches'])
    print(json.dumps([dict(method=a['method'],qualified=a['formal_protocol_qualified'],certificate=a['certificate'],U=a['U'],L=a['L'],T_cert=a['T_cert']) for a in arms]),flush=True)

def run(stop_after=None):
    frozen_identity();binding=read(OUT/'D_execution_binding.json');gate=read(OUT/'review/D_admission.json')
    assert gate['decision']=='ACCEPT' and gate['D_execution_binding_SHA']==sha(OUT/'D_execution_binding.json')
    assert binding['plan_SHA']==sha(OUT/'experiment_plan.json') and binding['inputs_SHA']==sha(OUT/'input_manifest.json')
    for n,h in binding['adapters'].items():assert sha(ROOT/n)==h,n
    for g in read(OUT/'experiment_plan.json')['D']:
        name=g['name'];assert sha(OUT/name/'identity.json')==binding['groups'][name]
        if (OUT/name/'reconstructed.json').exists():continue
        if stop_after is not None and g['number']>stop_after:break
        label=f'formal_D{g["number"]:02d}_01'
        assert not (OUT/'fees'/label).exists(),'inspect live process or failure; no automatic retry'
        print(json.dumps(dict(group=name,id=g['role']['id'],seed=g['seed'],methods=g['methods'],action='START')),flush=True)
        assert metered(label,'D',[PYTHON,ROOT/'scripts/round132_campaign.py','group',name,label],timeout=sum(g['role']['cap_seconds'] for _ in g['methods'])+1800)==0
    print('D_SERIAL_RUN_RETURNED',flush=True)

def status():
    records=[]
    for g in read(OUT/'experiment_plan.json')['D']:
        p=OUT/g['name']/'reconstructed.json'
        if p.exists():records.extend(dict(id=g['role']['id'],seed=g['seed'],**{k:a.get(k) for k in ['method','certificate','formal_protocol_qualified','T_cert','T_produce','U','L']}) for a in read(p)['arms'])
    print(json.dumps(dict(complete_arms=len(records),last=records[-3:],runtime=read(OUT/'runtime_status.json') if (OUT/'runtime_status.json').exists() else None,budget=budget())))
if __name__=='__main__':
    action=sys.argv[1]
    if action=='group':execute(sys.argv[2],sys.argv[3])
    elif action=='run':run(int(sys.argv[2]) if len(sys.argv)>2 else None)
    else:{'qualify':qualify,'prepare':prepare,'status':status}[action]()

"""Focused writer, actual physical Start, Native readback and boundary qualification."""
import collections,ast
import round108_reader as parser
from round143_qualify import point_residual
from round150_lp import readback
from round151_math import reference,scope_from_model,rows
from round151_build import COMPILER,SYSTEM
from round151_common import *
def build():
    configure();m=read(OUT/'candidate_manifest.json');pe=BUILD/'Round151Writer_v3.exe'
    assert metered('compile_writer_v3','build',[COMPILER,*m['flags'],ROOT/'scripts/round151_writer.cpp',
        *m['objects'],m['archive']['path'],*SYSTEM,'-o',pe],timeout=180)==0
    write(OUT/'writer_driver_v3.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round151_writer.cpp')))
def run_cpp():
    configure();driver=read(OUT/'writer_driver_v3.json');assert sha(driver['PE'])==driver['PE_SHA']
    target=OUT/'qualification/writer_v3';target.mkdir(parents=True,exist_ok=False)
    scope=read(OUT/'LP/arithmetic/N-B35-S.json')['scope']
    source=WORK/'restore/round151-inherited/N-B35-S/external/models/L0_epoch_0_generation_1.lp'
    obs=read(WORK/'restore/round151-inherited/N-B35-S/observations.json')
    witness=[r['payload'] for r in obs if r['payload']['kind']=='witness'][-1]
    input_path=ROOT/'results/unified_exact_round137/inputs/N-B35-S.txt'
    lines=[f'"{input_path.as_posix()}" "{source.as_posix()}" {scope["gamma_L"]:.17g} {scope["gamma_U"]:.17g} {scope["cutoff"]:.17g} {len(witness["routes"])}']
    for route in witness['routes']:
        values=[route['vehicle'],len(route['nodes']),*route['nodes'],len(route['operations'])]
        values.extend(v for op in route['operations'] for v in [op['station'],op['pickup'],op['drop']])
        lines.append(' '.join(map(str,values)))
    (target/'real_scope.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    write(target/'real_witness.json',dict(witness=witness,offline_only_not_complete_arm_injection=True,fixed_science=SCIENCE150))
    assert metered('qualification_writer_cpp_v3','diagnostic',[driver['PE'],target],60,90)==0
def native():
    configure();from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA;facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for tag in ['shortage','fixed','zero_floor','actual_NB35']:
            d=OUT/'qualification/writer_v3'/tag;off=parser.lp_model(d/'off.lp');on=parser.lp_model(d/'on.lp')
            meta=read(d/'round151_root.json');scope=scope_from_model(off,meta['Bminus'],meta['B'])
            proof=reference(scope,dict(meta,beta0=meta['beta0']))
            expected=rows(dict(meta,scope=scope,mode='conditional'))
            assert all(off[k]==on[k] for k in ['order','bounds','types','objective'])
            er=[(tuple(sorted(r['terms'].items())),'<=',0.) for r in expected]
            assert collections.Counter(on['rows'])==collections.Counter(off['rows'])+collections.Counter(er)
            assert all('r146_GD_' not in k for k in (d/'on.lp').read_text().split())
            for label in ['physical_start','nonminimal_epigraph']:
                p=read(d/(label+'.json'));assert set(p)==set(on['order'])
                quality=point_residual(on,p);assert max(quality.values())<=1e-6,(tag,label,quality)
                facts.append(dict(tag=tag,point=label,complete_columns=len(p),residual=quality))
            for label in ['on']+(['child_on'] if tag=='shortage' else []):
                path=d/(label+'.lp');parsed=parser.lp_model(path)
                current=scope_from_model(parsed,meta['Bminus'],meta['B'])
                wanted=rows(dict(meta,scope=scope,mode='conditional'),current)
                with gp.read(str(path),env=env) as model:
                    assert {v.VarName:v.VType for v in model.getVars()}==parsed['types']
                    assert all((v.LB,v.UB)==parsed['bounds'][v.VarName] for v in model.getVars())
                    readback(model,wanted)
                    assert sum(c.ConstrName.startswith('r151_') for c in model.getConstrs())==len(wanted)
                    facts.append(dict(tag=tag,model=label,SHA=sha(path),actual_Native_rows=len(wanted),
                        actual_Native_nonzeros=sum(len(r['terms']) for r in wanted),columns=model.NumVars))
    write(OUT/'qualification_native_writer.json',dict(PASS=True,Optimize=0,Native=binding(),facts=facts,
        actual_physical_model_Start=True,nonminimal_g_and_e_completion=True,GD=False,new_columns=0))
    print('PASS writer/actual Start/nonminimal epigraph/child/Native matrix qualification')
def run():
    run_cpp();assert metered('qualification_native_writer_v4','diagnostic',[LP_PYTHON,'-B',__file__,'native'],60,90)==0
def native_retry():
    configure();assert metered('qualification_native_writer_v2','diagnostic',[LP_PYTHON,'-B',__file__,'native'],60,90)==0
if __name__=='__main__':globals()[sys.argv[1]]()

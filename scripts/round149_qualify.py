"""Focused actual writer/Native/Start readback. No Optimize."""
import collections
import round108_reader as parser
from round143_qualify import point_residual
from round149_math import oracle,F
from round149_build import COMPILER,SYSTEM
from round149_common import *


def build_writer(attempt=''):
    manifest=read(OUT/'candidate_manifest.json');pe=BUILD/f'Round149Writer{attempt}.exe'
    assert metered('compile_writer'+attempt,'build',[COMPILER,*manifest['flags'],ROOT/'scripts/round149_writer.cpp',
        *manifest['objects'],manifest['archive']['path'],*SYSTEM,'-o',pe],timeout=180)==0
    write(OUT/f'writer_driver{attempt}.json',dict(PE=str(pe),PE_SHA=sha(pe),source_SHA=sha(ROOT/'scripts/round149_writer.cpp')))


def native_writer(attempt=''):
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA;facts=[];root=OUT/f'qualification/writer{attempt}'
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for tag in ['shortage','fixed','zero_floor','zero_GD']:
            folder=root/tag;gd=parser.lp_model(folder/'gd.lp');on=parser.lp_model(folder/'on.lp')
            meta=read(folder/'round149_root.json');embedding=read(folder/'on.lp.round149.json')
            exact=oracle(meta);assert exact['feasible']
            assert F(meta['dual_lower'])<=exact['dual'](F(meta['mu']),F(meta['nu']))<=exact['primal']
            assert 0<=F(meta['penalty_lower'])<=exact['primal']
            assert F(meta['beta'])>=min(F(meta['gamma_U']),F(meta['own_cutoff'])-F(meta['penalty_lower']))
            assert all(gd[k]==on[k] for k in ['order','bounds','types','objective'])
            expected=[]
            if meta['penalty_lower']>0 and meta['beta']<meta['gamma_U'] and meta['beta']>=1e-12:
                for name in on['order']:
                    if name.startswith('state_g_'):
                        expected.append((tuple(sorted({name:1.,'state_'+name[8:]:-meta['beta']}.items())),'<=',0.))
            assert collections.Counter(on['rows'])==collections.Counter(gd['rows'])+collections.Counter(expected)
            assert embedding['added_rows']==len(expected) and embedding['final_SHA']==sha(folder/'on.lp')
            for label in ['physical_start','nonminimal_epigraph']:
                point=read(folder/(label+'.json'));assert set(point)==set(on['order'])
                quality=point_residual(on,point);assert max(quality.values())<=1e-6,(tag,label,quality)
                assert point['G']<=meta['beta']+1e-12
                facts.append(dict(tag=tag,Start=label,complete=True,residual=quality))
            for name in (['on','child_on'] if tag=='shortage' else ['on']):
                p=folder/(name+'.lp');m=parser.lp_model(p)
                with gp.read(str(p),env=env) as model:
                    actual=0
                    for con in model.getConstrs():
                        if con.ConstrName.startswith('r149_'):
                            row=model.getRow(con);terms={row.getVar(i).VarName:row.getCoeff(i) for i in range(row.size())}
                            assert con.Sense=='<' and con.RHS==0 and len(terms)==2
                            suffix=con.ConstrName[len('r149_PF_'):]
                            assert terms=={f'state_g_{suffix}':1.,f'state_{suffix}':-meta['beta']};actual+=1
                    assert actual==(len(expected) if name=='on' else 0)
                    facts.append(dict(tag=tag,model=name,actual_Native_rows=actual,
                        matrix_SHA=sha(p),columns=model.NumVars,original_variables_preserved=True))
    write(OUT/f'qualification_native_writer{attempt}.json',dict(PASS=True,Optimize=0,Native=binding(),facts=facts))
    print('PASS actual writer, Native readback, child omission, positive/zero floors and complete/nonminimal g/e Starts')


def run(attempt=''):
    configure();driver=read(OUT/f'writer_driver{attempt}.json');assert sha(driver['PE'])==driver['PE_SHA']
    assert metered('qualification_writer_cpp'+attempt,'diagnostic',[driver['PE'],OUT/f'qualification/writer{attempt}'],60,90)==0
    assert metered('qualification_native_writer'+attempt,'diagnostic',[LP_PYTHON,'-B',__file__,'native_writer',attempt],60,90)==0


def failure_diagnostic():
    folder=OUT/'qualification/writer/fixed';model=parser.lp_model(folder/'on.lp')
    point=read(folder/'nonminimal_epigraph.json');bad=[]
    for terms,sense,rhs in model['rows']:
        lhs=math.fsum(v*point[k] for k,v in terms)
        violation=max(0.,lhs-rhs) if sense=='<=' else max(0.,rhs-lhs) if sense=='>=' else abs(lhs-rhs)
        if violation>1e-6:bad.append(dict(terms=terms,sense=sense,rhs=rhs,violation=violation))
    write(OUT/'engineering/nonminimal_fixture_failure.json',dict(Optimize=0,Native_load=0,
        failed_point_SHA=sha(folder/'nonminimal_epigraph.json'),violations=bad))
    print(json.dumps(bad))


def diagnose():
    assert metered('qualification_start_failure_diagnostic','diagnostic',[PYTHON,'-B',__file__,'failure_diagnostic'],30,60)==0


if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])

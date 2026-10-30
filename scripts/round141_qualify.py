"""Finite actual writer, physical-side Start, evidence and Native qualification."""
from round141_common import *
from fractions import Fraction as F
import collections
import round108_reader as core

def build():
    manifest=read(OUT/'candidate_build.json')
    old=read(ROOT/'results/unified_exact_round140/candidate_build.json')
    compiler=Path('D:/msys64/ucrt64/bin/g++.exe')
    target=Path(manifest['production_PE']).parent/'Round141Qualify.exe'
    args=[compiler,*old['flags'],ROOT/'scripts/round141_qualify.cpp',*manifest['objects'],
          manifest['archive']['path'],'-lkernel32','-luser32','-lgdi32','-lwinspool','-lshell32',
          '-lole32','-loleaut32','-luuid','-lcomdlg32','-ladvapi32','-o',target]
    assert metered(target.parent.name+'_compile_tiny','build',args,timeout=180)==0
    write(OUT/'qualification_build.json',dict(PE=str(target),PE_SHA=sha(target),source_SHA=sha(ROOT/'scripts/round141_qualify.cpp')))

def tiny():
    pe=read(OUT/'qualification_build.json');assert sha(pe['PE'])==pe['PE_SHA']
    tag=Path(pe['PE']).parent.name
    assert metered('tiny_cpp_'+tag,'diagnostic',[pe['PE'],OUT/'qualification'/('tiny_'+tag)],30,45)==0

def native_tiny():
    from round100_gurobi_runtime import gp,binding
    from round141_math import model_counts,serializable,child_rows
    assert binding()['sha256']==DLL_SHA
    tag=Path(read(OUT/'qualification_build.json')['PE']).parent.name
    root=OUT/'qualification'/('tiny_'+tag);facts=[]
    parsed={key:core.lp_model(root/(key+'.lp')) for key in ['parent','count_low','count_high','d0','d1','successor','successor_d0']}
    parent=parsed['parent'];add=serializable(model_counts(parent,0,2))
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        for name,declared in parsed.items():
            with gp.read(str(root/(name+'.lp')),env=env) as m:
                assert m.ObjCon==0 and m.NumVars==len(declared['order']) and m.NumConstrs==len(declared['rows'])
                assert {v.VarName:v.VType for v in m.getVars()}==declared['types']
                if name.startswith('count_'):
                    side='low' if name.endswith('low') else 'high'
                    child=child_rows(json.loads(json.dumps(add)),F(1),1,side)
                    terms={n:1. for n in declared['order'] if n.startswith('h_')}
                    terms.update({n:-v for n,v in child['coefficients'].items()})
                    assert collections.Counter(parent['rows'])<=collections.Counter(declared['rows'])
                    wanted=(tuple(sorted(terms.items())),'>=',child['constant'])
                    assert collections.Counter(declared['rows'])[wanted]==1
                if 'r141_b' in declared['types']:
                    b=m.getVarByName('r141_b');assert b.VType=='B' and b.LB==0 and b.UB==1 and b.BranchPriority==0 and b.Obj==0
                    row=m.getConstrByName('r141_objective_floor');e=m.getRow(row)
                    coefficients={e.getVar(j).VarName:e.getCoeff(j) for j in range(e.size())}
                    assert {k:v for k,v in coefficients.items() if k!='r141_b'}=={v.VarName:v.Obj for v in m.getVars() if v.Obj}
                    beta0,beta1=(.1,0.) if name=='d1' else (0.,0.)
                    assert F(row.RHS)+F(m.ObjCon)<=F(beta0)
                    assert F(row.RHS)-F(coefficients.get('r141_b',0))+F(m.ObjCon)<=F(beta1)
                facts.append(dict(model=name,SHA=sha(root/(name+'.lp')),rows=m.NumConstrs,columns=m.NumVars,ObjCon=m.ObjCon,types_exact=True))
        for i,c in enumerate(read(root/'tiny.json')['offset_cases']):
            with gp.Model(env=env) as m:
                x=m.addVar(name='F_linear',obj=1);b=m.addVar(name='r141_b',vtype=gp.GRB.BINARY)
                m.ObjCon=c['ObjCon'];m.addConstr(x-c['delta']*b>=c['base'],name='floor');m.update()
                path=root/f'offset_{i}.mps';m.write(str(path))
            with gp.read(str(path),env=env) as m:
                assert m.ObjCon==c['ObjCon'];row=m.getConstrByName('floor');e=m.getRow(row)
                actual={e.getVar(j).VarName:e.getCoeff(j) for j in range(e.size())}
                assert actual=={k:v for k,v in {'F_linear':1.,'r141_b':-c['delta']}.items() if v}
                assert F(row.RHS)+F(m.ObjCon)<=F(c['beta0'])
                assert F(row.RHS)+F(c['delta'])+F(m.ObjCon)<=F(c['beta1'])
    write(OUT/'qualification_native_tiny.json',dict(PASS=True,models=facts,actual_ObjCon_cases=8,
        Seed=0,Threads=1,Optimize=0,native_identity=binding()))

if __name__=='__main__':globals()[sys.argv[1]]()

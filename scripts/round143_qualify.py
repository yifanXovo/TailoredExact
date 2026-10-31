"""Small actual writer/Native/Start qualification, zero Optimize."""
import collections,gzip
import round108_reader as core
from fractions import Fraction as F
from round143_math import specification,rn_rows,outward
from round143_common import *

def build():
    from round143_build import COMPILER,SYSTEM,BUILD
    m=read(OUT/'candidate_manifest.json');target=BUILD/'Round143Qualify.exe'
    assert metered('compile_qualification','build',[COMPILER,*m['flags'],ROOT/'scripts/round143_qualify.cpp',*m['objects'],m['archive']['path'],*SYSTEM,'-o',target],timeout=180)==0
    write(OUT/'qualification_build.json',dict(PE=str(target),PE_SHA=sha(target),source_SHA=sha(ROOT/'scripts/round143_qualify.cpp')))

def tiny():
    q=read(OUT/'qualification_build.json');assert sha(q['PE'])==q['PE_SHA']
    assert metered('tiny_cpp','diagnostic',[q['PE'],OUT/'qualification/writer',ROOT/'results/unified_exact_round132/inputs/K-35-U.txt'],30,60)==0

def actual_spec(m,bm,b):
    n=max(int(name.split('_')[1]) for name in m['order'] if name.startswith('Y_'))
    scope=dict(panel=dict(V=n,total_initial=b,Q_vector=[b-bm]),B=b,Bminus=bm)
    s=specification(m,scope)
    if s['applicable']:
        # Reproduce directed dyadic sum conversion THEN outward reciprocals.
        sl=outward(F(s['S_L_exact']),False);su=outward(F(s['S_U_exact']),True)
        s['L_t']=math.nextafter(1/su,-math.inf);s['U_t']=math.nextafter(1/sl,math.inf)
        assert F(s['L_t'])<=1/F(s['S_U_exact']) and F(s['U_t'])>=1/F(s['S_L_exact'])
    return s

def expected_rows(s):
    result=rn_rows(s)
    for r in result:
        smallest=min([1.]+[abs(v) for v in r['terms'].values()]);scale=0
        while math.ldexp(smallest,scale)<1e-12:scale+=1
        r['terms']={k:math.ldexp(v,scale) for k,v in r['terms'].items()};r['rhs']=math.ldexp(r['rhs'],scale)
    return result

def check_matrix(m,s):
    counter=collections.Counter(m['rows']);wanted=expected_rows(s)
    for r in wanted:
        sense={'>':'>=','<':'<=','=':'='}[r['sense']]
        assert counter[(tuple(sorted(r['terms'].items())),sense,r['rhs'])]==1,r['name']
    rn={name for name in m['order'] if name.startswith('rn_')}
    expected=set()
    if s['applicable']:
        supports={int(i):ys for i,ys in s['supports'].items()}
        expected={'rn_t'}|{f'rn_Y_{i}' for i in supports}|{f'rn_w_{i}_{y}' for i,ys in supports.items() for y in ys}|{f'rn_h_{i}_{j}' for i in supports for j in supports if i<j}
        assert m['bounds']['rn_t']==(s['L_t'],s['U_t'])
        for i,ys in supports.items():
            cap=math.nextafter(s['U_t']*max(ys),math.inf) if max(ys) else 0.
            assert m['bounds'][f'rn_Y_{i}']==(0.,cap)
            for y in ys:assert m['bounds'][f'rn_w_{i}_{y}']==(0.,s['U_t'])
        for i in supports:
            for j in supports:
                if i<j:assert m['bounds'][f'rn_h_{i}_{j}']==(0.,1.)
    assert rn==expected and all(m['types'][name]=='C' for name in rn)
    assert not rn.intersection(dict(m['objective'][0]))
    return wanted

def point_residual(m,p):
    high=0.
    for terms,sense,rhs in m['rows']:
        lhs=math.fsum(v*p[k] for k,v in terms)
        violation=max(0,lhs-rhs) if sense=='<=' else max(0,rhs-lhs) if sense=='>=' else abs(lhs-rhs)
        high=max(high,violation)
    bound=max([max(lo-p[k],p[k]-hi,0.) for k,(lo,hi) in m['bounds'].items()] or [0.])
    integer=max([abs(p[k]-round(p[k])) for k,t in m['types'].items() if t in ('B','I')] or [0.])
    return dict(constraints=high,bounds=bound,integrality=integer)

def native():
    from round100_gurobi_runtime import gp,binding
    assert binding()['sha256']==DLL_SHA
    root=OUT/'qualification/writer';facts=[]
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Seed',0);env.setParam('Threads',1);env.start()
        for tag,bm,b in [('positive',2,3),('fixed',3,3),('zero_lower',0,3),('K35',251,326)]:
            off=core.lp_model(root/tag/'off.lp');on=core.lp_model(root/tag/'on.lp')
            s=actual_spec(on,bm,b);wanted=check_matrix(on,s)
            assert collections.Counter(off['rows'])+collections.Counter((tuple(sorted(r['terms'].items())),{'>':'>=','<':'<=','=':'='}[r['sense']],r['rhs']) for r in wanted)==collections.Counter(on['rows'])
            assert off['objective']==on['objective']
            for k in off['order']:assert all(off[x][k]==on[x][k] for x in ('bounds','types'))
            assert set(on['order'])-set(off['order'])=={k for k in on['order'] if k.startswith('rn_')}
            if tag=='K35':assert off==core.lp_model(OUT/'inherited/roots/K-35-U/inherited/original.lp')
            else:
                for mode,m in [('off',off),('on',on)]:
                    for kind in ([mode+'_start']+(['nonminimal_epigraph'] if mode=='on' and s['applicable'] else [])):
                        p=read(root/tag/(kind+'.json'));check=point_residual(m,p)
                        assert set(p)==set(m['order']) and max(check.values())<=1e-6,(tag,kind,check)
                        facts.append(dict(tag=tag,point=kind,complete_columns=len(p),residual=check))
            path=root/tag/'on.lp'
            with gp.read(str(path),env=env) as model:
                assert {v.VarName:v.VType for v in model.getVars()}==on['types']
                for v in model.getVars():assert (v.LB,v.UB)==on['bounds'][v.VarName]
                for r in wanted:
                    c=model.getConstrByName(r['name']);e=model.getRow(c)
                    assert c.Sense==r['sense'] and c.RHS==r['rhs'] and {e.getVar(i).VarName:e.getCoeff(i) for i in range(e.size())}==r['terms']
                facts.append(dict(tag=tag,model_SHA=sha(path),rows=model.NumConstrs,columns=model.NumVars,added_rows=len(wanted),
                    actual_Native_all_bounds_types_and_RN_rows=True,applicable=s['applicable'],S_L_exact=s['S_L_exact'],S_U_exact=s['S_U_exact']))
    write(OUT/'qualification_native_writer.json',dict(PASS=True,Optimize=0,native_identity=binding(),facts=facts,
        exact_historical_off_K35=True,original_integer_types_and_objective_retained=True,
        physical_Start_g_domain_rule_retained=True,nonminimal_epigraph_extensions_checked=True))
    print('PASS actual RN writer/complete Start/Native readback; Optimize=0')

if __name__=='__main__':
    action=sys.argv[1]
    if action=='native_meter':
        assert metered('native_writer','diagnostic',[LP_PYTHON,'-B',__file__,'native'],60,90)==0
    else:globals()[action]()

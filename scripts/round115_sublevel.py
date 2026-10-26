"""Exact inventory arithmetic only. No route generation or Optimize."""
from round115_common import ROOT,OUT,read,write,sha
from fractions import Fraction as R
import ast,itertools,json,re,sys,time
import round108_reader as core

def instance(path,interpretation):
    text=Path(path).read_text(encoding='utf-8');head=text.splitlines()[0]
    n,m=map(int,head.split()[:2]);Q=ast.literal_eval(head[head.index('['):])
    data={k:ast.literal_eval(re.search(r'^'+k+r'\s*=\s*(\[[^\n]+\])',text,re.M)[1]) for k in ['capacities','initial','target']}
    tokens=re.search(r'^weights\s*=\s*\[([^\]]+)\]',text,re.M)[1].split(',')
    convert=(lambda t:R(t.strip())) if interpretation=='input_decimal' else (lambda t:R.from_float(float(t)))
    data.update(n=n,M=m,Q=Q,w=list(map(convert,tokens)),lam=convert('0.15'),interpretation=interpretation)
    return data

from pathlib import Path
def objective(a,Y):
    n=a['n'];r=[R(y,d) for y,d in zip(Y,a['target'][1:])];den=n*sum(r)
    G=sum(abs(x-y) for i,x in enumerate(r) for y in r[i+1:])/den if den else R(0)
    P=sum(w*abs(r-1) for w,r in zip(a['w'][1:],r))
    return G+a['lam']*P

def bound(a):
    n=a['n'];D=a['target'][1:];C=a['capacities'][1:];B=sum(a['initial'][1:]);low=max(0,B-sum(a['Q']))
    assert n>=2 and a['lam']>0 and all(d>0 and 0<=d<=c and w>0 for d,c,w in zip(D,C,a['w'][1:]))
    delta=min(a['lam']*w/d for w,d in zip(a['w'][1:],D));states=[]
    for j,(d,c,w) in enumerate(zip(D,C,a['w'][1:]),1):
        for sigma in [-1,1]:
            if 0<=d+sigma<=c and low<=sum(D)+sigma<=B:
                phi=R(n-1,n*(n*d+sigma))+a['lam']*w/d
                Y=list(D);Y[j-1]+=sigma
                assert objective(a,Y)==phi
                states.append(dict(station=j,sigma=sigma,phi=str(phi),direct_F=str(objective(a,Y))))
    beta=min([2*delta]+[R(q['phi']) for q in states])
    minimizers=[dict(station=q['station'],sigma=q['sigma']) for q in states if R(q['phi'])==beta]
    return dict(B=B,sumD=sum(D),sumQ=sum(a['Q']),necessary_total_interval=[low,B],delta=str(delta),two_delta=str(2*delta),
        beta=str(beta),beta_float=float(beta),J=states,minimizers=minimizers,target_total_admissible=low<=sum(D)<=B)

def finite_checks():
    cases=[('balanced',(1,2),(2,3),3,2),('shortage',(2,1),(3,2),2,2),
        ('surplus',(1,2,1),(2,3,2),5,2),('capacity_boundary',(1,1),(1,1),2,2),('empty_J',(1,1),(1,1),0,0)]
    results=[]
    for name,D,C,B,Q in cases:
        a=dict(n=len(D),target=[0]+list(D),capacities=[0]+list(C),initial=[0,B]+[0]*(len(D)-1),Q=[Q],
            w=[R(0)]+[R(1)]*len(D),lam=R(3,20));b=bound(a);checked=0
        for Y in itertools.product(*(range(c+1) for c in C)):
            if not b['necessary_total_interval'][0]<=sum(Y)<=B or list(Y)==list(D):continue
            K=sum(abs(y-d) for y,d in zip(Y,D));F=objective(a,Y)
            assert F>=R(b['delta'])*K and F>=R(b['beta']);checked+=1
        results.append(dict(case=name,states_checked=checked,**b))
    assert not results[-1]['J']
    return results

def run(label='objective_sublevel_analysis'):
    tick=time.perf_counter();result=dict(Optimize=0,new_routes=0,production_search_uses_analysis=False,interpretations={},finite_checks=finite_checks())
    old=OUT/'inherited_r113';manifest=read(old/'input_manifest.json');p=next(p for p in manifest['roles'] if p['id']=='G50-C1')
    path=ROOT/p['input_path'];g50={}
    for interpretation in ['input_decimal','parsed_binary64']:
        a=instance(path,interpretation);b=bound(a);own=[]
        for arm,num in [('M-B',1),('P-S',3)]:
            raw=old/'authoritative/campaign/raw'/f'{num:02d}_G50-C1_S0_{arm}'/'result.json'
            r=read(raw);physical=core.full_fleet(ROOT,p,r);Y=physical['Y'][1:];U=objective(a,Y)
            assert U==R(b['beta']) and b['B']==b['sumD']==527 and b['sumQ']==120
            own.append(dict(arm=arm,result_SHA=sha(raw),input_SHA=sha(path),Y=Y,K=sum(abs(y-d) for y,d in zip(Y,a['target'][1:])),
                exact_U=str(U),float_evaluator_U=physical['F'],exact_U_equals_beta=U==R(b['beta']),strict_improvement_only_Y_equals_D=True,
                physical_feasibility_recomputed=True,new_route_constructed=False))
        assert [q['station'] for q in b['minimizers']]==[1,5,7,11,20,27,28,32,33,36,50]
        assert all(q['sigma']==-1 for q in b['J'])
        if interpretation=='input_decimal':assert b['delta']=='3/500' and b['beta']=='1837/224500'
        g50[interpretation]=dict(**b,own_fleets=own,positive_minimum_attained_by_existing_legal_fleet=True)
    result['G50-C1']=g50
    g100={};p=read(OUT/'input_manifest.json')['roles'][0];path=ROOT/p['input_path']
    for interpretation in ['input_decimal','parsed_binary64']:
        a=instance(path,interpretation);b=bound(a);own=[]
        for l in read(OUT/'campaign/identity.json')['launches']:
            d=Path(l['destination'])
            if not (d/'producer_receipt.json').is_file():continue
            raw=d/'result.json';physical=core.full_fleet(ROOT,p,read(raw));Y=physical['Y'][1:];U=objective(a,Y)
            own.append(dict(arm=l['arm'],result_SHA=sha(raw),producer_receipt_SHA=sha(d/'producer_receipt.json'),Y=Y,
                K=sum(abs(y-d) for y,d in zip(Y,a['target'][1:])),exact_U=str(U),U_float=float(U),
                sufficient_condition_applies=0<U<=R(b['beta']),strict_Y_equals_D=Y==a['target'][1:]))
        g100[interpretation]=dict(**b,own_fleets=own,zero_optimum_known=False)
    result['G100-R2']=g100;result['arithmetic_seconds']=time.perf_counter()-tick
    write(OUT/(label+'.json'),result)
    return result

if __name__=='__main__':print(json.dumps(run(sys.argv[1] if len(sys.argv)>1 else 'objective_sublevel_analysis')),flush=True)

"""Independent binary64 Fraction reference for production's fixed-dual caps."""
from fractions import Fraction as F
from round149_math import scope_from_model
from round151_common import *
def transport(x):
    return (0. if x<0 else 1e-12) if x and abs(x)<1e-12 else x
def reference(scope,actual):
    mu,nu=F(actual['mu']),F(actual['nu']);assert mu>=0 and nu>=0
    a=nu-mu;sites=scope['stations'];mins=[]
    for s in sites:
        c,w,lo,hi=map(F,[s['c'],s['omega'],s['lo'],s['hi']])
        points=[lo,hi]+([1/c] if lo<=1/c<=hi else [])
        mins.append(min(w*abs(c*y-1)+a*y for y in points))
    prefix=[F(0)]
    for m in mins:prefix.append(prefix[-1]+m)
    suffix=[F(0)]*(len(sites)+1)
    for j in range(len(sites)-1,-1,-1):suffix[j]=suffix[j+1]+mins[j]
    resource=mu*scope['Bminus']-nu*scope['B'];d=resource+prefix[-1]
    assert F(actual['dual_lower'])<=d
    assert 0<=F(actual['penalty_lower'])<=max(0,d)
    assert F(actual['beta0'])>=min(F(scope['gamma_U']),F(scope['cutoff'])-F(actual['penalty_lower']))
    by={(s['i'],s['y']):s for s in actual['states']};states=[]
    for j,s in enumerate(sites):
        c,w=F(s['c']),F(s['omega'])
        for y in s['support']:
            h=w*abs(c*y-1);diy=resource+prefix[j]+suffix[j+1]+h+a*y
            assert diy>=d
            v=by[(s['i'],y)]
            assert F(v['dual_lower'])<=diy
            assert 0<=F(v['penalty_lower'])<=max(0,diy)
            assert F(v['beta'])>=min(F(actual['beta0']),F(scope['cutoff'])-F(v['penalty_lower']))
            assert v['beta']<=actual['beta0']
            assert v['transported_beta']==transport(v['beta'])>=v['beta']
            assert v['transported_beta']<=transport(actual['beta0'])
            states.append(dict(i=s['i'],y=y,conditional_dual_exact=str(diy),delta_exact=str(diy-d)))
    assert len(states)==len(by)
    return dict(PASS=True,d_exact=str(d),states=states,fixed_actual_mu=str(mu),fixed_actual_nu=str(nu),
        exact_binary64_reference=True,no_lower_bound_subtraction=True,actual_C_subset_P=True,
        state_count=len(states),Optimize=0,Native_load=0)
def compiled(scope,target,mode='conditional'):
    driver=read(OUT/'rows_driver.json');assert sha(driver['PE'])==driver['PE_SHA']
    assert sha(ROOT/'include/Round151Research.hpp')==driver['header_SHA']
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    text=[f"{len(scope['stations'])} {scope['Bminus']} {scope['B']} {scope['cutoff']:.17g} {scope['gamma_U']:.17g} {mode}"]
    for s in scope['stations']:
        ys=s['support'];text.append(f"{s['c']:.17g} {s['omega']:.17g} {len(ys)} "+' '.join(map(str,ys)))
    source=target.with_suffix('.txt');source.write_text('\n'.join(text)+'\n',encoding='utf-8')
    tick=time.perf_counter();p=subprocess.run([driver['PE'],str(source)],capture_output=True,text=True,env=environment(),timeout=30)
    assert p.returncode==0,p.stderr
    actual=json.loads(p.stdout);proof=reference(scope,actual) if actual['feasible_resource_box'] else dict(PASS=True,infeasible_box=True)
    actual.update(scope=scope,mode=mode,Fraction=proof,driver_SHA=driver['PE_SHA'],header_SHA=driver['header_SHA'],outer_seconds=time.perf_counter()-tick)
    write(target,actual);return actual
def rows(actual,scope=None,mode=None):
    scope=scope or actual['scope'];mode=mode or actual['mode']
    supports={s['i']:set(s['support']) for s in scope['stations']};out=[]
    for s in actual['states']:
        if s['y'] not in supports[s['i']]:continue
        beta=transport(actual['beta0'] if mode=='uniform' else s['beta'])
        if beta>=scope['gamma_U']:continue
        suffix=f"{s['i']}_{s['y']}";terms={f'state_g_{suffix}':1.}
        if beta:terms[f'state_{suffix}']=-beta
        out.append(dict(name=f'r151_cap_{suffix}',sense='<',rhs=0.,terms=terms))
    return out
if __name__=='__main__':pass

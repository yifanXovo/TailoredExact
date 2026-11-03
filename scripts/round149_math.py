"""Exact diagnostic primal/dual oracle and actual C++ enclosure check; no Native."""
from fractions import Fraction as F
from round149_common import *


def oracle(scope):
    sites=scope['stations'];bm,b=F(scope['Bminus']),F(scope['B'])
    ys={s['i']:min(F(s['hi']),max(F(s['lo']),1/F(s['c']))) for s in sites}
    if sum(F(s['lo']) for s in sites)>b or sum(F(s['hi']) for s in sites)<bm:
        return dict(feasible=False)
    total=sum(ys.values());down=total>b;up=total<bm
    remaining=total-b if down else bm-total if up else F(0)
    mu=nu=F(0)
    for s in sorted(sites,key=lambda s:(F(s['omega'])*F(s['c']),s['i'])):
        if remaining<=0:break
        i=s['i'];capacity=ys[i]-s['lo'] if down else s['hi']-ys[i]
        take=min(remaining,capacity)
        if take<=0:continue
        ys[i]+=(-take if down else take);remaining-=take
        if down:nu=F(s['omega'])*F(s['c'])
        else:mu=F(s['omega'])*F(s['c'])
    assert remaining==0
    primal=sum(F(s['omega'])*abs(F(s['c'])*ys[s['i']]-1) for s in sites)
    def dual(mu,nu):
        value=mu*bm-nu*b
        for s in sites:
            c,w,lo,hi=F(s['c']),F(s['omega']),F(s['lo']),F(s['hi'])
            points=[lo,hi]+([1/c] if lo<=1/c<=hi else [])
            value+=min(w*abs(c*y-1)+(nu-mu)*y for y in points)
        return value
    assert dual(mu,nu)==primal
    return dict(feasible=True,p_exact=str(primal),primal=primal,inventory=ys,mu=mu,nu=nu,dual=dual)


def compiled(scope,target):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    driver=read(OUT/'rows_driver.json')
    assert sha(driver['PE'])==driver['PE_SHA'] and sha(ROOT/'include/Round149Research.hpp')==driver['header_SHA']
    sites=scope['stations'];text=[f"{len(sites)} {scope['Bminus']} {scope['B']} {scope['cutoff']:.17g} {scope['gamma_U']:.17g}"]
    for s in sites:
        support=s.get('support',list(range(s['lo'],s['hi']+1)))
        text.append(f"{s['c']:.17g} {s['omega']:.17g} {len(support)} "+' '.join(map(str,support)))
    inp=target.with_suffix('.txt');inp.write_text('\n'.join(text)+'\n',encoding='utf-8')
    tick=time.perf_counter()
    run=subprocess.run([driver['PE'],str(inp)],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stderr
    actual=json.loads(run.stdout);exact=oracle(scope)
    assert actual['feasible']==exact['feasible']
    if exact['feasible']:
        certified=exact['dual'](F(actual['mu']),F(actual['nu']))
        assert F(actual['dual_lower'])<=certified<=exact['primal']
        assert 0<=F(actual['penalty_lower'])<=exact['primal']
        assert float(exact['primal'])-actual['penalty_lower']<1e-10
        assert F(actual['beta'])>=min(F(scope['gamma_U']),F(scope['cutoff'])-F(actual['penalty_lower']))
        actual.update(exact_primal=str(exact['primal']),exact_dual_at_actual_multipliers=str(certified),
            exact_optimal_mu=str(exact['mu']),exact_optimal_nu=str(exact['nu']),exact_primal_dual_equal=True)
    actual.update(scope=scope,exact_outward_PASS=True,driver_SHA=driver['PE_SHA'],
        header_SHA=driver['header_SHA'],driver_outer_seconds=time.perf_counter()-tick)
    write(target,actual);return actual


def qualify():
    facts=[]
    cases=[('fixed_floor',[(2,2,.5,.3),(0,0,.25,.2)],0,2),
        ('shortage',[(0,8,.25,.3),(0,8,.5,.2)],0,3),
        ('surplus',[(0,8,.25,.3),(0,8,.5,.2)],9,12),
        ('zero',[(0,8,.25,.3),(0,8,.5,.2)],0,8),
        ('zero_weight',[(0,8,.25,0),(0,8,.5,.2)],0,1),
        ('kink_boundary',[(3,7,1/3,.11),(0,5,.7,.13)],4,5),
        ('infeasible',[(4,4,.25,.3),(3,3,.5,.2)],0,5)]
    for tag,sites,bm,b in cases:
        scope=dict(Bminus=bm,B=b,cutoff=4.,gamma_U=.9,
            stations=[dict(i=i,lo=lo,hi=hi,c=c,omega=w) for i,(lo,hi,c,w) in enumerate(sites,1)])
        actual=compiled(scope,OUT/'qualification/arithmetic'/f'{tag}.json')
        facts.append(dict(tag=tag,feasible=actual['feasible'],p=actual['penalty_lower'],
            beta=actual['beta'],rows=len(actual['rows']),exact_outward_PASS=True))
    write(OUT/'qualification_arithmetic.json',dict(PASS=True,Optimize=0,Native_load=0,cases=facts))
    print(json.dumps(facts))


if __name__=='__main__':
    if sys.argv[1]=='run':
        assert metered('qualification_arithmetic','diagnostic',[PYTHON,'-B',__file__,'qualify'],60,120)==0
    else:globals()[sys.argv[1]]()

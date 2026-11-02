"""Exact oracle for the actual binary64 ratios; no Optimize or Native import."""
from fractions import Fraction as F
from itertools import product
from round143_math import denominator
from round146_common import *
configure()
def oracle(spec,conditional=True):
    s={int(i):ys for i,ys in spec['supports'].items()};c={int(i):F(v) for i,v in spec['c_binary64'].items()}
    root=denominator(c,s,spec['Bminus'],spec['B']);states={}
    if not root['applicable']:return root,states
    n=len(s)
    for i,ys in s.items():
        for y in ys:
            bounds=denominator(c,dict(s,**{})|{i:[y]},spec['Bminus'],spec['B']) if conditional else root
            if not bounds['applicable']:
                assert bounds['reason']=='INFEASIBLE_BOX_TOTAL_SCOPE';states[i,y]=None;continue
            dl,du=F(bounds['S_L_exact']),F(bounds['S_U_exact'])
            states[i,y]=dict(lower=dl,upper=du,low=max(F(0),1-n*c[i]*y/dl),high=max(F(0),n*c[i]*y/du-1))
    return root,states
def compiled(spec,target,conditional=True):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    q=read(OUT/'rows_driver.json');assert sha(q['PE'])==q['PE_SHA'] and sha(ROOT/'include/Round146Research.hpp')==q['header_SHA']
    s={int(i):ys for i,ys in spec['supports'].items()};c={int(i):v for i,v in spec['c_binary64'].items()}
    inp=target.with_suffix('.txt')
    text=[f"{len(s)} {spec['Bminus']} {spec['B']} {int(conditional)}"]
    text += [f'{c[i]:.17g} {len(ys)} '+ ' '.join(map(str,ys)) for i,ys in sorted(s.items())]
    inp.write_text('\n'.join(text)+'\n',encoding='utf-8')
    run=subprocess.run([q['PE'],str(inp)],cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stderr
    actual=json.loads(run.stdout);root,exact=oracle(spec,conditional)
    assert actual['applicable']==root['applicable']
    if actual['applicable']:
        assert F(actual['lower'])<=F(root['S_L_exact']) and F(actual['upper'])>=F(root['S_U_exact'])
        for state in actual['states']:
            ideal=exact[state['i'],state['y']];assert state['feasible']==(ideal is not None)
            if ideal is None:assert state['low']==state['high']==0;continue
            assert F(state['lower'])<=ideal['lower']<=ideal['upper']<=F(state['upper'])
            for key in ('low','high'):
                assert 0<=F(state[key])<=ideal[key],(state,key,ideal)
                assert float(ideal[key])-state[key]<1e-10
            if c[state['i']]*state['y']==0:assert state['low']==1 and state['high']==0
    actual.update(exact_oracle_PASS=True,scope=spec,conditional=conditional,driver_SHA=q['PE_SHA'],header_SHA=q['header_SHA'])
    write(target,actual);return actual
def activity(rows,point):
    return [dict(name=r['name'],slack=math.fsum(a*point[k] for k,a in r['terms'].items())-r['rhs'],
                 violation_in_g=(r['rhs']-math.fsum(a*point[k] for k,a in r['terms'].items()))/r['terms']['G']) for r in rows]
def qualify():
    configure();tick=time.perf_counter();facts=[]
    cases=[('binary4',{i:[0,1] for i in range(1,5)},{i:1. for i in range(1,5)},1,3),
        ('heterogeneous_holes',{1:[0,2,5],2:[1,4],3:[0,3]},{1:.1,2:1/3,3:1.7},3,7),
        ('fixed',{1:[2],2:[0,3],3:[1]},{1:.125,2:.7,3:1.},3,5),
        ('zero_ratio',{1:[0,2],2:[1,3]},{1:0.,2:.3},1,4),
        ('infeasible_state',{1:[0,10],2:[1,2]},{1:.4,2:.2},1,3),
        ('zero_domain',{1:[0,1],2:[0,2]},{1:.2,2:.7},0,3),
        ('all_zero',{1:[0],2:[0]},{1:1.,2:1.},0,0),
        ('infeasible_domain',{1:[2],2:[3]},{1:1.,2:2.},0,4)]
    for tag,s,c,bm,b in cases:
        spec=dict(supports=s,c_binary64=c,Bminus=bm,B=b);a=compiled(spec,OUT/'qualification/rows'/f'{tag}.json');root,ex=oracle(spec)
        physical=0
        for yy in product(*s.values()):
            y=dict(zip(s,yy));total=sum(yy)
            if not bm<=total<=b:continue
            S=sum(F(c[i])*y[i] for i in s)
            if not S:assert not a['rows'];physical+=1;continue
            G=sum(abs(F(c[i])*y[i]-F(c[j])*y[j]) for i in s for j in s if i<j)/(len(s)*S)
            p={'G':G};p.update({f'state_{i}_{v}':F(y[i]==v) for i,ys in s.items() for v in ys})
            for row in a['rows']:assert sum(F(v)*p[k] for k,v in row['terms'].items())>=0
            for i in s:
                if a['applicable']:assert ex[i,y[i]]['lower']<=S<=ex[i,y[i]]['upper']
            physical+=1
        facts.append(dict(tag=tag,applicable=a['applicable'],rows=len(a['rows']),states=len(a['states']),integer_points=physical,all_exact=True))
    write(OUT/'qualification_exact_rows.json',dict(PASS=True,Optimize=0,Native_load=0,seconds=time.perf_counter()-tick,facts=facts))
    print(json.dumps(facts))
if __name__=='__main__':globals()[sys.argv[1]]()

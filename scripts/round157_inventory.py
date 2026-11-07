"""Exact current-coefficient inventory classes and bounded family enumeration."""
import ast, itertools, re
from collections import Counter, defaultdict
from fractions import Fraction as F
from round153_pricing import stock_value
from round152_math import h_exact
from round157_common import *

def instance(panel):
    path=ROOT/panel['input_path']; assert sha(path)==panel['input_sha256']
    text=path.read_text(encoding='utf-8-sig'); head=text.splitlines()[0]
    def vector(name):
        match=re.search(r'(?m)^\s*'+re.escape(name)+r'\s*=\s*(\[[^\n]*\])',text)
        assert match, name
        return ast.literal_eval(match[1])
    points=vector('points'); initial=vector('initial'); n=len(initial)-1
    assert int(head.split()[0])==n
    q=ast.literal_eval(head[head.index('['):]); assert q==panel['Q_vector']
    weights=vector('weights')
    if abs(max(weights[1:])-10)<=1e-6: weights=[v/10 for v in weights]
    distance=[[math.hypot(a[0]-b[0],a[1]-b[1])/1.5 for b in points] for a in points]
    return dict(n=n,Q=q,initial=initial,capacity=vector('capacities'),target=vector('target'),
                weights=weights,points=points,distance=distance,T=panel['T_seconds'],
                pickup=panel['pickup_seconds'],drop=panel['drop_seconds'],lam=panel['lambda'])

def value(scope,Y):
    costs={(s['i'],v):h_exact(s,v) for s in scope['stations'] for v in s['support']}
    return stock_value(scope,Y,1,costs)

def classes(scope,Y):
    groups=defaultdict(list)
    for s in scope['stations']:
        groups[(float(s['c']).hex(),float(s['omega']).hex())].append(s['i'])
    return [dict(stations=ids,c_hex=c,omega_hex=w,
                 counts={str(v):q for v,q in sorted(Counter(Y[i-1] for i in ids).items())})
            for (c,w),ids in sorted(groups.items(),key=lambda p:p[1][0])]

def signature(scope,Y):
    return json.dumps(classes(scope,Y),sort_keys=True,separators=(',',':'))

def family(scope,Y):
    supports={s['i']:set(s['support']) for s in scope['stations']}
    options=[]
    for group in classes(scope,Y):
        ids=group['stations']; vals=[Y[i-1] for i in ids]
        # The preselected families have at most 21 members. Generate multiset
        # permutations recursively rather than forming factorial duplicates.
        counts=Counter(vals); partial=[]; legal=[]
        def visit(pos):
            if pos==len(ids): legal.append(tuple(partial)); return
            for v in sorted(counts):
                if counts[v] and v in supports[ids[pos]]:
                    counts[v]-=1;partial.append(v);visit(pos+1);partial.pop();counts[v]+=1
        visit(0); assert legal
        options.append((ids,legal))
    result=[]
    for choices in itertools.product(*(x[1] for x in options)):
        member=list(Y)
        for (ids,_),choice in zip(options,choices):
            for i,v in zip(ids,choice):member[i-1]=v
        result.append(member)
    assert list(Y) in result and len({tuple(v) for v in result})==len(result)
    base=value(scope,Y)
    for member in result:
        v=value(scope,member)
        assert v['feasible'] and all(v[k]==base[k] for k in ('G','penalty','phi','S','total'))
    return result

def prepare():
    records={}
    for role,source in read(OUT/'inventory_sources.json').items():
        scope=source['scope'];assert scope['gamma_L']==0
        data=instance(source['panel'])
        for s in scope['stations']:
            i=s['i'];assert s['c']==1/data['target'][i]
            assert s['omega']==data['lam']*data['weights'][i]
        stocks=sorted(source['stocks'],key=lambda r:F(r['price_exact']))
        selected=[];seen=set()
        for stock in stocks:
            Y=stock['Y'];v=value(scope,Y);assert v['feasible'] and v['phi']==F(stock['price_exact'])
            sig=signature(scope,Y)
            if sig in seen:continue
            seen.add(sig);members=family(scope,Y)
            selected.append(dict(rank=len(selected)+1,Y=Y,J=float(v['phi']),J_exact=str(v['phi']),
                G=float(v['G']),H=float(v['penalty']),classes=classes(scope,Y),members=members,
                family_size=len(members),signature_SHA=__import__('hashlib').sha256(sig.encode()).hexdigest(),
                pickup_range=[min(sum(max(0,data['initial'][i]-m[i-1]) for i in range(1,data['n']+1)) for m in members),
                              max(sum(max(0,data['initial'][i]-m[i-1]) for i in range(1,data['n']+1)) for m in members)]))
            if len(selected)==2:break
        assert len(selected)==2
        witnesses=[]
        for path in source['witness_paths']:
            witness=read(path)
            witnesses.append(dict(path=path,SHA=sha(path),keys=list(witness),
                                  objective=witness.get('objective',witness.get('F')),witness=witness))
        records[role]=dict(scope=scope,panel=source['panel'],candidates=selected,
                           positive_control=min(witnesses,key=lambda w:w['objective']))
    write(OUT/'inventory_families.json',records)
    print(json.dumps({role:dict(candidates=[{k:v for k,v in c.items() if k not in ('members','classes')} for c in r['candidates']],
            positive_control={k:v for k,v in r['positive_control'].items() if k!='witness'},
            witness=r['positive_control']['witness']) for role,r in records.items()}),flush=True)

if __name__=='__main__':prepare()

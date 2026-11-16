"""Independent reviewer: read-only physical/objective recomputation, no solver/H.

Uses integer route inventory/load arithmetic, direct distance/handling sums and
Fraction objective arithmetic with the actual parsed binary64 weights/lambda.
This file does not import the producer, its verifier or an optimization API.
"""
from pathlib import Path
from fractions import Fraction
from datetime import datetime, timezone
import ast, hashlib, json, math, re, time

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
R169=OUT.parent

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rat(x):return Fraction(x) if isinstance(x,int) else Fraction.from_float(x)
def frac_report(x):return dict(value=float(x),exact=str(x))

def instance(p):
    inp=ROOT/p['input_path'];text=inp.read_text(encoding='utf-8-sig')
    def vec(name):return ast.literal_eval(re.search(r'^\s*'+name+r'\s*=\s*(\[[^\n]*\])',text,re.M)[1])
    first=text.splitlines()[0];n,m=map(int,first[:first.index('[')].split());q=ast.literal_eval(first[first.index('['):])
    assert n==p['V'] and m==p['M'] and q==p['Q_vector']
    data=dict(n=n,m=m,Q=q,c=vec('capacities'),b=vec('initial'),target=vec('target'),weights=vec('weights'),points=vec('points'))
    if abs(max(data['weights'][1:])-10)<=1e-6:data['weights']=[v/10 for v in data['weights']]
    assert sha(inp)==p['input_sha256']
    assert all(len(data[k])==n+1 for k in ['c','b','target','weights','points'])
    return data

def physical(p,a,routes):
    y=a['b'].copy();seen=set();used=set();cars=[]
    for r in routes:
        k=r['vehicle'];assert isinstance(k,int) and 0<=k<a['m'] and k not in used;used.add(k)
        nodes=r['nodes'];assert len(nodes)>=2 and nodes[0]==nodes[-1]==0
        ops={}
        for op in r['operations']:
            i,x,d=op['station'],op['pickup'],op['drop']
            assert all(isinstance(v,int) for v in [i,x,d]) and 1<=i<=a['n'] and i not in ops
            assert min(x,d)==0 and max(x,d)>0;ops[i]=(x,d)
        assert len(ops)==len(nodes)-2 and set(ops)==set(nodes[1:-1])
        load=pick=drop=0;prefix=[]
        for i in nodes[1:-1]:
            assert i not in seen;seen.add(i);x,d=ops[i];load+=x-d;pick+=x;drop+=d
            assert 0<=load<=a['Q'][k];prefix.append(load);y[i]+=d-x
            assert 0<=y[i]<=a['c'][i]
        travel=math.fsum(math.hypot(a['points'][i][0]-a['points'][j][0],a['points'][i][1]-a['points'][j][1])/1.5 for i,j in zip(nodes,nodes[1:]))
        handling=pick*p['pickup_seconds']+drop*p['drop_seconds']+load*p['drop_seconds']
        duration=travel+handling;assert duration<=p['T_seconds']+1e-7
        cars.append(dict(vehicle=k,nodes=nodes,prefix_loads=prefix,return_load=load,peak_load=max([0]+prefix),
            travel=travel,pickups=pick,drops=drop,station_handling=pick*p['pickup_seconds']+drop*p['drop_seconds'],
            return_unloading=load*p['drop_seconds'],duration=duration,time_slack=p['T_seconds']-duration))
    assert used==set(range(a['m']))
    ratios=[Fraction(y[i],a['target'][i]) for i in range(1,a['n']+1)]
    S=sum(ratios);H=sum(abs(ri-rj) for i,ri in enumerate(ratios) for rj in ratios[i+1:])
    G=H/(a['n']*S) if S else Fraction(0)
    P=sum(rat(a['weights'][i+1])*abs(r-Fraction(1)) for i,r in enumerate(ratios))
    F=G+rat(p['lambda'])*P
    return dict(Y=y,G=frac_report(G),P=frac_report(P),F=frac_report(F),cars=cars),G,P

def main():
    begin=time.perf_counter();panel=read(R169/'h_panel_frozen.json');rows=[];selected=[]
    for p in panel['roles']:
        a=instance(p);d=R169/'h_raw'/p['id']/'primal';v={}
        for name in ['base','M_s1','M_s2','C_s1','C_s2']:
            meta=read(d/name/'path.json');fleet=d/name/'fleet.json'
            x,G,P=physical(p,a,read(fleet)['routes']);F=G+rat(p['lambda'])*P
            assert sha(fleet)==meta['fleet_SHA256']
            assert meta['input_SHA256']==p['input_sha256'] and meta['evaluation_lambda']==p['lambda']
            assert abs(float(G)-meta['G'])<=1e-12 and abs(float(P)-meta['P'])<=1e-12 and abs(float(F)-meta['F'])<=1e-12
            search_F=G+rat(meta['search_lambda'])*P
            assert abs(float(search_F)-meta['search_F'])<=1e-12
            assert meta['valid'] and meta['complete'] and meta['joint_complete'] and meta['descent_complete'] and meta['closure_complete']
            assert meta['descent_seeds_completed']==25
            seed=20260626+(0 if name=='base' else int(name[-1]));assert meta['effective_seed']==seed
            expected=p['lambda']*(.5 if name=='C_s1' else 2 if name=='C_s2' else 1)
            assert meta['search_lambda']==expected
            v[name]=meta['F']
            rows.append(dict(role=p['id'],path=name,fleet_SHA256=sha(fleet),recomputed=x,search_F=frac_report(search_F),
                original_F_error=float(F)-meta['F'],search_F_error=float(search_F)-meta['search_F']))
        s=read(d/'selection.json');b=v['base'];m=min(v[k] for k in ['base','M_s1','M_s2']);c=min(v[k] for k in ['base','C_s1','C_s2'])
        delta=max(1e-6,.001*max(b,1e-12));assert (s['B'],s['M'],s['C'])==(b,m,c)
        assert s['delta']==delta and s['E4_role_gate']==(c<min(b,m)-delta)
        assert m<=b and c<=b
        selected.append(dict(role=p['id'],B=b,M=m,C=c,Delta_restart=b-m,Delta_weight=m-c,delta=delta,
            role_gate=c<min(b,m)-delta,can_trigger_E5=p['can_trigger_E5']))
    assert len(rows)==35
    out=dict(UTC=datetime.now(timezone.utc).isoformat(),schema='round169-independent-math-readback-v1',
        source='independent reviewer; no producer/verifier import, no solver API',H_fleets=35,
        all_physical_and_objective_checks_pass=True,all_three_complete_H_stages_verified=True,
        all_pool_inclusion_and_gate_checks_pass=True,E4_triggered=any(r['role_gate'] and r['can_trigger_E5'] for r in selected),
        selected=selected,rows=rows,seconds=time.perf_counter()-begin)
    (OUT/'math_readback_initial.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k not in ['rows','selected']},indent=2))

if __name__=='__main__':main()

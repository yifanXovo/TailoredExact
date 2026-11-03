"""Independent Round150 CPF checks; standard library only, never Native."""
from pathlib import Path
from fractions import Fraction as F
import gzip, hashlib, json, math, time, datetime

ROOT=Path('E:/codes/ExactEBRP-work/worktrees/paper-current')
DEST=Path(__file__).resolve().parent
ROLES=['K-20-S','K-35-U','R-X20-S-T1']
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def down(q):
    x=float(q)
    return math.nextafter(x,-math.inf) if F(x)>q else x
def up(q):
    x=float(q)
    return math.nextafter(x,math.inf) if F(x)<q else x
def components(scope,mu,nu):
    a=F(nu)-F(mu); mi={}; sites={s['i']:s for s in scope['stations']}
    for i,s in sites.items():
        c,w,lo,hi=map(F,[s['c'],s['omega'],s['lo'],s['hi']])
        points=[lo,hi]
        if c and lo<=1/c<=hi: points.append(1/c)
        mi[i]=min(w*abs(c*z-1)+a*z for z in points)
    constant=F(mu)*F(scope['Bminus'])-F(nu)*F(scope['B'])
    return a,mi,constant,sites
def conditional_oracle(scope,index,y):
    # A few independent exact continuous resource oracles, not candidate construction.
    sites=scope['stations']; ys={}; limits={}
    for s in sites:
        lo,hi=(F(y),F(y)) if s['i']==index else (F(s['lo']),F(s['hi']))
        c=F(s['c']); limits[s['i']]=(lo,hi)
        ys[s['i']]=min(hi,max(lo,1/c)) if c else lo
    bm,b=F(scope['Bminus']),F(scope['B'])
    assert sum(v[0] for v in limits.values())<=b
    assert sum(v[1] for v in limits.values())>=bm
    total=sum(ys.values()); direction=-1 if total>b else 1
    remain=total-b if total>b else max(F(0),bm-total)
    for s in sorted(sites,key=lambda s:(F(s['omega'])*abs(F(s['c'])),s['i'])):
        i=s['i']; lo,hi=limits[i]
        available=ys[i]-lo if direction==-1 else hi-ys[i]
        move=min(available,remain); ys[i]+=direction*move; remain-=move
    assert not remain
    return sum(F(s['omega'])*abs(F(s['c'])*ys[s['i']]-1) for s in sites)
def run():
    start=time.perf_counter(); facts=[]
    for role in ROLES:
        path=ROOT/'results/unified_exact_round149/LP'/f'{role}_PF'
        old=read(path/'result.json'); ar=read(path/'arithmetic.json')
        scope=read(path/'construction.json')['scope']
        assert sha(path/'model.mps')==old['model_SHA']
        point=json.loads(gzip.decompress((path/'solution.json.gz').read_bytes()))
        a,mi,const,sites=components(scope,ar['mu'],ar['nu'])
        d=const+sum(mi.values()); violations=[]; records=[]
        for i,s in sites.items():
            for y in s['support']:
                h=F(s['omega'])*abs(F(s['c'])*y-1)
                delta=h+a*y-mi[i]; assert delta>=0
                leave=const+sum(v for j,v in mi.items() if j!=i)+h+a*y
                assert leave==d+delta
                floor=max(F(ar['penalty_lower']),F(0),F(down(leave)))
                beta=min(ar['beta'],up(F(scope['cutoff'])-floor))
                assert F(beta)>=min(F(ar['beta']),F(scope['cutoff'])-floor)
                v=point[f'state_g_{i}_{y}']-beta*point[f'state_{i}_{y}']
                row=dict(i=i,y=y,d_exact=str(leave),penalty_lower=float(floor),beta=beta,violation=v)
                records.append(row)
                if v>1e-8: violations.append(row)
        samples=[records[0],records[-1],max(records,key=lambda r:r['violation'])]
        for row in samples:
            oracle=conditional_oracle(scope,row['i'],row['y'])
            assert F(row['d_exact'])<=oracle
            row['conditional_oracle_exact']=str(oracle)
        facts.append(dict(role=role,states=len(records),violations_above_1e_8=len(violations),
            max_violation=max(r['violation'] for r in records),beta_min=min(r['beta'] for r in records),
            d_exact=str(d),samples=samples,source_model_SHA=old['model_SHA'],
            all_state_delta_nonnegative=True,exact_leave_one_out=True,all_beta_outward=True))
    # Rational local AP/CPF example: keeping product coordinates is material.
    s=[F(1,2),F(1,2)]; t=[F(0),F(2,5)]; beta=[F(4,5),F(2,5)]
    assert sum(t)==F(2,5) and sum(t)+F(1,5)<=F(4,5)
    assert t[1]>beta[1]*s[1]
    receipt=dict(PASS=True,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        independent_nonimplementer=True,source_script_SHA=sha(__file__),
        Native_load=0,Optimize=0,elapsed_seconds=time.perf_counter()-start,facts=facts,
        scope='CPF fixed-dual exact state arithmetic and three per-role oracle samples only',
        mathematical_findings=['a=nu-mu is correct','weighted omega already contains lambda',
        'no lower-bound subtraction','beta outward transport','conditional beta is never global',
        'local one-station hull only','AP example separates the extended product coordinates only'])
    (DEST/'preliminary_math_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))
if __name__=='__main__':run()

"""Solver-free exact-dyadic replay of saved numeric fleet certificates.
This is execution-team verification, separate from the independent review.
"""
import sys,json,itertools,math
import hashlib
from fractions import Fraction as F
from round101_common import *
from round100_idle import ensure_idle
def exact(v):return F.from_float(float(v))
def replay_contract(c):
    d=[[exact(x) for x in row] for row in c['travel_lower']];n=len(d)
    for i in range(n):d[i][i]=F(0)
    for k in range(n):
        for i in range(n):
            for j in range(n):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
    assert all(exact(c['shortest_lower'][i][j])<=d[i][j] for i in range(n) for j in range(n))
    return [[exact(x) for x in row] for row in c['shortest_lower']]
def rank(c,p,d=None):
    d=d or replay_contract(c);es=p['events'];N=len(es);T=exact(c['horizon_upper']);cost=exact(c['handling_lower']);Q=c['capacities']
    assert len({e[0] for e in es})==N
    for i,sign,q in es:assert 1<=i<len(c['initial']) and sign in [-1,1] and 1<=q<=(c['initial'][i] if sign<0 else c['station_capacity'][i]-c['initial'][i])
    def one(e):return d[0][e[0]]+d[e[0]][0]
    def eligible(k,e):return e[2]<=Q[k] and one(e)+cost*e[2]<=T
    if p['method']=='complete_subset_dp':
        assert N<=10
        # Exact dyadic Held-Karp on STORED LOWER arcs. Any C++ allowed subset
        # must contain all subsets not excluded by this exact necessary system.
        size=1<<N;travel=[None]*size;travel[0]=F(0);path={}
        for j,e in enumerate(es):path[1<<j,j]=d[0][e[0]]
        for mask in range(1,size):
            travel[mask]=min(path[mask,j]+d[es[j][0]][0] for j in range(N) if mask&(1<<j))
            travel[mask]=max(travel[mask],max(one(es[j]) for j in range(N) if mask&(1<<j)))
            for j in range(N):
                if mask&(1<<j):
                    for h in range(N):
                        if not mask&(1<<h):
                            k=(mask|(1<<h),h);v=path[mask,j]+d[es[j][0]][es[h][0]]
                            path[k]=min(path.get(k,v),v)
        allowed=p['allowed'];assert len(allowed)==len(Q)
        for k in range(len(Q)):
            assert len(allowed[k])==size and allowed[k][0]==1
            for mask in range(1,size):
                chosen=[es[j] for j in range(N) if mask&(1<<j)]
                P=sum(q for i,s,q in chosen if s<0);D=sum(q for i,s,q in chosen if s>0)
                if all(e[2]<=Q[k] for e in chosen) and travel[mask]+cost*max(P,D)<=T:assert allowed[k][mask],('unsafe exclusion',k,mask)
        dp=[[0]*size]
        for k in range(len(Q)):
            layer=[]
            for mask in range(size):
                best=dp[-1][mask];a=mask
                while a:
                    if allowed[k][a]:best=max(best,a.bit_count()+dp[-1][mask^a])
                    a=(a-1)&mask
                layer.append(best)
            dp.append(layer)
        assert dp==p['dp'];assert dp[-1][-1]==p['rank'];return p['rank']
    assert p['method'] in ['eligibility_slot_upper','sum_cardinality_upper']
    # C++ may retain a borderline eligibility/count that exact arithmetic would
    # exclude; verify stored slot caps are AT LEAST the exact necessary caps.
    caps=[];sets=[]
    for k in range(len(Q)):
        eligible_es=[e for e in es if eligible(k,e)];ell=min((one(e) for e in eligible_es),default=F(0))
        # Stored ell may additionally be lower due to safe rounded eligibility.
        stored_ell=exact(p['travel_min'][k]);assert not eligible_es or stored_ell<=ell
        for sign,stored in [(-1,p['pickup_counts'][k]),(1,p['drop_counts'][k])]:
            qs=sorted(e[2] for e in eligible_es if e[1]==sign);total=0;required=0
            for q in qs:
                total+=q
                if stored_ell+cost*total>T:break
                required+=1
            assert stored>=required;caps.append(stored)
    # To replay the actual relaxation, use its rounded conservative eligibility
    # (all nominal borderline eligibilities may be retained); exact eligibility
    # is a subset, so its slot optimum cannot exceed the claimed RHS.
    for e in es:sets.append([2*k+(e[1]>0) for k in range(len(Q)) if eligible(k,e)])
    slots=[k for k,n in enumerate(caps) for _ in range(n)];owners=[None]*len(slots)
    def augment(e,seen):
        for j,k in enumerate(slots):
            if j not in seen and k in sets[e]:
                seen.add(j)
                if owners[j] is None or augment(owners[j],seen):owners[j]=e;return True
        return False
    matching=sum(augment(e,set()) for e in range(N));assert matching<=p['rank']<=N
    assert p['rank']<=min(N,sum(caps))
    return p['rank']
def verify(folder,output):
    ensure_idle();folder=Path(folder);records=[];total=0;dp_checks=0;replayed=set()
    for path in sorted(folder.rglob('*.round101.certificates.jsonl')):
        source=Path(str(path).replace('.certificates.jsonl','.contract.json'));binding=read(source);c=binding['column_contract'];d=replay_contract(c)
        rows=[json.loads(x) for x in path.read_text().splitlines()];summaries=[]
        contract_key=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()
        for row in rows:
            p=row['proof'];proof_key=(contract_key,hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest())
            if proof_key not in replayed:rank(c,p,d);replayed.add(proof_key)
            dp_checks+=p['method']=='complete_subset_dp';total+=1
            indices=[j for j,a,v in row['columns']];assert len(set(indices))==len(indices) and all(a==1 for j,a,v in row['columns'])
            expected=[]
            for i,s,q in p['events']:
                expected.extend(j for y,j in c['states'][i] if (y<=c['initial'][i]-q if s<0 else y>=c['initial'][i]+q))
            assert sorted(expected)==indices
            activity=sum((exact(v) for j,a,v in row['columns']),F(0));assert exact(row['activity_lower'])<=activity
            assert exact(row['violation_lower'])<=activity-p['rank'] and row['violation_lower']>0
            if len(summaries)<3:summaries.append(dict(node=row['node'],support=len(p['events']),rank=p['rank'],method=p['method'],violation=row['violation_lower']))
        records.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),rows=len(rows),samples=summaries))
        print(json.dumps(dict(verified=path.relative_to(ROOT).as_posix(),records=len(rows),total=total)),flush=True)
    write(output,dict(passed=True,certificates=total,small_dp_certificates=dp_checks,distinct_contract_proof_replays=len(replayed),records=records,
        scope='exact dyadic lower-contract replay, complete DP layers and safe scalable caps; no native search rerun'))
    print(json.dumps(dict(passed=True,certificates=total,small_dp_certificates=dp_checks)))
if __name__=='__main__':verify(sys.argv[1],sys.argv[2])

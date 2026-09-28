"""Independent exhaustive order oracle for saved development transitions only."""
import itertools
import time
from round96_prepare import ROOT,OUT,read,write,sha,citi
from round96_order_analyze import operations,duration

def oracle(w,p,dist,Q):
    original={r['vehicle']:r['nodes'][1:-1] for r in w['routes']}
    ops=operations(w);potential=duration(w,p,dist,len(Q));best=potential;chosen=None;count=0
    # Independent sequence construction from two adjacent blocks and all
    # Cartesian order/orientation choices, with original physical prefix scan.
    for k in range(len(Q)):
        route=original.get(k,[]);n=len(route)
        pickup=sum(ops[i][1] for i in route);drop=sum(ops[i][2] for i in route)
        handling=p['pickup_seconds']*pickup+p['drop_seconds']*drop+p['drop_seconds']*(pickup-drop)
        current=duration(w,p,dist,len(Q))
        for a,b,c in itertools.combinations(range(n+1),3):
            for swap,ra,rb in itertools.product(range(2),repeat=3):
                if not(swap or ra or rb):continue
                count+=1;left=route[a:b];right=route[b:c]
                if ra:left=left[::-1]
                if rb:right=right[::-1]
                blocks=right+left if swap else left+right
                trial=route[:a]+blocks+route[c:]
                if trial==route:continue
                load=0;valid=True
                for i in trial:
                    load+=ops[i][1]-ops[i][2]
                    if not 0<=load<=Q[k]:valid=False;break
                if not valid:continue
                travel=0.;last=0
                for i in trial:travel+=dist[last][i];last=i
                travel+=dist[last][0];total=travel+handling
                if total>p['T_seconds']+1e-7:continue
                values={r['vehicle']:r['duration'] for r in w['routes']};values[k]=total
                cand=sorted([values.get(j,0.) for j in range(len(Q))],reverse=True)
                if cand<best:best=cand;chosen=dict(vehicle=k,nodes=trial,key=[a,b,c,swap,ra,rb])
    return dict(found=chosen is not None,choice=chosen,potential=best,proposals=count)

def main():
    started=time.perf_counter();batch=read(OUT/'route_order/completed.json')
    cases={c['id']:c for c in read(OUT/'fixed_route_cases.json')['cases']};records=[]
    for item in batch['records']:
        cid=item['receipt']['id'];p=cases[cid]['panel'];root=OUT/'route_order'/cid/'order'
        Q=citi.parse_instance_mirror(ROOT/p['instance_path'])['Q'];count=item['result']['order_moves'];checked=[]
        for k in range(count+1):
            before=read(root/f'old_{k}'/'final.json');dist=read(root/f'old_{k}'/'actual_distances.json')
            result=oracle(before,p,dist,Q)
            if k<count:
                after=read(root/f'order_{k+1}.json');assert result['found']
                choice=result['choice'];actual={r['vehicle']:r['nodes'][1:-1] for r in after['routes']}
                assert actual[choice['vehicle']]==choice['nodes'],(cid,k,choice,actual)
                assert result['potential']==duration(after,p,dist,len(Q))
            else:assert not result['found'] and item['result']['exhausted'],(cid,k,result)
            checked.append(result)
        records.append(dict(id=cid,passes=checked))
    write(OUT/'route_order_oracle.json',dict(passed=True,records=records,optimizer_calls=0,
        source_sha256=sha(__file__),completed_sha256=sha(OUT/'route_order/completed.json'),
        elapsed_seconds=time.perf_counter()-started,scope='Offline exhaustive replay of each new best order and all six exhaustion claims.'))

if __name__=='__main__':main()

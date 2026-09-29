"""Independent replay of all accepted neutral order witnesses; no Optimize."""
import csv
from round96_prepare import ROOT, OUT, read, write, sha, evidence, citi

def operations(w):
    return {o[0]:(r['vehicle'],o[1],o[2]) for r in w['routes'] for o in r['operations']}

def duration(w,p,dist,M):
    values=[0.]*M
    for route in w['routes']:
        travel=0.
        for a,b in zip(route['nodes'],route['nodes'][1:]):travel+=dist[a][b]
        pickup=sum(o[1] for o in route['operations']);drop=sum(o[2] for o in route['operations'])
        handling=p['pickup_seconds']*pickup+p['drop_seconds']*drop+p['drop_seconds']*(pickup-drop)
        values[route['vehicle']]=travel+handling
    return sorted(values,reverse=True)

def main():
    cases={c['id']:c for c in read(OUT/'fixed_route_cases.json')['cases']}
    completed=read(OUT/'route_order/completed.json');rows=[];audits=[]
    for item in completed['records']:
        cid=item['receipt']['id'];case=cases[cid];p=case['panel'];root=OUT/'route_order'/cid
        fleet=citi.parse_instance_mirror(ROOT/p['instance_path'])['M']
        checked=[]
        for path in sorted(root.rglob('*.json')):
            obj=read(path)
            if not isinstance(obj,dict) or 'routes' not in obj:continue
            obj['F']=obj.get('F',obj.get('objective'));v=evidence.physical_module.physical(p,obj)
            assert v['original_T_feasible']
            checked.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),physical=v))
        moves=[];r=item['result'];count=r['order_moves']
        for k in range(1,count+1):
            old=root/'order'/f'old_{k-1}';before=read(old/'final.json');after=read(root/'order'/f'order_{k}.json')
            assert operations(before)==operations(after)
            dist=read(old/'actual_distances.json');a=duration(before,p,dist,fleet)
            b=duration(after,p,dist,fleet);assert b<a,(cid,k,a,b)
            assert before['F']==after['F'] and before['inventory']==after['inventory']
            moves.append(dict(number=k,before=a,after=b,inventory_owner_operation_preserved=True))
        audits.append(dict(id=cid,passed=True,witnesses=checked,order_moves=moves))
        rows.append(dict(id=cid,initial_F=r['initial_F'],R83_F=r['old_F'],order_F=r['order_F'],
            incremental_gain=r['old_F']-r['order_F'],R83_seconds=r['old_seconds'],order_seconds=r['order_seconds'],
            process_seconds=item['receipt']['wall_seconds'],order_moves=count,old_neutral_after_order=r['old_neutral_after_order'],
            inserted_after_order=r['insertions_after_order'],quantity_after_order=r['quantities_after_order']))
    dest=OUT/'route_order_audit';dest.mkdir(exist_ok=False)
    write(dest/'audit.json',dict(passed=True,optimizer_calls=0,records=audits,
        scope='Independent physical verification of every persisted witness and exact replay of each new neutral duration decrease.'))
    with (dest/'comparison.csv').open('x',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write(dest/'summary.json',dict(rows=rows,process_seconds=sum(r['process_seconds'] for r in rows),
        incremental_order_seconds=sum(r['order_seconds'] for r in rows),starts=6,optimizer_calls=0,
        improving_snapshots=sum(r['incremental_gain']>1e-7 for r in rows)))

if __name__=='__main__':main()

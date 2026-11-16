"""Tables, structural descriptions and expense aggregation; read-only science."""
from round169_common import *
import itertools
def changes(p,base,new):
    def decode(routes):
        owner={};order={};stock={};sign={}
        for r in routes:
            order[r['vehicle']]=r['nodes'][1:-1]
            for op in r['operations']:
                i=op['station'];owner[i]=r['vehicle'];stock[i]=op['drop']-op['pickup'];sign[i]=1 if stock[i]>0 else -1
        return owner,order,stock,sign
    bo,br,bq,bs=decode(base);best=None
    for perm in itertools.permutations(range(p['M'])):
        if any(p['Q_vector'][i]!=p['Q_vector'][perm[i]] for i in range(p['M'])):continue
        mapped=[dict(r,vehicle=perm[r['vehicle']]) for r in new];no,nr,nq,ns=decode(mapped)
        common=set(bo)&set(no);owners=[i for i in sorted(common) if bo[i]!=no[i]];inversions=[]
        for k in range(p['M']):
            fixed={i for i in common if bo[i]==no[i]==k};a=[i for i in br.get(k,[]) if i in fixed];b=[i for i in nr.get(k,[]) if i in fixed]
            where={i:j for j,i in enumerate(b)}
            inversions += [dict(vehicle=k,pair=[i,j]) for t,i in enumerate(a) for j in a[t+1:] if where[i]>where[j]]
        key=(len(owners),len(inversions),sum(br.get(k,[])!=nr.get(k,[]) for k in range(p['M'])),perm)
        v=dict(compatible_vehicle_relabel=list(perm),served_added=sorted(set(no)-set(bo)),served_removed=sorted(set(bo)-set(no)),
            owner_changes=[dict(station=i,old=bo[i],new=no[i]) for i in owners],relative_order_inversions=inversions,
            stock_changes=[dict(station=i,old_net=bq.get(i,0),new_net=nq.get(i,0)) for i in sorted(set(bq)|set(nq)) if bq.get(i,0)!=nq.get(i,0)],
            sign_flips=[i for i in sorted(common) if bs[i]!=ns[i]],old_orders=br,new_orders=nr)
        if best is None or key<best[0]:best=(key,v)
    v=best[1];v['only_quantity_change']=bool(v['stock_changes']) and not any(v[k] for k in ['served_added','served_removed','owner_changes','relative_order_inversions'])
    v['R168_parent_certificate_applied']=False
    return v

def h_tables():
    panel=read(OUT/'h_panel_frozen.json');result=read(OUT/'h_results.json');paths=[];structures=[];pools=[]
    for p,s in zip(panel['roles'],result['rows']):
        d=OUT/'h_raw'/p['id']/'primal';base=read(d/'base/fleet.json')['routes'];by={}
        for name in panel['path_order']:
            if not (d/name/'path.json').exists():continue
            x=read(d/name/'path.json');x['role']=p['id'];x['raw_initial_orders_txt_SHA256']=sha(d/name/'initial_random_orders.txt')
            x['initial_random_orders_SHA256_semantics']='SHA256 of LF-normalized in-memory initial chromosome transcript; raw txt may use CRLF'
            paths.append(x);by[name]=x
        for arm in ['M','C']:
            name=s['selected_'+arm];structures.append(dict(role=p['id'],arm=arm,selected=name,
                changes=changes(p,base,read(d/name/'fleet.json')['routes'])))
        pools.append(dict(role=p['id'],B=s['B'],M=s['M'],C=s['C'],Delta_restart=s['Delta_restart'],Delta_weight=s['Delta_weight'],
            weight_relative_to_B=(s['M']-s['C'])/s['B'] if s['B'] else 0,
            B_path_seconds=by['base']['path_seconds'],
            M_pool_path_seconds=sum(by[n]['path_seconds'] for n in ['base','M_s1','M_s2'] if n in by),
            C_pool_path_seconds=sum(by[n]['path_seconds'] for n in ['base','C_s1','C_s2'] if n in by),
            E4_role_gate=s['E4_role_gate'],can_trigger_E5=s['can_trigger_E5']))
    write(OUT/'h_path_results.json',dict(rows=paths,field_semantics='actual independently executed terminal H paths; search and original evaluation separate'))
    keys=[k for k in paths[0] if k not in ['notes']]
    with (OUT/'h_path_results.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(paths)
    write(OUT/'fleet_changes.json',dict(rows=structures,compatible_relabel_enumeration=True,description_not_causal_attribution=True))
    write(OUT/'h_pool_costs.json',dict(rows=pools,diagnostic_base_shared=True,not_three_arms_measured_wall_times=True,
        actual_H_paths=len(paths),sum_H_seconds=sum(p['H_seconds'] for p in paths),sum_path_seconds=sum(p['path_seconds'] for p in paths),
        shared_outer_seconds=result['shared_outer_seconds'],Optimize=0))
    print(json.dumps(pools,indent=2))
if __name__=='__main__':h_tables()

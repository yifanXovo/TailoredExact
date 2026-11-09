"""Read saved trajectories once; no grid, repricing or new solver calls."""
import csv
from round159_common import *

def run():
    records={};trajectories=[]
    for role,suffix in [('R-X35-S-T2','rx'),('N-B35-S','nb')]:
        source=read(OUT/'inputs_v2'/role/'source.json');d=source['data'];chain=[]
        ref=source['source']['endpoint']['U'];lower=source['source']['lower']
        for stage in ('baseline','joint'):
            label=f'{stage}_{suffix}';folder=OUT/'runs'/label;previous=read(folder/'start.json');changes=[]
            paths=sorted(folder.glob('*_events.jsonl'),key=lambda p:int(p.name.split('_')[1]))
            for path in paths:
                for line in path.read_text().splitlines():
                    p=json.loads(line);qty=[i for i in range(1,d['n']+1) if p['Y'][i-1]!=previous['Y'][i-1]]
                    active=lambda q,i:q['Y'][i-1]!=d['initial'][i]
                    owners=[i for i in range(1,d['n']+1) if active(previous,i) and active(p,i) and previous['owner'][i-1]!=p['owner'][i-1]]
                    activation=[i for i in qty if not active(previous,i) and active(p,i)]
                    zero=[i for i in qty if active(previous,i) and not active(p,i)]
                    flips=[i for i in qty if (previous['Y'][i-1]-d['initial'][i])*(p['Y'][i-1]-d['initial'][i])<0]
                    net_before=[0]*len(d['Q']);net_after=net_before.copy()
                    for q,net in [(previous,net_before),(p,net_after)]:
                        for i in range(1,d['n']+1):
                            if active(q,i):net[q['owner'][i-1]]+=d['initial'][i]-q['Y'][i-1]
                    delta=[a-b for a,b in zip(net_after,net_before)]
                    quantity_net=[0]*len(d['Q']);owner_net=quantity_net.copy()
                    for i in range(1,d['n']+1):
                        if not active(previous,i) and not active(p,i):continue
                        oldk=previous['owner'][i-1] if active(previous,i) else p['owner'][i-1]
                        oldq=d['initial'][i]-previous['Y'][i-1];newq=d['initial'][i]-p['Y'][i-1]
                        quantity_net[oldk]+=newq-oldq
                        if active(p,i) and p['owner'][i-1]!=oldk:
                            owner_net[oldk]-=newq;owner_net[p['owner'][i-1]]+=newq
                    assert [a+b for a,b in zip(quantity_net,owner_net)]==delta
                    row=dict(role=role,stage=stage,iteration=p['iteration'],before_J=previous['J'],after_J=p['J'],
                        quantity_stations=qty,owner_changes=owners,activated=activation,zeroed=zero,direction_flips=flips,per_car_net_change=delta,
                        quantity_net_on_old_owner=quantity_net,owner_net_compensation=owner_net,
                        event=path.relative_to(ROOT).as_posix(),seconds=p['seconds'])
                    changes.append(row);trajectories.append(row);previous=p
            checked=read(OUT/'review'/f'{label}.json');best=checked['best']
            receipt=read(OUT/'fees'/label/'receipt.json')
            chain.append(dict(stage=stage,U_R=best['J'],J_exact=best['J_exact'],eta_R=(best['J']-lower)/(ref-lower),
                accepted_events=len(changes),seconds=receipt['outer_seconds'],calls=len(checked['calls']),
                nodes=sum(c['nodes'] for c in checked['calls']),quantity_change_events=sum(bool(r['quantity_stations']) for r in changes),
                owner_change_events=sum(bool(r['owner_changes']) for r in changes),activation_events=sum(bool(r['activated']) for r in changes),
                zero_events=sum(bool(r['zeroed']) for r in changes),direction_flip_events=sum(bool(r['direction_flips']) for r in changes),
                non_equal_net_events=sum(any(r['quantity_net_on_old_owner']) and any(r['owner_net_compensation']) for r in changes),resource_witness=best))
        records[role]=dict(L_I=lower,U_I=source['source']['upper'],U_P_ref=ref,U_P=ref,initial_U_R=source['J'],
            initial_eta=(source['J']-lower)/(ref-lower),chain=chain,global_resource_lower='UNKNOWN above inherited L_I',
            price_reduction_from_fixed_owner=chain[0]['U_R']-chain[1]['U_R'],price_reduction_from_old_ref=ref-chain[1]['U_R'],
            whole_Q_ceiling_claim=False)
    write(OUT/'trajectory_analysis.json',dict(UTC=utc(),roles=records,events=trajectories,
        scope='Saved strict accepted trajectories only; not a closure/reachability theorem for historical move sequences'))
    report=OUT/'reports';report.mkdir(exist_ok=True)
    with (report/'resource_chain.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['role','stage','L_I','U_I','U_P_ref','U_R','eta_R','seconds','nodes','accepted_events','owner_change_events','activation_events','zero_events','direction_flip_events','non_equal_net_events']);w.writeheader()
        for role,r in records.items():
            for c in r['chain']:w.writerow({k:dict(role=role,**r,**c)[k] for k in w.fieldnames})
    print(json.dumps({role:{'U_R':r['chain'][-1]['U_R'],'eta_R':r['chain'][-1]['eta_R'],'joint_events':r['chain'][-1]['accepted_events'],
        'owner_events':r['chain'][-1]['owner_change_events'],'activation':r['chain'][-1]['activation_events'],'non_equal_net':r['chain'][-1]['non_equal_net_events']} for role,r in records.items()}))

if __name__=='__main__':run()

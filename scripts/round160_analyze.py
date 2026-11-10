"""Saved-event physical/original-J readback and finite scoped mechanism accounting."""
from collections import Counter
from fractions import Fraction as F
from round160_common import *
from round160_qualify import original
from round157_fleet import verify

def changes(d,a,b):
    quantity=[i for i in range(1,d['n']+1) if a['Y'][i-1]!=b['Y'][i-1]]
    owner=[i for i in range(1,d['n']+1) if a['owner'][i-1]>=0 and b['owner'][i-1]>=0 and a['owner'][i-1]!=b['owner'][i-1]]
    activation=[i for i in range(1,d['n']+1) if a['owner'][i-1]<0 and b['owner'][i-1]>=0]
    zero=[i for i in range(1,d['n']+1) if a['owner'][i-1]>=0 and b['owner'][i-1]<0]
    flips=[i for i in quantity if (d['initial'][i]-a['Y'][i-1])*(d['initial'][i]-b['Y'][i-1])<0]
    net=[];old_net_delta=[]
    for k in range(len(d['Q'])):
        def total(p):return sum(d['initial'][i]-p['Y'][i-1] for i in range(1,d['n']+1) if p['owner'][i-1]==k)
        net.append(total(b)-total(a))
        old_net_delta.append(sum(a['Y'][i-1]-b['Y'][i-1] for i in range(1,d['n']+1) if a['owner'][i-1]==k))
    ra={r['vehicle']:r for r in a['routes']};rb={r['vehicle']:r for r in b['routes']};order=[]
    for k in range(len(d['Q'])):
        common=set(ra.get(k,{}).get('nodes',[]))&set(rb.get(k,{}).get('nodes',[]))-{0}
        x=[i for i in ra.get(k,{}).get('nodes',[]) if i in common];y=[i for i in rb.get(k,{}).get('nodes',[]) if i in common]
        if x!=y:order.append(k)
    return dict(quantity=quantity,old_served_owner_changes=owner,activation=activation,zero=zero,flip=flips,
        car_net_change=net,quantity_net_on_old_owner=old_net_delta,common_station_order_changed_cars=order)

def analyze(version='v1'):
    reports=[];events=[];refs={'R-X35-S-T2':.2996694007364017,'N-B35-S':.450291503262878}
    for role,label in [('R-X35-S-T2','core_rx_'+version),('N-B35-S','core_nb_'+version)]:
        d=read(OUT/'inputs'/role/'source.json')['data'];run=OUT/'runs'/label;summary=read(run/'summary.json')
        queue=read(run/'anchor_queue_0.json');initial=read(run/'initial.json');final=read(run/'final.json')
        seen=[];blocks=[];ports=[];statuses=Counter();nodes=0;num_events=0;build=solve=validation=0.;selected=None
        for block in sorted(run.glob('block_*'),key=lambda p:int(p.name.split('_')[1])):
            nb=read(block/'neighborhood.json');parent=read(block/'parent.json');blocks.append(tuple(sorted(nb['B'])))
            ports.extend((p['vehicle'],*p['arc']) for p in nb['ports'])
            branch=block/'positive';r=read(branch/'result.json');statuses[r['Status']]+=1;nodes+=r['NodeCount'];build+=r['build_seconds'];solve+=r['solve_outer_seconds'];validation+=r['validation_seconds']
            previous=parent
            for e in sorted(branch.glob('event_*.json'),key=lambda p:int(p.stem.split('_')[1])):
                event=read(e);checked=verify(d,event);exact,G=original(d,event['Y']);assert checked['original_T_feasible']
                assert abs(float(exact)-event['J'])<1e-12 and previous['J']-event['J']>1e-10
                diff=changes(d,previous,event);row=dict(role=role,block=block.name,event=e.name,path=e.relative_to(ROOT).as_posix(),
                    parent_path=(block/'parent.json').relative_to(ROOT).as_posix(),B=nb['B'],J=event['J'],J_exact=str(exact),
                    previous_J=previous['J'],gain=previous['J']-event['J'],block_parent_J=parent['J'],block_gain=parent['J']-event['J'],
                    changes=diff,physical=checked,routes=event['routes'])
                events.append(row);num_events+=1;previous=event
                # Select a large-gain event actually involving an old served owner.
                if diff['old_served_owner_changes'] and (selected is None or row['block_gain']>selected['block_gain']):selected=row
        trace=[json.loads(s) for s in (run/'trajectory.jsonl').read_text().splitlines()];seen=[r['anchor'] for r in trace]
        assert len(queue)==len(set(queue))==d['n'] and set(seen)==set(queue) and len(seen)==len(queue)
        final_check=verify(d,final);assert final_check['original_T_feasible'];assert final['J']<=initial['J']
        assert num_events==summary['accepted']
        reports.append(dict(role=role,initial_J=initial['J'],final_J=final['J'],gain=initial['J']-final['J'],
            historical_late_physical=refs[role],below_historical_late=final['J']<refs[role],
            summary=summary,accepted=num_events,anchor_count=len(seen),anchor_coverage=sorted(set(seen)),
            blocks=len(blocks),unique_blocks=len(set(blocks)),duplicate_block_ratio=1-len(set(blocks))/len(blocks),
            ports=len(ports),unique_ports=len(set(ports)),duplicate_port_ratio=1-len(set(ports))/len(ports) if ports else 0,
            native_statuses=dict(statuses),total_nodes=nodes,build_seconds=build,solve_outer_seconds=solve,
            validation_nested_seconds=validation,physical_final=final_check,selected_owner_event=selected))
    write(OUT/f'trajectory_analysis_{version}.json',dict(UTC=utc(),PASS=True,version=version,sources=reports,events=events,
        all_accepted_physical=True,full_anchor_round_not_all_blocks=True,global_proof_changes=0))
    print(json.dumps([{k:r[k] for k in ['role','initial_J','final_J','gain','accepted','blocks','unique_blocks','native_statuses','total_nodes']} for r in reports]),flush=True)

def control(role,label,version='v1'):
    analysis=read(OUT/f'trajectory_analysis_{version}.json');source=next(r for r in analysis['sources'] if r['role']==role)
    chosen=source['selected_owner_event'];assert chosen is not None
    parent=ROOT/chosen['parent_path'];folder=OUT/'inputs'/role;p=read(folder/'source.json')['panel'];target=OUT/'runs'/label
    command=[PE,folder/'instance.txt',p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],str(parent)+'.txt',target,1800,512,1,'owner-fixed',*chosen['B']]
    assert not target.exists();subprocess.run(list(map(str,command)),env=meter.environment(),check=True)
    actual=read(target/'final.json');nb=read(target/'block_0/neighborhood.json');original_nb=read(parent.parent/'neighborhood.json')
    assert nb==original_nb
    write(target/'contrast.json',dict(PASS=True,role=role,selected=chosen,same_parent_B_ports_and_capacity=True,
        control_J=actual['J'],joint_selected_J=chosen['J'],control_summary=read(target/'summary.json'),
        pure_old_served_owner_only=True,unvisited_activation_and_eligible_owners_open=True,
        scope='Only this fixed parent/block/ports; no global or historical-closure inference',
        restricted_lower_proof='Not claimed; raw Native bound is not transported here'))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])

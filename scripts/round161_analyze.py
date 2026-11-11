"""Saved evidence only: physical routes, fractions, whole-native tables and costs."""
from round161_common import *
from round161_qualify import rows,cols,matrix
from fractions import Fraction as F
import ast,re,csv

def instance(role):
    folder=OUT/'inputs'/role;source=read(folder/'source.json');p=source['panel'];text=(folder/'instance.txt').read_text()
    def vector(key):return ast.literal_eval(re.search(r'(?m)^\s*'+key+r'\s*=\s*(\[[^\n]*\])',text)[1])
    points=vector('points');weights=vector('weights')
    if abs(max(weights[1:])-10)<=1e-6:weights=[w/10 for w in weights]
    return dict(n=p['V'],Q=p['Q_vector'],T=p['T_seconds'],tp=p['pickup_seconds'],td=p['drop_seconds'],lam=p['lambda'],
        initial=vector('initial'),target=vector('target'),capacity=vector('capacities'),weights=weights,points=points)

def fleet(d,event):
    Y=list(d['initial']);seen=set();vehicles=set();owner=[None]*(d['n']+1);details=[]
    for r in event['routes']:
        k=r['vehicle'];assert k not in vehicles and 0<=k<len(d['Q']);vehicles.add(k)
        nodes=r['nodes'];assert nodes[0]==nodes[-1]==0
        ops={o['station']:o for o in r['operations']};assert len(ops)==len(nodes)-2==len(r['operations'])
        assert set(ops)==set(nodes[1:-1]);load=0;P=0;D=0;prefix=[]
        for i in nodes[1:-1]:
            assert 1<=i<=d['n'] and i not in seen;seen.add(i);owner[i]=k;o=ops[i];p=o['pickup'];v=o['drop']
            assert p==int(p)>=0 and v==int(v)>=0 and (p==0 or v==0)
            load+=p-v;P+=p;D+=v;assert 0<=load<=d['Q'][k];prefix.append(load)
            Y[i]+=v-p;assert 0<=Y[i]<=d['capacity'][i]
        travel=[]
        for i,j in zip(nodes,nodes[1:]):
            dx=d['points'][i][0]-d['points'][j][0];dy=d['points'][i][1]-d['points'][j][1]
            travel.append(math.sqrt(dx*dx+dy*dy)/1.5)
        assert P-D==load
        travel=math.fsum(travel);handling=d['tp']*P+d['td']*(D+load);duration=travel+handling
        assert duration<=d['T']+1e-8
        details.append(dict(vehicle=k,nodes=nodes,operations=r['operations'],prefix_load=prefix,pickups=P,drops=D,
            return_load=load,travel=travel,handling=handling,duration=duration))
    ratios=[F(1./d['target'][i])*Y[i] for i in range(1,d['n']+1)];S=sum(ratios,F(0))
    G=sum((abs(a-b) for i,a in enumerate(ratios) for b in ratios[i+1:]),F(0))/(d['n']*S) if S else F(0)
    penalty=sum((F(d['lam']*d['weights'][i])*abs(ratios[i-1]-1) for i in range(1,d['n']+1)),F(0));J=G+penalty
    assert abs(float(J)-event['objective'])<1e-10
    return dict(J=float(J),G=float(G),penalty=float(penalty),S=float(S),Y=Y,owner=owner,vehicles=details,original_T_feasible=True)

def lp_diagnostics(folder,d):
    v=read(folder/'lp_values.json');ad=read(folder/'admission.json');block=read(folder/'block.json')
    if not v:return dict(available=False)
    n=d['n'];G=v['G'];S=sum((1./d['target'][i])*v[f'Y_{i}'] for i in range(1,n+1))
    if block['RN']:
        t=v['rn_t'];res=[(1./d['target'][i])*v[f'rn_Y_{i}']-t*(1./d['target'][i])*v[f'Y_{i}'] for i in range(1,n+1)]
        return dict(available=True,G=G,S=S,t=t,t_lower=block['t_lower'],t_upper=block['t_upper'],
            residual_definition='rho_i - t*c_i*Y_i',residuals=res,max_absolute=max(map(abs,res)))
    res=[v[f'zprod_{i}']-G*v[f'Y_{i}'] for i in range(1,n+1)]
    return dict(available=True,G=G,S=S,residual_definition='zprod_i - G*Y_i',residuals=res,max_absolute=max(map(abs,res)))

def events(folder):
    out=[]
    for p in sorted((folder/'journal').glob('event_*.json'),key=lambda p:int(p.stem.split('_')[1])):
        event=read(p);receipt=p.with_suffix('.commit').read_text().split();assert receipt[0]=='NEJ1'
        assert int(receipt[3])==p.stat().st_size and receipt[4]==sha(p)
        event['outer_observation_seconds']=float(receipt[2]);out.append(event)
    return out

def label_for(role,form,mode):
    return f'{role}_RNP_{mode}_v2' if form=='RN-P' else f'{role}_{form}_{mode}_v1'

def analyze():
    output=[];fleets=[];diagnostics=[];audits=[];identities=[];changes=[]
    for role in ('R-X35-S-T2','N-B35-S'):
        d=instance(role)
        for mode in ('LP','MIP'):
            original_old=None
            forms=['OLD','RN']+(['RN-P'] if (OUT/'runs'/label_for(role,'RN-P',mode)/'outcome.json').exists() else [])
            for form in forms:
                label=label_for(role,form,mode);folder=OUT/'runs'/label
                value=read(folder/'outcome.json');e=events(folder);ad=read(folder/'admission.json')
                call=next(x for x in e if x['kind']=='call');parameters=read(folder/'native.log.round161_parameters.json')
                assert call['model_sha256']==sha(folder/'model.lp')
                identities.append(dict(label=label,actual_LP_SHA=sha(folder/'model.lp'),actual_MPS_SHA=sha(folder/'model.mps'),
                    actual_domain_SHA=sha(folder/'actual_columns.jsonl'),actual_rows_SHA=sha(folder/'actual_rows.jsonl'),
                    original_LP_SHA=sha(folder/'original.lp'),scope=call,launch_SHA=sha(OUT/'launches'/f'{label}.json')))
                assert call['native_preconditions']==1 and not call['precondition_reason']
                assert call['settings']['MIPFocus']==0 and call['settings']['Threads']==1 and call['settings']['Seed']==0
                assert value['model_matches'] and value['zero_gaps'] and value['feasibility_gate']
                assert value['bound_available'] and value['proof_usable'] and not value['source_rejected']
                assert parameters['NodeLimit']==(4096 if mode=='MIP' else 1e100)
                assert call['upper_g']==ad['gamma_U'] and call['cutoff']==ad['cutoff'] and call['lower_g']==0
                current=rows(folder,'original')
                if form=='OLD':original_old=(current,cols(folder,'original'),ad)
                else:
                    assert current==original_old[0] and cols(folder,'original')==original_old[1]
                    assert ad['parent_J']==original_old[2]['parent_J'] and ad['gamma_U']==original_old[2]['gamma_U']
                    audits.append(dict(label=label,**matrix(folder)))
                raw=[x for x in e if x['kind']=='bound'];raw_final=raw[-1]['native_bound'] if raw else None
                assert raw_final is not None
                lower=min(raw_final,ad['cutoff']);assert abs(lower-value['qualified_lower'])<1e-9
                trajectory=[];first=None
                for x in e:
                    if x['kind']!='witness':continue
                    checked=fleet(d,x);fleets.append(dict(label=label,event=x['sequence'],outer_seconds=x['outer_observation_seconds'],**checked))
                    if x['source']=='native_MIPSOL_verified_original_routes' and first is None:first=x['outer_observation_seconds']
                    if x.get('improving'):trajectory.append(dict(time=x['outer_observation_seconds'],J=checked['J'],event=x['sequence']))
                U=min(x['J'] for x in fleets if x['label']==label);assert abs(U-value['physical_U'])<1e-9
                if mode=='MIP':
                    fs=[x for x in fleets if x['label']==label];parent=fs[0];best=min(fs,key=lambda x:x['J'])
                    changed=[i for i in range(1,d['n']+1) if parent['Y'][i]!=best['Y'][i]]
                    activated=[i for i in range(1,d['n']+1) if parent['owner'][i] is None and best['owner'][i] is not None]
                    removed=[i for i in range(1,d['n']+1) if parent['owner'][i] is not None and best['owner'][i] is None]
                    owners=[i for i in range(1,d['n']+1) if parent['owner'][i] is not None and best['owner'][i] is not None and parent['owner'][i]!=best['owner'][i]]
                    changes.append(dict(label=label,parent_J=parent['J'],best_J=best['J'],Y_changed=changed,activated=activated,deactivated=removed,owner_changed=owners,
                        interpretation='Original J depends only on Y; routes/owners/orders supply the verified physical implementation. Endpoint changes do not isolate Native search causality.'))
                fee=read(OUT/'fees'/label/'receipt.json');gap=U-lower
                output.append(dict(role=role,formulation=form,mode=mode,physical_U=U,raw_lower=raw_final,
                    qualified_lower=lower,global_transported_floor=lower,absolute_gap=gap,relative_gap=gap/U,
                    T_outer=fee['outer_seconds'],T_cpp=value['outer_seconds'],Native_Runtime=value['runtime'],Work=value['work'],nodes=value['nodes'],
                    T_build_convert_Start_and_registry=ad['build_seconds'],
                    T_other_environment_read_Start_return=fee['outer_seconds']-ad['build_seconds']-value['runtime'],
                    root_gap=(ad['parent_J']-lower)/ad['parent_J'] if mode=='LP' else None,
                    status=value['status'],censored=value['status']=='TIME_LIMIT',first_native_verified_U_seconds=first,
                    best_verified_U_seconds=trajectory[-1]['time'],T_cert=None,certified=False,
                    rows=value['rows'],columns=value['cols'],nonzeros=value['nonzeros'],binaries=value['binaries'],integers=value['integers'],continuous=value['continuous'],
                    presolved_rows=value['presolved_rows'],presolved_columns=value['presolved_cols'],presolved_nonzeros=value['presolved_nonzeros'],
                    min_coefficient=value['min_coefficient'],max_coefficient=value['max_coefficient'],trajectory=trajectory))
                if mode=='LP':diagnostics.append(dict(role=role,formulation=form,**lp_diagnostics(folder,d)))
    pairs=[]
    for role in ('R-X35-S-T2','N-B35-S'):
        for mode in ('LP','MIP'):
            old=next(x for x in output if x['role']==role and x['mode']==mode and x['formulation']=='OLD')
            for candidate in ('RN','RN-P'):
                candidates=[x for x in output if x['role']==role and x['mode']==mode and x['formulation']==candidate]
                if not candidates:continue
                rn=candidates[0]
                pairs.append(dict(role=role,mode=mode,candidate=candidate,OLD_U=old['physical_U'],RN_U=rn['physical_U'],
                    OLD_L=old['qualified_lower'],RN_L=rn['qualified_lower'],U_gain=old['physical_U']-rn['physical_U'],L_gain=rn['qualified_lower']-old['qualified_lower'],
                    OLD_Work=old['Work'],RN_Work=rn['Work'],OLD_nodes=old['nodes'],RN_nodes=rn['nodes'],
                    OLD_outer=old['T_outer'],RN_outer=rn['T_outer'],OLD_status=old['status'],RN_status=rn['status'],
                    same_PE=candidate=='RN',reused_paid_OLD_control=candidate=='RN-P'))
    write(OUT/'reports/bridge.json',dict(samples=output,pairs=pairs));write(OUT/'reports/fleets.json',fleets)
    write(OUT/'reports/LP_product_diagnostics.json',diagnostics);write(OUT/'reports/matrix_audits.json',dict(PASS=True,audits=audits))
    write(OUT/'reports/model_identities.json',identities);write(OUT/'reports/physical_changes.json',changes)
    flat=[{k:v for k,v in x.items() if k!='trajectory'} for x in output]
    with (OUT/'reports/bridge.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    print(json.dumps(pairs,indent=2))

if __name__=='__main__':analyze()

"""Pure aggregation of every fixed position; caps never become certificate times."""
from round134_common import *
import collections,csv,copy
import round108_reader as core

def csv_write(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader()
        writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows)

def gather(stage):
    manifest=read(OUT/f'{stage}_matrix_frozen.json');rows=[];missing=[];operations=[]
    for group in manifest['groups']:
        launch=group['launch'];d=Path(launch['destination']);endpoint=d/'round134_endpoint.json'
        if not (d/'verification_closeout.json').exists() or not endpoint.exists():
            missing.append(group['position']);continue
        e=read(endpoint);a=read(d/'audit.json');p=launch['panel'];physical=a['physical']
        result=read(d/'result.json');data=core.evidence.instance(ROOT,p);omega=math.fsum(data['w'][1:])
        assert e['certificate']==result['strict_certified_original_problem']
        assert e['formal_protocol_qualified'] and e['implementation_qualified']
        if e['certificate']:assert e['certificate_qualified'] and e['T_cert']==e['T_produce'] and e['performance_eligible']
        else:assert e['T_cert'] is None
        row=dict(stage=stage,position=group['position'],role=launch['id'],method=launch['method'],seed=launch['seed'],repeat=launch['repeat'],
            cap=p['cap_seconds'],lambda_value=p['lambda'],Omega=omega,rho=p['lambda']*omega,
            certificate=e['certificate'],certificate_basis=e.get('certificate_basis',
                'qualified_paid_start_original_compact_native_certificate' if e['certificate'] else 'qualified_paid_start_original_compact_open'),native_proof_qualified=e['native_proof_qualified'],
            independent_proof=e.get('independent_proof',False),source_rejected=bool(a['source_rejections']),
            performance_eligible=e['performance_eligible'],
            U=e['U'],L=e['L'],signed_gap=e['U']-e['L'],G=physical['G'],P=physical['P'],P_avg=physical['P']/omega,F=physical['F'],
            T_produce=e['T_produce'],T_cert=e['T_cert'],T_verify=e['T_verify'],T_total=e['T_total'],
            native_Optimize=e['native_Optimize'],LP=result.get('external_gini_tree_lp_optimize_count',0),
            target_MIP=result.get('external_gini_tree_partial_mip_optimize_count',0),terminal_MIP=result.get('external_gini_tree_terminal_mip_optimize_count',0),
            splits=result.get('external_gini_tree_split_count'),cache=result.get('external_gini_tree_in_memory_model_reuse_count'),
            input_SHA=e['input_SHA'],PE_SHA=e['PE_SHA'],arm_id=e['arm_id'],destination=str(d))
        led=d/'external/paper_optimize_ledger.csv'
        native=core.rows(led) if led.exists() else []
        row['Work']=sum(float(x['work']) for x in native) if native else result.get('gurobi_work')
        row['nodes']=sum(float(x['nodes']) for x in native) if native else result.get('gurobi_node_count')
        rows.append(row)
        routefacts=[]
        for route in physical['routes']:
            pickup=drop=load=peak=0
            by_station={op['station']:op for op in route['operations']}
            for station in route['nodes'][1:-1]:
                op=by_station[station]
                pickup+=op['pickup'];drop+=op['drop'];load+=op['pickup']-op['drop'];peak=max(peak,load)
            travel=sum(math.hypot(data['xy'][a][0]-data['xy'][b][0],data['xy'][a][1]-data['xy'][b][1])/1.5
                for a,b in zip(route['nodes'],route['nodes'][1:]))
            handling=pickup*(p['pickup_seconds']+p['drop_seconds'])
            routefacts.append(dict(vehicle=route['vehicle'],Q=p['Q_vector'][route['vehicle']],nodes=route['nodes'],
                pickups=pickup,drops=drop,return_load=load,peak_prefix_load=peak,
                travel_seconds=travel,handling_seconds=handling,duration_seconds=travel+handling))
        assert sum(physical['Y'][1:])+sum(r['return_load'] for r in routefacts)==sum(data['b'][1:])
        assert all(r['peak_prefix_load']<=r['Q'] for r in routefacts)
        y=physical['Y'];targets=data['D']
        operations.append(dict(stage=stage,position=group['position'],role=launch['id'],method=launch['method'],seed=launch['seed'],repeat=launch['repeat'],lambda_value=p['lambda'],
            station_inventory=y[1:],total_inventory=sum(y[1:]),total_initial=sum(data['b'][1:]),total_target=sum(targets[1:]),
            target_under=sum(y[i]<targets[i] for i in range(1,p['V']+1)),target_equal=sum(y[i]==targets[i] for i in range(1,p['V']+1)),
            target_over=sum(y[i]>targets[i] for i in range(1,p['V']+1)),
            pickups=sum(r['pickups'] for r in routefacts),drops=sum(r['drops'] for r in routefacts),returns=sum(r['return_load'] for r in routefacts),
            maximum_duration=physical['maximum_duration'],T=p['T_seconds'],routes=routefacts))
    write(OUT/f'reports/{stage}/arms.json',rows);csv_write(OUT/f'reports/{stage}/arms.csv',rows)
    write(OUT/f'reports/{stage}/operations.json',operations)
    write(OUT/f'reports/{stage}/completion.json',dict(expected=len(manifest['groups']),completed=len(rows),missing=missing,
        certification_counts=dict(collections.Counter(r['method'] for r in rows if r['certificate'])),
        full_production_caps_not_imputed=True))
    return rows,missing,operations

def pair(left,right):
    assert left['role']==right['role'] and left['seed']==right['seed'] and left['repeat']==right['repeat'] and left['cap']==right['cap']
    result=dict(role=left['role'],seed=left['seed'],repeat=left['repeat'],left=left['method'],right=right['method'],
        left_U=left['U'],left_L=left['L'],right_U=right['U'],right_L=right['L'],left_T_cert=left['T_cert'],right_T_cert=right['T_cert'],cap=left['cap'])
    a,b=left['certificate'],right['certificate']
    if not left['performance_eligible'] or not right['performance_eligible']:
        result.update(**{'class':'UNEVALUABLE'},direction='UNEVALUABLE',material=None,micro=left['role']=='SM-B10-B')
        return result
    result['class']='BOTH_CERTIFIED' if a and b else 'LEFT_ONLY_CERTIFIED' if a else 'RIGHT_ONLY_CERTIFIED' if b else 'BOTH_OPEN'
    if a and b:
        delta=left['T_cert']-right['T_cert'];fast=min(left['T_cert'],right['T_cert'])
        result.update(direction='Win' if delta<0 else 'Lose' if delta>0 else 'Tie',
            left_minus_right_seconds=delta,right_over_left_ratio=right['T_cert']/left['T_cert'],
            material=abs(delta)>=max(10.,.1*fast),micro=left['role']=='SM-B10-B')
    else:result.update(direction='Win' if a else 'Lose' if b else 'UNDETERMINED',material=None,micro=False)
    return result

def sensitivity(C,D):
    points=[r for r in C if r['role'] in ('K-15-S','UC-B20-B') and r['seed']==0 and r['method']=='S2']+D
    points=sorted(points,key=lambda r:(r['role'],r['lambda_value']))
    pairs=[]
    for role in ('K-15-S','UC-B20-B'):
        rr=[r for r in points if r['role']==role]
        if len(rr)!=3:continue
        assert [r['lambda_value'] for r in rr]==[.075,.15,.30]
        assert len({r['input_SHA'] for r in rr})==1 and len({r['Omega'] for r in rr})==1
        for a,b in zip(rr,rr[1:]):
            # These are accepted engineering original-objective bounds. No
            # primal tolerance is added or treated as an objective-error bound.
            ea=max(0,a['U']-a['L']);eb=max(0,b['U']-b['L'])
            dp=a['P_avg']-b['P_avg'];dg=b['G']-a['G'];ra,rb=a['rho'],b['rho']
            pairs.append(dict(role=role,lambda_a=a['lambda_value'],lambda_b=b['lambda_value'],delta_Pavg=dp,delta_G=dg,
                epsilon_a=ea,epsilon_b=eb,delta_G_lower=ra*dp-ea,delta_G_upper=rb*dp+eb,
                delta_Pavg_lower=-(ea+eb)/(rb-ra),both_certified=a['certificate'] and b['certificate'],
                conditional_on_accepted_original_objective_bound_policy=True,primal_tolerance_used_as_error=False,
                lower_inequality_residual=dg-(ra*dp-ea),upper_inequality_residual=(rb*dp+eb)-dg))
    write(OUT/'reports/D/six_points.json',points);csv_write(OUT/'reports/D/six_points.csv',points)
    write(OUT/'reports/D/tradeoff_relations.json',dict(points=len(points),adjacent_pairs=pairs,
        numerical_native_policy_is_not_rational_optimality_proof=True))
    return points,pairs

def roots():
    path=OUT/'math/root_plan.json'
    if not path.exists():return []
    result=[]
    for root in read(path)['roots']:
        role=root['role'];folder=OUT/'math/roots'/role
        if not all((folder/f'layer{k}/result.json').exists() for k in range(3)):continue
        rr=[read(folder/f'layer{k}/result.json') for k in range(3)];scope=read(folder/'scope.json')
        L=[r['numerical_lower'] for r in rr];U=scope['archived_best_physical']['F'];origin='archived R132 own physically verified best fleet'
        C=OUT/'reports/C/arms.json'
        if C.exists():
            own=[r for r in read(C) if r['role']==role and r['method']=='S2' and r['seed']==0]
            if own:U=own[0]['U'];origin='current final-version C S2 Seed0'
        result.append(dict(role=role,L0=L[0],L_old=L[1],L_old_TC=L[2],U=U,U_source=origin,
            cutoff=scope['root_scope']['cutoff'],g_interval=[scope['root_scope']['lower_g'],scope['root_scope']['upper_g']],
            old_increment=None if None in L[:2] else L[1]-L[0],TC_increment=None if None in L[1:] else L[2]-L[1],
            gap_after=None if L[2] is None else U-min(L[2],scope['root_scope']['cutoff']),
            statuses=[r['qualification'] for r in rr],construct_seconds=[r['construct_and_load_seconds'] for r in rr],
            solve_seconds=[r['solver_runtime'] for r in rr],sizes=[r['after'] for r in rr],
            quality=[r['quality'] for r in rr],strict_rational_gain_claim=False))
    write(OUT/'reports/roots.json',result);csv_write(OUT/'reports/roots.csv',result)
    return result

def main():
    C,cmissing,opsC=gather('C');D,dmissing,opsD=gather('D');groups=collections.defaultdict(dict)
    for row in C:groups[row['role'],row['seed'],row['repeat']][row['method']]=row
    pairs=[]
    for key,methods in groups.items():
        for baseline in ('P','PS'):
            if baseline in methods and 'S2' in methods:pairs.append(pair(methods['S2'],methods[baseline]))
    csv_write(OUT/'reports/C/pairs.csv',pairs);write(OUT/'reports/C/pairs.json',pairs)
    points,relations=sensitivity(C,D);root=roots()
    summary=dict(UTC=utc(),C_completed=len(C),C_missing=cmissing,D_completed=len(D),D_missing=dmissing,
        distinct_C_inputs=len({r['role'] for r in C}),C_certificates={m:sum(r['certificate'] for r in C if r['method']==m) for m in ('P','PS','S2')},
        C_denominators={m:sum(r['method']==m for r in C) for m in ('P','PS','S2')},
        pair_count=len(pairs),pair_classes=dict(collections.Counter(p['class'] for p in pairs)),
        pair_directions=dict(collections.Counter(p['direction'] for p in pairs)),
        substantive_certified_pairs=[p for p in pairs if p['material'] and not p['micro']],
        independent_certificate_count=sum(r['independent_proof'] for r in C),
        rejected_native_independent_certificates=[r['arm_id'] for r in C if r['source_rejected'] and r['independent_proof']],
        total_qualifications=len(C)+len(D),D_points=len(points),roots_completed=len(root),
        budget=budget(),not_holdout=True,historical_denominators_unchanged=True)
    write(OUT/'reports/summary.json',summary)
    print(json.dumps({k:summary[k] for k in ('C_completed','C_missing','D_completed','D_missing','C_certificates','C_denominators','roots_completed')}))
if __name__=='__main__':main()

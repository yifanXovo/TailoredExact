"""Pure finite summaries; distinguish saved-point cuts, new LP gains and full runs."""
from round138_common import *
import csv,collections,gzip
import round108_reader as core

def csv_write(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)

def LP():
    plan=read(OUT/'roots/plan.json');rows=[];checks=[];cache={}
    for a in plan['positions']:
        folder=OUT/'roots'/a['role'];target=folder/a['variant'];r=read(target/'result.json')
        assert r['source_plan_SHA']==sha(OUT/'roots/plan.json') and r['LP_Optimize']==1 and r['MIP_Optimize']==0
        assert r['params']['Seed']==0 and r['params']['Threads']==1
        assert r['quality']['ConstrVio']<=1e-6 and r['quality']['BoundVio']<=1e-6 and r['quality']['DualVio']<=1e-6
        modelpath=ROOT/read(folder/'additions.json')['stock_model'] if a['variant'] in ['stock','tc_stock'] else folder/'inherited/original.lp'
        assert sha(modelpath)==r['model_SHA']
        if str(modelpath) not in cache:cache[str(modelpath)]=core.lp_model(modelpath)
        model=cache[str(modelpath)];vector=json.loads(gzip.decompress((target/'solution.json.gz').read_bytes()))
        assert sha(target/'solution.json.gz')==r['solution_SHA']
        violation=0.
        for terms,sense,rhs in model['rows']:
            residual=math.fsum(c*vector[n] for n,c in terms)-rhs
            violation=max(violation,abs(residual) if sense=='=' else residual if sense=='<=' else -residual)
        assert violation<=1e-6,(a['role'],a['variant'],violation)
        fresh=read(folder/'base/result.json')['L'];scope=read(folder/'scope.json')
        assert abs(fresh-scope['L_saved'])<=1e-7
        row={k:r[k] for k in ['position','role','variant','L','G_aux','J','tau','S','runtime','Work','iterations']}
        row.update(delta_new_base=r['L']-fresh,delta_saved=r['delta_saved'],validated_U=scope['validated_U'],
            signed_gap=scope['validated_U']-r['L'],relative_gap=r['relative_gap'],new_rows=r['after']['rows']-len(core.lp_model(folder/'inherited/original.lp')['rows']),
            new_columns=r['after']['columns']-len(core.lp_model(folder/'inherited/original.lp')['order']))
        rows.append(row);checks.append(dict(position=a['position'],max_original_matrix_violation=violation,
            additions_SHA=sha(folder/'additions.json'),solver_script_SHA=sha(ROOT/'scripts/round138_lp.py'),
            result_SHA=sha(target/'result.json'),plan_SHA=sha(OUT/'roots/plan.json')))
    csv_write(OUT/'reports/LP.csv',rows)
    write(OUT/'reports/LP.json',dict(UTC=utc(),rows=rows,pure_checks=checks,Optimize=0,
        LP_optima_are_floating_point_not_rational_certificates=True,
        postsolve_additional_hash_binding=True,original_plan_registered_before_Optimize=True))
    print('20 LP summaries and solution/original-matrix replay checks pass')

def full():
    import inspect,types,round137_analyze as accepted
    ns=dict(vars(accepted),ROOT=ROOT,OUT=OUT)
    gather=types.FunctionType(accepted.gather.__code__,ns)
    matrix=read(OUT/'matrix_frozen.json');arms=[];missing=[]
    for stage in dict.fromkeys(g['stage'] for g in matrix['groups']):
        values,absent,ops=gather(stage);arms+=values;missing+=absent
    csv_write(OUT/'reports/new_arms.csv',arms)
    reused=read(OUT/'baseline_reuse.json')['baselines'];pairs=[]
    for b in reused:
        role=b['role'];match=[a for a in arms if a['role']==role and a['method']=='STOCK' and a['seed']==0]
        if not match:continue
        a=match[0];old=b['baseline']
        baseline={k:(float(old[k]) if old[k] else None) for k in ['U','L','T_produce','T_cert','G','P_avg','S','relative_gap']}
        baseline['certificate']=old['certificate']=='True'
        pair=dict(role=role,seed=0,baseline_origin='R137 frozen matching complete run',
            baseline_position=b['position'],candidate_position=a['position'],
            base_certificate=baseline['certificate'],stock_certificate=a['certificate'],
            base_U=baseline['U'],stock_U=a['U'],delta_U=a['U']-baseline['U'],
            base_L=baseline['L'],stock_L=a['L'],delta_L=a['L']-baseline['L'],
            base_signed_gap=baseline['U']-baseline['L'],stock_signed_gap=a['U']-a['L'],
            base_relative_gap=baseline['relative_gap'],stock_relative_gap=a['relative_gap'],
            base_T_cert=baseline['T_cert'],stock_T_cert=a['T_cert'],
            base_T_produce=baseline['T_produce'],stock_T_produce=a['T_produce'],
            base_G=baseline['G'],stock_G=a['G'],base_P_avg=baseline['P_avg'],stock_P_avg=a['P_avg'],
            base_S=baseline['S'],stock_S=a['S'])
        if baseline['certificate'] and a['certificate']:
            diff=abs(a['T_cert']-baseline['T_cert']);threshold=max(10.,.1*min(a['T_cert'],baseline['T_cert']))
            pair.update(substantive_certificate_time_difference=diff>=threshold,time_difference_seconds=a['T_cert']-baseline['T_cert'],time_threshold=threshold)
        pairs.append(pair)
    csv_write(OUT/'reports/pairs.csv',pairs)
    write(OUT/'reports/full.json',dict(UTC=utc(),new_arms=arms,core_pairs=pairs,missing_new_positions=missing,
        complete=not missing,baseline_reuse_positions=8,budget=budget(),Optimize=0))
    print(json.dumps(dict(completed=len(arms),missing=missing,pairs=len(pairs)),ensure_ascii=False))

if __name__=='__main__':globals()[sys.argv[1]]()

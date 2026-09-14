"""Independent original-route, budget and submitted numerical projection audit; no optimizer."""
import ast, csv, json, math, shutil, re
from decimal import Decimal, localcontext
from pathlib import Path
import verify_round64 as prior
import round65_research as run
from types import SimpleNamespace
ROOT,OUT,RAW=run.ROOT,run.OUT,run.RAW
prior.run=run
prior.physical_module.ROOT=ROOT
def rows(p):
    # The retained v2 micro exposed MinGW append tellp()==0 on a nonempty file.
    # Skip only exact repeated header records; source fixed before production.
    return [r for r in csv.DictReader(p.open(encoding='utf-8-sig',newline='')) if not all(k==v for k,v in r.items())] if p.exists() else []
def table(name,records):
    if not records:return
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in records for k in r)));w.writeheader();w.writerows(records)
def main():
    records=[];runs=[];proofs=[];prefix=[];costs=[];lifecycle=[];coverage=[]
    physical_panel=run.panel()
    prior.run=SimpleNamespace(panel=lambda:physical_panel,sha=run.sha)
    for e in run.runner.entries():
        if not e['charged']:continue
        folder=ROOT/e['destination'];completion=folder/'completion.json'
        if not completion.exists():continue
        done=run.read(completion);p=run.panel().get(e['id'])
        if not p:
            cmd=e['command']; arg=lambda n:cmd[cmd.index(n)+1]
            p=dict(instance_path=arg('--input'),T_seconds=arg('--T'),pickup_seconds=arg('--pickup-time'),drop_seconds=arg('--drop-time'),**{'lambda':arg('--lambda')})
            p['input_sha256']=run.sha(ROOT/p['instance_path'])
        physical_panel[e['id']]=p
        result_path=folder/'result.json'
        if not result_path.exists():
            runs.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],failure=True,wall=done['wall_seconds']));continue
        r=run.read(result_path)
        for path in [result_path,*folder.glob('**/*witness.json')]:
            witness=run.read(path)
            if 'routes' not in witness:continue
            checked=prior.physical_module.physical(p,witness);assert checked['original_T_feasible']
            records.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],path=str(path.relative_to(ROOT)),**checked))
            dest=OUT/'witnesses'/str(e['charged_number'])/path.relative_to(folder)
            dest.parent.mkdir(parents=True,exist_ok=True)
            run.write(dest,{k:witness[k] for k in ['objective','routes','verification'] if k in witness})
        calls=rows(folder/'external/paper_optimize_ledger.csv');budget=rows(folder/'external/optional_budget.csv')
        ow=cw=os=cs=0
        command=e['command'];arg=lambda n,default:command[command.index(n)+1] if n in command else default
        seed=float(arg('--round65-seed-credit',30));call_cap=30 if arg('--round65-controller','credit10')=='credit-seed' else 10
        for b in budget:
            optional=b['kind']=='optional';w=float(b['work']);t=float(b['seconds']);assert w>=0 and t>=0
            if optional:
                assert float(b['grant_work'])<=max(0,min(call_cap,seed+.1*cw-ow))+1e-6
                assert float(b['grant_seconds'])<=max(0,min(15,seed+.1*cs-os))+1e-6
            if optional:ow+=w;os+=t
            else:cw+=w;cs+=t
            for actual,expected in [(ow,b['optional_work']),(cw,b['core_work']),(os,b['optional_seconds']),(cs,b['core_seconds'])]:
                assert abs(actual-float(expected))<1e-6
            costs.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**b))
        proj=folder/'external/projection';aux=rows(proj/'calls.csv');proof=rows(proj/'proof_calls.csv');uses=rows(proj/'row_use.csv')
        for item in rows(proj/'main_shapes.csv'):
            if item['mode']=='proof':assert int(item['attached'])==0
            lifecycle.append(dict(number=e['charged_number'],id=e['id'],arm=e['arm'],**item))
        for call in calls:
            if call['solve_kind']=='LP':assert call['integer_domain_restored']=='1'
        if calls:assert r['external_gini_tree_backend_parameter_roundtrip_valid']
        phases=rows(folder/'phases.csv');phase=lambda name:next((float(x['process_seconds']) for x in phases if x['event']==name),None)
        leaves=rows(folder/'external/paper_leaf_ledger.csv')
        for event in rows(folder/'external/paper_tree_events.csv'):
            if event['event']=='optional_unknown_parent_retained':
                parent=next(l for l in leaves if l['leaf_id']==event['leaf_id'])
                assert parent['status']!='replaced'
                assert any(c['leaf_id']==event['leaf_id'] and c['solve_kind']!='LP' for c in calls) or done['wall_seconds']>=e['cap_seconds']-4
                coverage.append(dict(number=e['charged_number'],id=e['id'],leaf=event['leaf_id'],event='unknown_parent_retained',core_observed=any(c['leaf_id']==event['leaf_id'] and c['solve_kind']!='LP' for c in calls)))
        for call in calls:
            if call['solve_kind']=='LP' and call['native_status'] not in ['OPTIMAL','INFEASIBLE']:
                later=calls[calls.index(call)+1:]
                assert not any(c['leaf_id']==call['leaf_id'] and c['solve_kind']=='LP' for c in later)
                coverage.append(dict(number=e['charged_number'],id=e['id'],leaf=call['leaf_id'],event='incomplete_LP_no_repeat',core_observed=any(c['solve_kind']!='LP' for c in later)))
        result=dict(number=e['charged_number'],id=e['id'],arm=e['arm'],stage=e['stage'],cap=e['cap_seconds'],
            build=e['build_freeze'],executable_sha256=e['executable_sha256'],wall=done['wall_seconds'],status=r['status'],
            certificate=r.get('strict_certified_original_problem',False),
            UB=r.get('upper_bound',r['objective']),LB=r.get('lower_bound'),
            native_calls=len(calls) if calls else (1 if e['arm']=='P-GRB' else 0),
            mip_calls=sum(c['solve_kind']!='LP' for c in calls),aux_calls=len(aux),
            proof_calls=sum(c['status']=='launch' for c in proof),optional_work=ow,core_work=cw,optional_seconds=os,core_seconds=cs,
            splits=r.get('external_gini_tree_split_count'),failure=done['returncode']!=0 or 'failed' in r['status'])
        result.update(initial_UB=r.get('initial_upper_bound'),hga_seconds=r.get('incumbent_generation_time_seconds'),
                      first_LP_request=phase('first_lp_optimize_launch'),
                      proof_failure=(proj/'failures.txt').exists(),
                      startup_witness_present=(folder/'external/initial_witness.json').exists(),
                      witness_audit_failure=any('witness audit persistence failed' in n for n in r.get('notes',[])))
        result.update(controller=arg('--round65-controller','credit10'),release_load=arg('--round65-release-load','false'))
        initial=folder/'external/initial_witness.json'
        if initial.exists():result['initial_UB']=run.read(initial)['objective']
        else:
            decomposition=rows(folder/'external/initial_decomposition_ledger.csv')
            if decomposition:result['initial_UB']=float(decomposition[0]['U_proof_launch'])
        result['gap']=result['UB']-result['LB'] if result['LB'] is not None else None
        result['optimizer_calls']=result['native_calls']+result['aux_calls']+result['proof_calls']
        runs.append(result)
        if (proj/'physical.json').exists():
            data=run.read(proj/'physical.json');text=(ROOT/p['instance_path']).read_text(encoding='utf-8');header=text.splitlines()[0]
            capacities=ast.literal_eval(header[header.index('['):]);prior.check_resource_physics(e['id'],data,capacities)
            matrix=prior.resource_matrix(data,capacities)
            station_cap=ast.literal_eval(next(t.split('=',1)[1] for t in text.splitlines() if t.startswith('capacities')))
            for path in proj.glob('row_*.json'):
                row=run.read(path);assert row['scope']=='physical_global' and row['identity']==data['identity']
                with localcontext() as ctx:
                    ctx.prec=80;D=Decimal.from_float;z={};v={}
                    for name,y in row['multipliers'].items():
                        eq,a,b=matrix[name];assert eq=='1' or y>=0
                        # Each multiplier must belong to exactly the declared vehicle block.
                        assert all(int(n.split('_')[1])==row['vehicle'] for n in [*a,*b])
                        for n,c in a.items():z[n]=z.get(n,Decimal(0))+D(y)*D(c)
                        for n,c in b.items():v[n]=v.get(n,Decimal(0))+D(y)*D(c)
                    beta=Decimal(0)
                    for n,a in z.items():
                        family,k,i,j=n.split('_');k,i,j=int(k),int(i),int(j)
                        u=capacities[k] if family=='q' else data['upper'][i][j]
                        beta+=min(Decimal(0),a*D(float(u)))
                    corrected=beta
                    for n,a in v.items():
                        stored=D(row['coefficients'].get(n,0.));assert abs(stored-a)<Decimal('1e-10')
                        parts=n.split('_');family,k,i=parts[:3];k,i=int(k),int(i)
                        u=1 if family=='x' else capacities[k] if family=='load' else station_cap[i]
                        corrected+=min(Decimal(0),(stored-a)*D(float(u)))
                    assert D(row['rhs'])<=corrected+Decimal('1e-40'),(path,row['rhs'],corrected)
                activity=math.fsum(c*row['point'][n] for n,c in row['coefficients'].items())
                assert abs(activity-row['activity'])<1e-8 and row['rhs']-activity>1e-7
                proofs.append(dict(number=e['charged_number'],id=e['id'],vehicle=row['vehicle'],signature=row['signature'],support=len(row['coefficients']),violation=row['violation'],finite_bound_and_rounding_verified=True))
                target=OUT/'projection_evidence'/str(e['charged_number']);target.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(path,target/path.name);shutil.copyfile(proj/'physical.json',target/'physical.json')
                if (proj/'representation.json').exists():shutil.copyfile(proj/'representation.json',target/'representation.json')
            known={run.read(p)['signature'] for p in proj.glob('row_*.json')}
            assert all(u['signature'] in known for u in uses)
    for identity in ['C5','C7','C2']:
        base=RAW/'reliability_v1'/identity/'off';on=RAW/'reliability_v1'/identity/'reliable'
        if not (on/'completion.json').exists():continue
        a=rows(base/'hga.csv');b=rows(on/'hga.csv');keys=['generation','best_fitness','strict_improvement']
        assert a and b
        count=min(len(a),len(b));assert all(all(x[k]==y[k] for k in keys) for x,y in zip(a,b))
        prefix.append(dict(id=identity,baseline_generations=len(a)-1,candidate_generations=len(b)-1,matched_prefix=count,
                           final_fitness_equal=a[-1]['best_fitness']==b[-1]['best_fitness']))
    table('runs.csv',runs);table('witness_verification.csv',records);table('projection_verification.csv',proofs);table('hga_prefix_verification.csv',prefix)
    table('optional_call_costs.csv',costs);table('main_model_lifecycle.csv',lifecycle);table('unknown_coverage_checks.csv',coverage)
    print('runs',len(runs),'witnesses',len(records),'projection rows',len(proofs),'HGA pairs',len(prefix))
if __name__=='__main__':main()

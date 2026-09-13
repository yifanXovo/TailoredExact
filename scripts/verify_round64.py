"""Solver-free independent physical, LP-residual and identity checks."""
import argparse
import ast
import csv
import json
import math
import re
import shutil
from decimal import Decimal, localcontext
from pathlib import Path
from verify_round62 import check_lp_point
import analyze_round61 as physical_module
import round64_research as run
run.bind()
ROOT,OUT,RAW=run.ROOT,run.OUT,run.RAW
physical_module.ROOT=ROOT
def rows(path):return list(csv.DictReader(Path(path).open(encoding='utf-8-sig',newline='')))
def point(path):return {p['variable']:float(p['value']) for p in rows(path)}
def table(name,records):
    if not records:return
    fields=list(dict.fromkeys(k for r in records for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
def preflight():
    checks=[]
    historic={'D3':'66d0428e14ffd3e31764d324d6cd00d23f2eb3b3053d77f32178df87d7f630e5',
              'D4':'33e165ce2552c44f0787b696542f57aeee981aa404a3f93c70d0feb926ae2601',
              'D7':'a658fd055e72b5242bf933cb7df382c94385f2d52fa64307dccdc9c6e0ef8675'}
    for identity in ['D3','D4','D6','D7','C2','C3','C5']:
        p=run.panel()[identity];assert run.sha(ROOT/p['instance_path'])==p['input_sha256']
        folder=RAW/'preflight_v1'/identity
        for mode in ['off','q','t','sep','joint']:
            path=folder/mode/'canonical_model.lp';text=path.read_text()
            has_q='r64_q_balance_' in text;has_t='r63_balance_' in text
            assert has_q==(mode in ['q','sep','joint'])
            assert has_t==(mode in ['t','sep','joint'])
            assert ('r64_shared_' in text)==(mode=='joint')
            assert ('r63_carried_' in text)==(mode in ['sep','joint'])
            if mode=='off' and identity in historic:assert run.sha(path)==historic[identity]
            checks.append(dict(id=identity,mode=mode,model_sha256=run.sha(path),q_present=has_q,time_present=has_t,
                inherited_off_identical=mode=='off' and identity in historic))
    table('model_identity_preflight.csv',checks);print('solver-free preflight identities',len(checks))
    projected=[]
    for folder in sorted((RAW/'preflight_qcap_v4').glob('*')):
        identity=folder.name
        base=folder/'off/canonical_model.lp';old=RAW/'preflight_v1'/identity/'off/canonical_model.lp'
        assert run.sha(base)==run.sha(old),'F0 changed in QCAP build'
        q=folder/'q/canonical_model.lp';small=folder/'qcap/canonical_model.lp';content=small.read_text()
        assert run.sha(q)==run.sha(RAW/'preflight_v1'/identity/'q/canonical_model.lp'),'Q changed in QCAP build'
        assert 'r64_q_balance_' in content and 'r64_q_load_' in content and 'r63f_' not in content
        active=content.count('r64_q_time_capacity_')
        if not active:assert run.sha(q)==run.sha(small)
        projected.append(dict(id=identity,off_unchanged=True,qcap_model_sha256=run.sha(small),
            projected_capacity_rows=active,no_time_columns=True,identical_to_Q=run.sha(q)==run.sha(small)))
    table('qcap_model_identity_preflight.csv',projected)
    retained=[]
    for folder in sorted((RAW/'joint_identity_v4').glob('*')):
        identity=folder.name;new=folder/'joint/canonical_model.lp'
        old=RAW/'preflight_v1'/identity/'joint/canonical_model.lp'
        assert run.sha(new)==run.sha(old)
        launch=run.read(new.parent/'launch.json')
        assert not launch['charged'] and launch['executable_sha256']==run.read(OUT/'build_freeze_v4.json')['executables']['Round50IntervalMipExperiment.exe']
        retained.append(dict(id=identity,model_sha256=run.sha(new),existing_JOINT_model_unchanged=True,
            construction_executable_build='v4',performance_qualification_build='v3',optimizer_calls=0))
    table('retained_joint_identity_verification.csv',retained)
def probes():
    checked=[];strength=[]
    for path in RAW.glob('**/probe_result.json'):
        folder=path.parent;r=run.read(path);queries=rows(folder/'lp_queries.csv')
        assert len(rows(folder/'native_calls.csv'))==r['optimizer_calls']==r['query_limit']
        originals=point(folder/'original_pins.csv')
        for q in queries:
            arm=q['arm'];strength.append(dict(id=folder.name,stage=folder.parent.name,**q))
            assert q['valid']=='1'
            if q['optimal']!='1':continue
            values=point(folder/(arm+'_point.csv'))
            sep_source=arm.startswith('pinned_sep_')
            model=folder/((arm.removeprefix('pinned_sep_') if sep_source else arm.removeprefix('pinned_'))+'.lp')
            audit=check_lp_point(model,values)
            if arm.startswith('pinned_'):
                pinned=point(folder/'sep_original_pins.csv') if sep_source else originals
                pin_error=max(abs(values[n]-v) for n,v in pinned.items());assert pin_error<=1e-7
            else:pin_error=0
            if arm=='off':assert set(values)==set(originals)
            assert abs(audit['original_LP_objective_recomputed']-float(q['objective']))<=1e-7
            checked.append(dict(id=folder.name,arm=arm,pin_error=pin_error,**audit))
        assert r.get('pinned_control_feasible',r.get('pinned_sep_feasible'))
        if r.get('qcap_sep_point_checked'):assert r['sep_point_q_feasible']
        assert r['parameter_roundtrip']
        if r['micro']:
            assert r.get('pinned_candidate_infeasible',r.get('pinned_joint_infeasible'))
            data=run.read(folder/'resource.json');c=data['handling']
            rhs=math.fsum(min(c, data['upper'][1][j])*originals[f'x_0_1_{j}'] for j in [0,2])
            violation=c*originals['load_0_1']-rhs
            assert violation>.03
            checked.append(dict(id=folder.name,arm='direct_global_nonnegative_combination_certificate',
                violation=violation,scope='resource-block physical global; not actual complete F0'))
    table('lp_residual_verification.csv',checked);table('strength.csv',strength)
    print('independent LP/dual-combination checks',len(checked))
def witnesses(submitted=False):
    records=[];entries={e['charged_number']:e for e in run.runner.entries() if e['charged']};panels=run.panel()
    for number,e in entries.items():
        if e['id'] in panels:p=panels[e['id']]
        elif e['id'] in ['full_micro','warm_micro']:
            command=e['command']
            def arg(name):return command[command.index(name)+1]
            p=dict(instance_path=arg('--input'),T_seconds=arg('--T'),pickup_seconds=arg('--pickup-time'),drop_seconds=arg('--drop-time'))
            p['lambda']=arg('--lambda')
        else:continue
        if not submitted and not (ROOT/e['destination']/'completion.json').exists():continue
        if 'input_sha256' in p:assert run.sha(ROOT/p['instance_path'])==p['input_sha256']
        folder=OUT/'witnesses'/str(number) if submitted else ROOT/e['destination']
        paths=list(folder.glob('**/*witness.json'))
        if (folder/'result.json').exists() and 'routes' in run.read(folder/'result.json'):paths.append(folder/'result.json')
        for path in paths:
            witness=run.read(path);checked=physical_module.physical(p,witness);assert checked['original_T_feasible']
            records.append(dict(number=number,id=e['id'],arm=e['arm'],path=str(path.relative_to(ROOT)),**checked))
            if not submitted:
                dest=OUT/'witnesses'/str(number)/path.relative_to(folder);dest.parent.mkdir(parents=True,exist_ok=True)
                if path.name=='result.json':run.write(dest,{k:witness[k] for k in ['objective','routes','verification'] if k in witness})
                else:shutil.copyfile(path,dest)
    table('witness_verification.csv' if not submitted else 'submitted_witness_verification.csv',records)
    print('independent original route checks',len(records))

def resource_matrix(resource,capacities):
    """Independent physical equations; no native LP parser or solver needed."""
    expected={};V,M=resource['V'],resource['M'];c=resource['handling']
    def add(name,eq,a,b):expected[name]=(str(int(eq)),a,b)
    for k in range(M):
        for i in range(1,V+1):
            qb={f'q_{k}_{i}_{j}':1. for j in range(V+1) if j!=i};qload=dict(qb)
            fb={f'f_{k}_{i}_{j}':1. for j in range(V+1) if j!=i};b4={n:-v for n,v in fb.items()}
            for h in range(1,V+1):
                if h!=i:qb[f'q_{k}_{h}_{i}']=-1.;fb[f'f_{k}_{h}_{i}']=-1.
            fb_rhs={f'p_{k}_{i}':c,**{f'x_{k}_{h}_{i}':resource['travel'][h][i] for h in range(V+1) if h!=i}}
            add(f'q_balance_{k}_{i}',True,qb,{f'p_{k}_{i}':1.,f'd_{k}_{i}':-1.})
            add(f'q_load_{k}_{i}',True,qload,{f'load_{k}_{i}':1.})
            add(f'f_balance_{k}_{i}',True,fb,fb_rhs)
            add(f'B4_{k}_{i}',False,b4,{f'load_{k}_{i}':-c})
            for j in range(V+1):
                if j==i:continue
                q,f,x=f'q_{k}_{i}_{j}',f'f_{k}_{i}_{j}',f'x_{k}_{i}_{j}'
                add(f'q_cap_{k}_{i}_{j}',False,{q:1.},{x:float(capacities[k])})
                add(f'f_cap_{k}_{i}_{j}',False,{f:1.},{x:resource['upper'][i][j]})
                add(f'shared_{k}_{i}_{j}',False,{q:c,f:-1.},{})
    return expected

def check_resource_physics(identity,resource,capacities):
    """Check coefficient safety against original parsed physical distances.

    Decimal shortest paths use exact binary-double inputs, independently of
    the native downward-rounded Floyd computation. This verifies safe bounds,
    rather than treating a matching identity string as physical correctness.
    """
    p=run.panel()[identity];source=ROOT/p['instance_path'];assert run.sha(source)==p['input_sha256']
    content=source.read_text(encoding='utf-8');header=content.splitlines()[0]
    assert capacities==ast.literal_eval(header[header.index('['):])
    V,M=map(int,header[:header.index('[')].split());assert (V,M)==(resource['V'],resource['M']) and len(capacities)==M
    points=ast.literal_eval(re.search(r'(?m)^\s*points\s*=\s*(\[[^\n]*\])',content)[1]);assert len(points)==V+1
    dist=[]
    for a in points:
        row=[]
        for b in points:
            dx,dy=float(a[0])-float(b[0]),float(a[1])-float(b[1]);row.append(math.sqrt(dx*dx+dy*dy)/1.5)
        dist.append(row)
    with localcontext() as ctx:
        ctx.prec=100
        T=Decimal(str(p['T_seconds']));scale=max(Decimal(1),T);assert Decimal.from_float(resource['scale'])==scale
        c=Decimal(str(p['pickup_seconds']))+Decimal(str(p['drop_seconds']))
        assert 0<=Decimal.from_float(resource['handling'])<=c/scale
        shortest=[[Decimal.from_float(v) for v in row] for row in dist]
        for h in range(V+1):
            for i in range(V+1):
                for j in range(V+1):shortest[i][j]=min(shortest[i][j],shortest[i][h]+shortest[h][j])
        for i in range(V+1):
            assert len(resource['travel'][i])==len(resource['upper'][i])==V+1
            for j in range(V+1):
                tau=Decimal.from_float(dist[i][j]);stored=Decimal.from_float(resource['travel'][i][j])
                assert 0<=stored<=tau/scale
                upper=Decimal.from_float(resource['upper'][i][j]);assert upper>=0
                if i and i!=j:assert upper>=max(Decimal(0),(T-tau-shortest[j][0])/scale)
                else:assert upper==0

def projections():
    records=[]
    for path in RAW.glob('**/audit_result.json'):
        folder=path.parent;r=run.read(path)
        if not (folder/'sep_terms.csv').exists():continue
        assert len(rows(folder/'native_calls.csv'))==r['optimizer_calls']==2
        for p in rows(folder/'parameters.csv'):assert float(p['requested'])==float(p['actual'])
        p=point(folder/'sep_point.csv');audit=check_lp_point(folder/'sep.lp',p)
        records.append(dict(id=folder.name,kind='independent_auxiliary_SEP_feasibility',**audit))
        if not r['projection_certificate']:continue
        cert=run.read(folder/'projection_certificate.json');resource=run.read(folder/'resource.json')
        assert cert['identity']==resource['identity'] and cert['scope']=='original_physical_global' and not cert['submitted']
        assert run.sha(folder/'original_pins.csv')==cert['pins_sha256']
        pins=point(folder/'original_pins.csv')
        terms=rows(folder/'joint_terms.csv');dual={p['row']:p for p in rows(folder/'dual.csv')}
        physical=run.panel()[folder.name]
        header=(ROOT/physical['instance_path']).read_text(encoding='utf-8').splitlines()[0]
        capacities=ast.literal_eval(header[header.index('['):])
        check_resource_physics(folder.name,resource,capacities)
        expected=resource_matrix(resource,capacities)
        observed={n:[e,{},{}] for n,(e,a,b) in expected.items()}
        for t in terms:
            assert t['row'] in expected and t['equality']==expected[t['row']][0]
            observed[t['row']][1 if t['side']=='aux' else 2][t['variable']]=float(t['coefficient'])
        assert {n:tuple(v) for n,v in observed.items()}==expected,'auxiliary matrix is not the physical SEP/JOINT contract'
        aggregate={};projected={}
        for t in terms:
            y=dual[t['row']];value=float(y['normalized_multiplier']);assert y['equality']==t['equality']
            if y['equality']=='0':assert value>=0
            dst=aggregate if t['side']=='aux' else projected
            dst.setdefault(t['variable'],[]).append(value*float(t['coefficient']))
        aggregate={n:math.fsum(v) for n,v in aggregate.items()};projected={n:math.fsum(v) for n,v in projected.items()}
        bounds=rows(folder/'column_residuals.csv');beta=[];error=0
        for z in bounds:
            a=aggregate.get(z['variable'],0.);u=float(z['upper']);assert float(z['lower'])==0 and u>=0
            family,k,i,j=z['variable'].split('_');k,i,j=int(k),int(i),int(j)
            assert u==(capacities[k] if family=='q' else resource['upper'][i][j])
            error=max(error,abs(a-float(z['aggregate_coefficient'])))
            beta.append(min(0,a*u))
        rhs=math.fsum(beta);activity=math.fsum(a*pins[n] for n,a in projected.items())
        saved={t['variable']:float(t['coefficient']) for t in rows(folder/'projection_row.csv')}
        error=max(error,max((abs(saved[n]-a) for n,a in projected.items()),default=0.))
        assert error<1e-10 and abs(rhs-cert['rhs'])<1e-9 and abs(activity-cert['raw_activity'])<1e-9
        violation=rhs-activity;assert violation>1e-7 and abs(violation-cert['violation'])<1e-9
        records.append(dict(id=folder.name,kind='finite_bound_corrected_Farkas_combination',scope=cert['scope'],
            column_and_projection_residual=error,corrected_rhs=rhs,raw_activity=activity,violation=violation,original_terms=len(projected),
            nonzero_original_terms=sum(a!=0 for a in projected.values()),
            nonzero_dual_rows=sum(float(y['normalized_multiplier'])!=0 for y in dual.values()),submitted=False))
    table('projection_certificate_verification.csv',records);print('independent auxiliary/Farkas checks',len(records))

def warm_states():
    records=[];groups={}
    for e in run.runner.entries():
        folder=ROOT/e['destination']
        if not e['charged'] or not (folder/'completion.json').exists() or not (e['arm'].startswith('warm-') or e['arm']=='K1-H'):continue
        r=run.read(folder/'result.json')
        assert r['primal_heuristic']=='hga-tgbc' and not r['external_gini_tree_warm_start_enabled']
        assert r['external_gini_tree_warm_start_submitted_count']==0 and not r['incumbent_archive_selected']
        events=[v for v in rows(folder/'ub_events.csv') if v['source']=='native_hga_tgbc_initial']
        assert len(events)==1 and events[0]['verifier_passed']=='true' and events[0]['accepted']=='true'
        event=events[0];initial=folder/'external/initial_witness.json'
        interval=folder/'external/initial_decomposition_ledger.csv'
        ledger=folder/'external/paper_optimize_ledger.csv';calls=rows(ledger) if ledger.exists() else []
        state=dict(number=e['charged_number'],id=e['id'],arm=e['arm'],stage=e['stage'],cap=e['cap_seconds'],
            executable_sha256=e['executable_sha256'],initial_U=float(event['objective']),initial_hash=event['incumbent_hash'],
            generated_in_this_process=True,startup_accepted_seconds=float(event['time_seconds']),
            native_start_enabled=False,native_start_submitted=0,
            route_snapshot_sha256=run.sha(initial) if initial.exists() else None,
            initial_domain_sha256=run.sha(interval) if interval.exists() else None,
            first_canonical_model_sha256=calls[0]['model_sha256'] if calls else None)
        if initial.exists():
            w=run.read(initial);assert abs(w['objective']-state['initial_U'])<=1e-10
        records.append(state)
        groups.setdefault((e['id'],e['stage'],e['cap_seconds'],e['executable_sha256']),[]).append(state)
    comparisons=[]
    for group in groups.values():
        base=next((r for r in group if r['arm']=='warm-off'),None)
        if base is None:continue
        for r in group:
            if r is base:continue
            for key in ['initial_U','initial_hash','initial_domain_sha256']:assert r[key]==base[key],(r['number'],key)
            if r['arm']!='K1-H':assert r['route_snapshot_sha256']==base['route_snapshot_sha256']
            else:assert r['first_canonical_model_sha256']==base['first_canonical_model_sha256'],'stable and research OFF first F0 models differ'
            comparisons.append(dict(baseline=base['number'],candidate=r['number'],id=r['id'],
                identical_startup_hash_U_domain=True,identical_route_snapshot=r['arm']!='K1-H',native_starts_both_disabled=True,
                first_F0_identical_to_stable_reference=True if r['arm']=='K1-H' else None))
    table('warm_state_verification.csv',records);table('warm_pairs_verification.csv',comparisons)
    print('warm states',len(records),'matched pairs',len(comparisons))

def cold_states():
    records=[];groups={}
    for e in run.runner.entries():
        folder=ROOT/e['destination']
        if not e['charged'] or not e['arm'].startswith('cold-') or not (folder/'completion.json').exists():continue
        r=run.read(folder/'result.json');initial=folder/'external/initial_witness.json';w=run.read(initial)
        assert all(route['nodes']==[0,0] and not route['operations'] for route in w['routes']),'cold startup contained station service'
        assert r['primal_heuristic']=='greedy' and not r['external_gini_tree_warm_start_enabled']
        assert r['external_gini_tree_warm_start_submitted_count']==0 and not r['incumbent_archive_selected']
        assert not any(v['source']=='native_hga_tgbc_initial' and v['accepted']=='true' for v in rows(folder/'ub_events.csv'))
        domain=folder/'external/initial_decomposition_ledger.csv'
        state=dict(number=e['charged_number'],id=e['id'],arm=e['arm'],stage=e['stage'],cap=e['cap_seconds'],
            executable_sha256=e['executable_sha256'],initial_U=w['objective'],verified_empty_routes=True,
            route_snapshot_sha256=run.sha(initial),initial_domain_sha256=run.sha(domain),native_start_enabled=False)
        records.append(state)
        groups.setdefault((e['id'],e['stage'],e['cap_seconds'],e['executable_sha256']),[]).append(state)
    pairs=[]
    for group in groups.values():
        base=next((s for s in group if s['arm']=='cold-off'),None)
        if base is None:continue
        for s in group:
            if s is base:continue
            for key in ['initial_U','route_snapshot_sha256','initial_domain_sha256']:assert s[key]==base[key]
            pairs.append(dict(baseline=base['number'],candidate=s['number'],id=s['id'],identical_empty_start_U_domain=True,native_starts_both_disabled=True))
    table('cold_state_verification.csv',records);table('cold_pairs_verification.csv',pairs)
    print('cold states',len(records),'matched pairs',len(pairs))

def pack_projection_evidence():
    """Repackage existing charged diagnostics; never generate or optimize a cut."""
    for folder in sorted((RAW/'projection_v2').glob('*')):
        if not (folder/'projection_certificate.json').exists():continue
        cert=run.read(folder/'projection_certificate.json');resource=run.read(folder/'resource.json');p=run.panel()[folder.name]
        header=(ROOT/p['instance_path']).read_text(encoding='utf-8').splitlines()[0]
        capacities=ast.literal_eval(header[header.index('['):]);matrix=resource_matrix(resource,capacities)
        used={n for eq,a,b in matrix.values() for n in b};pins=point(folder/'original_pins.csv')
        proof=dict(id=folder.name,certificate=cert,resource=resource,capacities=capacities,
            physical_input_sha256=p['input_sha256'],physical_point={n:pins[n] for n in sorted(used)},
            sep_completion={n:v for n,v in point(folder/'sep_point.csv').items() if v!=0},
            dual={y['row']:float(y['normalized_multiplier']) for y in rows(folder/'dual.csv') if float(y['normalized_multiplier'])!=0},
            projected_row={y['variable']:float(y['coefficient']) for y in rows(folder/'projection_row.csv') if float(y['coefficient'])!=0},
            auxiliary_unlisted_values=0,pruned_tolerance=0,generated_new_evidence=False,
            source_hashes={name:run.sha(folder/name) for name in ['original_pins.csv','sep_point.csv','joint_terms.csv','dual.csv','projection_row.csv','column_residuals.csv','projection_certificate.json','audit_result.json']})
        run.write(OUT/'projection_evidence'/(folder.name+'.json'),proof)

def submitted_projections():
    records=[]
    for path in sorted((OUT/'projection_evidence').glob('*.json')):
        proof=run.read(path);r=proof['resource'];Q=proof['capacities'];cert=proof['certificate']
        check_resource_physics(proof['id'],r,Q)
        assert proof['physical_input_sha256']==run.panel()[proof['id']]['input_sha256']
        assert cert['identity']==r['identity'] and cert['pins_sha256']==proof['source_hashes']['original_pins.csv']
        assert cert['scope']=='original_physical_global' and not cert['submitted']
        assert proof['pruned_tolerance']==0 and proof['auxiliary_unlisted_values']==0 and not proof['generated_new_evidence']
        matrix=resource_matrix(r,Q);pins=proof['physical_point'];sep=proof['sep_completion'];alpha={};row={};error=0.
        def upper(n):
            family,k,i,j=n.split('_');return Q[int(k)] if family=='q' else r['upper'][int(i)][int(j)]
        for n,v in sep.items():assert -1e-7<=v<=upper(n)+1e-7
        for name,(eq,a,b) in matrix.items():
            if name.startswith('shared_'):continue
            activity=math.fsum(c*sep.get(n,0) for n,c in a.items())-math.fsum(c*pins[n] for n,c in b.items())
            error=max(error,abs(activity) if eq=='1' else max(0,activity))
        assert error<=1e-7
        for name,y in proof['dual'].items():
            eq,a,b=matrix[name];assert math.isfinite(y) and (eq=='1' or y>=0)
            for n,c in a.items():alpha.setdefault(n,[]).append(y*c)
            for n,c in b.items():row.setdefault(n,[]).append(y*c)
        alpha={n:math.fsum(v) for n,v in alpha.items()};row={n:math.fsum(v) for n,v in row.items()}
        beta=math.fsum(min(0,c*upper(n)) for n,c in alpha.items())
        activity=math.fsum(c*pins[n] for n,c in row.items());saved=proof['projected_row']
        residual=max((abs(row.get(n,0)-saved.get(n,0)) for n in set(row)|set(saved)),default=0)
        assert residual<=1e-10 and abs(beta-cert['rhs'])<=1e-9 and abs(activity-cert['raw_activity'])<=1e-9
        assert beta-activity>1e-7 and abs(beta-activity-cert['violation'])<=1e-9
        records.append(dict(id=proof['id'],path=str(path.relative_to(ROOT)),sha256=run.sha(path),
            sep_maximum_row_residual=error,projection_coefficient_residual=residual,corrected_rhs=beta,
            raw_activity=activity,strict_violation=beta-activity,dual_support=len(proof['dual']),
            source_point_in_full_F0='linked to full target-LP residual evidence; this file rechecks resource projection'))
    table('submitted_projection_verification.csv',records);print('submitted resource projection checks',len(records))
def main():
    p=argparse.ArgumentParser();p.add_argument('--preflight',action='store_true');p.add_argument('--submitted',action='store_true');p.add_argument('--package',action='store_true');a=p.parse_args()
    if a.preflight:preflight()
    elif a.submitted:witnesses(True);submitted_projections()
    elif a.package:pack_projection_evidence();submitted_projections()
    else:probes();projections();witnesses();warm_states();cold_states()
if __name__=='__main__':main()

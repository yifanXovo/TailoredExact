"""Solver-free independent physical, LP-residual and identity checks."""
import argparse
import ast
import csv
import json
import math
import shutil
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
def probes():
    checked=[];strength=[]
    for path in RAW.glob('**/probe_result.json'):
        folder=path.parent;r=run.read(path);queries=rows(folder/'lp_queries.csv')
        assert len(rows(folder/'native_calls.csv'))==r['optimizer_calls']==7
        originals=point(folder/'original_pins.csv')
        for q in queries:
            arm=q['arm'];strength.append(dict(id=folder.name,stage=folder.parent.name,**q))
            assert q['valid']=='1'
            if q['optimal']!='1':continue
            values=point(folder/(arm+'_point.csv'))
            model=folder/((arm.removeprefix('pinned_'))+'.lp')
            audit=check_lp_point(model,values)
            if arm.startswith('pinned_'):
                pin_error=max(abs(values[n]-v) for n,v in originals.items());assert pin_error<=1e-7
            else:pin_error=0
            if arm=='off':assert set(values)==set(originals)
            assert abs(audit['original_LP_objective_recomputed']-float(q['objective']))<=1e-7
            checked.append(dict(id=folder.name,arm=arm,pin_error=pin_error,**audit))
        assert r['pinned_sep_feasible']
        assert r['parameter_roundtrip']
        if r['micro']:
            assert r['pinned_joint_infeasible']
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
        if e['id'] not in panels:continue
        folder=OUT/'witnesses'/str(number) if submitted else ROOT/e['destination']
        paths=list(folder.glob('**/*witness.json'))
        if (folder/'result.json').exists() and 'routes' in run.read(folder/'result.json'):paths.append(folder/'result.json')
        for path in paths:
            witness=run.read(path);checked=physical_module.physical(panels[e['id']],witness);assert checked['original_T_feasible']
            records.append(dict(number=number,id=e['id'],arm=e['arm'],path=str(path.relative_to(ROOT)),**checked))
            if not submitted:
                dest=OUT/'witnesses'/str(number)/path.relative_to(folder);dest.parent.mkdir(parents=True,exist_ok=True)
                if path.name=='result.json':run.write(dest,{k:witness[k] for k in ['objective','routes','verification'] if k in witness})
                else:shutil.copyfile(path,dest)
    table('witness_verification.csv' if not submitted else 'submitted_witness_verification.csv',records)
    print('independent original route checks',len(records))

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
        expected={};V,M=resource['V'],resource['M'];c=resource['handling']
        def add(name,eq,a,b):expected[name]=(str(int(eq)),a,b)
        for k in range(M):
            for i in range(1,V+1):
                qb={f'q_{k}_{i}_{j}':1. for j in range(V+1) if j!=i}
                qload=dict(qb)
                fb={f'f_{k}_{i}_{j}':1. for j in range(V+1) if j!=i}
                b4={n:-v for n,v in fb.items()}
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
            nonzero_dual_rows=sum(float(y['normalized_multiplier'])!=0 for y in dual.values()),submitted=False))
    table('projection_certificate_verification.csv',records);print('independent auxiliary/Farkas checks',len(records))
def main():
    p=argparse.ArgumentParser();p.add_argument('--preflight',action='store_true');p.add_argument('--submitted',action='store_true');a=p.parse_args()
    if a.preflight:preflight()
    elif a.submitted:witnesses(True)
    else:probes();projections();witnesses()
if __name__=='__main__':main()

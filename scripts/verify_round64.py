"""Solver-free independent physical, LP-residual and identity checks."""
import argparse
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
def main():
    p=argparse.ArgumentParser();p.add_argument('--preflight',action='store_true');p.add_argument('--submitted',action='store_true');a=p.parse_args()
    if a.preflight:preflight()
    elif a.submitted:witnesses(True)
    else:probes();witnesses()
if __name__=='__main__':main()

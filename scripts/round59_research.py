"""Bounded, serial Round 59 execution. Never launches historical panels."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/gf_core_attribution_native_round59'
RAW = OUT / 'local_raw'
EXE = ROOT / 'build/round59-core/ExactEBRP.exe'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding='utf-8')

def freeze():
    target = OUT / 'panel.json'
    if target.exists():
        raise RuntimeError('panel already frozen')
    old = ROOT / 'results/gf_citibike443_k1_vs_pgrb_round58'
    rows = {r['scenario_id']: r for r in csv.DictReader((old/'round58_complete_panel.csv').open())}
    selected = [
        ('cb443_V08_compact_r2_balanced_M02_Q20_T03600', 'zero objective startup regression'),
        ('cb443_V20_regional_r2_surplus_M03_Q20_T18000', 'positive objective long-T regression'),
        ('major', 'historical major witness'),
        ('strong', 'historical strong positive control'),
        ('cb443_V20_compact_r2_balanced_M02_Q30_T03600', 'V20 K1 advantage'),
        ('cb443_V30_compact_r1_shortage_M03_Q30_T18000', 'V30 long-T lower-bound stagnation'),
        ('cb443_V50_regional_r1_shortage_M04_Q30_T18000', 'V50 long-T mixed; long native routes'),
        ('cb443_V08_compact_r2_shortage_M01_Q30_T01800', 'positive objective nonzero proof work'),
        ('cb443_V12_compact_r2_shortage_M01_Q30_T01800', 'confirmation small shortage'),
        ('cb443_V20_compact_r1_surplus_M02_Q30_T01800', 'confirmation V20 short horizon'),
    ]
    # The V12 selection is taken by structural role if the exact rotation differs.
    if selected[8][0] not in rows:
        selected[8] = (next(k for k,r in rows.items() if r['V']=='12' and r['inventory_regime']=='shortage'), selected[8][1])
    historical = json.loads((ROOT/'results/gf_k1_am_sf_station_state_chain_round55/k1_integration_panel_freeze.json').read_text())['instances']
    panel = []
    for i,(key,role) in enumerate(selected):
        if key in ('major','strong'):
            h = historical[0 if key=='major' else 1]
            r = dict(instance_path=h['input_path'], T_seconds=2850, pickup_seconds=60, drop_seconds=60, V=12, M=3, Q=30, inventory_regime='historical_unmodified')
            key = h['instance_id']
        else:
            r = dict(rows[key])
        r.update(id=f'D{i+1}' if i<8 else f'C{i-7}', scenario_id=key, role=role, stage='development' if i<8 else 'confirmation')
        r['input_sha256'] = sha(ROOT/r['instance_path'])
        panel.append(r)
    write(target, dict(baseline='edd65fe9f5bd37616366c1c6ca48379df062cdcf', panel=panel,
        budget=dict(max_performance_processes=80, max_instances=12, screen_cap=120, max_1800_runs=12, max_3600_runs=4),
        confirmation_not_for_selection=True, selection='historical roles; frozen before Round59 performance'))

def execute(command, dest, identity):
    dest.mkdir(parents=True, exist_ok=False)
    ledger = OUT/'processes.jsonl'
    entries = [json.loads(s) for s in ledger.read_text().splitlines()] if ledger.exists() else []
    if len(entries)>=80:
        raise RuntimeError('80 process budget exhausted')
    identity.update(command=command, executable_sha256=sha(command[0]), started=time.time(), process_number=len(entries)+1)
    write(dest/'launch.json', identity)
    with ledger.open('a') as f:
        f.write(json.dumps(identity)+'\n')
    env = dict(os.environ)
    env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    start=time.monotonic()
    with (dest/'stdout.log').open('w') as out, (dest/'stderr.log').open('w') as err:
        p=subprocess.Popen(command,cwd=ROOT,env=env,stdout=out,stderr=err)
        try:
            rc=p.wait(timeout=identity['cap'])
            watchdog=False
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(); rc=p.returncode; watchdog=True
    write(dest/'completion.json',dict(returncode=rc,wall_seconds=time.monotonic()-start,watchdog=watchdog))
    print(identity['id'],identity['arm'],rc,round(time.monotonic()-start,2),flush=True)
    if rc != 0:
        raise RuntimeError(f'failed run: {dest}')

def run(stage, only):
    panel=json.loads((OUT/'panel.json').read_text())['panel']
    fps={r['instance_id']:r['expected_gurobi_model_fingerprint'] for r in json.loads((ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json').read_text())['entries']}
    arms={'P-GRB':None,'K1-H':'paper-k1-am-sf','K1-S':'research-round59-k1-s','F0-Single-S':'research-round59-f0-single-s'}
    for r in panel:
        if r['stage']!=stage or (only and r['id']!=only): continue
        assert sha(ROOT/r['instance_path'])==r['input_sha256']
        for arm,preset in arms.items():
            dest=RAW/'screen120'/r['id']/arm
            if (dest/'completion.json').exists():
                if json.loads((dest/'completion.json').read_text())['returncode']==0: continue
                dest=dest.parent/(arm+'-retry1')
                if (dest/'completion.json').exists():
                    if json.loads((dest/'completion.json').read_text())['returncode']==0: continue
                    raise RuntimeError('retry failed; inspect before continuing')
            cap=120
            cmd=[str(EXE),'--input',r['instance_path'],'--lambda','0.15','--T',str(r['T_seconds']),
                 '--time-limit',str(cap-6),'--process-wall-time-limit',str(cap),'--process-shutdown-margin','3',
                 '--threads','1','--mip-threads','1','--gurobi-seed','0','--gurobi-presolve','-1',
                 '--out',str(dest/'result.json'),'--log',str(dest/'native.log'),
                 '--process-phase-ledger',str(dest/'process_phases.csv')]
            if preset:
                cmd+=['--method','gcap-frontier','--algorithm-preset',preset,
                      '--external-gini-artifact-dir',str(dest/'external'),
                      '--heuristic-candidates-csv',str(dest/'heuristic_candidates.csv'),
                      '--primal-heuristic-generation-log',str(dest/'hga_generations.csv'),
                      '--progress-log',str(dest/'progress.csv')]
            else:
                cmd+=['--method','gurobi','--plain-baseline','--gurobi-model-export',str(dest/'compact.lp')]
                if r['scenario_id'] in fps:
                    cmd+=['--round24-expected-gurobi-model-fingerprint',str(fps[r['scenario_id']]),'--round24-executable-sha256',sha(EXE),'--round24-manifest-executable-sha256',sha(EXE)]
            execute(cmd,dest,dict(id=r['id'],arm=arm,cap=cap,stage=stage,scope='full_instance'))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','development','confirmation'])
    parser.add_argument('--only')
    args=parser.parse_args()
    if args.action=='freeze': freeze()
    else: run(args.action,args.only)

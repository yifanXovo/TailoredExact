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
            r = dict(instance_path=h['input_path'], T_seconds=2850 if key=='major' else 2400, pickup_seconds=60, drop_seconds=60, V=12, M=3, Q=30, inventory_regime='historical_unmodified')
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

def run(stage, only, cap=120, selected_arms=None):
    panel=json.loads((OUT/'panel.json').read_text())['panel']
    fps={r['instance_id']:r['expected_gurobi_model_fingerprint'] for r in json.loads((ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json').read_text())['entries']}
    fps.update({k:r['gurobi_model_fingerprint'] for k,r in json.loads((ROOT/'results/gf_small_hard_light_round39/gurobi_fingerprints.json').read_text())['instances'].items()})
    arms={'P-GRB':None,'K1-H':'paper-k1-am-sf','K1-S':'research-round59-k1-s','F0-Single-S':'research-round59-f0-single-s'}
    for r in panel:
        if r['stage']!=stage or (only and r['id']!=only): continue
        assert sha(ROOT/r['instance_path'])==r['input_sha256']
        for arm,preset in arms.items():
            if selected_arms and arm not in selected_arms: continue
            dest=RAW/('screen'+str(cap))/r.get('artifact_id',r['id'])/arm
            if (dest/'completion.json').exists():
                if json.loads((dest/'completion.json').read_text())['returncode']==0: continue
                dest=dest.parent/(arm+'-retry1')
                if (dest/'completion.json').exists():
                    if json.loads((dest/'completion.json').read_text())['returncode']==0: continue
                    raise RuntimeError('retry failed; inspect before continuing')
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

def diagnostics(phase):
    panel=json.loads((OUT/'panel.json').read_text())['panel']
    exe=ROOT/'build/round59-core/Round50IntervalMipExperiment.exe'
    policies={
        'F0':('interval-mip-core-no-exhaustive-subset-duration',[]),
        'Compact':('interval-mip-core-no-exhaustive-subset-duration',['--round59-compact']),
        'OriginalCompact':('interval-mip-core-no-exhaustive-subset-duration',[]),
        'Monitor':('interval-mip-core-no-exhaustive-subset-duration',['--round59-monitor']),
        'Static':('interval-mip-core-no-exhaustive-subset-duration',['--round59-cuts','static']),
        'Pool':('interval-mip-core-no-exhaustive-subset-duration',['--round59-cuts','pool']),
        'Focus1':('interval-mip-core-no-exhaustive-subset-duration',['--round59-primal-focus']),
        'Focus3':('interval-mip-core-no-exhaustive-subset-duration',['--round59-bound-focus']),
        'PreCrush':('round53-c1-precrush-only',[]),
        'StatusPreCrush':('round53-c3-status-precrush',[]),
        'DryRun':('round53-c4-separator-dry-run',[]),
        'Dynamic':('round53-c5-live',[]),
    }
    plans={'roots':(['D2','D3','D4'],['F0','Compact'],'lp'),
           'original':(['D3','D4'],['F0','OriginalCompact'],'solve'),
           'cuts':(['D3','D4'],['F0','Monitor','Static','Pool'],'solve'),
           'callback':(['D3'],['PreCrush','StatusPreCrush','DryRun','Dynamic'],'solve'),
           'focus':(['D3','D4'],['Focus1'],'solve'),
           'hga_lp':(['D2'],['F0','Compact'],'lp'),
           'hga_state':(['D2'],['F0','Compact'],'solve'),
           'startup_state':(['D6','D7'],['F0'],'solve')}
    ids,arms,mode=plans[phase]
    for r in panel:
        if r['id'] not in ids: continue
        if phase=='startup_state' and not (OUT/('frozen_startup_'+r['id']+'.json')).exists(): continue
        for arm in arms:
            dest=RAW/('diagnostic_current_'+phase)/r['id']/arm
            if (dest/'completion.json').exists():
                if json.loads((dest/'completion.json').read_text())['returncode']==0: continue
                raise RuntimeError('failed diagnostic needs inspection')
            policy,extra=policies[arm]
            cmd=[str(exe),'--mode',mode,'--state-id',r['id']+'-'+phase,
                 '--input',r['instance_path'],'--artifact-dir',str(dest),
                 '--policy',policy,'--T',str(r['T_seconds']),'--process-cap','120','--round59-current-f0',
                 ]+extra
            if arm=='OriginalCompact':
                origin=RAW/'screen120'/r.get('artifact_id',r['id'])/'P-GRB/compact.lp'
                cmd+=['--round59-original-compact-sha256',sha(origin)]
            if phase in ['hga_lp','hga_state','startup_state']:
                frozen_path=OUT/('frozen_startup_'+r['id']+'.json') if phase=='startup_state' else OUT/'frozen_hga_state.json'
                frozen=json.loads(frozen_path.read_text())
                assert frozen.get('status')=='valid'
                assert sha(ROOT/frozen['source_result'])==frozen['source_result_sha256']
                cmd+=['--gamma-lower',str(frozen['gamma_lower']),'--gamma-upper',str(frozen['gamma_upper']),
                      '--cutoff',str(frozen['U'])]
            else:
                cmd+=['--round59-empty-state']
            execute(cmd,dest,dict(id=r['id'],arm=arm,cap=120,stage='diagnostic_current_'+phase,
                scope='restricted_state_diagnostic',incumbent_source=str(frozen_path.relative_to(OUT)) if phase in ['hga_lp','hga_state','startup_state'] else 'independently verified empty routes',incumbent_epoch=0))

def micro():
    exe=ROOT/'build/round59-core/Round50IntervalMipExperiment.exe'
    for arm in ['off','static','pool']:
        dest=RAW/'micro'/arm
        cmd=[str(exe),'--mode','solve','--state-id','tiny-positive',
             '--input','tests/data/round59_tiny.txt','--artifact-dir',str(dest),
             '--policy','interval-mip-core-no-exhaustive-subset-duration',
             '--T','5','--pickup-time','1','--drop-time','1','--process-cap','15',
             '--round59-empty-state','--round59-cuts',arm]
        execute(cmd,dest,dict(id='micro',arm=arm,cap=15,stage='correctness',scope='tiny_exact_only'))
        r=json.loads((dest/'result.json').read_text())
        assert r['certificate'] and abs(r['verified_upper_bound']-5/24)<1e-7
    # T=5: a pickup at station 2 or 3 needs >=6 time; two visits
    # also need >=6. Only station 1 pickup=1 fits (travel 2 + handling 2).
    # It yields Y=(2,1,2), G=2/15 and lambda*P=3/40, hence F=5/24.

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','development','confirmation','roots','original','cuts','callback','focus','hga_lp','hga_state','startup_state','micro'])
    parser.add_argument('--only')
    parser.add_argument('--cap',type=int,choices=[120,300,600],default=120)
    parser.add_argument('--arms',nargs='+',choices=['P-GRB','K1-H','K1-S','F0-Single-S'])
    args=parser.parse_args()
    if args.action=='freeze': freeze()
    elif args.action=='micro': micro()
    elif args.action in ['development','confirmation']: run(args.action,args.only,args.cap,args.arms)
    else: diagnostics(args.action)

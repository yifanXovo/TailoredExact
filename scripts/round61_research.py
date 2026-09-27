"""Round61 bounded serial experiments. Every charged launch is write-ahead logged."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/gf_transfer_block_native_time_round61'
RAW = OUT / 'local_raw'
BUILD = ROOT / 'build/round61-dev'
LEDGER = OUT / 'processes.jsonl'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def freeze():
    target = OUT / 'protocol.json'
    if target.exists():
        raise RuntimeError('protocol already frozen')
    old = json.loads((ROOT / 'results/gf_core_attribution_native_round59/panel.json').read_text())
    rows = {p['id']: p for p in old['panel']}
    selected = []
    for identity in ['D1','D2','D3','D4','D6','D7','C1','C2']:
        p = dict(rows[identity])
        p['round61_stage'] = 'confirmation' if identity.startswith('C') else 'development'
        p['round61_role'] = ('not used for Round61 selection; previously public'
                             if identity.startswith('C') else p['role'])
        p['lambda'] = float(p.get('lambda', .15))
        assert sha(ROOT / p['instance_path']) == p['input_sha256']
        selected.append(p)
    assert rows['D3']['T_seconds'] == 2850 and rows['D4']['T_seconds'] == 2400
    write(target, {
        'base_commit':'fe00f198a8b8620513017b02708315b5841c4daf',
        'base_branch':'codex/round60-verified-candidate-native-injection',
        'panel':selected,
        'solver':{'engine':'Gurobi 13.0.2','Threads':1,'Seed':0,'Presolve':-1,'MIPGap':0,'MIPGapAbs':0},
        'frozen_outer':{'K0':1,'split':'midpoint','score':'balanced-normalized-closure',
            'tau':.08,'target':'native-target','closure':'exact-parent','cutoff':'F <= U'},
        'PREFIX':{'population':24,'seed':20260626,'decoder_iterations':10,
            'generations_after_initialization':16,'safety_seconds':30,
            'rationale':'uniform short existing-heuristic baseline; not theoretically optimal'},
        'BLOCK':{'start':'empty routes','maximum_rounds':32,'pairs_per_round':24,
            'singles_per_round':8,'quantity_evaluations_per_round':2048,'safety_seconds':20,
            'ranking':'ratio contrast divided by normalized incremental travel; cheapest feasible vehicle',
            'quantity_order':'q-major round robin across shortlist; full feasible enumeration when budget allows',
            'accept':'best complete strictly improving feasible move; independent snapshot verification'},
        'batch':{'fixed_methods':['LEGACY60','BLOCK','PREFIX'],'physical_cap_seconds':60,
                 'optimizer_calls':0,'no_hidden_parameter_sweep':True},
        'decision':{'certification_time_absolute_seconds':10,'certification_time_relative':.10,
            'absolute_gap_absolute':.001,'absolute_gap_relative':.05,
            'both_absolute_and_relative_required':True,'certificate_change':'separate'},
        'budget':{'maximum_charged_launches':72,'native_micro_maximum':4,
            'reserved_long_confirmation':16,'maximum_optimizer_concurrency':1,
            'long_pairs':['D3','D7','C2'],'long_seconds':600,'D4_protection_seconds':600,
            'watchdog':'invalid budget evidence; charged; never overwrite'},
        'candidate_freeze':'after development quality and at most two justified revisions; before confirmation',
        'novelty':'no theoretical novelty claimed for transfer blocks or HGA reuse'
    })

def panel():
    return {p['id']:p for p in json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))['panel']}

def entries():
    return [json.loads(s) for s in LEDGER.read_text(encoding='utf-8').splitlines()] if LEDGER.exists() else []

def execute(cmd, dest, identity, cap, kind='performance', solver_calls=1):
    if dest.exists():
        raise RuntimeError(f'refusing to overwrite {dest}')
    charged = kind != 'build-only'
    ledger = entries()
    count = sum(e['charged'] for e in ledger)
    if charged and count >= 72: raise RuntimeError('72 launch budget exhausted')
    if kind == 'native-micro' and sum(e['kind']=='native-micro' for e in ledger)>=4:
        raise RuntimeError('native micro budget exhausted')
    lock = OUT/'active_run.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
    try:
        dest.mkdir(parents=True)
        record = dict(identity, command=list(map(str,cmd)), executable_sha256=sha(cmd[0]),
            cap_seconds=cap, kind=kind, charged=charged, charged_number=count+1 if charged else None,
            solver_calls_planned=solver_calls, started_unix=time.time(), destination=str(dest.relative_to(ROOT)))
        write(dest/'launch.json', record)
        with LEDGER.open('a',encoding='utf-8') as f: f.write(json.dumps(record)+'\n')
        env=dict(os.environ); env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
        start=time.monotonic()
        with (dest/'stdout.log').open('w') as stdout, (dest/'stderr.log').open('w') as stderr:
            p=subprocess.Popen(list(map(str,cmd)),cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            watchdog=False
            try: code=p.wait(timeout=cap+10)
            except subprocess.TimeoutExpired:
                p.kill(); p.wait(); code=p.returncode; watchdog=True
        wall=time.monotonic()-start
        write(dest/'completion.json',dict(returncode=code,wall_seconds=wall,watchdog=watchdog,
            within_budget=wall<=cap,solver_calls_planned=solver_calls))
        print(identity, 'code',code,'wall',round(wall,3),'charged',count+int(charged),flush=True)
        if code or watchdog: raise RuntimeError(f'failed charged run {dest}')
    finally:
        lock.unlink()

def quality(ids, stage='quality_v1'):
    for identity in ids:
        p=panel()[identity]
        if p['round61_stage']=='confirmation' and not (OUT/'candidate_freeze.json').exists():
            raise RuntimeError('confirmation unavailable before candidate freeze')
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
        dest=RAW/stage/identity
        cmd=[BUILD/'Round61CandidateExperiment.exe','--input',p['instance_path'],'--out',dest,
             '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
             '--lambda',p['lambda'],'--mode','batch']
        execute(cmd,dest,{'id':identity,'arm':'LEGACY60+BLOCK+BLOCK-R+PREFIX+PREFIX-R','stage':stage},90,'construction',0)

def publication():
    for identity in ['D6','D7']:
        p=panel()[identity]
        for mode in ['prefix-off','prefix-on']:
            dest=RAW/'publication'/identity/mode
            cmd=[BUILD/'Round61CandidateExperiment.exe','--input',p['instance_path'],'--out',dest,
                 '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
                 '--lambda',p['lambda'],'--mode',mode]
            execute(cmd,dest,{'id':identity,'arm':mode,'stage':'publication'},40,'construction',0)

def fixed_command(p,dest,mode,cap,build=False):
    return [BUILD/'Round50IntervalMipExperiment.exe','--mode','build' if build else 'solve',
        '--state-id',p['id']+'-F0-'+mode,'--input',p['instance_path'],'--artifact-dir',dest,
        '--policy','interval-mip-core-no-exhaustive-subset-duration','--T',p['T_seconds'],
        '--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--lambda',p['lambda'],
        '--process-cap',cap,'--round59-empty-state','--round59-current-f0',
        '--round59-monitor','--round61-candidate-mode',mode]

def fixed(ids,modes,cap,stage):
    for identity in ids:
        p=panel()[identity]
        for mode in modes:
            dest=RAW/stage/identity/mode
            execute(fixed_command(p,dest,mode,cap),dest,
                    {'id':identity,'arm':mode,'stage':stage,'scope':'fixed_simple_F0'},cap)

def micro():
    p=dict(id='micro',instance_path='tests/data/round59_tiny.txt',T_seconds=5,
           pickup_seconds=1,drop_seconds=1,**{'lambda':.15})
    dest=RAW/'native_micro'/'submit'
    execute(fixed_command(p,dest,'submit',15),dest,
            {'id':'micro','arm':'submit','stage':'native_micro'},15,'native-micro')

def oracle(ids,cap=120):
    old=json.loads((ROOT/'results/gf_verified_candidate_native_round60/fixed_inventory_selection.json').read_text())
    inventories={p['id']:p['fixed_inventory'] for p in old}
    for identity in ids:
        p=panel()[identity]
        for mode in ['lp','mip']:
            oracle_one(p,inventories[identity],mode,cap,'oracle_history')

def oracle_one(p,inventory,mode,cap,stage):
    dest=RAW/stage/p['id']/mode
    cmd=[BUILD/'Round61TimeOracle.exe','--input',p['instance_path'],'--out',dest,
         '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
         '--lambda',p['lambda'],'--mode',mode,'--cap',cap,'--inventory',','.join(map(str,inventory))]
    execute(cmd,dest,{'id':p['id'],'arm':mode,'stage':stage,'scope':'inventory_time_diagnostic',
                     'fixed_inventory':inventory},cap,'oracle')

def oracle_micro():
    p=dict(id='transfer',instance_path='tests/data/round61_transfer.txt',T_seconds=12,
           pickup_seconds=1,drop_seconds=1,**{'lambda':.15})
    oracle_one(p,[0,5,5],'lp',10,'oracle_micro')
    oracle_one(p,[0,5,5],'mip',10,'oracle_micro')
    p['id']='supply_infeasible'
    oracle_one(p,[0,5,6],'mip',10,'oracle_micro')
    p['id']='released_supplier';p['T_seconds']=20
    oracle_one(p,[0,-1,6],'mip',10,'oracle_micro')

def full_command(p,dest,preset,mode,cap):
    return [BUILD/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],
        '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
        '--time-limit',cap-6,'--process-wall-time-limit',cap,'--process-shutdown-margin',3,
        '--threads',1,'--mip-threads',1,'--gurobi-seed',0,'--gurobi-presolve',-1,
        '--method','gcap-frontier','--algorithm-preset',preset,'--round61-candidate-mode',mode,
        '--out',dest/'result.json','--log',dest/'native.log','--process-phase-ledger',dest/'phases.csv',
        '--external-gini-artifact-dir',dest/'external','--heuristic-candidates-csv',dest/'heuristic.csv',
        '--primal-heuristic-generation-log',dest/'hga.csv','--progress-log',dest/'progress.csv']

def full(ids,cap,stage,k1=False):
    for identity in ids:
        p=panel()[identity]
        for mode in ['off','submit']:
            dest=RAW/stage/identity/mode
            preset='research-round59-k1-s' if k1 else 'research-round59-f0-single-s'
            execute(full_command(p,dest,preset,mode,cap),dest,
                {'id':identity,'arm':('K1-S' if k1 else 'Single-S')+'-'+mode,'stage':stage,
                 'scope':'full_original_problem'},cap,solver_calls='recorded_by_native_lifecycle')

def reference(identity,cap):
    p=panel()[identity]
    expected={e['instance_id']:e['expected_gurobi_model_fingerprint'] for e in json.loads(
        (ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json').read_text())['entries']}
    for arm in ['P-GRB','K1-H']:
        dest=RAW/'references'/identity/arm
        if arm=='K1-H': cmd=full_command(p,dest,'paper-k1-am-sf','off',cap)
        else:
            cmd=[BUILD/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],
                 '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
                 '--time-limit',cap-6,'--process-wall-time-limit',cap,'--process-shutdown-margin',3,
                 '--threads',1,'--mip-threads',1,'--gurobi-seed',0,'--gurobi-presolve',-1,
                 '--method','gurobi','--plain-baseline','--out',dest/'result.json','--log',dest/'native.log',
                 '--process-phase-ledger',dest/'phases.csv','--gurobi-model-export',dest/'compact.lp',
                 '--round24-expected-gurobi-model-fingerprint',expected[p['scenario_id']],
                 '--round24-executable-sha256',sha(BUILD/'ExactEBRP.exe'),
                 '--round24-manifest-executable-sha256',sha(BUILD/'ExactEBRP.exe')]
        execute(cmd,dest,{'id':identity,'arm':arm,'stage':'references','scope':'same_build_unchanged_reference'},cap,
                solver_calls='recorded_by_native_lifecycle')

def main():
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['freeze','quality','publication','fixed','micro','oracle','oracle-micro','full','k1','reference'])
    p.add_argument('--ids',nargs='+',default=['D1','D2','D3','D4','D6','D7'])
    p.add_argument('--stage',default='quality_v1')
    p.add_argument('--cap',type=int,default=120)
    p.add_argument('--modes',nargs='+',default=['off','archive','submit']); a=p.parse_args()
    if a.action=='freeze': freeze()
    elif a.action=='quality': quality(a.ids,a.stage)
    elif a.action=='publication': publication()
    elif a.action=='fixed': fixed(a.ids,a.modes,a.cap,a.stage)
    elif a.action=='micro': micro()
    elif a.action=='oracle': oracle(a.ids,a.cap)
    elif a.action=='oracle-micro': oracle_micro()
    elif a.action=='full': full(a.ids,a.cap,a.stage)
    elif a.action=='k1': full(a.ids,a.cap,a.stage,True)
    elif a.action=='reference': reference(a.ids[0],a.cap)

if __name__=='__main__': main()

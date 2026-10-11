"""Frozen R90 three-arm external confirmation using the R94 scope repair.

prepare: six build-only original references, zero Optimize.
run: one requested never-started arm; no automated restart or implicit extension.
"""
import argparse
import json
import math
import os
import subprocess
import time
from pathlib import Path

import round90_lp_g_g3 as r90
import round94_lpg_contemporary as r94
import round94_lpg_formal_recovery_v3 as scope
from round96_prepare import ROOT,OUT,read,write,sha

CAMP=OUT/'external'
REFERENCE=Path('E:/codes/ExactEBRP-round66/build/round83/v1/Round65ReferenceBuild.exe')
BIN='build/research/round90-lp-g-split/ExactEBRP.exe'
SHA='bac65ff3b5b099852f2eedd7ef462ad700e5c1131778bd56dca310b3dd0af2f2'
COMMON=read(ROOT/'results/unified_exact_round94/preregistration.json')['common']

def source_bindings():
    paths=['scripts/round96_external.py','scripts/round90_lp_g_g3.py','scripts/round88_a1_g3.py',
           'scripts/round94_lpg_contemporary.py','scripts/round94_lpg_formal_recovery_v3.py',
           'scripts/round86_native_evidence.py','scripts/analyze_round61.py','scripts/round70_affinity.py',
           'scripts/round83_audit_v2.py','scripts/round75_startup.py',
           'results/unified_exact_round96/external_protocol.md','results/unified_exact_round96/external_inputs.json']
    return {p:sha(ROOT/p) for p in paths}

def ensure_idle():
    assert not r90.foreign_heavy_processes(), 'solver or build process active'
    raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match 'round96_fixed_route|round96_.*prototype' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    assert not raw, ('R96 diagnostic/prototype active',raw)

def prepare():
    start=time.perf_counter();ensure_idle();assert sha(ROOT/BIN)==SHA
    assert not CAMP.exists(), 'do not overwrite'
    inputs=read(OUT/'external_inputs.json')['roles'];assert len(inputs)==6
    inherited=read(ROOT/'results/unified_exact_round87/campaign/identity.json')
    assert sha(REFERENCE)==inherited['reference_binary_sha256']
    oldprereg=read(ROOT/'results/unified_exact_round94/preregistration.json')
    d6,priority,unused,old=r94.modules(oldprereg)
    baseline=read(ROOT/old['frozen_priority_preregistration'])
    rows=d6.source_rows(r90,old,baseline['source_hashes'])
    blobs=d6.audit_preserved_blobs(rows,old['source_preservation_ref']);assert len(blobs)==166
    CAMP.mkdir();write(CAMP/'source_snapshot.json',dict(ref=old['source_preservation_ref'],blobs=blobs,optimizer_calls=0))
    references={};env=dict(os.environ);env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    for p in inputs:
        assert sha(ROOT/p['input_path'])==p['input_sha256'];dest=CAMP/'reference'/p['id'];dest.mkdir(parents=True)
        command=list(map(str,[REFERENCE,p['input_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],dest]))
        write(dest/'launch.json',dict(command=command,optimizer_calls=0,binary_sha256=sha(REFERENCE)))
        tick=time.perf_counter()
        with (dest/'stdout.log').open('x') as so,(dest/'stderr.log').open('x') as se:
            ret=subprocess.run(command,cwd=ROOT,env=env,stdout=so,stderr=se,timeout=30)
        write(dest/'completion.json',dict(returncode=ret.returncode,wall_seconds=time.perf_counter()-tick,optimizer_calls=0))
        assert ret.returncode==0;references[p['id']]=read(dest/'build.json');assert references[p['id']]['optimizer_calls']==0
    prereg=dict(common=COMMON,candidate_binary=BIN,candidate_binary_sha256=SHA)
    launches=[]
    for item in inputs:
        p=dict(item,reference=references[item['id']])
        for arm in p['method_order']:
            num=len(launches)+1;dest=CAMP/'raw'/f'{num:02d}_{p["id"]}_{arm}'
            command=(r90.audited_runner_utilities.command_for(prereg,p,arm,dest) if arm=='P-GRB' else r90.command_for(prereg,p,arm,dest))
            launches.append(dict(number=num,id=p['id'],arm=arm,stage='external',panel=p,
                destination=str(dest),cap_seconds=p['cap_seconds'],hard_stop_seconds=p['cap_seconds']-2,command=command))
    assert len(launches)==18 and sum(r['cap_seconds'] for r in launches)==59400
    for rid in references:
        pair=[r['command'].copy() for r in launches if r['id']==rid and r['arm']!='P-GRB']
        for c in pair:
            for flag in ['--round90-lp-g-split','--out','--log','--process-phase-ledger','--external-gini-artifact-dir',
                         '--primal-heuristic-generation-log','--progress-log','--native-evidence-dir']:
                c[c.index(flag)+1]='<only-permitted-difference>'
        assert pair[0]==pair[1]
    write(CAMP/'identity.json',dict(candidate_binary_sha256=SHA,source_ref=old['source_preservation_ref'],
        source_snapshot_sha256=sha(CAMP/'source_snapshot.json'),references=references,launches=launches,
        bindings=source_bindings(),prereg_sha256=sha(OUT/'external_inputs.json'),runner_sha256=sha(__file__),
        reference_binary_sha256=sha(REFERENCE),prepared_unix=time.time(),optimizer_calls=0,
        elapsed_before_write=time.perf_counter()-start))

def completed():
    path=CAMP/'summary.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

def run(number):
    ensure_idle();identity=read(CAMP/'identity.json');assert source_bindings()==identity['bindings']
    assert sha(ROOT/BIN)==SHA==identity['candidate_binary_sha256']
    gate=read(OUT/'external_admission.json')
    assert gate['admitted'] is True and gate['identity_sha256']==sha(CAMP/'identity.json')
    records=completed();assert len(records)==number-1 and all(r['audit_passed'] for r in records)
    launch=identity['launches'][number-1];assert launch['number']==number
    assert not Path(launch['destination']).exists(), 'never rerun a paid prefix'
    assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
    r90.CAMPAIGN=CAMP;r90.audit_launch=scope.audit_adapter(r90)
    prereg=dict(common=COMMON,candidate_binary=BIN,candidate_binary_sha256=SHA)
    result=r90.run_one(launch,prereg,identity)
    records.append(result);same=[r for r in records if r['id']==launch['id']]
    lower=[];upper=[]
    for row in same:
        audit=read(Path(row['destination'])/'audit.json');assert audit['passed']
        lower.extend(x for x in (audit['LB'],row['endpoint']['L']) if x is not None)
        upper.extend(w['F'] for w in audit['witnesses'])
        if audit.get('final_physical_verification'):upper.append(audit['final_physical_verification']['F'])
    assert not upper or max(lower)<=min(upper)+1e-7,'cross-arm contradiction'
    write(CAMP/f'cross_arm_{launch["id"]}_{len(same)}.json',dict(passed=True,
        strongest_L=max(lower),best_physical_U=min(upper) if upper else None,
        scope='offline consistency only; never combined certificate'))
    if len(same)==3:
        write(CAMP/f'decision_signals_{launch["id"]}.json',dict(signals=r94.severe_signals(records,launch['id']),
            action='retain all outcomes; no algorithm-specific fallback or unscheduled extensions'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);parser.add_argument('--number',type=int)
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    else:
        assert args.number and 1<=args.number<=18;run(args.number)

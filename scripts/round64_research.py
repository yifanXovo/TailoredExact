"""Bounded serial Round64 driver. No input names or results select runtime policy."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import time
import round61_research as runner

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/os.environ.get('EBRP_ROUND64_RESULTS','results/gf_shared_load_time_round64')
if not OUT.resolve().is_relative_to(ROOT.resolve()):raise RuntimeError('output outside checkout')
RAW=OUT/'local_raw';BUILD=ROOT/'build/round64'
sha=runner.sha;write=runner.write
def bind():
    runner.ROOT=ROOT;runner.OUT=OUT;runner.RAW=RAW;runner.BUILD=BUILD;runner.LEDGER=OUT/'processes.jsonl'
bind()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def panel():return {p['id']:p for p in read(OUT/'protocol.json')['panel']}
def freeze():
    if (OUT/'protocol.json').exists():raise RuntimeError('already frozen')
    old=read(ROOT/'results/gf_cumulative_time_resource_round63/protocol.json')
    lookup={p['id']:p for p in old['panel']}
    selected=[dict(lookup[i],stage='development',role='inherited development/protection') for i in ['D3','D4','D6','D7','C2','C3','C5']]
    source=ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/round58_primary_panel.csv'
    metadata=list(csv.DictReader(source.open(encoding='utf-8-sig',newline='')))
    confirmations=[('C6','cb443_V50_compact_r1_shortage_M04_Q30_T01800','V50 shortage short-T; anticipated nonzero/proof difficult'),
                   ('C7','cb443_V20_regional_r2_balanced_M02_Q20_T10800','regional, balanced, Q20 and intermediate operating horizon')]
    for identity,scenario,role in confirmations:
        p=dict(next(p for p in metadata if p['scenario_id']==scenario))
        p.update(id=identity,stage='confirmation',role=role,input_sha256=p['instance_file_sha256'])
        selected.append(p)
    for p in selected:
        p['lambda']=float(p.get('lambda',.15))
        # Read-only identity check is not candidate performance or selection.
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
    assert int(lookup['D3']['T_seconds'])==2850 and int(lookup['D4']['T_seconds'])==2400
    write(OUT/'protocol.json',dict(frozen_unix=time.time(),base_pr=124,
        base_branch='codex/round63-cumulative-time-resource',base_commit='f734d6781fd7125703489245cdb4dc27fb74625c',
        round63_service_source='b1bde3eab6c6fb9c4e1c4575acbdfa9141a46eaf',
        round63_resource_source='dc8d3e4a0ee3f63f0858b2c3b38a59a92cd1e783',panel=selected,
        solver=old['solver'],frozen_outer=old['frozen_outer'],decision=old['decision'],
        budget=dict(maximum_charged_launches=72,native_micro_maximum=4,optimizer_concurrency=1,
                    reserved_final_minimum=22,maximum_1800=4,maximum_3600=2),
        initial_allocation=dict(structure=4,native_micro=4,cold_execution=12,warm_lifecycle=4,long_full_references_confirmation=22,reserve=26),
        structural_batch=dict(arms=['off','q','t','sep','joint','pinned_sep','pinned_joint'],maximum_internal_optimizations=7,
                              common_cap_seconds=120,all_F0_variables_pinned=True,new_auxiliaries_free=True),
        startup=dict(cold='inherited simple greedy',warm='inherited stable full HGA; each formal process pays construction/verification',
                     native_start='disabled identically; only incumbent/cutoff/domain changes',archive='off',PREFIX='off'),
        formulation=dict(modes=['off','q','t','sep','joint'],scope='canonical LP and MIP global physical',
                         lifecycle='unchanged controlled per-leaf model-object reuse',callback='off',PreCrush='unchanged'),
        confirmation=dict(source_sha256=sha(source),selection='published metadata; chosen before Round64 performance',
                          order=['C6','C7'],no_posthoc_replacement=True),
        long_required_pairs=['C5','D7','C6'],separate_D4_protection=True))

def build_freeze(version):
    filename='build_freeze_'+version+'.json'
    if (OUT/filename).exists():raise RuntimeError('cannot overwrite measured build')
    write(OUT/filename,dict(version=version,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        executables={p.name:sha(p) for p in sorted(BUILD.glob('*.exe'))},
        source_files={str(p.relative_to(ROOT)):sha(p) for directory in ['src','include','tests'] for p in sorted((ROOT/directory).glob('*')) if p.is_file()},
        cmake_sha256=sha(ROOT/'CMakeLists.txt'),tests_sha256=sha(BUILD/'tests.log'),protocol_sha256=sha(OUT/'protocol.json')))
    write(OUT/'active_build.json',dict(file=filename,sha256=sha(OUT/filename)))

def execute(cmd,dest,p,arm,stage,cap,kind='performance',calls=1):
    bind();entries=runner.entries()
    if p.get('stage')=='confirmation':
        freeze=read(OUT/'confirmation_freeze.json')
        for path,key in [(OUT/'active_build.json','active_build_sha256'),(Path(__file__),'driver_sha256'),
                         (OUT/'protocol.json','protocol_sha256'),(OUT/'selected_candidate.json','selection_sha256')]:
            assert sha(path)==freeze[key]
        if arm not in freeze['allowed_arms']:raise RuntimeError('confirmation arm changed')
        if kind!='build-only' and cap!=freeze['cap_seconds']:raise RuntimeError('confirmation cap changed')
        if p['id']=='C7' and not any(e['id']=='C6' and e['charged'] for e in entries):raise RuntimeError('C6 must open first')
    if 'input_sha256' in p:assert sha(ROOT/p['instance_path'])==p['input_sha256']
    if kind!='build-only':
        active=read(OUT/'active_build.json');assert sha(OUT/active['file'])==active['sha256']
        frozen=read(OUT/active['file']);assert sha(cmd[0])==frozen['executables'][Path(cmd[0]).name]
        for seconds,maximum in [(1800,4),(3600,2)]:
            if cap==seconds and sum(e['charged'] and e['cap_seconds']==seconds for e in entries)>=maximum:raise RuntimeError('long cap exhausted')
    runner.execute(cmd,dest,dict(id=p['id'],arm=arm,stage=stage,build_freeze=None if kind=='build-only' else active['file']),cap,kind,calls)
    if (dest/'result.json').exists():
        result=read(dest/'result.json');status=result.get('status','')
        if status=='failed' or status.endswith('_failed'):raise RuntimeError('charged semantic failure '+status)

def fixed(ids,modes,cap,stage,build):
    for identity in ids:
        p=panel()[identity]
        for mode in modes:
            dest=RAW/stage/identity/mode
            cmd=runner.fixed_command(p,dest,'off',cap,build)+['--round64-shared-mode',mode]
            execute(cmd,dest,p,mode,stage,cap,'build-only' if build else 'performance',0 if build else 1)

def probe(ids,cap,stage,micro=False):
    for identity in (['resource_micro'] if micro else ids):
        p=dict(id=identity) if micro else panel()[identity];dest=RAW/stage/identity
        cmd=[BUILD/'Round64ResourceProbe.exe','--out',dest,'--cap',cap]
        if micro:cmd+=['--micro']
        else:
            source=RAW/'preflight_v1'/identity/'off'/'canonical_model.lp'
            cmd+=['--input',p['instance_path'],'--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
                  '--model',source,'--expected-sha',sha(source)]
        execute(cmd,dest,p,'five-LP-and-pinned-controls',stage,cap,'native-micro' if micro else 'LP',7)

def full(ids,modes,cap,stage,warm=False,single=False):
    preset='research-round64-k1-h' if warm else 'research-round64-single-s' if single else 'research-round64-k1-s'
    for identity in ids:
        p=panel()[identity]
        for mode in modes:
            arm=('warm' if warm else 'single' if single else 'cold')+'-'+mode;dest=RAW/stage/identity/arm
            cmd=runner.full_command(p,dest,preset,'off',cap)+['--round64-shared-mode',mode,'--ub-event-log',dest/'ub_events.csv']
            execute(cmd,dest,p,arm,stage,cap,calls='all calls in external/paper_optimize_ledger.csv')

def projection(ids,cap,stage):
    for identity in ids:
        p=panel()[identity];dest=RAW/stage/identity
        pins=RAW/'strength_v1'/identity/'original_pins.csv'
        cmd=[BUILD/'Round64ProjectionAudit.exe','--input',p['instance_path'],'--T',p['T_seconds'],
             '--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--pins',pins,
             '--expected-sha',sha(pins),'--expected-resource-identity',read(pins.parent/'resource.json')['identity'],'--out',dest,'--cap',cap]
        execute(cmd,dest,p,'SEP-JOINT-Farkas',stage,cap,'LP-audit',2)

def full_micro(stage,cap):
    p=dict(id='full_micro',instance_path='tests/data/round59_tiny.txt',T_seconds=5,pickup_seconds=1,drop_seconds=1,**{'lambda':.15})
    for mode in ['off','joint']:
        dest=RAW/stage/p['id']/mode
        cmd=runner.full_command(p,dest,'research-round64-k1-s','off',cap)+['--round64-shared-mode',mode]
        execute(cmd,dest,p,mode,stage,cap,'native-micro','all calls in external/paper_optimize_ledger.csv')

def warm_micro(stage,cap):
    p=dict(id='warm_micro',instance_path='tests/data/round59_tiny.txt',T_seconds=5,pickup_seconds=1,drop_seconds=1,**{'lambda':.15})
    dest=RAW/stage/p['id']
    cmd=runner.full_command(p,dest,'research-round64-k1-h','off',cap)+['--round64-shared-mode','joint','--ub-event-log',dest/'ub_events.csv']
    execute(cmd,dest,p,'warm-joint',stage,cap,'native-micro','all calls in external/paper_optimize_ledger.csv')

def reference(ids,cap,stage):
    expected={e['instance_id']:e['expected_gurobi_model_fingerprint'] for e in read(
        ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json')['entries']}
    for identity in ids:
        p=panel()[identity]
        for arm in ['P-GRB','K1-H']:
            dest=RAW/stage/identity/arm
            if arm=='K1-H':cmd=runner.full_command(p,dest,'paper-k1-am-sf','off',cap)+['--ub-event-log',dest/'ub_events.csv']
            else:cmd=[BUILD/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],'--T',p['T_seconds'],
                '--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--time-limit',cap-6,
                '--process-wall-time-limit',cap,'--process-shutdown-margin',3,'--threads',1,'--mip-threads',1,
                '--gurobi-seed',0,'--gurobi-presolve',-1,'--method','gurobi','--plain-baseline',
                '--out',dest/'result.json','--log',dest/'native.log','--process-phase-ledger',dest/'phases.csv',
                '--gurobi-model-export',dest/'compact.lp','--round24-expected-gurobi-model-fingerprint',expected[p['scenario_id']],
                '--round24-executable-sha256',sha(BUILD/'ExactEBRP.exe'),'--round24-manifest-executable-sha256',sha(BUILD/'ExactEBRP.exe')]
            execute(cmd,dest,p,arm,stage,cap,calls='actual unchanged native lifecycle')

def confirm_freeze(mode,cap):
    if (OUT/'confirmation_freeze.json').exists():raise RuntimeError('already frozen')
    if any(e['id'] in ['C6','C7'] for e in runner.entries()):raise RuntimeError('confirmation already opened')
    selected=read(OUT/'selected_candidate.json');assert selected['mode']==mode
    write(OUT/'confirmation_freeze.json',dict(frozen_unix=time.time(),mode=mode,cap_seconds=cap,
        allowed_arms=['off',mode,'cold-off','cold-'+mode,'warm-off','warm-'+mode,'P-GRB','K1-H'],
        active_build_sha256=sha(OUT/'active_build.json'),driver_sha256=sha(Path(__file__)),
        protocol_sha256=sha(OUT/'protocol.json'),selection_sha256=sha(OUT/'selected_candidate.json')))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','build-freeze','build','fixed','probe','micro','full-micro','warm-micro','projection','cold','warm','single','reference','confirm-freeze'])
    parser.add_argument('--ids',nargs='+',default=['D4']);parser.add_argument('--modes',nargs='+',default=['off']);parser.add_argument('--cap',type=int,default=120)
    parser.add_argument('--stage',default='preflight');parser.add_argument('--version',default='v1');a=parser.parse_args()
    if a.action=='freeze':freeze()
    elif a.action=='build-freeze':build_freeze(a.version)
    elif a.action=='confirm-freeze':confirm_freeze(a.modes[0],a.cap)
    elif a.action in ['build','fixed']:fixed(a.ids,a.modes,a.cap,a.stage,a.action=='build')
    elif a.action in ['probe','micro']:probe(a.ids,a.cap,a.stage,a.action=='micro')
    elif a.action=='projection':projection(a.ids,a.cap,a.stage)
    elif a.action=='full-micro':full_micro(a.stage,a.cap)
    elif a.action=='warm-micro':warm_micro(a.stage,a.cap)
    elif a.action=='reference':reference(a.ids,a.cap,a.stage)
    else:full(a.ids,a.modes,a.cap,a.stage,a.action=='warm',a.action=='single')
if __name__=='__main__':main()

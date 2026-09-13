"""Bounded, serial Round63 campaign. No results or answers select algorithm rules."""
import argparse
import csv
import json
import os
from pathlib import Path
import time
import round61_research as runner

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/os.environ.get('EBRP_ROUND63_RESULTS','results/gf_cumulative_time_resource_round63')
if not OUT.resolve().is_relative_to(ROOT.resolve()): raise RuntimeError('output outside checkout')
RAW=OUT/'local_raw'; BUILD=ROOT/'build/round63'
def bind_runner():
    runner.ROOT=ROOT; runner.OUT=OUT; runner.RAW=RAW; runner.BUILD=BUILD; runner.LEDGER=OUT/'processes.jsonl'
bind_runner()
sha=runner.sha; write=runner.write

def freeze():
    if (OUT/'protocol.json').exists(): raise RuntimeError('already frozen')
    old=json.loads((ROOT/'results/gf_passive_threshold_conflicts_round62/protocol.json').read_text(encoding='utf-8'))
    lookup={p['id']:p for p in old['panel']}
    panels=[dict(lookup[i],stage='development') for i in ['D3','D4','D6','D7','C2','C3']]
    sources={}
    # Choose using published metadata only, before parsing either confirmation input.
    # Exclude all Round62 inputs, including its public C1/C3 confirmations.
    excluded={p['instance_path'] for p in old['panel']}
    for identity,filename,V in [('C4','round58_primary_panel.csv',20),('C5','round58_matched_T_panel.csv',50)]:
        source=ROOT/'results/gf_citibike443_k1_vs_pgrb_round58'/filename
        rows=list(csv.DictReader(source.open(encoding='utf-8-sig',newline='')))
        eligible=[p for p in rows if int(p['V'])==V and p['instance_path'] not in excluded]
        if identity=='C5': eligible=[p for p in eligible if float(p['T_seconds'])==18000]
        p=dict(sorted(eligible,key=lambda p:p['scenario_id'])[0])
        p.update(id=identity,stage='confirmation',input_sha256=p['instance_file_sha256'],
                 role='previously public; no Round63 performance opened before candidate freeze')
        panels.append(p); excluded.add(p['instance_path']); sources[filename]=sha(source)
    for p in panels:
        p['lambda']=float(p.get('lambda',.15))
        if p['stage']=='development': assert sha(ROOT/p['instance_path'])==p['input_sha256']
    assert int(lookup['D3']['T_seconds'])==2850 and int(lookup['D4']['T_seconds'])==2400
    write(OUT/'protocol.json',dict(frozen_unix=time.time(),base_commit='71e955acad596acba2a9e74e738173113116d9f7',
        base_branch='codex/round62-passive-threshold-conflicts',base_pr=123,
        round62_measured_commit='7936ed53951113297df07d2fb243954e2f784906',
        original_workspace_head='4a9cbd0e3d43870e953b3a6678b343a9ac4fc25a',
        remote_main='1459308492a5eceed523dee53b5f9d79141b5242',panel=panels,
        solver=old['solver'],frozen_outer=old['frozen_outer'],decision=old['decision'],
        threshold_generator=old['thresholds'],archive='off in all core A/B arms',
        qualification='relative to actual OFF: no certificate loss or dual-threshold regression on protection/confirmation; at least one qualifying improvement. Historical best research arm is descriptive, not an additional veto. Round62 gates unchanged.',
        budget=dict(maximum_charged_launches=72,native_micro_maximum=4,reserved_final=20,
                    service_supplement_target=10,maximum_1800=4,maximum_3600=2,optimizer_concurrency=1),
        initial_allocation=dict(A=10,B_strength_and_micro=10,B_execution_screen=12,
                                final_long_K1_references_confirmation=20,adaptive_reserve=20),
        confirmation_selection=dict(sources=sources,rule='lexicographically first eligible scenario_id; exclude all Round62 inputs; C4 V20 primary, C5 V50 matched T18000',
                                    opening_order=['C4','C5'],status='metadata selected; inputs unopened'),
        separation=dict(normalized_violation_tolerance=1e-7,negative_input_tolerance=1e-8,
            max_queries_per_model=64,max_rows_per_model=256,root_callback_queries=16,
            tree_node_stride=64,max_total_callback_queries=64,one_cut_per_vehicle_per_query=True,
            dominance='identical physical family/vehicle/support deduplication; no cross-support dominance claim',
            scope='global physical T and safely rounded shortest lower bounds')))

def panel(): return {p['id']:p for p in json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))['panel']}

def build_freeze(version):
    filename='build_freeze_'+version+'.json'
    if (OUT/filename).exists(): raise RuntimeError('cannot overwrite build freeze')
    write(OUT/filename,dict(version=version,executables=[dict(name=p.name,sha256=sha(p)) for p in sorted(BUILD.glob('*.exe'))],
        source_files={str(p.relative_to(ROOT)):sha(p) for directory in ['src','include'] for p in sorted((ROOT/directory).glob('*')) if p.is_file()},
        tests_sha256=sha(BUILD/'tests.log'),protocol_sha256=sha(OUT/'protocol.json')))
    write(OUT/'active_build.json',dict(file=filename,sha256=sha(OUT/filename)))

def execute(cmd,dest,p,arm,stage,cap,kind='performance',calls=1):
    bind_runner()
    if p.get('stage')=='confirmation':
        if not (OUT/'confirmation_freeze.json').exists():raise RuntimeError('confirmation closed')
        frozen=json.loads((OUT/'confirmation_freeze.json').read_text())
        assert sha(OUT/'active_build.json')==frozen['active_build_sha256']
        assert sha(Path(__file__))==frozen['driver_sha256']
        allowed=['off',frozen['resource_mode']] if kind=='build-only' else frozen['allowed_arms']
        if arm not in allowed:raise RuntimeError('arm outside confirmation freeze')
        if cap!=frozen['cap_seconds'] and kind!='build-only':raise RuntimeError('confirmation cap changed')
        if p['id']=='C5' and not any(e['id']=='C4' for e in runner.entries()):raise RuntimeError('C4 must open first')
    if 'input_sha256' in p: assert sha(ROOT/p['instance_path'])==p['input_sha256']
    entries=runner.entries()
    for seconds,maximum in [(1800,4),(3600,2)]:
        if cap==seconds and sum(e['charged'] and e['cap_seconds']==seconds for e in entries)>=maximum: raise RuntimeError('long cap exhausted')
    build=None
    if kind!='build-only':
        active=json.loads((OUT/'active_build.json').read_text()); build=active['file']
        assert sha(OUT/build)==active['sha256']
        expected={p['name']:p['sha256'] for p in json.loads((OUT/build).read_text())['executables']}
        assert sha(cmd[0])==expected[Path(cmd[0]).name]
    runner.execute(cmd,dest,dict(id=p['id'],arm=arm,stage=stage,build_freeze=build),cap,kind,calls)
    result=dest/'result.json'
    if result.exists():
        status=json.loads(result.read_text(encoding='utf-8')).get('status','')
        if status=='failed' or status.endswith('_failed'):
            raise RuntimeError('charged semantic engine failure: '+status+' at '+str(dest))

def fixed(ids,modes,cap,stage,kind):
    bind_runner()
    for identity in ids:
        p=panel()[identity]
        for mode in modes:
            dest=RAW/stage/identity/mode
            cmd=runner.fixed_command(p,dest,'off',cap,kind=='build')
            cmd[cmd.index('--mode')+1]=kind
            cmd+=['--round63-time-mode',mode]
            execute(cmd,dest,p,mode,stage,cap,'build-only' if kind=='build' else 'LP' if kind=='lp' else 'performance',
                    0 if kind=='build' else 2 if kind=='solve' and mode in ['root','root-dry'] else 1)

def full(ids,modes,cap,stage,k1,threshold='off'):
    bind_runner()
    for identity in ids:
        p=panel()[identity]
        for mode in modes:
            arm=('K1' if k1 else 'Single')+'-'+threshold+'-'+mode
            dest=RAW/stage/identity/arm
            cmd=runner.full_command(p,dest,'research-round59-k1-s' if k1 else 'research-round59-f0-single-s','off',cap)
            cmd+=['--round62-threshold-mode',threshold,'--round63-time-mode',mode]
            execute(cmd,dest,p,arm,stage,cap,calls='all calls in external/paper_optimize_ledger.csv')

def reference(ids,cap,stage):
    bind_runner()
    expected={e['instance_id']:e['expected_gurobi_model_fingerprint'] for e in json.loads(
        (ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json').read_text())['entries']}
    for identity in ids:
        p=panel()[identity]
        for arm in ['P-GRB','K1-H']:
            dest=RAW/stage/identity/arm
            if arm=='K1-H':cmd=runner.full_command(p,dest,'paper-k1-am-sf','off',cap)
            else:
                cmd=[BUILD/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],'--T',p['T_seconds'],
                    '--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--time-limit',cap-6,
                    '--process-wall-time-limit',cap,'--process-shutdown-margin',3,'--threads',1,'--mip-threads',1,
                    '--gurobi-seed',0,'--gurobi-presolve',-1,'--method','gurobi','--plain-baseline',
                    '--out',dest/'result.json','--log',dest/'native.log','--process-phase-ledger',dest/'phases.csv',
                    '--gurobi-model-export',dest/'compact.lp','--round24-expected-gurobi-model-fingerprint',expected[p['scenario_id']],
                    '--round24-executable-sha256',sha(BUILD/'ExactEBRP.exe'),
                    '--round24-manifest-executable-sha256',sha(BUILD/'ExactEBRP.exe')]
            execute(cmd,dest,p,arm,stage,cap,calls='native lifecycle / original single P-GRB')

def service(ids,cap,stage,build=False):
    """The unchanged Round62 dictionary; three same-lifecycle arms per role."""
    bind_runner()
    for identity in ids:
        for threshold in ['off','projection','projection-service']:
            if build:
                p=panel()[identity];dest=RAW/stage/identity/threshold
                cmd=runner.fixed_command(p,dest,'off',cap,True)+['--round62-threshold-mode',threshold]
                execute(cmd,dest,p,threshold,stage,cap,'build-only',0)
            else:full([identity],['off'],cap,stage,identity in ['C2','C3'],threshold)

def confirm_freeze(mode,cap):
    if mode not in ['explicit','root','coupled']:raise RuntimeError('freeze one developed resource execution')
    path=OUT/'confirmation_freeze.json'
    if path.exists():raise RuntimeError('confirmation already frozen')
    if any(e['id'] in ['C4','C5'] for e in runner.entries()):raise RuntimeError('confirmation already opened')
    candidate=OUT/'selected_candidate.json'
    if not candidate.exists():raise RuntimeError('write reviewable selection rationale first')
    selected=json.loads(candidate.read_text());assert selected['resource_mode']==mode
    active=json.loads((OUT/'active_build.json').read_text())
    write(path,dict(frozen_unix=time.time(),resource_mode=mode,cap_seconds=cap,
        allowed_arms=['K1-off-off','K1-off-'+mode,'K1-H','P-GRB'],threshold_mode='off',
        active_build_sha256=sha(OUT/'active_build.json'),build_freeze=active,
        driver_sha256=sha(Path(__file__)),protocol_sha256=sha(OUT/'protocol.json'),
        selection_sha256=sha(candidate),opening_order=['C4','C5'],
        previous_evidence_charged=[e['charged_number'] for e in runner.entries() if e['charged']],
        uniformity='one frozen execution, no per-instance fallback/winner selection',
        source_status='previously public; not used in Round63 selection; no sealed-new claim'))

def coupling(ids,cap,stage):
    for identity in ids:
        p=panel()[identity];dest=RAW/stage/identity
        source=RAW/'preflight_v4'/identity/'off'/'canonical_model.lp'
        cmd=[BUILD/'Round63ResourceProbe.exe','--coupling-probe','--input',p['instance_path'],
             '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],
             '--model',source,'--expected-sha',sha(source),'--out',dest,'--cap',cap]
        execute(cmd,dest,p,'explicit-carried-load-LP',stage,cap,'LP',4)

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','build-freeze','build','lp','solve','full','k1','reference','service','service-build','confirm-freeze','coupling'])
    p.add_argument('--ids',nargs='+',default=['D4']);p.add_argument('--modes',nargs='+',default=['off'])
    p.add_argument('--version',default='v1');p.add_argument('--cap',type=int,default=120)
    p.add_argument('--stage',default='dev');p.add_argument('--threshold',default='off');a=p.parse_args()
    if a.action=='freeze': freeze()
    elif a.action=='build-freeze': build_freeze(a.version)
    elif a.action=='confirm-freeze':confirm_freeze(a.modes[0],a.cap)
    elif a.action=='coupling':coupling(a.ids,a.cap,a.stage)
    elif a.action in ['build','lp','solve']: fixed(a.ids,a.modes,a.cap,a.stage,a.action)
    elif a.action=='reference':reference(a.ids,a.cap,a.stage)
    elif a.action in ['service','service-build']:service(a.ids,a.cap,a.stage,a.action=='service-build')
    else: full(a.ids,a.modes,a.cap,a.stage,a.action=='k1',a.threshold)
if __name__=='__main__': main()

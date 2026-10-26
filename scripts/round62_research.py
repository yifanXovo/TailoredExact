"""Round62 bounded serial experiments; reuse the write-ahead Round61 runner."""
import argparse
import csv
import json
import os
from pathlib import Path
import round61_research as previous

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/os.environ.get('EBRP_ROUND62_RESULTS','results/gf_passive_threshold_conflicts_round62')
if not OUT.resolve().is_relative_to(ROOT.resolve()):raise RuntimeError('Round62 output must stay inside this checkout')
RAW=OUT/'local_raw'
BUILD=ROOT/'build/round62'
previous.OUT=OUT;previous.RAW=RAW;previous.BUILD=BUILD;previous.LEDGER=OUT/'processes.jsonl'
sha=previous.sha;write=previous.write

def freeze():
    if (OUT/'protocol.json').exists():raise RuntimeError('already frozen')
    old=json.loads((ROOT/'results/gf_transfer_block_native_time_round61/protocol.json').read_text(encoding='utf-8'))
    panels={p['id']:p for p in old['panel']};selected=[]
    for identity in ['D1','D3','D4','D6','D7','C2','C1']:
        p=dict(panels[identity]);p['stage']='confirmation' if identity=='C1' else 'development'
        p['round62_role']='not used for Round62 selection; previously public' if identity=='C1' else ('known regression used for development' if identity=='C2' else p['role'])
        selected.append(p)
    source=ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/round58_primary_panel.csv'
    rows=list(csv.DictReader(source.open(encoding='utf-8-sig',newline='')))
    eligible=[p for p in rows if int(p['V'])==30 and p['instance_path'] not in {x['instance_path'] for x in selected}]
    p=dict(sorted(eligible,key=lambda p:p['scenario_id'])[0]);p.update(id='C3',stage='confirmation',
        round62_role='V30; not used for Round62 selection; previously public',input_sha256=p['instance_file_sha256'])
    selected.append(p)
    for p in selected:
        assert sha(ROOT/p['instance_path'])==p['input_sha256']
        p['lambda']=float(p.get('lambda',.15))
    assert int(panels['D3']['T_seconds'])==2850 and int(panels['D4']['T_seconds'])==2400
    write(OUT/'protocol.json',dict(base_commit='4a9cbd0e3d43870e953b3a6678b343a9ac4fc25a',
        base_branch='codex/round61-transfer-block-native-time-oracle',remote_pr122_head='4a9cbd0e3d43870e953b3a6678b343a9ac4fc25a',
        remote_main='1459308492a5eceed523dee53b5f9d79141b5242',panel=selected,
        solver=old['solver'],frozen_outer=old['frozen_outer'],PREFIX=old['PREFIX'],decision=old['decision'],
        thresholds=dict(initial_events='maximal feasible quantity per station/direction',candidate_limit='2*V',
            clique_search_nodes=50000,raw_conflicts=64,final_conflicts=32,weakening_checks=4096,
            weakening='ascending station/direction; binary search; reprove every edge and vehicle union',
            numerical_margin='1e-5*max(1,T)',scope='global physical domains; no LP/local/cutoff premises'),
        budget=dict(maximum_charged=72,maximum_native_micro=4,maximum_1800=4,maximum_3600=2,
            long_confirmation_reserved=14,optimizer_concurrency=1,compilation_concurrent=False),
        confirmation_selection=dict(C1='retained public Round61 confirmation; not used for Round62 selection',
            C3='lexicographically first V30 Round58 primary scenario on an input absent from development panel',source_sha256=sha(source))))

def panel():return {p['id']:p for p in json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))['panel']}

def execute(cmd,dest,p,arm,stage,cap,kind='performance',calls=1):
    if p.get('stage')=='confirmation' and not (OUT/'confirmation_freeze.json').exists():raise RuntimeError('confirmation is not open')
    if 'input_sha256' in p:assert sha(ROOT/p['instance_path'])==p['input_sha256']
    ledger=previous.entries()
    if kind!='build-only' and not (OUT/'build_freeze.json').exists():raise RuntimeError('freeze build before performance')
    if cap==1800 and sum(e['cap_seconds']==1800 for e in ledger)>=4:raise RuntimeError('1800 cap exhausted')
    if cap==3600 and sum(e['cap_seconds']==3600 for e in ledger)>=2:raise RuntimeError('3600 cap exhausted')
    frozen_name=json.loads((OUT/'active_build.json').read_text())['file'] if (OUT/'active_build.json').exists() else 'build_freeze.json'
    if kind!='build-only':
        frozen=json.loads((OUT/frozen_name).read_text());expected={e['name']:e['sha256'] for e in frozen['executables']}
        if Path(cmd[0]).name in expected and sha(cmd[0])!=expected[Path(cmd[0]).name]:raise RuntimeError('executable differs from active frozen build')
    previous.execute(cmd,dest,dict(id=p['id'],arm=arm,stage=stage,build_freeze=frozen_name),cap,kind,calls)

def fixed(ids,modes,cap,stage,kind):
    for identity in ids:
        p=panel()[identity]
        for mode in modes:
            dest=RAW/stage/identity/mode;cmd=previous.fixed_command(p,dest,'off',cap,kind=='build')
            cmd[cmd.index('--state-id')+1]=identity+'-F0-'+mode
            cmd[cmd.index('--mode')+1]=kind;cmd+=['--round62-threshold-mode',mode]
            execute(cmd,dest,p,mode,stage,cap,'build-only' if kind=='build' else 'LP' if kind=='lp' else 'performance',0 if kind=='build' else 1)

def full(ids,modes,threshold,cap,stage,k1):
    for identity in ids:
        p=panel()[identity]
        for mode in modes:
            arm=('K1-' if k1 else 'Single-')+mode+'-'+threshold;dest=RAW/stage/identity/arm
            cmd=previous.full_command(p,dest,'research-round59-k1-s' if k1 else 'research-round59-f0-single-s',mode,cap)
            cmd+=['--round62-threshold-mode',threshold]
            execute(cmd,dest,p,arm,stage,cap,calls='all native calls in external/paper_optimize_ledger.csv')

def proof(ids,stage):
    for identity in ids:
        p=panel()[identity];dest=RAW/stage/identity
        cmd=[BUILD/'Round62ThresholdProbe.exe','--input',p['instance_path'],'--T',p['T_seconds'],
             '--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--out',dest]
        if identity=='D4':cmd+=['--events','1:-1:5,2:1:1,3:1:6,6:1:6'] # explicit diagnostic only
        execute(cmd,dest,p,'automatic-thresholds',stage,20,'proof',0)

def reference(identity,cap,stage='references'):
    p=panel()[identity]
    expected={e['instance_id']:e['expected_gurobi_model_fingerprint'] for e in json.loads(
        (ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json').read_text())['entries']}
    for arm in ['P-GRB','K1-H']:
        dest=RAW/stage/identity/arm
        if arm=='K1-H':cmd=previous.full_command(p,dest,'paper-k1-am-sf','off',cap)
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

def oracle_pair(identity='D4',cap=120,stage='threshold_oracle'):
    p=panel()[identity]
    evidence=json.loads((RAW/'proof_v1'/identity/'generated.json').read_text())
    events=evidence['conflicts'][0]['events']
    event_argument=','.join(f"{e['station']}:{e['direction']}:{e['q']}" for e in events)
    for mode in ['cheap','force-native']:
        dest=RAW/stage/identity/mode
        cmd=[BUILD/'Round61TimeOracle.exe','--input',p['instance_path'],'--out',dest,'--T',p['T_seconds'],
            '--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--lambda',p['lambda'],
            '--mode','mip','--cap',cap,'--threshold-decision','--thresholds',event_argument]
        if mode=='force-native':cmd+=['--force-native']
        execute(cmd,dest,p,mode,stage,cap,'oracle',0 if mode=='cheap' else 1)


def projection_audit(ids,cap=120,stage='projection_audit'):
    for identity in ids:
        p=panel()[identity];dest=RAW/stage/identity
        source=RAW/'mip_v2'/identity/'off'/'canonical_model.lp'
        model=previous.json.loads((source.parent/'model_fingerprint.json').read_text())
        assert sha(source)==model['sha256']
        cmd=[BUILD/'Round62ProjectionAudit.exe','--input',p['instance_path'],
             '--model',source,'--expected-model-sha256',sha(source),'--out',dest,
             '--T',p['T_seconds'],'--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--cap',cap]
        execute(cmd,dest,p,'projection-containment',stage,cap,'LP-audit','at most 33; native_calls.csv and audit_result.json')

def build_freeze(version):
    name='build_freeze.json' if version=='v1' else 'build_freeze_'+version+'.json'
    if (OUT/name).exists():raise RuntimeError('never overwrite build freeze')
    write(OUT/name,dict(executables=[dict(name=n,sha256=sha(BUILD/n)) for n in
        ['ExactEBRP.exe','Round50IntervalMipExperiment.exe','Round61TimeOracle.exe','Round62ThresholdProbe.exe','Round62NativeMicro.exe','Round62ProjectionAudit.exe'] if (BUILD/n).exists()],
        source_files={str(p.relative_to(ROOT)):sha(p) for folder in ['src','include'] for p in sorted((ROOT/folder).glob('*')) if p.is_file()},
        tests_sha256=sha(BUILD/'tests.log')))
    write(OUT/'active_build.json',dict(file=name,sha256=sha(OUT/name)))

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','build-freeze','build','lp','solve','full','k1','proof'])
    p.add_argument('--ids',nargs='+',default=['D4']);p.add_argument('--modes',nargs='+',default=['off'])
    p.add_argument('--build-id',default='v1')
    p.add_argument('--threshold',default='off');p.add_argument('--cap',type=int,default=120);p.add_argument('--stage',default='dev');a=p.parse_args()
    if a.action=='freeze':freeze()
    elif a.action=='build-freeze':build_freeze(a.build_id)
    elif a.action in ['build','lp','solve']:fixed(a.ids,a.modes,a.cap,a.stage,a.action)
    elif a.action in ['full','k1']:full(a.ids,a.modes,a.threshold,a.cap,a.stage,a.action=='k1')
    elif a.action=='proof':proof(a.ids,a.stage)
if __name__=='__main__':main()

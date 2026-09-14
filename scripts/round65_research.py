"""Round65 bounded serial production campaign; no policy selects on scenario names."""
import argparse, csv, json, os, subprocess
from pathlib import Path
import round61_research as runner

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/os.environ.get('EBRP_ROUND65_OUTPUT','results/gf_budgeted_proof_round65')
if not OUT.resolve().is_relative_to(ROOT):raise RuntimeError('campaign output must stay inside the worktree')
RAW=OUT/'local_raw'
BUILD=ROOT/os.environ.get('EBRP_ROUND65_BUILD','build/round65')
runner.ROOT=ROOT; runner.OUT=OUT; runner.RAW=RAW; runner.BUILD=BUILD; runner.LEDGER=OUT/'processes.jsonl'
sha=runner.sha; write=runner.write
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def panel(): return {p['id']:p for p in read(OUT/'protocol.json')['panel']}
def freeze():
    if (OUT/'protocol.json').exists(): raise RuntimeError('panel already frozen')
    old=read(ROOT/'results/gf_shared_load_time_round64/protocol.json')
    chosen=[]
    for identity in ['D3','D4','D7','C2','C5','C6','C7']:
        p=dict(next(x for x in old['panel'] if x['id']==identity))
        p['stage']='development';p['role']='public historical development/protection'
        chosen.append(p)
    source=ROOT/'reference/citibike443-regional-v1/manifests/T_scenario_manifest.csv'
    rows=list(csv.DictReader(source.open(encoding='utf-8')))
    for identity,scenario in [('C8','cb443_V30_regional_r1_shortage_M03_Q30_T03600'),
                              ('C9','cb443_V20_compact_r1_balanced_M02_Q20_T10800')]:
        p=dict(next(r for r in rows if r['scenario_id']==scenario))
        p.update(id=identity,stage='confirmation',role='public metadata selected before Round65 results; not sealed',
                 input_sha256=p['instance_file_sha256'])
        chosen.append(p)
    for p in chosen: assert sha(ROOT/p['instance_path'])==p['input_sha256']
    write(OUT/'protocol.json',dict(base='8f23af309079b605f73e0e780a753d806aaf0b46',
        base_branch='codex/round64-shared-load-time',panel=chosen,manifest_sha256=sha(source),
        solver=old['solver'],startup='full stable paid HGA, seed20260626 pop24 decoder10 stagnation2000; starts disabled',
        outer='K0=1 midpoint balanced-normalized-closure tau=.08 native-target exact-parent F<=U',
        optional=dict(seed_work=30,seed_seconds=30,rho=.1,call_work=10,call_seconds=15,remaining_fraction=.5),
        budget=dict(maximum_charged_launches=72,native_micro_maximum=4,reserved_final_minimum=18,
                    reliability_maximum=8,maximum_1800=4,maximum_3600=2),
        gates=dict(time_seconds=10,time_relative=.1,gap_absolute=.001,gap_relative=.05,both_required=True),
        confirmations=['C8','C9'],long_pairs=['C6','D7','C8'],no_outcome_replacement=True))
def build_freeze(version):
    p=OUT/('build_freeze_'+version+'.json')
    if p.exists():raise RuntimeError('measured build immutable')
    write(p,dict(version=version,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        executables={f.name:sha(f) for f in BUILD.glob('*.exe')},
        source_files={str(f.relative_to(ROOT)):sha(f) for directory in ['src','include','tests'] for f in (ROOT/directory).rglob('*') if f.is_file()},
        tests_sha256=sha(BUILD/'tests.log'),protocol_sha256=sha(OUT/'protocol.json')))
    write(OUT/'active_build.json',dict(file=p.name,sha256=sha(p)))

def confirmation_freeze(policy,cap,controller,release_load):
    path=OUT/'confirmation_freeze.json'
    if path.exists():raise RuntimeError('confirmation policy already immutable')
    assert not any(e['id'] in ['C8','C9'] and e['charged'] for e in runner.entries())
    write(OUT/'main_policy.json',dict(name='uniform-'+policy+'-verified-zero',budget=True,
          projection=policy if policy in ['proof','sparse'] else 'off',verified_zero=True,
          seed_credit=30,controller=controller,release_load=release_load,selection_ledger_sha256=sha(OUT/'processes.jsonl')))
    write(path,dict(build=sha(OUT/'active_build.json'),protocol=sha(OUT/'protocol.json'),driver=sha(Path(__file__)),
                   policy=sha(OUT/'main_policy.json'),arms=['candidate','K1-H','P-GRB'],cap=cap,
                   confirmations=['C8','C9'],no_revision_after_confirmation=True))

def reference_build(identities):
    expected=read(OUT/'new_reference_fingerprints.json') if (OUT/'new_reference_fingerprints.json').exists() else {}
    for identity in identities:
        p=panel()[identity];dest=RAW/'reference_build'/identity
        if p.get('stage')=='confirmation':assert (OUT/'confirmation_freeze.json').exists()
        cmd=[BUILD/'Round65ReferenceBuild.exe',p['instance_path'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'],p['lambda'],dest]
        runner.execute(cmd,dest,dict(id=identity,arm='plain-build',stage='reference_build'),30,'build-only',0)
        r=read(dest/'build.json');assert r['optimizer_calls']==0
        expected[p['scenario_id']]=r['fingerprint']
        write(OUT/'new_reference_fingerprints.json',expected)
def execute(p,arm,cap,stage,kind='performance',credit=30):
    if (OUT/'pause_before_launch').exists():raise RuntimeError('campaign paused before any charged launch')
    if cap not in [20,30,120,180,240,300,600,1200,1800,3600]: raise RuntimeError('undeclared cap')
    active=read(OUT/'active_build.json');assert sha(OUT/active['file'])==active['sha256']
    frozen=read(OUT/active['file']);assert sha(BUILD/'ExactEBRP.exe')==frozen['executables']['ExactEBRP.exe']
    if p.get('stage')=='confirmation':
        freeze=read(OUT/'confirmation_freeze.json')
        for path,key in [(OUT/'active_build.json','build'),(OUT/'protocol.json','protocol'),(Path(__file__),'driver')]:
            assert sha(path)==freeze[key]
        assert sha(OUT/'main_policy.json')==freeze['policy']
        assert arm in freeze['arms'] and cap==freeze['cap']
        if p['id']=='C9':
            previous=[e for e in runner.entries() if e['id']=='C8' and e['charged']]
            assert set(e['arm'] for e in previous)==set(freeze['arms'])
            assert all((ROOT/e['destination']/'completion.json').exists() for e in previous)
    entries=runner.entries()
    if cap>=1800: assert sum(e['charged'] and e['cap_seconds']==cap for e in entries)<(4 if cap==1800 else 2)
    assert sha(ROOT/p['instance_path'])==p['input_sha256']
    dest=RAW/stage/p['id']/arm
    warm=not arm.startswith('cold-')
    mode=arm.removeprefix('cold-')
    preset='paper-k1-am-sf' if arm=='K1-H' else 'research-round65-k1-h' if warm else 'research-round65-k1-s'
    cmd=runner.full_command(p,dest,preset,'off',cap)+['--ub-event-log',dest/'ub_events.csv']
    if frozen['version'] not in ['v1','v2','v3']:cmd+=['--round65-witness-audit','true']
    if arm=='P-GRB':
        expected={e['instance_id']:e['expected_gurobi_model_fingerprint'] for e in read(ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json')['entries']}
        # New metadata roles require a separately recorded build-only fingerprint.
        if p['scenario_id'] not in expected: expected.update(read(OUT/'new_reference_fingerprints.json'))
        cmd=[BUILD/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],'--T',p['T_seconds'],
             '--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--time-limit',cap-6,
             '--process-wall-time-limit',cap,'--process-shutdown-margin',3,'--threads',1,'--mip-threads',1,
             '--gurobi-seed',0,'--gurobi-presolve',-1,'--method','gurobi','--plain-baseline',
             '--out',dest/'result.json','--log',dest/'native.log','--process-phase-ledger',dest/'phases.csv',
             '--gurobi-model-export',dest/'compact.lp','--round24-expected-gurobi-model-fingerprint',expected[p['scenario_id']],
             '--round24-executable-sha256',sha(BUILD/'ExactEBRP.exe'),'--round24-manifest-executable-sha256',sha(BUILD/'ExactEBRP.exe')]
    elif arm!='K1-H':
        controller='credit-seed' if mode.startswith('seed-') else 'credit10'
        release_load=mode.endswith('-free')
        mode=mode.removeprefix('seed-').removesuffix('-free')
        policy=read(OUT/'main_policy.json') if mode=='candidate' else None
        if policy:
            mode=policy['projection'] if policy['projection']!='off' else 'bounded'
            credit=policy['seed_credit']
            controller=policy['controller'];release_load=policy['release_load']
        if mode not in ['off','bounded','proof','sparse','joint','bounded-joint','reliable']: raise RuntimeError('unknown arm')
        cmd+=['--round65-budget',str(mode in ['bounded','proof','sparse','bounded-joint']).lower(),
              '--round65-projection',mode if mode in ['proof','sparse'] else 'off',
              '--round64-shared-mode','joint' if mode in ['joint','bounded-joint'] else 'off',
              '--round65-seed-credit',credit,'--round65-hga-zero-stop',str(mode=='reliable' or bool(policy and policy['verified_zero'])).lower(),
              '--round60-hga-candidate-log',dest/'hga_events.csv']
        if frozen['version'] not in ['v1','v2','v3']:
            cmd+=['--round65-controller',controller,'--round65-release-load',str(release_load).lower()]
    runner.execute(cmd,dest,dict(id=p['id'],arm=arm,stage=stage,build_freeze=active['file']),cap,kind,
                   'all native, proof reoptimization and auxiliary calls in ledgers')
    if (dest/'result.json').exists():
        result=read(dest/'result.json')
        if 'failed' in result.get('status',''): raise RuntimeError('charged semantic failure '+result['status'])
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','build-freeze','run','micro','confirmation-freeze','reference-build'])
    p.add_argument('--version');p.add_argument('--ids',nargs='+',default=[]);p.add_argument('--arms',nargs='+',default=['off','bounded'])
    p.add_argument('--cap',type=int,default=120);p.add_argument('--stage',default='dev');p.add_argument('--credit',type=float,default=30)
    p.add_argument('--policy',choices=['bounded','proof','sparse'],default='bounded')
    p.add_argument('--controller',choices=['credit10','credit-seed'],default='credit10')
    p.add_argument('--release-load',action='store_true')
    a=p.parse_args()
    if a.action=='freeze':return freeze()
    if a.action=='build-freeze':return build_freeze(a.version)
    if a.action=='confirmation-freeze':return confirmation_freeze(a.policy,a.cap,a.controller,a.release_load)
    if a.action=='reference-build':return reference_build(a.ids)
    if a.action=='micro':
        q=dict(id='micro',instance_path='tests/data/round59_tiny.txt',T_seconds=5,pickup_seconds=1,drop_seconds=1,**{'lambda':.15})
        q['input_sha256']=sha(ROOT/q['instance_path'])
        for arm in a.arms:execute(q,arm,a.cap,a.stage,'native-micro',a.credit)
    else:
        for identity in a.ids:
            for arm in a.arms:execute(panel()[identity],arm,a.cap,a.stage,credit=a.credit)
if __name__=='__main__':main()

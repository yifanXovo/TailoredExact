"""Serial Round66 experiments; the global run cap never selects an algorithm."""
import argparse, csv, json, os, subprocess
from pathlib import Path
import round61_research as runner

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/unified_exact_round66'
BUILD=ROOT/'build/round66'
RAW=OUT/'local_raw'
runner.ROOT=ROOT;runner.OUT=OUT;runner.RAW=RAW;runner.BUILD=BUILD
runner.LEDGER=OUT/'processes.jsonl'
sha=runner.sha;write=runner.write
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def panel():return {p['id']:p for p in read(OUT/'protocol.json')['panel']}

def freeze():
    if (OUT/'protocol.json').exists():raise RuntimeError('immutable protocol exists')
    old=read(ROOT/'results/gf_core_attribution_native_round59/panel.json')['panel']
    selected=[]
    for identity in ['D3','D4','D6','C2']:
        p=dict(next(p for p in old if p['id']==identity))
        p['lambda']=float(p.get('lambda',.15));selected.append(p)
    for identity,m,seed in [('E7',2,1210444511),('E8',3,1167625600)]:
        name=f'round39_small_easy_V12_M{m}_Q30_slot0{7 if m==2 else 8}_seed{seed}'
        path=f'reference/qualification_round39/small-easy/{name}.txt'
        selected.append(dict(id=identity,scenario_id=name,instance_path=path,input_sha256=sha(ROOT/path),
            V=12,M=m,Q=30,T_seconds=3600,pickup_seconds=60,drop_seconds=60,**{'lambda':.15},
            role='historical C6 non-startup loss; current K1 not yet known'))
    selected.append(dict(id='micro',scenario_id='round59_tiny',instance_path='tests/data/round59_tiny.txt',
        input_sha256=sha(ROOT/'tests/data/round59_tiny.txt'),V=3,M=1,Q=3,T_seconds=5,
        pickup_seconds=1,drop_seconds=1,**{'lambda':.15},role='native correctness only'))
    for p in selected:assert sha(ROOT/p['instance_path'])==p['input_sha256']
    write(OUT/'protocol.json',dict(base='112d6b26905848557048d52083d3709b46e15750',panel=selected,
        plan_sha256=sha(OUT/'research_map.md'),mathematics_sha256=sha(OUT/'mathematics.md'),
        initial_maximum_performance=16,initial_maximum_micro=2,
        initial_worst_case_seconds=6*120+10*300+2*20,
        resource_plan_revisions=[],solver=dict(version='13.0.2',Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0),
        candidate='K1-R plus arc-load replacement, no optional budgets/projection',confirmation_opened=False))
    write(OUT/'build_v1.json',dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        working_source={str(p.relative_to(ROOT)):sha(p) for d in ['src','include','tests'] for p in (ROOT/d).glob('*.cpp')},
        headers={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'include').glob('*.hpp')},
        binary=sha(BUILD/'ExactEBRP.exe'),tests=sha(BUILD/'tests.log'),driver=sha(Path(__file__))))

def refbuild(ids):
    fingerprints=read(OUT/'fingerprints.json') if (OUT/'fingerprints.json').exists() else {}
    historical={e['instance_id']:e['expected_gurobi_model_fingerprint'] for e in read(
        ROOT/'results/gf_citibike443_k1_vs_pgrb_round58/pgrb_expected_fingerprints.json')['entries']}
    for identity in ids:
        p=panel()[identity];dest=RAW/'reference_build'/identity
        runner.execute([BUILD/'Round65ReferenceBuild.exe',p['instance_path'],p['T_seconds'],
            p['pickup_seconds'],p['drop_seconds'],p['lambda'],dest],dest,
            dict(id=identity,arm='reference-build',stage='reference-build'),30,'build-only',0)
        b=read(dest/'build.json');assert b['optimizer_calls']==0
        if p['scenario_id'] in historical:assert b['fingerprint']==historical[p['scenario_id']]
        fingerprints[identity]=b;write(OUT/'fingerprints.json',fingerprints)

def run(ids,arms,cap,stage):
    protocol=read(OUT/'protocol.json');freeze=read(OUT/'build_v1.json')
    assert sha(BUILD/'ExactEBRP.exe')==freeze['binary']
    assert sha(Path(__file__))==freeze['driver']
    for identity in ids:
        p=panel()[identity];assert sha(ROOT/p['instance_path'])==p['input_sha256']
        for arm in arms:
            kind='native-micro' if identity=='micro' else 'performance'
            limit=protocol['initial_maximum_micro'] if kind=='native-micro' else protocol['initial_maximum_performance']
            assert sum(e['kind']==kind for e in runner.entries())<limit,'declare resource revision before launch'
            assert cap in [20,120,300,600] and (cap==20 if identity=='micro' else cap>=120)
            dest=RAW/stage/identity/arm
            if arm=='P-GRB':
                cmd=[BUILD/'ExactEBRP.exe','--input',p['instance_path'],'--lambda',p['lambda'],'--T',p['T_seconds'],
                    '--pickup-time',p['pickup_seconds'],'--drop-time',p['drop_seconds'],'--time-limit',cap-6,
                    '--process-wall-time-limit',cap,'--process-shutdown-margin',3,'--threads',1,'--mip-threads',1,
                    '--gurobi-seed',0,'--gurobi-presolve',-1,'--method','gurobi','--plain-baseline',
                    '--out',dest/'result.json','--log',dest/'native.log','--process-phase-ledger',dest/'phases.csv',
                    '--gurobi-model-export',dest/'compact.lp','--round24-expected-gurobi-model-fingerprint',
                    read(OUT/'fingerprints.json')[identity]['fingerprint'],
                    '--round24-executable-sha256',freeze['binary'],'--round24-manifest-executable-sha256',freeze['binary']]
            else:
                assert arm in ['K1-R','ARC','Q-PLUS','K1-AM']
                preset='paper-k1-am-sf' if arm=='K1-AM' else 'research-round65-k1-h'
                cmd=runner.full_command(p,dest,preset,'off',cap)+['--round65-witness-audit','true',
                    '--ub-event-log',dest/'ub_events.csv']
                if arm!='K1-AM':cmd+=['--round65-hga-zero-stop','true','--round60-hga-candidate-log',dest/'hga_events.csv']
                if arm=='ARC':cmd+=['--round66-arc-load-replacement','true']
                if arm=='Q-PLUS':cmd+=['--round64-shared-mode','q']
            runner.execute(cmd,dest,dict(id=identity,arm=arm,stage=stage,scope='original_problem',
                build=sha(OUT/'build_v1.json'),input_sha256=p['input_sha256']),cap,kind,'all actual native calls in ledger')
            if not (dest/'result.json').exists():raise RuntimeError('result missing')
            r=read(dest/'result.json')
            if 'failed' in r.get('status',''):raise RuntimeError(r['status'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','refbuild','run'])
    ap.add_argument('--ids',nargs='+',default=[]);ap.add_argument('--arms',nargs='+',default=['K1-R','ARC'])
    ap.add_argument('--cap',type=int,default=120);ap.add_argument('--stage',default='screen')
    a=ap.parse_args()
    if a.action=='freeze':freeze()
    elif a.action=='refbuild':refbuild(a.ids)
    else:run(a.ids,a.arms,a.cap,a.stage)
if __name__=='__main__':main()

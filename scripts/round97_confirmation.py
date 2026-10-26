"""One frozen candidate, three reserved roles, serial original-problem confirmation.

Preparation requires the post-development candidate freeze and only exports
original models through a build-only executable. Run never selects a candidate,
changes a role/window, retries a completed arm, or admits a failed predecessor.
"""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path
import round97_campaign_v2 as campaign
import round97_development_v2 as development
import round97_vector_audit as vectors
from round97_campaign_v2 import ROOT, OUT, BUILD, read, write, sha, ext, r90, helper_bindings

CAMP=OUT/'confirmation01'
FREEZE=OUT/'confirmation_candidate_freeze.json'
INPUTS=OUT/'confirmation_inputs.json'
RECIPE=OUT/'confirmation_recipe.json'
REFERENCE=BUILD/'Round65ReferenceBuild.exe'


def candidate():
    frozen=read(FREEZE)
    assert frozen['schema']=='round97-one-candidate-confirmation-freeze-v1'
    assert frozen['development_complete'] and frozen['allow_confirmation']
    assert frozen['selected_operator'] in ('r83','r96') and frozen['mode']=='feedback'
    assert frozen['source_hashes']==campaign.bindings()
    assert frozen['candidate_binary_sha256']==sha(BUILD/'ExactEBRP.exe')
    assert frozen['input_manifest_sha256']==sha(INPUTS)
    assert frozen['recipe_sha256']==sha(RECIPE)
    assert frozen['confirmation_runner_sha256']==sha(__file__)
    for path,expected in frozen['decision_evidence_bindings'].items():
        assert sha(ROOT/path)==expected,path
    assert frozen['prohibited_changes']==[
        'startup','physics','objective','numerical_tolerances','native_parameters',
        'reserved_inputs','role_windows','operator_after_confirmation_starts']
    development.qualified()
    return frozen


def expected_schedule():
    return [('C1','P-GRB',900),('C1','FEEDBACK',900),('C1','OFF',900),
            ('C2','OFF',1800),('C2','P-GRB',1800),('C2','FEEDBACK',1800),
            ('C3','FEEDBACK',3600),('C3','OFF',3600),('C3','P-GRB',3600)]


def expected_launches(frozen,roles,references,prereg):
    launches=[]
    assert [(p['id'],a,p['cap_seconds']) for p in roles for a in p['method_order']]==expected_schedule()
    for original in roles:
        panel=dict(original,reference=references[original['id']])
        for arm in panel['method_order']:
            number=len(launches)+1;dest=CAMP/'raw'/f"{number:02d}_{panel['id']}_{arm}"
            mode='off' if arm=='P-GRB' else 'observe' if arm=='OFF' else 'feedback'
            operator='none' if arm=='P-GRB' else 'r83' if arm=='OFF' else frozen['selected_operator']
            command=(r90.audited_runner_utilities.command_for(prereg,panel,arm,dest)
                     if arm=='P-GRB' else r90.command_for(prereg,panel,'ENS-C',dest)+
                     ['--round97-native-closure',mode,'--round97-native-operator',operator])
            launches.append(dict(number=number,id=panel['id'],arm=arm,mode=mode,operator=operator,
                stage='frozen_design_isolated_confirmation',panel=panel,destination=str(dest),
                cap_seconds=panel['cap_seconds'],hard_stop_seconds=panel['cap_seconds']-2,command=command))
    return launches


def prepare():
    ext.ensure_idle();started=time.perf_counter()
    frozen=candidate();assert not CAMP.exists()
    inputs=read(INPUTS);recipe=read(RECIPE)
    assert inputs['optimizer_calls']==0 and inputs['recipe_sha256']==sha(RECIPE)
    roles=inputs['roles'];assert len(roles)==3
    assert [(p['id'],a,p['cap_seconds']) for p in roles for a in p['method_order']]==expected_schedule()
    assert REFERENCE.is_file()
    references={};CAMP.mkdir()
    env=dict(os.environ)
    env['PATH']='D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;'+env.get('PATH','')
    for panel in roles:
        assert sha(ROOT/panel['input_path'])==panel['input_sha256']
        dest=CAMP/'reference'/panel['id'];dest.mkdir(parents=True)
        command=list(map(str,[REFERENCE,panel['input_path'],panel['T_seconds'],
            panel['pickup_seconds'],panel['drop_seconds'],panel['lambda'],dest]))
        write(dest/'launch.json',dict(command=command,optimizer_calls=0,
            binary_sha256=sha(REFERENCE),source_sha256=sha(ROOT/'src/round65_reference_build.cpp')))
        tick=time.perf_counter()
        with (dest/'stdout.log').open('x') as stdout,(dest/'stderr.log').open('x') as stderr:
            ret=subprocess.run(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=60)
        write(dest/'completion.json',dict(returncode=ret.returncode,
            wall_seconds=time.perf_counter()-tick,optimizer_calls=0,
            accounting='Nested in preparation wrapper; do not add twice.'))
        assert ret.returncode==0
        reference=read(dest/'build.json')
        assert reference['optimizer_calls']==0 and reference['canonical_sha256']==sha(dest/'original.lp')
        references[panel['id']]=reference
    prereg=dict(candidate_binary=(BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix(),
        candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'),common=ext.COMMON)
    launches=expected_launches(frozen,roles,references,prereg)
    assert [(r['id'],r['arm'],r['cap_seconds']) for r in launches]==expected_schedule()
    assert sum(r['cap_seconds'] for r in launches)==18900
    production=read(OUT/'production_v2_identity.json')
    reference_paths=[p for p in (CAMP/'reference').rglob('*') if p.is_file()]
    write(CAMP/'identity.json',dict(schema='round97-frozen-confirmation-v1',
        source_ref=production['source_ref'],source_hashes=campaign.bindings(),
        candidate_binary_sha256=sha(BUILD/'ExactEBRP.exe'),
        dll_sha256=sha('D:/gurobi1302/win64/bin/gurobi130.dll'),
        runner_sha256=sha(__file__),auditor_sha256=sha(campaign.__file__),
        prereg_sha256=sha(FREEZE),input_manifest_sha256=sha(INPUTS),recipe_sha256=sha(RECIPE),
        build_identity_sha256=sha(OUT/'production_v2_identity.json'),
        reference_binary_sha256=sha(REFERENCE),
        reference_bindings={p.relative_to(ROOT).as_posix():sha(p) for p in reference_paths},
        helper_hashes=helper_bindings(),prereg=prereg,references=references,launches=launches,
        maximum_starts=9,maximum_process_seconds=18900,optimizer_calls_in_preparation=0,
        wall_seconds_before_write=time.perf_counter()-started,
        policy='All once-generated reserved roles and outcomes retained. Uniform frozen candidate. No post-confirmation tuning, replacement inputs, extended windows, or adopted defaults.'))
    write(CAMP/'prepared_batch.json',dict(batch_sha256=sha(CAMP/'identity.json'),
        candidate_freeze_sha256=sha(FREEZE),optimizer_calls=0))
    print(json.dumps(dict(prepared='confirmation01',starts=9,maximum_process_seconds=18900,optimizer_calls=0)))


def identity_check(identity):
    frozen=candidate()
    assert read(CAMP/'identity.json')==identity
    prepared=read(CAMP/'prepared_batch.json')
    assert prepared['batch_sha256']==sha(CAMP/'identity.json')
    assert prepared['candidate_freeze_sha256']==sha(FREEZE) and prepared['optimizer_calls']==0
    assert identity['runner_sha256']==sha(__file__)
    assert identity['auditor_sha256']==sha(campaign.__file__)
    assert identity['prereg_sha256']==sha(FREEZE)
    assert identity['input_manifest_sha256']==sha(INPUTS)
    assert identity['recipe_sha256']==sha(RECIPE)
    assert identity['source_hashes']==campaign.bindings()
    assert identity['candidate_binary_sha256']==frozen['candidate_binary_sha256']
    assert identity['dll_sha256']==sha('D:/gurobi1302/win64/bin/gurobi130.dll')
    assert identity['build_identity_sha256']==sha(OUT/'production_v2_identity.json')
    assert identity['reference_binary_sha256']==sha(REFERENCE)
    for group in ['helper_hashes','reference_bindings']:
        for path,expected in identity[group].items():assert sha(ROOT/path)==expected,path
    prereg=dict(candidate_binary=(BUILD/'ExactEBRP.exe').relative_to(ROOT).as_posix(),
        candidate_binary_sha256=frozen['candidate_binary_sha256'],common=ext.COMMON)
    assert identity['prereg']==prereg
    references={role:read(CAMP/'reference'/role/'build.json') for role in ('C1','C2','C3')}
    assert identity['references']==references
    assert identity['launches']==expected_launches(frozen,read(INPUTS)['roles'],references,prereg)


def completed_roles(identity,role):
    """A failed end-of-role audit is a failed predecessor, even after three good arms."""
    batch_sha=sha(CAMP/'identity.json')
    for prior in ('C1','C2','C3')[:('C1','C2','C3').index(role)]:
        queue=CAMP/('queue_'+prior)
        assert read(queue/'identity.json')['batch_sha256']==batch_sha
        status=read(queue/'status.json')
        assert status['phase']=='role_complete_requires_root_analysis' and status['role']==prior
        events=[json.loads(s) for s in (queue/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        assert events[-1]==status
        consistency=queue/'cross_arm_consistency.json';receipt=read(consistency)
        assert status['consistency_sha256']==sha(consistency)
        assert receipt['passed'] and receipt['optimizer_calls']==0 and receipt['batch_sha256']==batch_sha
        for path,expected in receipt['evidence_bindings'].items():assert sha(ROOT/path)==expected,path
        assert status['completed_prefix']==max(r['number'] for r in identity['launches'] if r['id']==prior)


def prefix(identity,count):
    path=CAMP/'summary.jsonl'
    rows=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    assert len(rows)==count
    for launch,row in zip(identity['launches'][:count],rows,strict=True):
        assert (row['number'],row['id'],row['arm'])==(launch['number'],launch['id'],launch['arm'])
        raw=Path(launch['destination']);audit=read(raw/'audit.json');receipt=read(raw/'completion.json')
        assert row['audit_passed'] and audit['passed']
        assert row['endpoint']==audit['endpoint'] and row['completion']==receipt
        assert receipt['stop_reason']=='normal_return' and receipt['returncode']==0 and receipt['within_cap']
        assert (raw/'result.json').exists()
        if launch['arm']!='P-GRB' and (raw/'external/round97/events.jsonl').exists():
            vector_path=OUT/f"confirmation01_{launch['number']:02d}_vectors.json"
            assert read(vector_path)['passed'] and read(vector_path)['optimizer_calls']==0
            matches=[e for p in CAMP.glob('queue_*/events.jsonl') for e in map(json.loads,p.read_text().splitlines())
                     if e['phase']=='actual_model_vectors_passed' and e.get('number')==launch['number']]
            assert len(matches)==1 and matches[0]['audit_sha256']==sha(vector_path)
    return rows


def run_role(role):
    ext.ensure_idle();identity=read(CAMP/'identity.json');identity_check(identity)
    assert role in ('C1','C2','C3')
    completed_roles(identity,role)
    selected=[r for r in identity['launches'] if r['id']==role]
    assert len(selected)==3
    prefix(identity,selected[0]['number']-1)
    assert all(not Path(r['destination']).exists() for r in selected)
    frozen_batch_sha=sha(CAMP/'identity.json')
    assert read(CAMP/'identity.json')==identity
    queue=CAMP/('queue_'+role);queue.mkdir(exist_ok=False)
    write(queue/'identity.json',dict(batch_sha256=frozen_batch_sha,runner_sha256=sha(__file__),
        role=role,new_launch_numbers=[r['number'] for r in selected],maximum_new_starts=3,
        maximum_new_process_seconds=sum(r['cap_seconds'] for r in selected),
        policy='Three original registered arms only; stop on any audit failure or abnormal return; no automatic rerun.'))
    tick=time.perf_counter()
    def record(phase,**extra):
        row=dict(phase=phase,unix=time.time(),queue_elapsed_seconds=time.perf_counter()-tick,**extra)
        with (queue/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n');f.flush()
        tmp=queue/'status.json.tmp';tmp.write_text(json.dumps(row,indent=2)+'\n');tmp.replace(queue/'status.json')
        print(json.dumps(row),flush=True)
    try:
        for launch in selected:
            assert sha(CAMP/'identity.json')==frozen_batch_sha,'batch changed after queue freeze'
            identity_check(identity);number=launch['number'];prefix(identity,number-1)
            assert sha(ROOT/launch['panel']['input_path'])==launch['panel']['input_sha256']
            ext.ensure_idle();record('launching_registered_arm',number=number,id=role,arm=launch['arm'])
            r90.CAMPAIGN=CAMP;r90.audit_launch=campaign.auditor
            r90.run_one(launch,identity['prereg'],identity)
            raw=Path(launch['destination']);receipt=read(raw/'completion.json');audit=read(raw/'audit.json')
            assert receipt['stop_reason']=='normal_return' and receipt['returncode']==0 and audit['passed']
            record('registered_arm_audited',number=number,endpoint=audit['endpoint'])
            ext.ensure_idle()
            if launch['arm']!='P-GRB' and (raw/'external/round97/events.jsonl').exists():
                label=f'confirmation01_{number:02d}_vectors';started=time.perf_counter()
                record('auditing_actual_model_vectors',number=number)
                vectors.check(str(raw),label);path=OUT/(label+'.json');assert read(path)['passed']
                record('actual_model_vectors_passed',number=number,optimizer_calls=0,
                    wrapper_seconds=time.perf_counter()-started,audit_path=path.relative_to(OUT).as_posix(),audit_sha256=sha(path))
            prefix(identity,number)
        role_rows=[r for r in prefix(identity,selected[-1]['number']) if r['id']==role]
        uppers=[r['endpoint']['U'] for r in role_rows if r['endpoint']['U'] is not None]
        lowers=[r['endpoint']['L'] for r in role_rows]
        assert not uppers or max(lowers)<=min(uppers)+1e-7,'cross-arm physical/bound contradiction'
        write(queue/'cross_arm_consistency.json',dict(passed=True,optimizer_calls=0,
            batch_sha256=frozen_batch_sha,
            evidence_bindings={str((Path(r['destination'])/name).relative_to(ROOT).as_posix()):
                sha(Path(r['destination'])/name) for r in selected for name in ('audit.json','completion.json')},
            strongest_L=max(lowers),best_physical_U=min(uppers) if uppers else None,
            scope='Offline contradiction check only; never a combined certificate.'))
        record('role_complete_requires_root_analysis',role=role,completed_prefix=selected[-1]['number'],
            consistency_sha256=sha(queue/'cross_arm_consistency.json'))
    except BaseException as error:
        record('stopped_failure_no_restart',error=repr(error));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run-role']);p.add_argument('--role')
    a=p.parse_args()
    if a.action=='prepare':prepare()
    else:run_role(a.role)

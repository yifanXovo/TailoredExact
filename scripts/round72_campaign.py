"""Same-byte bounded validation; rebind inherited R71 runners to new outputs."""
import argparse,shutil,subprocess
from pathlib import Path
import package_round71 as package
run=package.run
ROOT=run.ROOT
STAGE=ROOT/'results/unified_exact_round72'
OUT=STAGE/'campaign'
ORIGINAL=ROOT/'results/unified_exact_round71'

def bind():
    run.OUT=OUT;run.RAW=OUT/'local_raw';run.BUILD=ROOT/'build/round71'
    package.bind()

def freeze():
    assert not OUT.exists(),'Never replace a frozen campaign'
    package.bind();old,old_protocol=run.assert_frozen()
    assert run.OUT==ORIGINAL and not (ORIGINAL/'active_run.lock').exists()
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='codex/round72-vdsx-validation'
    diagnostic=run.read(STAGE/'diagnostic_audit.json')
    assert diagnostic['completed']==6 and diagnostic['physical_and_trace_checks_passed']
    bind();OUT.mkdir()
    shutil.copyfile(STAGE/'formal_campaign_plan.md',OUT/'plan.md')
    for name in ['mathematics.md','affinity_qualification.json']:
        shutil.copyfile(ORIGINAL/name,OUT/name)
    qualification=run.read(ORIGINAL/'qualification.json')
    qualification.update(inherited_ctest_tests=49,newly_executed_ctest_tests=0,
        inherited_qualification_path=str(ORIGINAL/'qualification.json'),
        configure_build_test_attempts=[],preflight_total_wall_seconds=0,
        inherited_native_test_calls=39,total_qualification_native_optimizer_calls=0,
        qualification_scope='Identical qualified R71 bytes; zero new build/test executions')
    run.write(OUT/'qualification.json',qualification)
    protocol=dict(old_protocol)
    protocol.update(base='73ce04d9a3c5031c2b5a1021523502f0a9a85168',
        panel=[p for p in old_protocol['panel'] if p['id'] in ['D3','C2','D4','D7']],
        caps=dict(D3=300,C2=300,D4=300,D7=3600),
        allowed_arms={i:(['P-GRB','K1-R','DS-X'] if i=='D7' else ['P-GRB','DS','DS-X']) for i in ['D3','C2','D4','D7']},
        plan_sha256=run.sha(OUT/'plan.md'),mathematics_sha256=run.sha(OUT/'mathematics.md'),
        maximum_performance=12,maximum_micro=0,maximum_reference_exports=4,worst_case_seconds=13500,
        validation_scope='Same frozen R71 candidate, fresh exposed-role validation; conditional D7 requires a recorded gate')
    for p in protocol['panel']:p['role']='Round72 exposed validation/protection; see plan.md'
    run.write(OUT/'protocol.json',protocol)
    identity=dict(old)
    identity.update(qualification=run.sha(OUT/'qualification.json'),
        execution_freeze_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        inherited_build_manifest_sha256=run.sha(ORIGINAL/'build_v1.json'),
        wrapper=run.sha(__file__),qualification_scope='49 inherited CTests; zero new CTests/native qualification calls')
    run.write(OUT/'build_v1.json',identity)
    assert_frozen()

def assert_frozen():
    bind();identity,protocol=run.assert_frozen()
    assert run.sha(__file__)==identity['wrapper']
    assert run.sha(STAGE/'formal_campaign_plan.md')==protocol['plan_sha256']
    assert run.sha(OUT/'qualification.json')==identity['qualification']
    assert run.sha(run.BUILD/'Round65ReferenceBuild.exe')==identity['reference_binary']
    assert run.sha(run.BUILD/'tests.log')==identity['tests']
    assert not (ORIGINAL/'active_run.lock').exists() and not (STAGE/'active_run.lock').exists()
    return identity,protocol

def execute(ids):
    assert_frozen()
    for identity in ids:
        if identity=='D7':
            gate=run.read(OUT/'long_gate.json')
            assert gate['admitted'] and gate['completed_short_runs']==9
            assert gate['runs_sha256']==run.sha(OUT/'runs.csv')
            arms=['P-GRB','K1-R','DS-X'];cap=3600
        else:arms=['P-GRB','DS','DS-X'];cap=300
        if not (run.RAW/'reference_build'/identity).exists():run.refbuild([identity])
        for arm in arms:
            run.run([identity],[arm],cap,'development')
            import round71_endpoint as endpoint
            endpoint.check(sum(e['charged'] for e in run.runner.entries()))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','run','package','verify'])
    parser.add_argument('--ids',nargs='+',choices=['D3','C2','D4','D7'],default=[])
    args=parser.parse_args()
    if args.action=='freeze':freeze();return
    assert_frozen()
    if args.action=='run':execute(args.ids)
    elif args.action=='package':package.main()
    else:
        import round71_delivery as delivery
        delivery.main()

if __name__=='__main__':main()

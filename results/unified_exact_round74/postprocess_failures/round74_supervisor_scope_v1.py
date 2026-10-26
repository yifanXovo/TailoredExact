"""Audit the actual K1 false-negative guard without modifying its frozen run."""
import json
import time
from pathlib import Path
from round73_qualify import ROOT,sha,write
import round73_native_evidence as evidence

OUT=ROOT/'results/unified_exact_round74/campaign'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    started=time.perf_counter();assert not (OUT/'active_run.lock').exists()
    destination=OUT/'supervisor_scope_correction.json'
    assert not destination.exists(),'Never replace this exception audit'
    frozen=read(OUT/'identity.json');summary=read(OUT/'summary.json')
    assert summary['completed']==4
    assert all(r['audit']['passed'] for r in summary['records'][:3])
    done=summary['records'][3];launch=frozen['launches'][3]
    assert done['arm']==launch['arm']=='K1-R' and done['number']==4
    assert not done['audit']['passed'] and done['audit']['error']=='AssertionError()'
    assert sha(ROOT/'scripts/round74_research.py')==frozen['driver_sha256']
    assert sha(evidence.__file__)==frozen['reader_sha256']
    assert sha(evidence.physical_module.__file__)==frozen['physical_sha256']
    assert sha(ROOT/'build/round73/v6/ExactEBRP.exe')==frozen['binary_sha256']
    assert sha(OUT.parent/'plan.md')==frozen['plan_sha256']
    for name,digest in frozen['source'].items():assert sha(ROOT/name)==digest,name
    folder=ROOT/launch['destination'];assert read(folder/'launch.json')==launch
    p=launch['panel'];assert sha(ROOT/p['instance_path'])==p['input_sha256']
    completion=read(folder/'completion.json');affinity=read(folder/'affinity.json')
    assert completion['returncode']==0 and completion['stop_reason']=='normal_return'
    assert completion['within_cap'] and completion['wall_seconds']<=launch['cap']
    assert completion['restored']==affinity['binding']['before']
    assert affinity['child']['process_mask']==4
    records=read(folder/'observations.json')
    for r in records:
        assert evidence.receipt(folder/'journal'/f'event_{r["sequence"]}.commit',
            r['first_observed_seconds'],launch['cap'])==r
    audited=evidence.audit(ROOT,p,records,frozen['binary_sha256'])
    assert audited['native_calls_started']>=1
    assert audited['native_calls_returned']==audited['native_calls_started']
    assert audited['native_physical_witnesses']==0 and audited['physical_witnesses']==1
    assert audited['global_native_bound_events']>0
    physical_event=next(r['payload'] for r in records if r['payload']['kind']=='witness')
    assert physical_event['call']==0 and physical_event['source']=='same_run_verified_startup'
    result=read(folder/'result.json')
    assert not any(t in result['status'].lower() for t in ['failed','invalid','error','numeric'])
    assert all(result[k] for k in ['external_gini_tree_root_coverage_valid',
        'external_gini_tree_parent_child_coverage_valid','external_gini_tree_backend_parameter_roundtrip_valid'])
    physical=evidence.physical_module.physical(p,result)
    assert physical['original_T_feasible'] and abs(physical['F']-result['upper_bound'])<1e-7
    assert abs(audited['UB']-result['upper_bound'])<1e-7
    assert audited['LB']<=physical['F']+1e-7 and result['lower_bound']<=physical['F']+1e-7
    assert not result['strict_certified_original_problem']
    scopes={r['payload']['call']:r['payload'] for r in records if r['payload']['kind']=='call'}
    for r in records:
        e=r['payload']
        if e['kind']=='bound' and e['global_available']:
            evidence.replay_bound(scopes[e['call']],e['native_bound'],audited['witnesses']+[physical])
    mip=[c for c in scopes.values() if c['native_preconditions']]
    assert len(mip)==1
    assert not mip[0]['lower_g']-1e-7<=physical_event['G']<=mip[0]['upper_g']+1e-7
    native=Path(mip[0]['native_log_path']).read_text(encoding='utf-8')
    assert 'Solution count 0' in native and 'Time limit reached' in native
    audited.update(passed=True,normal_result_certificate=False,
        endpoint=dict(U=result['upper_bound'],L=result['lower_bound'],
            gap=result['upper_bound']-result['lower_bound'],certificate=False,
            source='normal_finalized_physical_endpoint',status=result['status']),
        supervisor_scope_correction=True)
    correction=dict(independent_checks_passed=True,number=4,arm='K1-R',
        original_summary_sha256=sha(OUT/'summary.json'),original_audit=done['audit'],
        raw_audit_sha256=sha(folder/'audit.json'),driver_sha256=frozen['driver_sha256'],
        source_plan_sha256=frozen['plan_sha256'],validated_audit=audited,
        offending_guard="assert audited['native_physical_witnesses']>=1",
        reason='The original contract requires a physical same-run UB and complete-domain LB, not a new feasible point in every native proof interval. The retained HGA witness lies outside the active MIP interval; that interval correctly returns with no incumbent.',
        gates_preserved='Original physical objective/routes, input/build/commands, numerical tolerances, native settings, model hashes, scope/coverage, contradictions, whole-run cost and affinity restoration.',
        native_mip_solutions=0,native_mip_scope=dict(leaf=mip[0]['leaf'],lower_g=mip[0]['lower_g'],upper_g=mip[0]['upper_g']),
        startup_G=physical_event['G'],new_optimizer_calls=0,new_runs=0,
        wall_seconds=time.perf_counter()-started,script_sha256=sha(__file__),
        scope='One retained supervisor false negative; raw run, failed audit and summary remain byte-identical. No candidate-specific solver exception or new native witness is introduced.')
    write(destination,correction)
    print(json.dumps({k:v for k,v in correction.items() if k!='validated_audit'},indent=2))


if __name__=='__main__':main()

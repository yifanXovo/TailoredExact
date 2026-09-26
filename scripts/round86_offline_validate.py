"""Offline evidence-reader regressions and explicit counterfactual fixtures; zero Optimize."""
import ast
import copy
import hashlib
import json
import time
from pathlib import Path
import round86_native_evidence as evidence
import round86_analyze as analysis
import round85_analyze as old_analysis
from round83_qualify import ROOT, sha, write

OUT=ROOT/'results/unified_exact_round86'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def main():
    started=time.perf_counter()
    assert not (OUT/'offline_validation_v2.json').exists()
    assert not (OUT/'campaign').exists()
    assert not (ROOT/'results/unified_exact_round85/campaign/active_run.lock').exists()
    scripts=['round86_native_evidence.py','round86_research.py','round86_analyze.py',
             'round86_offline_validate.py','round86_mechanism.py','round86_summarize.py',
             'round86_plot.py','round86_confirmation_audit.py','round86_package.py']
    for name in scripts:ast.parse((ROOT/'scripts'/name).read_text(encoding='utf-8'))
    generation=read(OUT/'generation.json')
    import subprocess
    for name,digest in generation['generators'].items():
        data=subprocess.check_output(['git','show',generation['freeze_commit']+':'+name.replace(chr(92),'/')],cwd=ROOT)
        assert sha(ROOT/name)==digest
        if name.replace(chr(92),'/')=='scripts/generate_citibike443_regional_v1.py':
            assert data.replace(b'\r\n',b'\n')==(ROOT/name).read_bytes().replace(b'\r\n',b'\n')
        else:
            assert hashlib.sha256(data).hexdigest()==digest
    old=ROOT/'results/unified_exact_round85/campaign'
    identity=read(old/'identity.json');summary=read(old/'summary.json');tests=[]
    def passed(name,detail=None):tests.append(dict(name=name,passed=True,detail=detail))
    def rejects(name,fn):
        try:fn()
        except AssertionError as exc:passed(name,str(exc));return
        raise AssertionError('Invalid evidence unexpectedly accepted: '+name)
    for launch,done in zip(identity['launches'],summary['records']):
        folder=ROOT/launch['destination'];records=read(folder/'observations.json')
        audited=evidence.audit(ROOT,launch['panel'],records,identity['binary_sha256'])
        for k in ['UB','LB','gap','physical_witnesses','native_calls_started','native_calls_returned']:
            assert audited[k]==done['audit'][k],(launch['number'],k)
        evidence.finalize_endpoint(ROOT,launch['panel'],launch['arm'],audited,records,
            read(folder/'result.json'),done['stop_reason'],identity['references'][launch['panel']['id']])
        assert audited['endpoint']==done['audit']['endpoint']
        for t in old_analysis.checkpoint_times(launch['cap']):
            assert analysis.checkpoint(records,done,t)==old_analysis.checkpoint(records,done,t)
        passed('historical_observed_run_'+str(launch['number']))
    passed('all_84_historical_checkpoints_unchanged')
    launch=identity['launches'][0];folder=ROOT/launch['destination'];panel=launch['panel']
    original=read(folder/'observations.json');result=read(folder/'result.json')
    # Altered records below are logic fixtures, never current/historical performance data.
    records=[]
    for row in original:
        if row['payload']['kind']=='witness':continue
        r=copy.deepcopy(row);r['sequence']=len(records)+1;r['payload']['sequence']=r['sequence'];records.append(r)
    audited=evidence.audit(ROOT,panel,records,identity['binary_sha256'])
    assert audited['UB'] is None and audited['gap'] is None and audited['physical_witnesses']==0
    assert audited['LB']>0
    passed('no_observed_U_retains_qualified_full_original_L')
    missing=copy.deepcopy(result)
    missing.update(status='time_limit',gurobi_solution_count=0,verified_incumbent_objective_available=False,
        upper_bound=None,gap=None,strict_certified_original_problem=False)
    no_ub=copy.deepcopy(audited)
    evidence.finalize_endpoint(ROOT,panel,'P-GRB',no_ub,records,missing,'normal_return',identity['references'][panel['id']])
    assert no_ub['endpoint']['U'] is None and no_ub['endpoint']['gap'] is None
    assert no_ub['endpoint']['L']==max(audited['LB'],missing['lower_bound'])
    no_ub['passed']=True
    done=dict(audit=no_ub,wall_seconds=2,stop_reason='normal_return')
    ep=analysis.endpoint(done);assert not ep['available'] and ep['relative_gap'] is None
    assert not analysis.checkpoint(records,done,3)['available']
    passed('normal_no_U_does_not_become_available_or_zero_gap')
    final=copy.deepcopy(audited)
    evidence.finalize_endpoint(ROOT,panel,'P-GRB',final,records,result,'normal_return',identity['references'][panel['id']])
    assert final['final_only_physical_witness'] and final['physical_witnesses']==0 and not final['witnesses']
    assert final['endpoint']['U']==result['upper_bound']
    final['passed']=True;done_final=dict(audit=final,wall_seconds=2,stop_reason='normal_return')
    assert not analysis.checkpoint(records,done_final,1.9)['available']
    assert analysis.checkpoint(records,done_final,2)['available']
    passed('final_only_physical_route_is_available_only_after_exit')
    gap=analysis.compare(analysis.endpoint(done_final),ep,12)
    assert gap['classification']=='certificate_loss_missing_candidate_UB'
    assert analysis.compare(ep,analysis.endpoint(done_final),12)['classification']=='certificate_gain_missing_reference_UB'
    passed('missing_U_cannot_hide_certificate_gain_or_loss')
    interrupted=copy.deepcopy(audited)
    evidence.finalize_endpoint(ROOT,panel,'P-GRB',interrupted,records,None,'whole_run_hard_stop',identity['references'][panel['id']])
    assert interrupted['endpoint']['U'] is None and not interrupted['endpoint']['certificate']
    passed('interrupted_no_U_remains_open')
    no_bound=copy.deepcopy(missing);no_bound['lower_bound']=None;no_bound['native_mip_best_bound_available']=False
    t=copy.deepcopy(audited)
    evidence.finalize_endpoint(ROOT,panel,'P-GRB',t,records,no_bound,'normal_return',identity['references'][panel['id']])
    assert t['endpoint']['L']==audited['LB']
    passed('unavailable_native_final_L_uses_only_previously_qualified_L')
    scopes=[r['payload'] for r in records if r['payload']['kind']=='call'];scope=scopes[0]
    bad=copy.deepcopy(scope);bad['native_preconditions']=False
    rejects('full_scope_without_native_preconditions',lambda:evidence.replay_bound(bad,.01,[]))
    bad_cut=copy.deepcopy(scope);bad_cut['full_original']=False
    rejects('restricted_cutoff_without_physical_witness',lambda:evidence.replay_bound(bad_cut,.01,[]))
    bad_records=copy.deepcopy(records)
    next(r['payload'] for r in bad_records if r['payload']['kind']=='bound')['inconsistent']=True
    rejects('inconsistent_bound_flag',lambda:evidence.audit(ROOT,panel,bad_records,identity['binary_sha256']))
    too_high=copy.deepcopy(records)
    for r in too_high:
        if r['payload']['kind']=='bound' and r['payload']['global_available']:
            r['payload']['native_bound']=result['upper_bound']+.01
            r['payload']['global_bound']=r['payload']['native_bound']
    contradictory=evidence.audit(ROOT,panel,too_high,identity['binary_sha256'])
    rejects('final_only_witness_contradicts_prior_L',lambda:evidence.finalize_endpoint(ROOT,panel,'P-GRB',contradictory,too_high,result,'normal_return',identity['references'][panel['id']]))
    wrong_model=copy.deepcopy(result);wrong_model['gurobi_model_fingerprint']=-1
    rejects('wrong_original_model_finalization',lambda:evidence.finalize_endpoint(ROOT,panel,'P-GRB',copy.deepcopy(audited),records,wrong_model,'normal_return',identity['references'][panel['id']]))
    invalid=copy.deepcopy(missing);invalid['gurobi_solution_count']=1
    rejects('native_solution_without_verified_physical_U',lambda:evidence.finalize_endpoint(ROOT,panel,'P-GRB',copy.deepcopy(audited),records,invalid,'normal_return',identity['references'][panel['id']]))
    fixture=ROOT/'build/round86/offline_receipt_fixture_v2';fixture.mkdir(parents=True,exist_ok=False)
    data=json.dumps(dict(schema=1,sequence=1)).encode('utf-8');(fixture/'event_1.json').write_bytes(data)
    receipt=fixture/'event_1.commit';receipt.write_text(f'NEJ1 1 0.5 {len(data)} {hashlib.sha256(data).hexdigest()}\n',encoding='ascii')
    assert evidence.receipt(receipt,.75,1)['effective_available_seconds']==.75
    rejects('receipt_later_than_cutoff',lambda:evidence.receipt(receipt,1.1,1))
    (fixture/'event_1.json').write_bytes(data+b' ')
    rejects('receipt_hash_or_length_mismatch',lambda:evidence.receipt(receipt,.75,1))
    passed('receipt_availability_after_complete_observation')
    output=dict(passed=True,tests=tests,test_count=len(tests),historical_runs_checked=21,
        validation_revision=2,prior_successful_receipt='offline_validation.json',
        preregistered_generator_git_bytes_checked=True,
        historical_checkpoints_checked=84,optimizer_calls=0,new_performance_runs=0,
        script_sha256={'scripts/'+n:sha(ROOT/'scripts'/n) for n in scripts},
        historical_identity_sha256=sha(old/'identity.json'),historical_summary_sha256=sha(old/'summary.json'),
        wall_seconds=time.perf_counter()-started,
        scope='Offline reader tests only. Counterfactual event/result fixtures are not native observations, performance rows, qualification calls or new evidence about algorithm speed.')
    write(OUT/'offline_validation_v2.json',output)
    print(json.dumps({k:v for k,v in output.items() if k not in ['tests','script_sha256']},indent=2))


if __name__=='__main__':main()

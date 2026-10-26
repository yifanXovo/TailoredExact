"""Controlled zero-Optimize checks of the bounded legacy-scope disposition."""
from pathlib import Path
import datetime,hashlib,json,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
import round133_read as reader
from round133_common import ROOT,OUT,BASE,ORIGINAL_PE_SHA,git,sha,write

def main():
    started=time.perf_counter();checks=[]
    def check(name,predicate):
        assert predicate,name
        checks.append(dict(name=name,passed=True))
    def rejects(name,fn):
        try:fn()
        except (AssertionError,FileNotFoundError):checks.append(dict(name=name,passed=True));return
        raise AssertionError(name+' was incorrectly accepted')
    source_files=['scripts/round133_common.py','scripts/round133_campaign.py','scripts/round133_read.py','scripts/round133_small_native.py']
    for name in source_files:compile((ROOT/name).read_bytes(),name,'exec')
    checks.append(dict(name='all_four_helpers_syntax_compile_and_import',passed=True))
    fixture=OUT/'infra/legacy_scope_controlled_fixture'
    fixture.mkdir(parents=True,exist_ok=False)
    inp=fixture/'input.txt'
    inp.write_text('2 1 [1]\ncapacities = [100000,2,2]\ninitial = [50000,1,0]\ntarget = [0,1,1]\nweights = [0,1,1]\nmin_ratio = [0,0,0]\npoints = [(0,0),(0,0),(0,0)]\n',encoding='utf-8')
    p=dict(input_path=str(inp),V=2,M=1,Q_vector=[1],T_seconds=1,pickup_seconds=60,drop_seconds=60,**{'lambda':2.**-39})
    launch=dict(version='original_E3',method='S2',arm='M-B',panel=p,command=['old.exe','--round127-mode','ms2'])
    names=('src/IntervalRowFactory.cpp','src/CplexBaseline.cpp')
    old_hashes={name:hashlib.sha256(git('show',BASE+':'+name)).hexdigest() for name in names}
    old_identity=dict(stage='D3',candidate_binary_sha256=ORIGINAL_PE_SHA,measured_source_commit=BASE,source_hashes=old_hashes)
    old_policy=reader.emitter_scope_policy(launch,old_identity)
    check('recognition_is_bound_to_fixed_old_E3_D3_ms2_emitters',old_policy['bounded_old_D3_recognition'])
    candidate_policy=reader.emitter_scope_policy(dict(launch,version='candidate'),dict(source_hashes={name:sha(ROOT/name) for name in names}))
    check('both_bound_candidate_emitters_no_longer_call_legacy_guard',candidate_policy['candidate_shortcut_removed_from_both_bound_sources'])
    cutoff=.5+p['lambda']
    call=dict(call=1,lower_g=.5,upper_g=.5,gmax=.5,cutoff=cutoff,full_original=False)
    model=dict(bounds={'Y_1':(1.,1.),'Y_2':(0.,0.)},rows=[((('e_1',1.),('e_2',1.)),'>=',1.),((),'<=' ,-1.)])
    boundary=reader.no_improver_shortcut_analysis(launch,call,model,old_policy,cutoff)
    check('equal_cutoff_old_marker_requires_scope_disposition',boundary['model_scope_issue'])
    marker=boundary['identified_legacy_shortcut_rows'][0]
    check('loaded_box_diagnostic_does_not_claim_physical_embedding',marker['physical_box_embedding_independently_proved'] is False)
    check('equal_cutoff_is_not_an_empty_inclusive_domain_proof',boundary['inclusive_domain_empty_proved_by_marker'] is False)
    check('near_cutoff_floor_is_not_automatic_old_qualification',marker['analytic_floor_qualification_automatically_granted'] is False)
    candidate_shape=reader.no_improver_shortcut_analysis(launch,call,model,candidate_policy,cutoff)
    check('genuine_candidate_constant_domain_rows_are_not_blanket_banned',not candidate_shape['model_scope_issue'] and candidate_shape['actual_constant_infeasibility_rows_zero_based']==[1])
    other=reader.no_improver_shortcut_analysis(launch,call,dict(model,rows=[((),'<=' ,-1.)]),old_policy,cutoff)
    check('unmatched_true_domain_empty_row_is_not_old_shortcut',not other['model_scope_issue'])
    no_guard=reader.no_improver_shortcut_analysis(launch,dict(call,lower_g=0.,cutoff=2.),model,old_policy,cutoff)
    check('old_source_guard_must_actually_be_satisfied',not no_guard['model_scope_issue'])
    issue=dict(models=[boundary],native_numerical_contradiction_claimed=False)
    arm=reader.legacy_unevaluable_arm(dict(F=cutoff),issue,dict(controlled_fixture_only=True))
    check('old_observation_has_no_proof_implementation_or_performance_qualification',all(arm[k] is False for k in
        ('implementation_qualified','model_scope_qualified','native_proof_qualified','performance_eligible','performance_evidence_eligible','certificate','certificate_qualified','formal_protocol_qualified')))
    check('old_observation_retains_independent_UB_floor0_without_old_control_repair',arm['U']==cutoff and arm['L']==0 and arm['gap']==cutoff and arm['old_raw_producer_did_not_recover_full_domain_open'])
    journal=dict(calls={1:call},native_quality=[],native_infeasible=[dict(call=1)],source_rejections=[])
    chain=dict(actual=[1],ledger=[dict(native_status='INFEASIBLE')])
    witness=dict(G=.5,F=cutoff,source='controlled_legal_boundary')
    source=reader.independent_source_checks(launch,journal,{1:'LP'},chain,{},[witness],{1})
    check('only_known_old_marker_INFEASIBLE_is_not_mislabeled_numeric',source['infeasibility'][0]['native_numerical_counterexample_claimed'] is False)
    rejects('ordinary_nonmarker_infeasibility_still_requires_rejection',lambda:reader.independent_source_checks(launch,journal,{1:'LP'},chain,{},[witness]))
    rejects('candidate_cannot_use_the_old_model_scope_exception',lambda:reader.independent_source_checks(dict(launch,version='candidate'),journal,{1:'LP'},chain,{},[witness],{1}))
    old_out=reader.OUT
    try:
        reader.OUT=fixture/'missing_review_gate'
        rejects('old_UNEV_compatibility_requires_prospective_independent_admission',reader.legacy_scope_gate)
    finally:reader.OUT=old_out
    receipt=dict(schema='round133-controlled-legacy-scope-check-v1',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        passed=True,checks=checks,check_count=len(checks),Optimize=0,native_starts=0,
        no_candidate_or_legacy_native_process_started=True,no_production_review_gate_created=True,
        helper_hashes={name:sha(ROOT/name) for name in source_files},driver_SHA=sha(__file__),
        seconds=time.perf_counter()-started,scope='bounded old marker recognition/disposition, source binds and helper syntax/import only')
    write(OUT/'infra/legacy_scope_fixture_receipt.json',receipt)
    print(json.dumps(dict(passed=True,checks=len(checks),Optimize=0,seconds=receipt['seconds'])),flush=True)

if __name__=='__main__':main()

"""Read-only finite admission before the only formal E2 seal."""
from round128_common import *
from round127_admission import root_model
from round128_qualify import root_diff
from round127_qualify import compare
from compare_round112_startup import reconstruct as H
import round108_reader as core
import collections

def check():
    q=OUT/'qualification';bridges=[];mdr=[]
    for role in ['S12','R98-C2']:
        left=read(q/f'native_{role}_E1/identity.json');right=read(q/f'native_{role}_E2_final/identity.json')
        la=read(q/f'native_{role}_E1/reconstructed.json')['arms'];ra=read(q/f'native_{role}_E2_final/reconstructed.json')['arms']
        assert all(a['formal_protocol_qualified'] and a['numbers_qualified'] and a['certificate_qualified'] for a in la+ra)
        for method in ['MB','P','MS2']:
            a=next(l for l in left['launches'] if l['method']==method);b=next(l for l in right['launches'] if l['method']==method)
            da,db=Path(a['destination']),Path(b['destination']);p=b['panel']
            assert right['candidate_binary_sha256']==sha(E2)
            if method!='P':
                ha,hb=H(ROOT,p,da),H(ROOT,p,db)
                assert ha['complete'] and hb['complete'] and ha['fleet']==hb['fleet'] and ha['semantic_traces']==hb['semantic_traces']
                pa,ca=root_model(da);pb,cb=root_model(db)
                assert (ca['lower_g'],ca['upper_g'],ca['cutoff'])==(cb['lower_g'],cb['upper_g'],cb['cutoff'])
                assert core.lp_model(pa)==core.lp_model(pb)
            else:assert core.lp_model(da/'compact.lp')==core.lp_model(db/'compact.lp')
            sa=[x['payload']['settings'] for x in read(da/'observations.json') if x['payload']['kind']=='call']
            sb=[x['payload']['settings'] for x in read(db/'observations.json') if x['payload']['kind']=='call']
            assert sa and sb and all(s==sa[0] for s in sa+sb)
            bridges.append(dict(role=role,method=method,actual_full_H_equal=method!='P',P_H_absent=method=='P',
                actual_initial_root_and_native_settings_equal=True,E1_PE_SHA=left['candidate_binary_sha256'],E2_PE_SHA=right['candidate_binary_sha256']))
    names=['native_S12_E2_final','native_zero_S_duration60','native_zero_S_duration3600','native_tiny_positive_U']
    for name in names:
        i=read(q/name/'identity.json');a=read(q/name/'reconstructed.json')['arms']
        for l in i['launches']:
            if l['method']!='MD-R':continue
            d=Path(l['destination']);rows=core.rows(d/'external/paper_optimize_ledger.csv');r=read(d/'result.json')
            assert [x['solve_kind'] for x in rows]==['LP','MIP'] and {x['leaf_id'] for x in rows}=={'L0'}
            assert rows[0]['model_sha256']==rows[1]['model_sha256'] and int(rows[0]['integer_domain_restored'])==1
            assert all(x['native_status']=='OPTIMAL' for x in rows)
            starts=[(p,read(p)) for p in (d/'external/native_logs').glob('*.round68.start.json')]
            pre=[(p,s) for p,s in starts if s['status']=='round128_pre_lp_validated_without_Start_submission']
            submitted=[(p,s) for p,s in starts if s['submitted']]
            assert len(pre)==len(submitted)==1 and pre[0][1]['mapping_complete'] and pre[0][1]['rows_valid'] and pre[0][1]['objective_valid']
            assert submitted[0][1]['readback_valid'] and submitted[0][1]['rows_valid']
            assert r['external_gini_tree_split_count']==r['external_gini_tree_partial_mip_optimize_count']==r['external_gini_tree_canonical_artifact_invalidation_count']==0
            assert r['external_gini_tree_warm_start_submitted_count']==1 and r['external_gini_tree_lifecycle_complete']
            result=next(x for x in a if x['method']=='MD-R');assert result['certificate'] and result['formal_protocol_qualified']
            mdr.append(dict(group=name,PE_SHA=i['candidate_binary_sha256'],calls=2,only_root=True,pre_LP_own_Start_checked=True,
                submitted_Start_count=1,U=result['U'],L=result['L'],signed_gap=result['U']-result['L']))
    review=OUT/'review/preformal_source_review.md';assert review.exists()
    open_dir=q/'native_R98-C2_MD_R_open_final'
    open_identity=read(open_dir/'identity.json');open_arm=read(open_dir/'reconstructed.json')['arms'][0]
    open_raw=Path(open_identity['launches'][0]['destination']);open_calls=core.rows(open_raw/'external/paper_optimize_ledger.csv')
    assert [x['solve_kind'] for x in open_calls]==['LP','MIP']
    assert all(open_arm[k] for k in ['formal_protocol_qualified','numbers_qualified','certificate_qualified'])
    if open_calls[-1]['native_status']!='OPTIMAL':assert not open_arm['certificate'] and open_arm['T_cert'] is None
    assert read(q/'formal_role_root_differences.json')['final_E2_PE_SHA']==sha(E2)
    assert source_bindings()==read(OUT/'E2_build.json')['source_bindings']
    summary=dict(UTC=utc(),status='PASS',bridges=bridges,MD_R_native_chains=mdr,
        boundary_checks=len(read(q/'boundary_vectors.json')['records']),formal_root_differences_SHA=sha(q/'formal_role_root_differences.json'),
        actual_Gurobi_version='13.0.2',qualified_methods=['P','MB','MD-R','MS2'],second_executor_review_SHA=sha(review),
        extra_medium_MD_R_return=dict(status=open_calls[-1]['native_status'],certificate=open_arm['certificate'],T_cert=open_arm['T_cert'],
            actual_full_root_calls=2,all_physical_model_Start_source_return_coverage_gates_qualified=True),
        qualifications_are_finite_not_universal_rational_matrix_proof=True,no_formal_performance_used=True,
        prior_failed_prequalification='native_S12_E2: actual complete Start/LP/MIP, erroneous unpopulated result counter gate; preserved, not relabelled successful')
    write(q/'admission_summary.json',summary)
    frozen=read(OUT/'E2_build.json');frozen.update(UTC_frozen=utc(),qualification_summary_SHA=sha(q/'admission_summary.json'),
        protocol_SHA=sha(OUT/'experiment_manifest.json'),contract_SHA=sha(OUT/'md_root_contract.md'),qualified_methods=summary['qualified_methods'],
        final_source_seal=True,E0_unchanged_SHA=sha(E0),E1_unchanged_SHA=sha(E1))
    write(OUT/'E2_frozen.json',frozen)
    write(OUT/'review/performance_admission.json',dict(decision='ACCEPT',qualified_methods=summary['qualified_methods'],E2_frozen_SHA=sha(OUT/'E2_frozen.json'),
        PE_SHA=sha(E2),DLL_SHA=sha(DLL),no_outcome_selected_methods=True))
    print(json.dumps(dict(admitted=summary['qualified_methods'],PE_SHA=sha(E2),H_bridges=len(bridges),MD_R_chains=len(mdr),budget=budget())))

if __name__=='__main__':check()

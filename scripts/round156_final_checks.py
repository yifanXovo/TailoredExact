"""Final bounded reconciliation of already qualified scientific artifacts.

Run only after all nine arms, the complete price reader, relocation reader,
provenance, report generation and manual claim readback have passed. The
last receipt is closed before the administrative cost export is finalized.
"""
import math
from round156_common import *

def run(complete_review,relocation_review):
    from round100_idle import ensure_idle
    configure();ensure_idle();own=os.environ['ROUND140_METERED_PARENT_LABEL'];b=budget()
    assert [r['label'] for r in b['unclosed']]==[own]
    audit_paths=['review/residual_admit_v1/result.json','review/rn_admit_v2/result.json',
        'review/actual_oracle_v1/result.json','review/fresh_producer_audit_v1/result.json',
        'review/r155_clock_correction.json',f'review/{complete_review}/result.json',
        f'review/{relocation_review}/result.json']
    audits=[]
    for name in audit_paths:
        r=read(OUT/name);assert r['PASS'],name
        audits.append(dict(path=name,SHA256=sha(OUT/name)))
    matrix=read(OUT/'confirmation_matrix.json')
    assert matrix['candidate_decision_SHA']==sha(OUT/'candidate_decision.json')
    assert matrix['candidate_manifest_SHA']==sha(OUT/'candidate_manifest.json')
    for method,digest in matrix['helper_manifests'].items():assert sha(OUT/f'helper_manifest_{method}.json')==digest
    arms=read(OUT/'reports/complete_arms.json')['arms'];pairs=read(OUT/'reports/complete_pairs.json')['pairs']
    assert len(arms)==9 and len(pairs)==6
    assert len({(r['role'],r['method']) for r in arms})==9
    for row in arms:
        endpoint=Path(row['destination'])/'round156_endpoint.json';e=read(endpoint)
        assert sha(endpoint)==row['endpoint_SHA']
        assert (row['U'],row['proof_L'],row['raw_L'])==(e['U'],e['L'],e.get('raw_search_L',e['L']))
        assert row['absolute_gap']==row['U']-row['proof_L']
        assert math.isclose(row['T_total'],row['T_produce']+row['T_verify'],abs_tol=1e-8,rel_tol=0.)
        assert row['certificate'] or row['T_cert'] is None
    for row in pairs:
        assert math.isclose(row['delta_gap'],row['delta_U']-row['delta_proof_L'],abs_tol=1e-15,rel_tol=0.)
    selected=read(OUT/'candidate_decision.json')
    assert selected['selected']=='RN16384_original_gap' and not selected['instance_identity_conditions']
    assert not selected['time_based_component_switch'] and not selected['old_4096_restart']
    oracle=read(OUT/'reports/oracle_comparison.json');rn=next(r for r in oracle['rows'] if r['method']=='RN')
    assert rn['resolved'] and rn['qualified_gap']<1e-4 and rn['lower_gain']>1e-3
    cond=next(r for r in oracle['rows'] if r['method']=='residual_U')
    base=next(r for r in oracle['rows'] if r['method']=='residual')
    assert cond['lower']>base['lower'] and cond['qualified_gap']>rn['qualified_gap'] and cond['outer_seconds']>rn['outer_seconds']
    fresh=read(OUT/'reports/fresh_producers.json')['rows'];assert len(fresh)==5
    k=next(r for r in fresh if r['role']=='K-20-S');assert k['gap']>1e-4 and k['Status']==8
    errata=read(OUT/'reports/r155_common_checkpoints.json')
    assert len(errata['rows'])==18 and len(errata['changed_bounds'])==1
    assert read(OUT/'source_manifest.json')['production_measured_source_commit']=='092bad58d677cd8bef934d91e11d8abff93cba83'
    reuse=read(OUT/'reuse_index.json');assert reuse['old_carriers_downloaded']==reuse['old_carriers_repacked']==0
    manual=read(OUT/'review/claims_readback.json');assert manual['PASS']
    for name,digest in manual['checked_files'].items():assert sha(ROOT/name)==digest
    protected=read(OUT/'infra/protected_initial.json')
    for record in protected:
        assert sha(Path(record['tree'])/record['relative'])==record['sha256']
    outcome=[dict(role=p['role'],delta_U=p['delta_U'],delta_proof_L=p['delta_proof_L'],delta_gap=p['delta_gap'],
        delta_T_total=p['delta_T_total'],delta_T_cert=p['delta_T_cert']) for p in pairs if p['first']=='E' and p['second']=='Eplus']
    write(OUT/'final_decision.json',dict(UTC=utc(),study_complete=True,scientific_blockers=[],
        selected_uniform_producer='RN16384_original_gap',selection_before_panel_SHA=sha(OUT/'candidate_decision.json'),
        matched_RN_precision_met=True,more_RN_sufficient_at_required_precision=True,
        residual_product_model_improvement_observed=True,residual_efficiency_advantage_over_RN=False,
        preselected_K20_unresolved_preserved=True,complete_arms=9,complete_Eplus_vs_E=outcome,
        stable_default='GI-TBC/B',default_promotion=False,instance_specific_policy=False,
        no_new_general_fractional_programming_theorem=True,full_inventory_hull_saturation_claim=False,
        additional_65536_or_16h_not_required='The primary original-objective precision target was already met; the capacity was not a minimum spend.',
        optional_dual_line_segment='Not opened; no result is claimed for this optional opportunity.',
        publication_recovery_cleanup_pending=True))
    write(OUT/'review/final_scientific_review.json',dict(UTC=utc(),disposition='ACCEPT_COMPLETE_ROUND156',
        scientific_blockers=[],audits=audits,complete_arms=9,complete_inventory_price_reconstructions=8,
        matched_oracle_calls=4,actual_residual_stock_lifts=29,fresh_rule_checks=5,
        original_goal_SHA=sha(OUT/'goal.md'),matrix_SHA=sha(OUT/'confirmation_matrix.json'),
        source_manifest_SHA=sha(OUT/'source_manifest.json'),reuse_index_SHA=sha(OUT/'reuse_index.json'),
        manual_claim_readback_SHA=sha(OUT/'review/claims_readback.json'),
        final_decision_SHA=sha(OUT/'final_decision.json'),same_agent_independent_reconstruction=True,
        nonimplementer_agent_review=False,Optimize=0,protected_initial_files_checked=len(protected),
        final_reader_snapshot=dict(path=f'engineering/source_snapshots/{own}.json',SHA256=sha(OUT/'engineering/source_snapshots'/f'{own}.json')),
        cost_status='This final verification outer is still open inside this reader; export costs only after its actual receipt closes.',
        closed_cost_before_this_verification=b['G1_seconds'],current_fee_label=own,
        remaining_capacity_before_this_verification=b['remaining_G1_seconds'],source_SHA=sha(__file__)))
    print(json.dumps(dict(disposition='ACCEPT_COMPLETE_ROUND156',complete_arms=9,default_promotion=False)),flush=True)

if __name__=='__main__':run(*sys.argv[1:])

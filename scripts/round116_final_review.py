"""One additional, implementer-authored seven-question organized-result review.

Runs only after actual public export, fresh restoration and core equality.
No third-party executor, native rerun, new route, bound, or failed-arm promotion.
"""
import argparse, collections, difflib, json, time
from fractions import Fraction
from pathlib import Path
import round108_reader as core
import read_round116 as admitted
import round116_source_check as source_check

def patch_check(root):
    old=(root/'scripts/read_round116.py').read_text(encoding='utf-8')
    new=(root/'scripts/read_round116_reporting.py').read_text(encoding='utf-8')
    before="vector=[dict(id=r['id'],**next(v for v in pairs if v['id']==r['id'] and v['candidate']==X and v['control']=='P-GRB'))"
    after="vector=[dict(next(v for v in pairs if v['id']==r['id'] and v['candidate']==X and v['control']=='P-GRB'))"
    assert old.count(before)==1
    expected=old.replace('Current-only manifest reconstruction using the qualified R114/R115 predicates.',
        'Offline reporting repair of the retained, unchanged admitted reader.').replace(before,after)
    assert new==expected, 'offline reporting repair exceeds the one duplicate-keyword fix'
    return dict(admitted_reader_SHA=core.sha(root/'scripts/read_round116.py'),
        reporting_reader_SHA=core.sha(root/'scripts/read_round116_reporting.py'),
        only_changes=['docstring identifies offline version','remove duplicate id keyword in already labeled pair vector'],
        native_and_proof_predicates_changed=False)

def run(root):
    tick=time.perf_counter();root=Path(root).resolve();out=root/admitted.ROUND
    candidate=core.read(out/'candidate_identity.json');fixed=core.read(out/'fixed_manifest.json')
    data=core.read(out/'reports_final/current_core.json');summary=data['summary'];arms=data['arms'];pairs=data['pairs']
    stop=core.read(out/'execution_stop.json');math=core.read(out/'objective_structure_analysis.json')
    restore=core.read(out/'public_restore_receipt.json');comparison=core.read(out/'public_reconstruction_comparison.json')
    assert restore['fresh_empty_directory'] and restore['one_restore'] and restore['all_manifest_hashes_equal']
    assert comparison['all_current_core_equal'] and comparison['organized_current_core_equal'] and not comparison['original_root_fallback']
    assert comparison['restored_root']==restore['root'] and comparison['export_commit']==restore['commit']
    for n,h in candidate['helpers'].items():assert core.sha(root/n)==h
    for n,h in candidate['source_bindings'].items():assert core.sha(root/n)==h
    assert len(candidate['source_bindings'])==206 and len(fixed['launches'])==len(arms)==24 and len(pairs)==36
    assert candidate['full_argv']==[l['command'] for l in fixed['launches']]
    patch=patch_check(root)
    lineage=source_check.check(root)
    manifest=core.read(out/'input_manifest.json');snapshot=core.read(out/'source/snapshot.json')
    assert core.sha(root/snapshot['license_path'])==candidate['license_SHA']
    assert snapshot['unique_first_valid_snapshot'] and lineage['source_rows']==865
    assert summary['execution_stage']==summary['decision']['execution_stage']==stop['execution_stage']=='BLOCKED'
    assert summary['decision']['priority']=='BLOCKED' and summary['decision']['full_panel_A_D_assessed'] is False
    assert summary['actual_formal_children']==18 and summary['qualified_formal_arms']==17 and summary['evaluable_pairs']==24
    lookup={(a['id'],a['arm']):a for a in arms};clocks=[];starts=[]
    for a in arms:
        l=next(l for l in fixed['launches'] if (l['id'],l['arm'])==(a['id'],a['arm']))
        d=admitted.portable(root,l['destination'])
        if not a['formal_protocol_qualified']:
            assert a['proof_evidence']=='UNVERIFIABLE' and a['U'] is None and a['L'] is None and a['T_total'] is None
            continue
        p=core.read(d/'producer_receipt.json');v=core.read(d/'arm_total_receipt.json')
        assert p['verification_passed'] is None and p['state']=='PRODUCED_PENDING_VERIFICATION'
        assert core.sha(d/'producer_receipt.json')==v['producer_receipt_SHA']==a['producer_receipt_SHA']
        assert p['T_produce']==a['T_produce'] and v['T_verify']==a['T_verify'] and v['T_total']==a['T_total']
        assert p['T_produce']<=l['cap_seconds'] and abs(a['T_total']-a['T_produce']-a['T_verify'])<1e-8
        ind=core.read(d/'independent_evidence.json')
        assert all(w['arm']==a['arm'] and w['input_SHA']==a['input_SHA'] for w in ind['witnesses'])
        assert admitted.proof_class(a)==a['proof_evidence']
        if a.get('source_reduced'):assert not a['native_proof_qualified'] and not a['certificate']
        if a['proof_evidence']=='OWN_ZERO_CERTIFICATE':assert a['own_exact_zero'] and a['U']==0
        if a['proof_evidence']=='CLEAN_NONZERO_CERTIFICATE':assert a['U']>0 and a['certificate'] and a['native_proof_qualified']
        if a['arm']=='P-S':
            start=core.read(d/'audit.json')['Start']
            assert start['all_native_columns_checked'] and start['all_original_numeric_rows_checked']
            assert start['before_SHA']==start['after_SHA'] and start['maximum_row_violation']<=1e-7
            starts.append(dict(id=a['id'],**start))
        clocks.append(dict(id=a['id'],arm=a['arm'],T_produce=a['T_produce'],T_verify=a['T_verify'],T_total=a['T_total']))
    assert len(starts)==4
    for p in pairs:
        expected=admitted.pair(lookup[p['id'],p['candidate']],lookup[p['id'],p['control']])
        for k,v in expected.items():assert p[k]==v
        if p['evaluable']:assert abs(p['dGap']-(p['dU']-p['dL']))<1e-12
    reliability=core.rows(out/'reports_final/numerical_reliability.csv')
    assert len(reliability)==24
    for r in reliability:r['rejected_calls']=int(r['rejected_calls']) if r['rejected_calls']!='unknown' else 'unknown'
    assert admitted.phase_decision(arms,pairs,False,reliability)==summary['decision']
    fees=core.rows(out/'reports_final/fees.csv')
    assert sum(int(q['starts']) for q in fees)==summary['budget_starts']==35
    assert abs(sum(float(q['seconds']) for q in fees)-summary['budget_seconds'])<1e-8
    assert summary['budget_seconds']<=65000
    assert sum(int(q['starts']) for q in fees if q['qualification']=='True')==10
    assert sum(float(q['seconds']) for q in fees if q['qualification']=='True')<=1800
    assert math['Optimize']==0 and math['necessary_conditions_only'] and not math['production_search_uses_analysis']
    assert not math['formal_UB_LB_certificate_fields_updated'] and len(math['roles'])==6
    for role in math['roles']:
        for interpretation,m in role['interpretations'].items():
            assert m['necessary_total_interval']==[max(0,m['B']-m['sumQ']),m['B']]
            delta=Fraction(m['delta']);assert delta>0
            for q in m['own_fleets']:
                if 'exact_U' not in q:continue
                U=Fraction(q['exact_U']);assert U>=delta*q['K']
                assert q['stronger_production_bound_or_certificate_added'] is False
                assert q['new_route_constructed'] is False
                if U>0:assert q['strict_improvement_inventory_K_max']==-(-(U/delta).numerator//(U/delta).denominator)-1
    checks={
        '1':dict(result='PASS',basis='206 source and all admitted helper bytes match; fixed24 argv/recipe/input identities retained; exact PE/DLL hashes bound to actual admission and production receipts. No new native run or result redraw.'),
        '2':dict(result='PASS',basis='Official first-valid source/license SHA,865 raw/entity row mappings, UTF-8 IDs/capacities, saved projection/inverse contract and all6 generated input bytes rechecked. Forward PROJ ran at preparation; this portable review does not independently rerun PROJ. One snapshot and synthetic demand scope are explicit.'),
        '3':dict(result='PASS_WITH_EXPLICIT_MISSING_POSITIONS',basis='Actual H100 and four qualified current P-S full-column/original-row Start records; per-arm own witnesses retain ownership. Full same-H/exposure tables have fixed six-role denominators. Failed/pending and unstarted methods do not receive contract qualification.'),
        '4':dict(result='PASS',basis='17 producer-pending/serial-total receipts and same-origin arithmetic checked; current/restored reader verified sealed outputs; failed arm retains pending with unknown completed verification/total. All fees include actual exit observation; old clocks are untouched.'),
        '5':dict(result='PASS',basis='24-position numerical reliability and proof categories checked independently of pair WINs; whole-call source reconciliation is retained. Unknown failed/unstarted evidence is UNVERIFIABLE. Own-zero and clean positive native proof are distinct; no universal numerical guarantee.'),
        '6':dict(result='PASS',basis='Six exact coefficient interpretations and stock bounds,delta/K/U identities checked; beta/strict-K are inventory necessary conditions only. No route/oracle/lattice inference or formal LB/certificate update.'),
        '7':dict(result='PASS_WITH_BLOCKED_PANEL',basis='18 actual starts,17 qualified arms,24/36 evaluable pairs,35 conservative starts within65000 seconds. Launch18 required return check failed;19–24 are unstarted. Unique BLOCKED disposition excludes full-panel A–D and automatic next round.')}
    bound_names=['final_report.md','paper_candidate_spec.md','research_phase_decision.json','objective_structure_analysis.json',
        'execution_stop.json','reports_final/current_core.json','reports_final/numerical_reliability.csv','reports_final/arms.csv','reports_final/pairs.csv',
        'public_export_receipt.json','public_restore_receipt.json','public_reconstruction_comparison.json']
    result=dict(decision='ACCEPT_BLOCKED_ORGANIZED_RESULT_FOR_DRAFT_PUBLICATION',
        reviewer='implementer-authored separate executable; not a third-party executor',
        independent_third_party_executor=False,scope='one additional seven-question review after organization and actual restored-core equality; zero native replay',
        checks=checks,actual_execution_stage='BLOCKED',actual_stage_decision=summary['decision'],
        patch_semantics=patch,source_lineage=lineage,current_full_Starts=starts,actual_qualified_clocks=clocks,
        native_PE_or_DLL_executed_in_review=False,Optimize=0,native_starts=0,
        bound_files={n:core.sha(out/n) for n in bound_names},validator_SHA=core.sha(__file__),
        signed_unix=time.time(),engineering_seconds=time.perf_counter()-tick,
        does_not_cover_own_future_commit_or_remote_state=True)
    core.write(out/'review/whole_goal01/signed_review.json',result)
    print(json.dumps({k:result[k] for k in ['decision','reviewer','actual_execution_stage','engineering_seconds']}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);run(parser.parse_args().root)

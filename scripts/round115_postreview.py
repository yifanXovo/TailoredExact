"""Once-only organized-delivery review on the restored root; no third-party claim."""
from pathlib import Path
from fractions import Fraction as R
import argparse, csv, inspect, json, time
import round115_common as common
import round115_sublevel as mathcheck
import round115_campaign as campaign
import round108_reader as core
import round114_ps as ps

csv.field_size_limit(64*1024*1024)

def review(root):
    tick=time.perf_counter();root=Path(root).resolve();out=root/'results/unified_exact_round115'
    read,sha=common.read,common.sha
    assert common.ROOT==root, 'review imported a different root'
    summary=read(out/'reports_final/summary.json');candidate=read(out/'candidate_identity.json')
    mathematical=read(out/'objective_sublevel_analysis.json');identity=read(out/'campaign/identity.json')
    science=read(root/'delivery_receipts/public_restore_receipt.json')
    rebuild=read(root/'delivery_receipts/reconstruction_receipt.json')
    base=read(root/'delivery_receipts/remote_base_preflight.json')
    proofs={};own={};clocks={}
    for l in identity['launches']:
        d=core.portable(root,l['destination']).resolve();assert d.is_relative_to(root)
        clocks[l['arm']]=common.clock_evidence(d,l)
        own[l['arm']]=core.full_fleet(root,l['panel'],read(d/'result.json'))
        assert own[l['arm']]==read(d/'production_checks.json')['final_physical_verification']==read(d/'independent_evidence.json')['physical']
        assert read(d/'audit.json')['independent_evidence_audit_passed']
        assert read(d/'verification_closeout.json')['no_new_solution_or_certificate_backfilled']

    # 1: use actual producer boundaries including prelaunch/H/closeout, not Runtime.
    assert all(c['main_clock']=='T_produce' and c['within_cap'] for c in clocks.values())
    for l in identity['launches']:
        d=core.portable(root,l['destination']);p=read(d/'producer_receipt.json')
        n=read(d/'native_end_receipt.json')
        assert p['T_produce']>=n['complete_seconds_until_native_end']
        assert p['first_arm_includes_wrapper_creation_and_import']==(l['number']==1)
        assert p['includes_H_models_online_checks_native_cleanup_serialization_supervision']
    proofs['1']=dict(result='PASS',basis='Actual perf-counter producer seal boundaries and SHA/phase receipts; original prelaunch/H/online work retained. Runtime remains nested diagnostic.',
        clocks=clocks)

    # 2: byte-level source/producer identity and no producer/verify backfill.
    for n,h in read(out/'production_identity.json')['source_bindings'].items():assert sha(root/n)==h
    for n,h in candidate['helpers'].items():assert sha(root/n)==h
    for k,n in [('offline_reader_SHA','read_round115.py'),('mathematical_verifier_SHA','round115_sublevel.py'),
            ('qualification_test_SHA','qualify_round115.py'),('qualification_post_driver_SHA','qualify_round115_post.py')]:
        assert candidate[k]==sha(root/'scripts'/n)
    assert candidate['measurement_policy_SHA']==sha(out/'measurement_policy_v2.md')
    assert candidate['dependency_graph_SHA']==sha(out/'producer_dependency_graph.json')
    old=inspect.getsource(campaign.supervisor.run_one)
    prefix=old[:old.index('    audit_started = time.perf_counter()\n')]
    assert 'child.kill()' in prefix and 'child.wait(' in prefix
    assert all(read(core.portable(root,l['destination'])/'producer_receipt.json')['verification_passed'] is None for l in identity['launches'])
    proofs['2']=dict(result='PASS',basis='All admitted helper/206 source/reader/math/policy/graph bytes match; sealed physical fleets exactly equal independent postproduction checks. Pending receipts remain null. Original source-extracted supervisor prefix retains cleanup and deadline behavior.',
        new_UB_or_native_certificate_backfilled=False,producer_SHA=sha(root/'scripts/round115_campaign.py'))

    # 3: original historical eligibility and denominators, no old-clock reconstruction.
    oldarms=list(csv.DictReader((out/'reports_final/inherited_arms.csv').open(newline='',encoding='utf-8')))
    cold=next(a for a in oldarms if a['id']=='G50-C1' and a['arm']=='P-GRB')
    assert cold['formal_protocol_qualified']=='False' and all(cold[k]=='' for k in ['U','L','complete_seconds'])
    history=list(csv.DictReader((out/'historical_r114/new_arms.csv').open(newline='',encoding='utf-8')))
    ens=next(a for a in history if a['arm']=='ENS-C')
    assert ens['formal_protocol_qualified']=='False' and float(ens['complete_seconds'])==3605.688342700014
    assert summary['old_G50_P_pairs_still_unqualified']==3 and summary['no_historical_clock_recreated']
    proofs['3']=dict(result='PASS',basis='Signed inherited G50 cold-P clock/U/L stay absent; original R114 ENS whole3605.688342700014 stays ineligible. Six new pairs contain only origin115.',
        historical_clocks_rewritten=False,old_G50_P_missing=True)

    # 4: same source/argv/windows/problem and symmetric whole-call rejection.
    assert [l['arm'] for l in identity['launches']]==['P-GRB','ENS-C','P-S','M-B']
    assert all(l['cap_seconds']==3600 and l['hard_stop_seconds']==3598 for l in identity['launches'])
    assert candidate['full_argv']==[l['command'] for l in identity['launches']]
    gate=read(out/'review/performance_admission.json')
    assert gate['native_argv_semantic_identity'] and gate['candidate_identity_SHA']==sha(out/'candidate_identity.json')
    claims=read(out/'reports_final/cohort_reconciliation.json')
    assert {(q['arm'],q['call']) for q in claims['damaged_calls']}=={('P-GRB',1),('ENS-C',4),('P-S',1),('M-B',4)}
    assert all(q['call_rejected_as_a_whole'] and q['domain_verified'] for q in claims['rejections'])
    for l in identity['launches']:
        assert sha(root/l['panel']['input_path'])==l['panel']['input_sha256']
        observations=read(core.portable(root,l['destination'])/'observations.json')
        assert all(q['payload']['settings']==ps.SETTINGS for q in observations if q['payload']['kind']=='call')
    psind=read(core.portable(root,identity['launches'][2]['destination'])/'independent_evidence.json')
    assert psind['narrow_missing_return']['branch']=='BOUND_WITNESS_LATCH_LAST_MIP_OWN_ZERO_NORMAL_RETURN'
    assert psind['narrow_missing_return']['journal_returned']==0 and psind['narrow_missing_return']['independently_verified_returned']==1
    start=read(out/'formal_compact_Start.json');assert start['all_native_columns_checked'] and start['all_original_numeric_rows_checked']
    proofs['4']=dict(result='PASS',basis='All original argv/settings/windows/input/identity match. All four damaged calls are wholly rejected under the same unchanged policy. P-S missing returned is explicitly retained under the inherited narrow gate; actual return and all-column Start remain checked.',
        engine_repaired=False,damaged_calls=claims['damaged_calls'])

    # 5: independently recompute original rational objective/conservation on restored input.
    finite=mathcheck.finite_checks();core.start_reader.ROOT=root
    roles=read(out/'inherited_r113/input_manifest.json')['roles'];g50=next(p for p in roles if p['id']=='G50-C1')
    calculated={}
    for mode in ['input_decimal','parsed_binary64']:
        a=mathcheck.instance(root/g50['input_path'],mode);b=mathcheck.bound(a)
        assert b['B']==b['sumD']==527 and b['sumQ']==120 and all(q['sigma']==-1 for q in b['J'])
        assert b['beta']==mathematical['G50-C1'][mode]['beta']
        for arm,num in [('M-B',1),('P-S',3)]:
            raw=out/'inherited_r113/authoritative/campaign/raw'/f'{num:02d}_G50-C1_S0_{arm}'/'result.json'
            Y=core.full_fleet(root,g50,read(raw))['Y'][1:]
            assert mathcheck.objective(a,Y)==R(b['beta'])
        calculated[mode]=dict(beta=b['beta'],delta=b['delta'],minimizers=b['minimizers'],necessary_total_interval=b['necessary_total_interval'])
    proofs['5']=dict(result='PASS',basis='Direct rational Gini/penalty, all J states/phi, finite n2/3 capacity/total enumeration, and restored legal G50 own fleets independently reproduce beta under both coefficient interpretations. Positive sigma is excluded by total conservation. J is necessary only; no routing sufficiency or beta lattice claim.',
        arithmetic=calculated,finite_cases=len(finite),Optimize=0)

    # 6: current G100 prior/after distinction, no unmeasured speedup or mechanism.
    assert own['P-S']['Y'][1:]==core.evidence.instance(root,identity['launches'][2]['panel'])['D'][1:] and own['P-S']['F']==0
    for mode in ['input_decimal','parsed_binary64']:
        a=mathcheck.instance(root/identity['launches'][0]['panel']['input_path'],mode);b=mathcheck.bound(a)
        assert b['beta']==mathematical['G100-R2'][mode]['beta']
        for arm in ['P-GRB','ENS-C','M-B']:assert mathcheck.objective(a,own[arm]['Y'][1:])>R(b['beta'])
        m=mathematical['G100-R2'][mode]
        assert m['zero_optimum_known_at_preregistration'] is False and m['zero_optimum_known_after_R115'] is True
    assert not mathematical['production_search_uses_analysis'] and mathematical['Optimize']==0 and mathematical['new_routes']==0
    phase=read(out/'research_phase_decision.json');assert phase['priority']=='A' and not phase['automatic_followup']
    assert all(v['status']=='MIXED' and v['heterogeneous_measurement_policy'] for v in summary['scientific_status'].values())
    proofs['6']=dict(result='PASS',basis='G100 positive U exceeds beta; actual P-S own sealed zero now establishes optimum. G50 target existence was already known from ENS. Exact sublevel qualification is offline and unmeasured as an algorithm; inherited R61 full-fleet scope and phase A are explicit.',
        production_mechanism_changed=False,phase='A')

    # 7: actual restore/core equality and paid budgets; future PR assertions excluded.
    assert summary['conservative_starts']==12<=24 and summary['outer_seconds_upper']==12590.651394605637<20000
    assert summary['qualification_starts']==7<=10 and summary['qualification_seconds']<600
    assert (summary['layered_arm_positions'],summary['total_qualified_measurements'],summary['pair_positions'],summary['evaluable_pairs'])==(20,19,30,27)
    assert science['fresh_empty_directory'] and science['all_manifest_hashes_equal'] and not science['original_root_fallback']
    assert Path(science['root']).resolve()==root and rebuild['exit_code']==0
    assert rebuild['core_comparison']['all_fields_equal'] and not rebuild['core_comparison']['original_worktree_fallback']
    assert base['headRefName']=='codex/round114-bound-claim-isolation-g100' and base['state']=='OPEN' and base['isDraft']
    assert base['headRefOid']=='e436748521cf5aabbe84a24a5e9cf3836550563c'
    proofs['7']=dict(result='PASS',basis='Actual Git-exported empty-root hash restore and all current core fields reproduce; fixed denominators/old missing comparisons/budgets are preserved. R114 intended stacked base is verified live. New PR publication is pending and is explicitly not claimed in this review.',
        budget_seconds=summary['outer_seconds_upper'],positions=20,qualified=19,pairs=30,evaluable=27,
        reconstructed_files=rebuild['core_comparison']['files'],public_commit=science['commit'],new_PR_remote_verification_pending=True)

    bound=['final_report.md','research_phase_decision.md','research_phase_decision.json','measurement_policy_v2.md',
        'objective_sublevel_analysis.md','objective_sublevel_analysis.json','objective_sublevel_analysis_raw.json',
        'reports_final/summary.json','reports_final/new_arms.csv','reports_final/new_pairs.csv',
        'reports_final/backend_conclusions.json','secondary_time_comparison.json','secondary_total_pairs.csv','pr_body.md']
    result=dict(decision='ACCEPT_COMPLETE_SCIENTIFIC_DELIVERY_FOR_DRAFT_PUBLICATION',checks=proofs,
        reviewer='implementer-authored separate executable on restored root; no independent person or agent',
        independent_third_party_executor=False,reviewed_unix=time.time(),seconds=time.perf_counter()-tick,
        Optimize=0,native_starts=0,performance_replay=False,original_worktree_core_fallback=False,
        reviewer_SHA=sha(__file__),bound_files={n:sha(out/n) for n in bound},
        actual_restore_receipt_SHA=sha(root/'delivery_receipts/public_restore_receipt.json'),
        actual_reconstruction_receipt_SHA=sha(root/'delivery_receipts/reconstruction_receipt.json'),
        already_organized_complete_payload=True,checks_run_once=True,future_PR_verification_not_in_review=True)
    common.write(out/'review/whole_goal01/signed_review.json',result)
    print(json.dumps(dict(decision=result['decision'],checks={k:v['result'] for k,v in proofs.items()},
        seconds=result['seconds'],independent_third_party_executor=False)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);args=parser.parse_args();review(args.root)

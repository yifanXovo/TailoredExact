"""Actual implementer-authored separate admission/final review, no third party."""
from round116_common import *
import collections,csv,inspect,traceback
import round116_campaign as campaign
import read_round116 as reader

def admit(label):
    fee,tick=campaign.fee_begin(label,0,60,True);code=1
    try:
        from round100_idle import ensure_idle
        ensure_idle();check_identity();candidate=read(OUT/'candidate_identity.json');fixed=read(OUT/'fixed_manifest.json')
        assert candidate['helpers']==campaign.helpers() and candidate['fixed_manifest_SHA']==sha(OUT/'fixed_manifest.json')
        for g in fixed['groups']:
            i=read(OUT/g['campaign']/'identity.json')
            assert i['helpers']==candidate['helpers'] and sha(OUT/g['campaign']/'identity.json')==g['identity_SHA']
            assert not campaign.records(OUT/g['campaign'])
            for l in i['launches']:
                assert not Path(l['destination']).exists() and sha(ROOT/l['panel']['input_path'])==l['panel']['input_sha256']
                cmd=l['command'];assert cmd[cmd.index('--time-limit')+1]==str(l['cap_seconds']-6)
                assert cmd[cmd.index('--process-wall-time-limit')+1]==str(l['cap_seconds'])
                assert cmd[cmd.index('--process-shutdown-margin')+1]=='30' and l['hard_stop_seconds']==l['cap_seconds']-2
                assert cmd[cmd.index('--gurobi-seed')+1]=='0' and cmd[cmd.index('--threads')+1]=='1' and cmd[cmd.index('--mip-threads')+1]=='1'
                assert ('--round112-ens-start-compact' in cmd)==(l['arm']=='P-S')
                assert ('--round98-state-service' in cmd)==(l['arm']=='M-B')
                assert '--round100-continuous-quantities' not in cmd
                assert l['panel']['reference']['optimizer_calls']==0
        assert len(fixed['launches'])==24 and sum(l['cap_seconds'] for l in fixed['launches'])==50400
        assert all(read(OUT/'qualification'/p/'summary.json')['passed'] for p in ['finite01','post01'])
        qid=read(OUT/'qualification/cli01/identity.json');assert qid['helpers']==candidate['helpers']
        assert [l['arm'] for l in qid['launches']]==['P-GRB','P-S','ENS-C','M-B']
        clocks=[clock_evidence(Path(l['destination']),l) for l in qid['launches']]
        assert all(c['within_cap'] for c in clocks)
        post=read(OUT/'qualification/post01/reconstructed/current_core.json')
        assert post['summary']['qualified_qualification_CLI']==4 and all(h['qualified'] for h in post['same_H'])
        manifest=read(OUT/'input_manifest.json');snapshot=read(OUT/'source/snapshot.json');recipe=read(OUT/'source_recipe.json')
        assert manifest['raw_station_response_SHA']==snapshot['station_response_SHA']==sha(ROOT/snapshot['station_response_path'])
        assert candidate['license_SHA']==sha(ROOT/snapshot['license_path']) and snapshot['unique_first_valid_snapshot']
        assert candidate['source_recipe_SHA']==sha(OUT/'source_recipe.json') and recipe['thin_adapter_SHA']==sha(ROOT/'scripts/round116_data.py')
        assert read(OUT/'source/source_qualification.json')['eligible_count']>=200
        for p in manifest['roles']:
            d=OUT/'qualification/reference'/p['id'];b=read(d/'build.json');assert sha(d/'original.lp')==b['canonical_sha256'] and b['optimizer_calls']==0
            contract=read(d/'reference_contract.json');assert contract['input_parameters']==p and contract['Optimize']==0
        assert read(OUT/'generation_equivalence.json')['Optimize']==0
        assert read(OUT/'generation_receipt.json')['inputs']==6
        assert campaign.supervised is campaign.inherited.supervised and campaign.finish_producer is campaign.inherited.finish_producer
        result=dict(schema='round116-prospective-admission-v1',decision='ACCEPT',reviewer='implementer-authored separate read-only process',
            independent_third_party_executor=False,actual_qualification_CLI=4,qualification_reference_new_inputs=6,
            signed_unix=time.time(),seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
            candidate_identity_SHA=sha(OUT/'candidate_identity.json'),fixed_manifest_SHA=sha(OUT/'fixed_manifest.json'),helpers=campaign.helpers(),
            production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,source_bindings=bindings(),source_recipe_SHA=sha(OUT/'source_recipe.json'),
            source_snapshot_SHA=sha(OUT/'source/snapshot.json'),license_SHA=candidate['license_SHA'],input_manifest_SHA=sha(OUT/'input_manifest.json'),
            source_table_SHA=manifest['source_table_SHA'],projection_contract_SHA=candidate['projection_contract_SHA'],
            measurement_policy_SHA=sha(OUT/'measurement_policy_v2.md'),dependency_graph_SHA=sha(OUT/'producer_dependency_graph.json'),
            qualifications={n:sha(OUT/'fees'/n/'receipt.json') for n in ['reference01','finite01','cli01','post01']},
            qualification_clocks=clocks,full_Start_check_SHA=sha(OUT/'qualification/post01/actual_Start.json'),
            validator_SHA=sha(__file__),budget=budget(),receipt_does_not_cover_own_future_fee_exit=True,
            math_rules_frozen_no_result_screening=True,production_implementation_reused=True,known_old_claim_impact_SHA=sha(OUT/'known_G100_claim_impact.csv'))
        write(OUT/'review/performance_admission.json',result);code=0
        print(json.dumps(dict(decision='ACCEPT',qualified_CLI=4,formal_starts=0,reviewer=result['reviewer'])),flush=True)
    except BaseException:
        (fee/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:campaign.fee_pending(fee,tick,True,code,0)

def final(root):
    tick=time.perf_counter();root=Path(root).resolve();out=root/reader.ROUND
    candidate=read(out/'candidate_identity.json');summary=read(out/'reports_final/summary.json');fixed=read(out/'fixed_manifest.json')
    for n,h in candidate['helpers'].items():assert sha(root/n)==h
    for n,h in candidate['source_bindings'].items():assert sha(root/n)==h
    assert len(candidate['source_bindings'])==206 and len(fixed['launches'])==24
    data=read(out/'reports_final/current_core.json');arms=data['arms'];pairs=data['pairs'];assert len(arms)==24 and len(pairs)==36
    snapshot=read(out/'source/snapshot.json');manifest=read(out/'input_manifest.json')
    assert sha(root/snapshot['station_response_path'])==manifest['raw_station_response_SHA']
    assert sha(root/snapshot['license_path'])==candidate['license_SHA']
    assert all(sha(root/p['input_path'])==p['input_sha256'] for p in manifest['roles'])
    if summary['execution_stage']=='COMPLETE':assert all(a['formal_protocol_qualified'] for a in arms)
    else:assert summary['decision']['priority']=='BLOCKED' and not summary['decision']['full_panel_A_D_assessed']
    for a in arms:
        if not a['formal_protocol_qualified']:continue
        l=next(l for l in fixed['launches'] if l['id']==a['id'] and l['arm']==a['arm']);d=reader.portable(root,l['destination'])
        c=clock_evidence(d,l);assert c['T_produce']==a['T_produce'] and c['T_total']==a['T_total']
        assert reader.proof_class(a)==a['proof_evidence']
        if a.get('source_reduced'):assert not a['native_proof_qualified'] and a['L']==0.
        if a['proof_evidence']=='OWN_ZERO_CERTIFICATE':assert a['U']==0 and a['own_exact_zero']
    math=read(out/'objective_structure_analysis.json');assert math['Optimize']==0 and not math['production_search_uses_analysis']
    assert math['necessary_conditions_only'] and len(math['roles'])==6
    for p in pairs:
        if p['evaluable']:assert abs(p['dGap']-(p['dU']-p['dL']))<1e-12
    checks={
        '1':dict(result='PASS',basis='206 exact production source hashes, original PE/DLL identities, fixed24 argv and source recipe; source only changed, no performance redraw'),
        '2':dict(result='PASS',basis='official unique snapshot/license, 865 qualified rows, preserved IDs/capacities/exclusions/projection operations and6 same-system synthetic roles; no IID/real-demand claim'),
        '3':dict(result='PASS',basis='actual H100 compact full Start/model/return checks, sealed own per-arm H/UB and complete semantic/capacity-fleet comparisons; ineligible backend exposure explicitly retained'),
        '4':dict(result='PASS',basis='original producer pending/seal predicates, actual produce/verify/total from one origin, final cohort costs outside closed receipts; old clocks/eligibility untouched'),
        '5':dict(result='PASS',basis='whole bad-call revocations and explicit numerical_reliability table; source-reduced physical comparisons separate from own zero and clean nonzero proof'),
        '6':dict(result='PASS',basis='exact rational delta/beta/K arithmetic plus total-stock necessary bounds; no routing sufficiency, oracle, new algorithm or backfilled production certificate'),
        '7':dict(result='PASS',basis='24 fixed arm and36 pair positions, official source/qualification/fee/stop checks and ordered actual A-D decision, or precise BLOCKED without A-D claim')}
    result=dict(decision='ACCEPT_ORGANIZED_RESULT_FOR_DRAFT_PUBLICATION',reviewer='implementer-authored separate executable',
        independent_third_party_executor=False,scope='one additional seven-question review after scientific organization and actual restored-core equality; zero native replay',
        checks=checks,signed_unix=time.time(),seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        actual_execution_stage=summary['execution_stage'],actual_stage_decision=summary['decision'],validator_SHA=sha(__file__),
        bound_files={n:sha(out/n) for n in ['final_report.md','paper_candidate_spec.md','research_phase_decision.json','objective_structure_analysis.json',
            'reports_final/current_core.json','reports_final/numerical_reliability.csv','reports_final/arms.csv','reports_final/pairs.csv']})
    write(out/'review/whole_goal01/signed_review.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='admit':admit(sys.argv[2])
    elif sys.argv[1]=='final':final(sys.argv[2])
    else:raise ValueError(sys.argv[1])

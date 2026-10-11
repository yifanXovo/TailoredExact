"""Actual separate read-only validation process; implementer-authored, not third-party."""
from round115_common import *
import csv,json,inspect,sys,time
import round115_campaign as campaign
import read_round115 as reader
import round115_sublevel as arithmetic

def admit():
    tick=time.perf_counter();candidate=read(OUT/'candidate_identity.json');identity=read(OUT/'campaign/identity.json')
    check_identity();assert not campaign.records(OUT/'campaign') and not budget()['unclosed']
    assert candidate['helpers']==campaign.helpers()==identity['helpers']
    assert candidate['campaign_identity_SHA']==sha(OUT/'campaign/identity.json')
    assert candidate['qualification_campaign_identity_SHA']==sha(OUT/'qualification/cli01/identity.json')
    for key,name in [('qualification_test_SHA','qualify_round115.py'),('qualification_post_driver_SHA','qualify_round115_post.py'),
            ('offline_reader_SHA','read_round115.py'),('mathematical_verifier_SHA','round115_sublevel.py')]:
        assert candidate[key]==sha(ROOT/'scripts'/name)
    assert candidate['measurement_policy_SHA']==sha(OUT/'measurement_policy_v2.md') and candidate['dependency_graph_SHA']==sha(OUT/'producer_dependency_graph.json')
    for n in ['finite01','post01']:assert read(OUT/'qualification'/n/'summary.json')['passed']
    qid=read(OUT/'qualification/cli01/identity.json');assert [l['arm'] for l in qid['launches']]==['P-GRB','P-S','ENS-C','M-B']
    assert all(l['cap_seconds']==120 and l['seed']==0 for l in qid['launches'])
    clocks=[clock_evidence(Path(l['destination']),l) for l in qid['launches']];assert all(c['within_cap'] for c in clocks)
    same=read(OUT/'qualification/post01/same_H.json');assert all(q['qualified'] for q in same['comparisons'])
    previous=read(Path('E:/codes/ExactEBRP-round114/results/unified_exact_round114/campaign/identity.json'))
    def semantic(cmd):
        return [s.replace(str(ROOT),'ROOT').replace(str(ROOT).replace('\\','/'),'ROOT')
            .replace('E:\\codes\\ExactEBRP-round114','ROOT').replace('E:/codes/ExactEBRP-round114','ROOT')
            .replace('round115','round114') for s in cmd]
    for a,b in zip(identity['launches'],previous['launches']):
        assert a['arm']==b['arm'] and a['cap_seconds']==b['cap_seconds']==3600 and a['hard_stop_seconds']==b['hard_stop_seconds']
        assert semantic(a['command'])==semantic(b['command']),('native argv drift',a['arm'])
    # Source-extracted production supervisor preserves the entire original prefix.
    ns=dict(vars(campaign.supervisor));campaign.supervisor_function(ns)
    original=inspect.getsource(campaign.supervisor.run_one);cut=original.index('    audit_started = time.perf_counter()\n')
    assert 'child.kill()' in original[:cut] and 'child.wait(' in original[:cut]
    arithmetic.finite_checks()
    mathematical=arithmetic.run('objective_sublevel_preformal')
    assert all(q['exact_U_equals_beta'] for q in mathematical['G50-C1']['input_decimal']['own_fleets'])
    b=budget();assert b['qualification_starts']<=10 and b['qualification_seconds']<=600
    assert b['remaining_starts']>=5 and b['remaining_outer_seconds']>=14520
    result=dict(schema='round115-prospective-admission-v2',decision='ACCEPT',reviewer='implementer-authored separate read-only process',
        independent_third_party_executor=False,review_boundary='actual fixed CLI and independent arithmetic/control checks; no third-party rerun claimed',
        signed_unix=time.time(),seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        production_identity_SHA=sha(OUT/'production_identity.json'),production_PE_SHA=PE_SHA,DLL_SHA=DLL_SHA,helpers=campaign.helpers(),
        measurement_policy_SHA=candidate['measurement_policy_SHA'],dependency_graph_SHA=candidate['dependency_graph_SHA'],
        qualification_receipts={n:sha(OUT/'fees'/n/'receipt.json') for n in ['finite01','cli01','post01']},
        qualification_clocks=clocks,same_H_SHA=sha(OUT/'qualification/post01/same_H.json'),native_argv_semantic_identity=True,
        mathematical_preformal_SHA=sha(OUT/'objective_sublevel_preformal.json'),
        original_R90_supervision_prefix_retained=True,full_audit_moved_only_after_native_stopped=True,
        validator_SHA=sha(__file__),budget=b)
    write(OUT/'review/performance_admission.json',result)
    print(json.dumps(dict(decision=result['decision'],seconds=result['seconds'],budget=b)),flush=True)

def final_review(root):
    tick=time.perf_counter();root=Path(root);out=root/'results/unified_exact_round115'
    summary=read(out/'reports_final/summary.json');math=read(out/'objective_sublevel_analysis.json');candidate=read(out/'candidate_identity.json')
    for n,h in candidate['helpers'].items():assert sha(root/n)==h
    assert all(read(out/'qualification'/n/'summary.json')['passed'] for n in ['finite01','post01'])
    assert summary['new_qualified_measurements']==4 and summary['evaluable_pairs']==27 and summary['total_qualified_measurements']==19
    assert summary['old_G50_P_pairs_still_unqualified']==3 and summary['main_clock']=='T_produce'
    assert read(out/'research_phase_decision.json')['priority'] in ['A','B','C']
    for mode in ['input_decimal','parsed_binary64']:
        b=math['G50-C1'][mode];assert all(q['exact_U_equals_beta'] for q in b['own_fleets'])
        assert all(q['sigma']==-1 for q in b['J']) and b['B']==b['sumD']==527
    assert math['Optimize']==0 and not math['production_search_uses_analysis']
    for l in read(out/'campaign/identity.json')['launches']:
        d=reader.namespace['portable'](root,l['destination']);c=clock_evidence(d,l)
        assert c['within_cap'] and read(d/'audit.json')['independent_evidence_audit_passed']
    # Review is after the complete scientific organization, once; restored-root repetition
    # is a reconstruction verification rather than another performance or scientific review.
    result=dict(decision='ACCEPT_COMPLETE_SCIENTIFIC_DELIVERY',scope='actual read-only arithmetic/source/evidence review of organized results',
        reviewer='implementer-authored separate executable; no independent person or agent',independent_third_party_executor=False,
        Optimize=0,native_starts=0,seconds=time.perf_counter()-tick,reviewed_unix=time.time(),
        checks={str(i):'PASS' for i in range(1,8)},new_arms=4,new_pairs=6,qualified_positions=19,evaluable_pairs=27,
        preserved_old_missing_G50_P=True,reviewer_SHA=sha(__file__),
        bound_files={n:sha(out/n) for n in ['final_report.md','research_phase_decision.md','research_phase_decision.json',
            'measurement_policy_v2.md','objective_sublevel_analysis.md','objective_sublevel_analysis.json','reports_final/summary.json',
            'reports_final/new_arms.csv','reports_final/new_pairs.csv','reports_final/backend_conclusions.json']})
    write(out/'review/whole_goal01/signed_review.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='admit':admit()
    elif sys.argv[1]=='final':final_review(sys.argv[2])
    else:raise ValueError(sys.argv[1])

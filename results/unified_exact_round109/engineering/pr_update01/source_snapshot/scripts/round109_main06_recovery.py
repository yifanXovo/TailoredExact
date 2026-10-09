"""Explicit known-call mathematical/return evidence repair; no solver work.

Original files, failed audit and absent returned/whole receipts stay intact.
The two known tuples are not a generic fallback for another numerical fault.
"""
from pathlib import Path
import copy,hashlib,math,sys
import round108_reader as core
import round109_numerical_recovery as prior
read,write,sha=core.read,core.write,core.sha
REL=prior.REL
SIDE=REL/'campaign/reader_recovery/main06_numerical02.json'
PREFIX=REL/'campaign/reader_recovery/main06_original_summary01.jsonl'
KEY=(17,'G50-C2',0,'P-GRB')
SOURCES=['round109_main06_recovery.py','round109_interval_pairs.py','round109_prepaid_wrapper.py','round109_reader.py','round109_decisions.py']

def inherited_proof(root):
    root=Path(root);saved=read(root/prior.SIDE);actual=prior.facts(root)
    snapshot=root/REL/'engineering/main06_reader_source_before01/round109_reader_before.py'
    assert sha(snapshot)==saved['reader_SHA']=='75b7d1e1f5cd313f65ab13fac162ca71dbba2fedac4796eafcf4a4492674501b'
    # Sole current-vs-historical difference is the separately bound reader.
    # Every original raw/model/helper/source check is still recomputed.
    actual['reader_SHA']=sha(snapshot);assert actual==saved
    return saved

def functional(r,c,phases,text):
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    assert r['gurobi_optimize_count']==1 and r['gurobi_optimize_return_code']==r['native_mipopt_return_code']==0
    assert r['gurobi_solver_finalization_reached'] is True and r['native_mip_solver_finalization_reached'] is True
    for k in ['native_mip_evidence_capture_complete','native_mip_problem_freed','native_mip_environment_closed','native_mip_lifecycle_valid']:
        assert r[k] is True
    for k in ['native_mip_freeprob_return_code','native_mip_close_return_code']:assert r[k]==0
    for k in ['native_mip_environment_count','native_mip_problem_count','native_mip_model_read_count','native_mip_mipopt_count','native_mip_freeprob_count','native_mip_close_count']:
        assert r[k]==1
    assert r['gurobi_status']==2 and 'Optimal solution found (tolerance 0.00e+00)' in text
    assert 'Best objective 0.000000000000e+00, best bound 0.000000000000e+00' in text
    events=[v['event'] for v in phases]
    for name in ['plain_gurobi_optimize_launch','final_result_serialization_start','final_result_serialization_complete','process_exit']:assert events.count(name)==1
    assert events.index('plain_gurobi_optimize_launch')<events.index('final_result_serialization_start')<events.index('final_result_serialization_complete')<events.index('process_exit')
    assert phases[-1]['event']=='process_exit' and phases[-1]['status']=='complete' and phases[-1]['detail']=='rc=0'

def facts(root):
    root=Path(root).resolve();out=root/REL;ident=read(out/'campaign/identity.json');cand=read(out/'candidate_identity.json')
    old=inherited_proof(root);launch=ident['launches'][16];assert prior.key(launch)==KEY
    contract=read(out/'review/main06_recovery_contract_review01.json')
    assert contract['decision']=='CONDITIONAL_ACCEPT_READER_AND_PREPAID_SLOT_RECOVERY'
    assert contract['candidate_identity_SHA']==sha(out/'candidate_identity.json') and contract['original_campaign_identity_SHA']==sha(out/'campaign/identity.json')
    diag=out/'review/main06_diagnosis02/audit.json';witness=out/'review/main06_diagnosis02/exact_binary64_witness.json'
    if not witness.exists():
        matches=[v for v in diag.parent.glob('*.json') if sha(v)==contract['own_exact_cold_vector_SHA']];assert len(matches)==1;witness=matches[0]
    assert sha(diag)==contract['actual_independent_diagnosis_SHA'] and sha(witness)==contract['own_exact_cold_vector_SHA']
    assert read(diag)['decision']=='ACCEPT_DIAGNOSIS_CONDITIONAL_RECOVERY'
    d=core.portable(root,launch['destination']);p=launch['panel'];r=read(d/'result.json');c=read(d/'completion.json');obs=read(d/'observations.json')
    calls=[v['payload'] for v in obs if v['payload']['kind']=='call'];bs=[v['payload'] for v in obs if v['payload']['kind']=='bound']
    failure=[v['payload'] for v in obs if v['payload']['kind']=='failure']
    assert len(calls)==1 and [(v['sequence'],v['native_bound']) for v in bs]==[(3,0.),(37,1.816725899087706e-6)]
    assert failure==[dict(schema=1,sequence=142,kind='failure',reason='full_bound_witness_inconsistency')]
    assert len(obs)==142 and not any(v['payload']['kind'] in ['returned','not_started'] for v in obs)
    for i,v in enumerate(obs,1):
        assert v['payload']['sequence']==v['sequence']==i
        raw=d/'journal'/f'event_{i}.json';commit=(d/'journal'/f'event_{i}.commit').read_text().split()
        assert sha(raw)==v['sha256'] and read(raw)==v['payload'] and int(commit[1])==i and int(commit[3])==raw.stat().st_size and commit[4]==sha(raw)
    phases=core.rows(d/'phases.csv');functional(r,c,phases,(d/'native.log').read_text())
    assert read(d/'audit.json')['passed'] is False and read(d/'audit.json')['error']=="AssertionError('full_bound_witness_inconsistency')"
    assert r['algorithm_preset']=='custom' and r['gurobi_hga_start_requested'] is False and r['gurobi_native_domain_audit_passed'] is True
    model_SHA=sha(d/'compact.lp');assert model_SHA==p['reference']['canonical_sha256']==sha(out/'campaign/reference'/p['id']/'original.lp')
    saved_launch=read(d/'launch.json');assert saved_launch['command']==launch['command'] and saved_launch['panel']==p and saved_launch['prereg_sha256']==ident['prereg_sha256']
    prior.scope(calls[0],c,saved_launch['command'],launch['command'],model_SHA)
    for name,field in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:assert r[field]==p['reference'][name]
    assert sha(root/p['input_path'])==p['input_sha256']
    info,model=core.model_contract(root,p,d/'compact.lp','P-GRB');q=core.evidence.instance(root,p)
    L=prior.floor(p['lambda'],q['w'][1:],q['D'][1:],model['objective'],model['bounds'])
    ph=core.full_fleet(root,p,r);assert ph['F']==ph['G']==ph['P']==0. and ph['Y'][1:]==q['D'][1:]
    zero=obs[140]['payload'];assert zero['kind']=='witness' and zero['source']=='native_MIPSOL_verified_original_routes' and zero['objective']==zero['G']==zero['P']==0
    zph=core.full_fleet(root,p,zero);assert zph['F']==0. and zph['Y']==ph['Y']
    assert r['native_mip_best_bound']==r['native_mip_objective']==r['upper_bound']==r['lower_bound']==0. and r['strict_certified_original_problem'] is True
    fee=out/'fees/main06/receipt.json';f=read(fee);assert sha(fee)==contract['prepaid_coupon']['original_receipt_SHA']
    assert f['exit_code']==1 and f['conservative_process_starts']==4 and f['actual_native_children_with_launch']==2
    ens=core.portable(root,ident['launches'][15]['destination'])/'whole_arm_receipt.json'
    lower=c['fully_observed_end_to_end_seconds'];unrounded=f['outer_seconds']-read(ens)['complete_seconds'];upper=math.ceil(unrounded*1e6)/1e6
    assert [lower,upper]==contract['timing']['interval'];prior.interval(lower,upper,launch['cap_seconds'])
    assert not (d/'whole_arm_receipt.json').exists()
    snapshot=root/PREFIX;prefix=snapshot.read_bytes();current=(out/'campaign/summary.jsonl').read_bytes()
    assert current.startswith(prefix) and len(prefix.splitlines())==17
    final=read_lines(prefix)[-1];assert final['number']==17 and final['audit_passed'] is False and final['endpoint'] is None
    coupon=contract['prepaid_coupon'];assert coupon['command']==ident['launches'][17]['command'] and coupon['ordinal']==3 and coupon['original_number']==18 and coupon['no_refund'] and coupon['consume_once']
    assert not (out/'fees/main06/18_before.json').exists()
    files=[diag,witness,out/'review/main06_recovery_contract_review01.json',fee,out/'fees/main06/launch.json',out/'fees/main06/failure.txt',
        ens,root/PREFIX,root/prior.SIDE,out/'review/performance_admission_resumption01.json',root/p['input_path'],out/'campaign/reference'/p['id']/'original.lp']
    files += [d/n for n in ['launch.json','completion.json','audit.json','observations.json','result.json','native.log','phases.csv','compact.lp']]
    files += sorted((d/'journal').glob('*'))
    revision=out/'engineering/main06_revision01_preserved'
    old_side=out/'campaign/reader_recovery/main06_numerical01.json';old_plan=out/'campaign/prepaid_recovery_plan01.json'
    assert sha(old_side)=='52593b64c0bf35d09e548d70eb2b339f99d07ab3bb9f8b4b485134d133d35e79'
    assert sha(old_plan)=='8a45671e925bd22744204e4bb21385809d09594adec8c4b3dcbf871d9aff24db'
    for name,digest in read(old_side)['current_reader_source_bindings'].items():assert sha(revision/Path(name).name)==digest
    files += [old_side,old_plan,out/'main06_finite01/audit.json',out/'engineering/main06_sidecar_prepare01/receipt.json',
        out/'engineering/main06_prepaid_plan01/receipt.json',out/'engineering/main06_finite01/receipt.json',out/'engineering/main06_reader_rebuild01/receipt.json']
    files += sorted(revision.glob('*.py'))
    return dict(key=list(KEY),all42_native_argv=[x['command'] for x in ident['launches']],original_candidate_identity_SHA=sha(out/'candidate_identity.json'),
        original_campaign_identity_SHA=sha(out/'campaign/identity.json'),original_performance_admission_SHA=sha(out/'review/performance_admission.json'),
        production_PE_SHA=cand['production_PE_SHA'],DLL_SHA=cand['DLL_SHA'],source_bindings=cand['source_bindings'],frozen_performance_helpers=ident['helpers'],
        prior15_sidecar_SHA=sha(root/prior.SIDE),prior15_proof=old,old_reader_snapshot_SHA=sha(root/REL/'engineering/main06_reader_source_before01/round109_reader_before.py'),
        raw_files={v.relative_to(root).as_posix():sha(v) for v in files},qualified_L=L,qualified_L_source='independently_proved_own_original_full_domain_nonnegative_floor',
        physical_floor_proof='True G>=0 including original zero-denominator G0; positive D, lambda/weights nonnegative; original absolute weighted penalty>=0',
        cold_floor_proof='Original objective constant0; G/e domains and all objective coefficients nonnegative',
        complete_own_physical_zero_certificate=True,certificate_source='own exactly zero complete physical fleet and own original full-domain floor',native_certificate_used=False,borrowed_ENS_certificate_or_bound=False,
        raw_callback_sequences=[3,37],reject_all_native_bounds=True,raw_final_native_L=0.,raw_failure_sequence=142,raw_returned_journal_sequence=None,
        independently_verified_actual_optimize_return_code=0,native_return_source='frozen api.optimize rc fields, matching full native log, serialization/process-exit lifecycle',
        missing_returned_journal_preserved=True,original_failed_audit_and_summary_preserved=True,model_domain=info,
        exact_complete_seconds=None,complete_seconds_interval=[lower,upper],unrounded_upper=unrounded,cap_seconds=launch['cap_seconds'],later_repair_time_in_original_interval=False,
        prepaid_coupon=coupon,current_reader_source_bindings={'scripts/'+name:sha(root/'scripts'/name) for name in SOURCES},solver_calls=0)

def read_lines(data):
    import json
    return [json.loads(v) for v in data.splitlines()]

def prepare(root):
    root=Path(root).resolve();ident=read(root/REL/'campaign/identity.json');assert not core.portable(root,ident['launches'][17]['destination']).exists()
    target=root/PREFIX;assert target.exists() and target.read_bytes()==(root/REL/'campaign/summary.jsonl').read_bytes()
    write(root/SIDE,facts(root));print('Known-call own-zero full-domain certificate and single prepaid native slot frozen; no solver work.')

def verify(root):
    root=Path(root).resolve();saved=read(root/SIDE);assert saved==facts(root),'altered main06 proof/source/raw must HOLD';return saved

def journal(root,launch,d):
    if prior.key(launch)!=KEY:return core.evidence.journal(root,launch['panel'],d)
    proof=verify(root);obs=read(d/'observations.json');calls={};ws=[];bs=[];trace=[];rawL=0.
    for v in obs:
        e=v['payload'];kind=e['kind']
        if kind=='call':calls[e['call']]=dict(e,native_bounds_mathematically_qualified=False,actual_normal_return_from_independent_rc_source=True,returned_journal_missing=True)
        elif kind=='witness':
            w=core.evidence.physical(root,launch['panel'],e);assert core.close(w['G'],e['G']) and core.close(w['P'],e['P'])
            ws.append(dict(w,source=e['source'],sequence=e['sequence'],available=v['effective_available_seconds']))
        elif kind=='bound':
            rawL=max(rawL,e['global_bound']);bs.append(dict(e,native_bound_mathematically_qualified=False,rejection_reason='known_call_positive_claim_disproved_by_own_zero_fleet_and_exact_cold_vector'))
        elif kind=='failure':assert e['sequence']==142
        elif kind=='identity':assert e['input_sha256']==launch['panel']['input_sha256']
        else:raise AssertionError(('unexpected known-call event',kind))
        if ws:
            U=min(w['F'] for w in ws);trace.append(dict(sequence=e['sequence'],available=v['effective_available_seconds'],kind=kind,U=U,L=0.,gap=U,
                raw_native_L_before_rejection=rawL,native_bound_mathematically_qualified=False,lower_bound_source=proof['qualified_L_source']))
    return dict(calls=calls,witnesses=ws,bounds=bs,started=1,returned=0,not_started=0,trace=trace,returned_ids=set(),not_started_ids=set(),
        returned_native_proofs=[],journal_failures=[v for v in obs if v['payload']['kind']=='failure'],independently_proved_actual_native_returns=1)

def apply_floor(ep,j,proof,launch,certificate):
    a=ep['arm'];a.update(L=0.,gap=a['U'],certificate=certificate,certificate_qualified=True,numbers_qualified=True,
        complete_seconds=None,complete_seconds_interval=proof['complete_seconds_interval'],complete_seconds_lower=proof['complete_seconds_interval'][0],complete_seconds_upper=proof['complete_seconds_interval'][1],
        formal_performance=True,original_whole_clock_unknown=True,supervisor_legacy_seconds=ep['completion']['fully_observed_end_to_end_seconds'],
        native_call_bounds_mathematically_qualified=False,lower_bound_source=proof['qualified_L_source'],
        certificate_basis='own_exact_physical_zero_and_own_full_original_domain_nonnegative_floor' if certificate else 'own_nonnegative_original_full_domain_floor_open_after_explicit_native_bound_rejection',
        numerical_reader_recovery=SIDE.as_posix(),later_evidence_repair_engineering_in_original_window=False)
    a['relative_gap'],a['relative_gap_null_reason']=core.decision.relative(a)
    ep['analytical_floor_proof']=proof;ep['rejected_raw_native_chronology']=copy.deepcopy(ep.get('chronological_cover',[]));ep['chronological_cover']=[]
    for b in j['bounds']+j['returned_native_proofs']:b.update(native_bound_mathematically_qualified=False,rejection_reason='explicit_known_call_native_bound_rejection')
    for call in j['calls'].values():call['native_bounds_mathematically_qualified']=False
    j['trace']=copy.deepcopy(j['trace'])
    for z in j['trace']:z.update(raw_native_L_before_rejection=z.get('raw_native_L_before_rejection',z['L']),L=0.,gap=z['U'],native_bound_mathematically_qualified=False,lower_bound_source=proof['qualified_L_source'])
    return ep

def endpoint(root,launch,ident,d,j,formal,original):
    key=prior.key(launch)
    if not formal or key not in [KEY,prior.KEY]:return original(root,launch,ident,d,j,formal)
    allproof=verify(root)
    if key==prior.KEY:
        ep=original(root,launch,ident,d,j,False);old_L=ep['arm']['L'];ep=apply_floor(ep,j,allproof['prior15_proof'],launch,False)
        ep['arm']['raw_native_lower_bound_rejected']=old_L;return ep
    r=read(d/'result.json');c=read(d/'completion.json');ph=core.full_fleet(root,launch['panel'],r);p=launch['panel']
    assert ph['F']==0. and allproof['complete_own_physical_zero_certificate']
    arm=dict(id=p['id'],arm=launch['arm'],U=ph['F'],L=0.,gap=0.,certificate=True,certificate_qualified=True,numbers_qualified=True,
        status=r['status'],stop_reason=c['stop_reason'],PE_SHA=ident['candidate_binary_sha256'],DLL_SHA=ident['dll_sha256'],V=p['V'],M=p['M'],Q_vector=p['Q_vector'],
        T_seconds=p['T_seconds'],cap_seconds=p['cap_seconds'],input_SHA=p['input_sha256'],native_Optimize=1,route_oracle=0,IIS=0,source_commit=ident['measured_source_commit'],
        tiny_negative_gap_within_original_tolerance=False,exact_native_first_witness_time_observed=False,raw_claimed_U=r['upper_bound'],raw_claimed_L=r['lower_bound'],
        raw_claimed_strict_certificate=r['strict_certified_original_problem'],raw_claimed_relative_gap=r.get('gap'),raw_tree_termination_reason=r.get('external_gini_tree_failure_reason'),
        qualified_bounds_rebuilt_from_actual_native_journal_and_cover=False,own_full_domain_floor_certificate=True,raw_audit_passed=False,
        journal_return_missing=True,returned_journal_sequence=None,independent_actual_native_return_code=0)
    ep=dict(arm=arm,physical=ph,cover=dict(L=0.,complete_coverage=True,all_relevant_closed=True,live_leaves=0,open_leaves=0,covered_gini_upper=(p['V']-1.)/p['V'],timeline=[],leaves=[]),
        controller=core.evidence.controller_tables(d,r),result=r,completion=c,chronological_cover=[],native_final_without_returned_journal=dict(raw_native_L=r['native_mip_best_bound'],native_log_final_L=0.,
            returned_journal_sequence=None,mathematically_qualified_as_native_bound=False,actual_return_code=0,return_source=allproof['native_return_source']))
    return apply_floor(ep,j,allproof,launch,True)

def record_view(root,records):
    proof=verify(root);value=copy.deepcopy(records)
    for r in value:
        if r['number']==15:
            assert r['audit_passed'] and r['endpoint']['L']==proof['prior15_proof']['raw_final_native_L']
            r['endpoint'].update(L=0.,gap=r['endpoint']['U'],source='computed_own_floor_after_explicit_known_call_rejection')
        if r['number']==17:
            assert r['audit_passed'] is False and r['endpoint'] is None and r['audit_error']=="AssertionError('full_bound_witness_inconsistency')"
            r.update(raw_audit_passed=False,computed_mathematical_qualification=True,audit_passed=True,endpoint=dict(U=0.,L=0.,gap=0.,certificate=True,
                source='own_full_domain_floor_and_exact_physical_zero',status='optimal'))
    return value

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(sys.argv[2])
    elif sys.argv[1]=='verify':print(verify(sys.argv[2])['complete_seconds_interval'])
    else:raise ValueError(sys.argv[1])

"""Uniform offline evidence predicates. No automatic numerical recovery or solve.

Normal evidence uses the audited inherited reader. A damaged current cold call
can use an explicit separately signed current proof, never a historical tuple.
Other new/scoped failures HOLD. Raw files and flags are never rewritten.
"""
from pathlib import Path
from fractions import Fraction
import copy, math, re, collections
import round108_reader as core
import round109_seed_scope as computed
from round109_numerical_recovery import floor
from round109_main06_recovery import functional

ROUND=Path('results/unified_exact_round110')

def side_path(launch):
    return ROUND/'campaign/reader_recovery'/f'{launch["number"]:02d}_{launch["id"]}_S{launch["seed"]}_{launch["arm"]}.json'

def has_rejection(root,launch):
    return (Path(root)/side_path(launch)).is_file()

def located(root,relative):
    path=(Path(root)/relative).resolve()
    assert path.is_relative_to(Path(root).resolve()), 'evidence path outside explicit root'
    return path

def clock_interval(native_end_seconds,outer_seconds,preceding_complete_seconds,cap):
    assert math.isfinite(native_end_seconds) and native_end_seconds>0
    assert math.isfinite(outer_seconds) and all(math.isfinite(t) and t>0 for t in preceding_complete_seconds)
    lower=math.nextafter(native_end_seconds,-math.inf)
    upper=math.nextafter(outer_seconds-sum(preceding_complete_seconds),math.inf)
    assert 0<lower<=upper<cap
    return [lower,upper]

def returned_lifecycle(r,c,phases,text,m):
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    assert r['gurobi_optimize_count']==r['native_mip_mipopt_count']==1
    assert r['gurobi_optimize_return_code']==r['native_mipopt_return_code']==0
    for field in ['native_mip_evidence_capture_complete','native_mip_problem_freed','native_mip_environment_closed',
                  'native_mip_lifecycle_valid','gurobi_solver_finalization_reached','native_mip_solver_finalization_reached']:
        assert r[field] is True,field
    for field in ['native_mip_freeprob_return_code','native_mip_close_return_code']:assert r[field]==0
    for field in ['native_mip_environment_count','native_mip_problem_count','native_mip_model_read_count','native_mip_freeprob_count','native_mip_close_count']:
        assert r[field]==1
    size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',text)
    types=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',text)
    assert size and types and (int(size[1]),int(size[2]))==(len(m['rows']),len(m['order']))
    counts=collections.Counter(m['types'].values())
    assert dict(C=int(types[1]),I=int(types[2])-int(types[3]),B=int(types[3]))=={k:counts.get(k,0) for k in ['C','I','B']}
    assert 'Best objective ' in text and 'best bound ' in text
    events=[row['event'] for row in phases]
    names=['plain_gurobi_optimize_launch','final_result_serialization_start','final_result_serialization_complete','process_exit']
    assert all(events.count(name)==1 for name in names)
    assert [events.index(name) for name in names]==sorted(events.index(name) for name in names)
    assert phases[-1]['event']=='process_exit' and phases[-1]['status']=='complete' and phases[-1]['detail']=='rc=0'

def verify_rejection(root,launch,d):
    root=Path(root).resolve();d=Path(d);saved=core.read(root/side_path(launch));p=launch['panel']
    assert saved['schema']=='round110-current-cold-call-rejection-v1'
    assert saved['key']==[launch['number'],launch['id'],launch['seed'],launch['arm']]
    assert launch['arm']=='P-GRB', 'scoped ENS/M-B damage requires separate domain-specific proof; HOLD'
    ident=core.read(root/ROUND/'campaign/identity.json')
    assert saved['production_PE_SHA']==ident['candidate_binary_sha256'] and saved['DLL_SHA']==ident['dll_sha256']
    assert saved['campaign_identity_SHA']==core.sha(root/ROUND/'campaign/identity.json')
    assert saved['command']==launch['command'] and saved['input_SHA']==core.sha(root/p['input_path'])==p['input_sha256']
    for relative,digest in saved['raw_bindings'].items():
        path=(root/relative).resolve();assert path.is_relative_to(root) and core.sha(path)==digest
    independent_path=located(root,saved['independent_audit_path'])
    independent=core.read(independent_path)
    assert core.sha(independent_path)==saved['independent_audit_SHA']
    assert independent['decision']=='ACCEPT_CURRENT_CALL_REJECTION' and independent['current_key']==saved['key']
    assert independent['Optimize']==0 and independent['native_environment']==0
    for field in ['campaign_identity_SHA','production_PE_SHA','DLL_SHA','model_SHA','raw_bindings','time','exact_vector_path','exact_vector_SHA']:
        assert independent[field]==saved[field],('signed independent current-call binding differs',field)
    obs=core.read(d/'observations.json');c=core.read(d/'completion.json');r=core.read(d/'result.json')
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    assert core.read(d/'launch.json')['command']==launch['command']
    calls=[v['payload'] for v in obs if v['payload']['kind']=='call']
    assert len(calls)==1;call=calls[0]
    assert call['call']==1 and call['full_original']==1 and call['model_scope']=='complete_original_compact_milp'
    assert call['settings']==computed.expected(launch['seed'])
    assert call['model_sha256']==core.sha(d/'compact.lp')==p['reference']['canonical_sha256']
    assert saved['model_SHA']==call['model_sha256']
    assert call['lower_g']==0 and call['upper_g']==call['gmax'] and call['cutoff']==0
    assert r['gurobi_hga_start_requested'] is False and r['gurobi_optimize_count']==1
    assert r['gurobi_native_domain_audit_passed'] and r['gurobi_optimize_return_code']==0
    m=core.lp_model(d/'compact.lp');a=core.evidence.instance(root,p)
    floor(p['lambda'],a['w'][1:],a['D'][1:],m['objective'],m['bounds'])
    vector_path=located(root,saved['exact_vector_path'])
    assert core.sha(vector_path)==saved['exact_vector_SHA']
    vector=core.read(vector_path);values={n:Fraction(*v) for n,v in vector['complete_column_values'].items()}
    assert set(values)==set(m['bounds'])
    for n,(lo,hi) in m['bounds'].items():
        assert (not math.isfinite(lo) or values[n]>=Fraction(lo)) and (not math.isfinite(hi) or values[n]<=Fraction(hi))
        assert m['types'][n]=='C' or values[n].denominator==1
    for terms,sense,rhs in m['rows']:
        lhs=sum((values[n]*Fraction(v) for n,v in terms),Fraction(0));rhs=Fraction(rhs)
        assert lhs==rhs if sense=='=' else lhs<=rhs if sense=='<=' else lhs>=rhs
    terms,constant=m['objective'];objective=sum((values[n]*Fraction(v) for n,v in terms),Fraction(constant))
    lower_claims=[v['payload']['native_bound'] for v in obs if v['payload']['kind']=='bound']
    assert lower_claims and any(Fraction(lb)>objective+Fraction(1,10**7) for lb in lower_claims)
    assert saved['reject_all_call_native_lower_claims'] and saved['withdraw_necessary_dependent_closures']
    returned_lifecycle(r,c,core.rows(d/'phases.csv'),(d/'native.log').read_text(encoding='utf-8'),m)
    returned=[v['payload'] for v in obs if v['payload']['kind']=='returned']
    assert len(returned)<=1 and all(v['return_code']==0 and v['call']==1 for v in returned)
    if not returned:
        assert any(v['payload']['kind']=='failure' for v in obs)
        functional(r,c,core.rows(d/'phases.csv'),(d/'native.log').read_text(encoding='utf-8'))
    else: assert call['native_preconditions']==1 if launch['seed']==0 else call['native_preconditions']==0
    physical=core.full_fleet(root,p,r)
    assert saved['own_U']==physical['F'] and saved['certificate_from_own_exact_zero']==(physical['F']==0.)
    timing=saved['time'];assert timing['exact_seconds'] is None
    fee_path=located(root,saved['original_fee_path']);fee_launch=core.read(fee_path/'launch.json');fee=core.read(fee_path/'receipt.json')
    assert fee_launch['qualification'] is False and fee_launch['command'][2]=='billed'
    first,last=map(int,fee_launch['command'][4:6]);assert first<=launch['number']<=last
    assert fee['exit_code']==1 and fee['conservative_process_starts']==fee_launch['conservative_process_starts']
    preceding=[]
    for number in range(first,launch['number']):
        previous=ident['launches'][number-1];receipt_path=core.portable(root,previous['destination'])/'whole_arm_receipt.json'
        assert receipt_path.relative_to(root).as_posix() in saved['raw_bindings']
        receipt=core.read(receipt_path);assert receipt['number']==number
        preceding.append(receipt['complete_seconds'])
    end=core.read(d/'native_end_receipt.json')
    assert end['completion_SHA']==core.sha(d/'completion.json') and end['observations_SHA']==core.sha(d/'observations.json')
    assert timing['interval']==clock_interval(end['complete_seconds_until_native_end'],fee['outer_seconds'],preceding,p['cap_seconds'])
    required=[d/'launch.json',d/'completion.json',d/'observations.json',d/'result.json',d/'audit.json',d/'native_end_receipt.json',
              d/'postexit_audit_receipt.json',d/'compact.lp',d/'native.log',d/'phases.csv',fee_path/'launch.json',fee_path/'receipt.json']
    assert all(path.relative_to(root).as_posix() in saved['raw_bindings'] for path in required)
    assert saved['qualified_L']==0 and saved['qualified_L_source']=='independently_proved_own_original_full_domain_nonnegative_floor'
    return saved

def qualify_seed(root,launch,observations,completion,ident):
    if has_rejection(root,launch):
        verify_rejection(root,launch,core.portable(root,launch['destination']))
        return None
    return computed.qualify(root,launch,observations,completion,ident)

def journal(root,launch,d):
    if not has_rejection(root,launch):return core.evidence.journal(root,launch['panel'],d)
    proof=verify_rejection(root,launch,d);obs=core.read(d/'observations.json');calls={};witnesses=[];bounds=[];trace=[];returned=set();rawL=0.
    for v in obs:
        e=v['payload'];kind=e['kind']
        if kind=='call':calls[e['call']]=dict(e,native_bounds_mathematically_qualified=False,
            returned_journal_missing=not any(z['payload']['kind']=='returned' for z in obs),actual_normal_return_from_independent_rc_source=True)
        elif kind=='witness':
            w=core.evidence.physical(root,launch['panel'],e)
            assert core.close(w['G'],e['G']) and core.close(w['P'],e['P'])
            witnesses.append(dict(w,source=e['source'],sequence=e['sequence'],available=v['effective_available_seconds']))
        elif kind=='bound':
            if e['global_bound'] is not None:rawL=max(rawL,e['global_bound'])
            bounds.append(dict(e,native_bound_mathematically_qualified=False,rejection_reason='current_call_exact_in_domain_counterexample'))
        elif kind=='returned':returned.add(e['call'])
        elif kind=='identity':assert e['input_sha256']==launch['panel']['input_sha256']
        elif kind=='failure':pass # preserved and qualified only by independently bound current proof
        else:raise AssertionError(('unknown current damaged-call event',kind))
        if witnesses:
            U=min(w['F'] for w in witnesses)
            trace.append(dict(sequence=e['sequence'],available=v['effective_available_seconds'],kind=kind,U=U,L=0.,gap=U,
                raw_native_L_before_rejection=rawL,native_bound_mathematically_qualified=False,lower_bound_source=proof['qualified_L_source']))
    return dict(calls=calls,witnesses=witnesses,bounds=bounds,started=1,returned=len(returned),not_started=0,trace=trace,
        returned_ids=returned,not_started_ids=set(),returned_native_proofs=[],journal_failures=[v for v in obs if v['payload']['kind']=='failure'],
        independently_proved_actual_native_returns=not bool(returned))

def endpoint(root,launch,ident,d,j,formal,original):
    if not has_rejection(root,launch):return original(root,launch,ident,d,j,formal)
    proof=verify_rejection(root,launch,d);r=core.read(d/'result.json');c=core.read(d/'completion.json');p=launch['panel'];physical=core.full_fleet(root,p,r)
    U=physical['F'];cert=U==0.;lo,hi=proof['time']['interval'];audit=core.read(d/'audit.json')
    arm=dict(id=p['id'],arm=launch['arm'],U=U,L=0.,gap=U,certificate=cert,certificate_qualified=True,numbers_qualified=True,
        status=r['status'],stop_reason=c['stop_reason'],PE_SHA=ident['candidate_binary_sha256'],DLL_SHA=ident['dll_sha256'],V=p['V'],M=p['M'],Q_vector=p['Q_vector'],
        T_seconds=p['T_seconds'],cap_seconds=p['cap_seconds'],input_SHA=p['input_sha256'],native_Optimize=1,route_oracle=0,IIS=0,source_commit=ident['measured_source_commit'],
        tiny_negative_gap_within_original_tolerance=False,exact_native_first_witness_time_observed=False,raw_claimed_U=r['upper_bound'],raw_claimed_L=r['lower_bound'],
        raw_claimed_strict_certificate=r['strict_certified_original_problem'],raw_claimed_relative_gap=r.get('gap'),raw_tree_termination_reason=r.get('external_gini_tree_failure_reason'),
        qualified_bounds_rebuilt_from_actual_native_journal_and_cover=False,own_full_domain_floor_certificate=cert,raw_audit_passed=audit['passed'],
        journal_return_missing=not bool(j['returned_ids']),independent_actual_native_return_code=0,complete_seconds=None,complete_seconds_interval=[lo,hi],
        complete_seconds_lower=lo,complete_seconds_upper=hi,formal_performance=formal,original_whole_clock_unknown=True,
        supervisor_legacy_seconds=c['fully_observed_end_to_end_seconds'],native_call_bounds_mathematically_qualified=False,lower_bound_source=proof['qualified_L_source'],
        certificate_basis='own_exact_physical_zero_and_own_full_original_domain_nonnegative_floor' if cert else 'own_nonnegative_original_full_domain_floor_open_after_explicit_native_bound_rejection',
        numerical_reader_recovery=side_path(launch).as_posix(),later_evidence_repair_engineering_in_original_window=False)
    arm['relative_gap'],arm['relative_gap_null_reason']=core.decision.relative(arm)
    proof=dict(proof,physical_floor_proof='nonnegative true G including zero denominator; lambda/weights nonnegative; positive targets',
        cold_floor_proof='original nonnegative G/e objective coefficients and lower bounds')
    rejected=[dict(v['payload'],available=v['effective_available_seconds'],native_bound_mathematically_qualified=False,
        rejection_reason='all current-call lower claims rejected by exact same-domain vector') for v in core.read(d/'observations.json') if v['payload']['kind']=='bound']
    rejected.append(dict(kind='native_final_claim',call=1,L=r['native_mip_best_bound'],returned_journal_present=bool(j['returned_ids']),
        native_bound_mathematically_qualified=False,rejection_reason='all current-call lower claims rejected, including final'))
    result=dict(arm=arm,physical=physical,cover=dict(L=0.,complete_coverage=True,all_relevant_closed=cert,live_leaves=0,open_leaves=0 if cert else 1,
        covered_gini_upper=(p['V']-1.)/p['V'],timeline=[],leaves=[]),controller=core.evidence.controller_tables(d,r),result=r,completion=c,
        chronological_cover=[],analytical_floor_proof=proof,rejected_raw_native_chronology=rejected)
    if not j['returned_ids']:
        result['native_final_without_returned_journal']=dict(raw_native_L=r['native_mip_best_bound'],returned_journal_sequence=None,
            mathematically_qualified_as_native_bound=False,actual_return_code=0,return_source='current bound raw API/log/serialization/cleanup/normal-exit proof')
    return result

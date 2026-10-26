"""Explicit current scoped-call evidence extension, with no online recovery.

The frozen cold evidence module stays byte-identical. Only a signed current
scoped proposal activates this path; every other case keeps the original gate.
"""
from round110_evidence import *
import round110_evidence as cold
_checked_scoped_bytes={}


def scoped(root,launch):
    return has_rejection(root,launch) and core.read(Path(root)/side_path(launch)).get('schema')=='round110-current-scoped-call-rejection-v1'


def verify_signed_scope_binding(root,launch,d):
    """Cheap eligibility gate over an independently signed complete proof.

    Rehash all proof-bound bytes. Full matrix arithmetic stays in offline
    verify_rejection; no parser/solver/row traversal occurs in this gate.
    """
    assert scoped(root,launch)
    root=Path(root).resolve();d=Path(d);s=core.read(root/side_path(launch));p=launch['panel']
    assert s['key']==[launch['number'],launch['id'],launch['seed'],launch['arm']]==[25,'G100-C1',0,'M-B']
    ident=core.read(root/ROUND/'campaign/identity.json')
    assert s['production_PE_SHA']==ident['candidate_binary_sha256'] and s['DLL_SHA']==ident['dll_sha256']
    assert s['campaign_identity_SHA']==core.sha(root/ROUND/'campaign/identity.json')
    assert s['command']==launch['command'] and s['input_SHA']==core.sha(root/p['input_path'])==p['input_sha256']
    for relative,digest in s['raw_bindings'].items():assert core.sha(located(root,relative))==digest
    audit=located(root,s['independent_audit_path']);a=core.read(audit)
    assert core.sha(audit)==s['independent_audit_SHA'] and a['decision']=='ACCEPT_CURRENT_SCOPED_CALL_REJECTION'
    assert a['current_key']==s['key'] and a['Optimize']==a['native_environment']==0
    for field in ['campaign_identity_SHA','production_PE_SHA','DLL_SHA','model_SHA','raw_bindings','time','exact_vector_path','exact_vector_SHA']:
        assert a[field]==s[field],('signed current scoped binding differs',field)
    assert s['damaged_calls']==[4] and s['preserved_distinct_LP_calls']==[1,2,3]
    assert s['reject_all_call_native_lower_claims'] and s['withdraw_necessary_dependent_closures']
    assert a['own_U']==s['own_U']==0. and a['own_complete_original_domain_floor']==s['qualified_L']==0.
    assert a['certificate_from_own_exact_zero'] and s['certificate_from_own_exact_zero']
    assert a['result']['L']==0. and s['qualified_L_source']=='independently_proved_own_original_full_domain_nonnegative_floor'
    required=[d/'launch.json',d/'result.json',d/'observations.json',d/'completion.json',d/'audit.json',
        d/'native_end_receipt.json',d/'postexit_audit_receipt.json',located(root,s['exact_vector_path'])]
    required += list((d/'external/models').glob('*.lp'))+list((d/'external/native_logs').glob('*.gurobi.log'))
    assert all(q.relative_to(root).as_posix() in s['raw_bindings'] for q in required)
    assert core.sha(located(root,s['exact_vector_path']))==s['exact_vector_SHA']
    return s


def verify_rejection(root,launch,d):
    if not scoped(root,launch):return cold.verify_rejection(root,launch,d)
    root=Path(root).resolve();d=Path(d);p=launch['panel'];s=verify_signed_scope_binding(root,launch,d)
    # Reuse a proof only within this process after rehashing every bound file.
    # The root, signed sidecar and signed audit are also part of this key.
    verified_key=(str(root),core.sha(root/side_path(launch)),s['independent_audit_SHA'],tuple(sorted(s['raw_bindings'].items())))
    if verified_key in _checked_scoped_bytes:return s
    obs=core.read(d/'observations.json');r=core.read(d/'result.json');c=core.read(d/'completion.json')
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    assert core.read(d/'launch.json')['command']==launch['command'] and core.read(d/'audit.json')['passed'] is False
    calls=[v['payload'] for v in obs if v['payload']['kind']=='call'];assert [v['call'] for v in calls]==[1,2,3,4]
    ledger=core.rows(d/'external/paper_optimize_ledger.csv');assert len(ledger)==4
    models={}
    for call,row in zip(calls,ledger):
        assert call['settings']==computed.expected(launch['seed'])
        assert call['model_sha256']==row['model_sha256'] and call['leaf']==row['leaf_id'] and int(row['optimize_return_code'])==0
        assert core.portable(root,call['native_log_path'])==core.portable(root,row['native_log'])
        model=core.portable(root,call['model_path']);assert core.sha(model)==call['model_sha256']
        if call['model_sha256'] not in models:models[call['model_sha256']]=core.model_contract(root,p,model,'M-B')[1]
        core.model_scope_contract(call,models[call['model_sha256']],p)
        text=core.portable(root,call['native_log_path']).read_text(encoding='utf-8')
        assert ('Optimal objective' in text if row['solve_kind']=='LP' else 'Optimal solution found' in text)
    assert [q['solve_kind'] for q in ledger]==['LP','LP','LP','MIP']
    returned=[v['payload']['call'] for v in obs if v['payload']['kind']=='returned'];assert returned==[1,2,3]
    call=calls[-1];assert call['model_sha256']==s['model_SHA'] and call['native_preconditions']==1 and call['full_original']==0
    assert call['lower_g']==0 and call['upper_g']==call['cutoff']>0
    m=models[s['model_SHA']];instance=core.evidence.instance(root,p)
    floor(p['lambda'],instance['w'][1:],instance['D'][1:],m['objective'],m['bounds'])
    vp=located(root,s['exact_vector_path']);assert core.sha(vp)==s['exact_vector_SHA']
    v=core.read(vp);values={n:Fraction(*q) for n,q in v['complete_column_values'].items()}
    assert set(values)==set(m['bounds']) and v['current_model_SHA']==s['model_SHA']
    coefficients={}
    def exact(x):
        if x not in coefficients:coefficients[x]=Fraction(x)
        return coefficients[x]
    for n,(lo,hi) in m['bounds'].items():
        assert (not math.isfinite(lo) or values[n]>=exact(lo)) and (not math.isfinite(hi) or values[n]<=exact(hi))
        assert m['types'][n]=='C' or values[n].denominator==1
    for terms,sense,rhs in m['rows']:
        lhs=sum((values[n]*exact(x) for n,x in terms if values[n]),Fraction(0));target=exact(rhs)
        assert lhs==target if sense=='=' else lhs<=target if sense=='<=' else lhs>=target
    objective=sum((values[n]*exact(x) for n,x in m['objective'][0] if values[n]),exact(m['objective'][1]))
    assert [objective.numerator,objective.denominator]==v['exact_objective']
    claims=[q['payload']['native_bound'] for q in obs if q['payload']['kind']=='bound' and q['payload']['call']==4]
    assert any(exact(lb)>objective+Fraction(1,10**7) for lb in claims)
    physical=core.full_fleet(root,p,r);assert physical['F']==physical['G']==physical['P']==s['own_U']==s['qualified_L']==0.
    assert s['certificate_from_own_exact_zero'] and s['qualified_L_source']=='independently_proved_own_original_full_domain_nonnegative_floor'
    fee=located(root,s['original_fee_path']);fl=core.read(fee/'launch.json');fr=core.read(fee/'receipt.json')
    assert fl['command'][4:6]==['25','27'] and fr['exit_code']==1 and fr['conservative_process_starts']==4
    end=core.read(d/'native_end_receipt.json')
    assert end['completion_SHA']==core.sha(d/'completion.json') and end['observations_SHA']==core.sha(d/'observations.json')
    assert not (d/'whole_arm_receipt.json').exists() and s['time']['exact_seconds'] is None
    assert s['time']['interval']==clock_interval(end['complete_seconds_until_native_end'],fr['outer_seconds'],[],p['cap_seconds'])
    assert not s['time']['later_repair_engineering_in_original_interval']
    _checked_scoped_bytes[verified_key]=True
    return s


def qualify_seed(root,launch,observations,completion,ident):
    if scoped(root,launch):verify_rejection(root,launch,core.portable(root,launch['destination']));return None
    return cold.qualify_seed(root,launch,observations,completion,ident)


def journal(root,launch,d):
    if not scoped(root,launch):return cold.journal(root,launch,d)
    proof=verify_rejection(root,launch,d);obs=core.read(d/'observations.json')
    calls={};witnesses=[];bounds=[];trace=[];returned=set();rawL=0.
    for seq,v in enumerate(obs,1):
        e=v['payload'];assert e['sequence']==seq
        raw=d/'journal'/f'event_{seq}.json';assert core.sha(raw)==v['sha256'] and core.read(raw)==e
        commit=(d/'journal'/f'event_{seq}.commit').read_text().split()
        assert int(commit[1])==seq and int(commit[3])==raw.stat().st_size and commit[4]==core.sha(raw)
        kind=e['kind']
        if kind=='identity':assert seq==1 and e['input_sha256']==launch['panel']['input_sha256']
        elif kind=='call':
            assert e['call'] not in calls
            calls[e['call']]=dict(e,native_bounds_mathematically_qualified=e['call']!=4,
                returned_journal_missing=e['call']==4,actual_normal_return_from_independent_rc_source=e['call']==4)
        elif kind=='witness':
            w=core.evidence.physical(root,launch['panel'],e);assert core.close(w['G'],e['G']) and core.close(w['P'],e['P'])
            witnesses.append(dict(w,source=e['source'],sequence=seq,available=v['effective_available_seconds']))
        elif kind=='bound':
            if e['global_bound'] is not None:rawL=max(rawL,e['global_bound'])
            assert e['call']==4,'a newly damaged LP/native call requires its own proof'
            bounds.append(dict(e,native_bound_mathematically_qualified=False,rejection_reason='exact_counterexample_in_this_current_scoped_call'))
        elif kind=='returned':assert e['return_code']==0 and e['call'] in [1,2,3];returned.add(e['call'])
        elif kind=='failure':assert seq==25 and e['reason']=='local_bound_witness_inconsistency'
        else:raise AssertionError(('unreviewed current scoped event',kind))
        if witnesses:
            U=min(w['F'] for w in witnesses)
            trace.append(dict(sequence=seq,available=v['effective_available_seconds'],kind=kind,U=U,L=0.,gap=U,
                raw_native_L_before_rejection=rawL,native_bound_mathematically_qualified=False,lower_bound_source=proof['qualified_L_source']))
    assert returned=={1,2,3} and set(calls)=={1,2,3,4}
    return dict(calls=calls,witnesses=witnesses,bounds=bounds,started=4,returned=3,not_started=0,trace=trace,
        returned_ids=returned,not_started_ids=set(),returned_native_proofs=[],journal_failures=[v for v in obs if v['payload']['kind']=='failure'],
        independently_proved_actual_native_returns=1,independently_proved_actual_native_return_ids=[4])


def endpoint(root,launch,ident,d,j,formal,original):
    if not scoped(root,launch):return cold.endpoint(root,launch,ident,d,j,formal,original)
    proof=verify_rejection(root,launch,d);r=core.read(d/'result.json');c=core.read(d/'completion.json');p=launch['panel']
    physical=core.full_fleet(root,p,r);assert physical['F']==0.
    lo,hi=proof['time']['interval'];controller=core.evidence.controller_tables(d,r)
    safe=dict(j,bounds=[]);safe['return_sequences']={v['payload']['call']:v['payload']['sequence'] for v in core.read(d/'observations.json') if v['payload']['kind']=='returned'}
    lp_proofs=core.scoped_proofs(safe,controller,0.);assert [q['call'] for q in lp_proofs]==[1,2,3]
    chronology=core.chronological_cover(safe,controller,0.)
    arm=dict(id=p['id'],arm=launch['arm'],U=0.,L=0.,gap=0.,certificate=True,certificate_qualified=True,numbers_qualified=True,
        status=r['status'],stop_reason=c['stop_reason'],PE_SHA=ident['candidate_binary_sha256'],DLL_SHA=ident['dll_sha256'],V=p['V'],M=p['M'],Q_vector=p['Q_vector'],
        T_seconds=p['T_seconds'],cap_seconds=p['cap_seconds'],input_SHA=p['input_sha256'],native_Optimize=4,route_oracle=0,IIS=0,source_commit=ident['measured_source_commit'],
        tiny_negative_gap_within_original_tolerance=False,exact_native_first_witness_time_observed=False,raw_claimed_U=r['upper_bound'],raw_claimed_L=r['lower_bound'],
        raw_claimed_strict_certificate=r['strict_certified_original_problem'],raw_claimed_relative_gap=r.get('gap'),raw_tree_termination_reason=r.get('external_gini_tree_failure_reason'),
        qualified_bounds_rebuilt_from_actual_native_journal_and_cover=False,own_full_domain_floor_certificate=True,raw_audit_passed=False,
        journal_return_missing=True,independent_actual_native_return_code=0,complete_seconds=None,complete_seconds_interval=[lo,hi],complete_seconds_lower=lo,complete_seconds_upper=hi,
        formal_performance=formal,original_whole_clock_unknown=True,supervisor_legacy_seconds=c['fully_observed_end_to_end_seconds'],
        native_call_bounds_mathematically_qualified=False,damaged_native_calls=[4],preserved_distinct_LP_calls=[1,2,3],lower_bound_source=proof['qualified_L_source'],
        certificate_basis='own_exact_physical_zero_and_own_full_original_domain_nonnegative_floor',numerical_reader_recovery=side_path(launch).as_posix(),
        later_evidence_repair_engineering_in_original_window=False)
    arm['relative_gap'],arm['relative_gap_null_reason']=core.decision.relative(arm)
    floor_proof=dict(proof,physical_floor_proof='nonnegative true G, nonnegative lambda/weights and positive targets; exact ownY=D',
        cold_floor_proof='nonnegative original objective terms; this scope-specific counterexample rejects only call4')
    rejected=[dict(v['payload'],available=v['effective_available_seconds'],native_bound_mathematically_qualified=False,
        rejection_reason='all lower claims of current scoped call4 rejected, including zero') for v in core.read(d/'observations.json') if v['payload']['kind']=='bound' and v['payload']['call']==4]
    log=core.portable(root,j['calls'][4]['native_log_path']);text=log.read_text(encoding='utf-8')
    final=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',text);assert final
    rejected.append(dict(kind='native_final_claim',call=4,L=float(final[-1]),returned_journal_present=False,native_bound_mathematically_qualified=False,
        rejection_reason='all damaged scoped-call lower claims rejected, including final'))
    timeline=[];damaged_native_seen=False
    for number,row in enumerate(core.rows(d/'external/global_bound_trace.csv'),1):
        damaged_native_seen=damaged_native_seen or row['event_type'].startswith('native_') or 'terminal_mip' in row['event_source']
        dependent=damaged_native_seen
        timeline.append(dict(row=number,**row,recomputed_complete_cover_bound=0.,
            recomputed_lower_source=proof['qualified_L_source'],raw_native_claim_mathematically_qualified=not dependent,
            own_incumbent_physical_qualification_separate=row['event_type']=='incumbent_improvement',
            necessary_dependent_native_closure_withdrawn=dependent))
    leaves=[dict(row,native_closure_mathematically_qualified=False,necessary_dependent_native_closure_withdrawn=True,
        own_full_domain_zero_certificate=True) for row in core.rows(d/'external/paper_leaf_ledger.csv')]
    cover=dict(L=0.,complete_coverage=True,all_relevant_closed=True,live_leaves=len(leaves),open_leaves=0,
        covered_gini_upper=(p['V']-1.)/p['V'],timeline=timeline,leaves=leaves,scoped_proofs=lp_proofs,
        closure_basis=arm['certificate_basis'],native_call4_closure_withdrawn=True)
    return dict(arm=arm,physical=physical,cover=cover,controller=controller,result=r,completion=c,chronological_cover=chronology,
        analytical_floor_proof=floor_proof,rejected_raw_native_chronology=rejected,
        native_final_without_returned_journal=dict(call=4,raw_native_L=float(final[-1]),returned_journal_sequence=None,
            mathematically_qualified_as_native_bound=False,actual_return_code=0,return_source='current tree Optimize ledger/log/source/normal-exit proof'))

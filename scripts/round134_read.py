"""Round133 future-evidence qualification using the established pure checks.

Raw schema1 observations are immutable. New source/quality events are explicitly
validated. LP qualification is separate from integer-model prerequisites. A
source-rejected arm has a verified full-domain floor0/open disposition, while
ordinary native OPTIMAL with an excessive physical gap remains qualified-open.
No solver, native library or optimization is imported by this module.
"""
from round134_common import *
import collections, contextlib, copy, csv, inspect, re, types
from fractions import Fraction as F
import round108_reader as core
import round111_seed_audit as models
import round114_audit as old_audit
import round114_ps as old_ps
import round112_audit as compact_start
import round118_call_logs as call_logs
import round122_evidence as parameter_checks
import compare_round112_startup as startup
import round86_native_evidence as commits
import round90_lp_g_g3 as native_runner

import round133_postverify_repair as accepted_h
startup.reconstruct=accepted_h.reconstruct_accepted
compact_start.start_audit=accepted_h.start_audit_accepted

def exact_zero(physical,data,p):
    y=physical['Y'];d=data['D'];w=data['w'];lam=p['lambda']
    return (p['V']>0 and len(y)==len(d)==len(w)==p['V']+1 and
        math.isfinite(lam) and lam>=0 and
        all(type(y[i]) is int and y[i]>=0 and d[i]>0 and
            math.isfinite(w[i]) and w[i]>=0 and
            y[i]*d[1]==y[1]*d[i] and
            (lam==0 or w[i]==0 or y[i]==d[i]) for i in range(1,p['V']+1)))

TOL=1e-7

def legacy_scope_gate():
    path=OUT/'review/legacy_shortcut_reader_admission.json'
    gate=read(path)
    assert gate['decision']=='ACCEPT' and gate['reader_SHA']==sha(__file__)
    assert gate['policy']=='OLD_D3_MARKER_UNEVALUABLE_AFTER_COMPLETE_AUDIT'
    return dict(path=str(path),SHA256=sha(path),policy=gate['policy'])

def legacy_unevaluable_arm(physical,issue,admission):
    """A complete old observation, with no newly granted proof qualification."""
    assert issue['models'] and issue['native_numerical_contradiction_claimed'] is False
    return dict(U=physical['F'],L=0.,gap=physical['F'],certificate=False,
        certificate_basis='OLD_MODEL_SCOPE_ANALYTIC_SHORTCUT_UNQUALIFIED',
        source_reduced=False,native_proof_qualified=False,model_scope_qualified=False,
        implementation_qualified=False,formal_protocol_qualified=False,certificate_qualified=False,numbers_qualified=True,
        performance_eligible=False,performance_evidence_eligible=False,
        implementation_failure_disposition_verified=False,
        controlled_legacy_model_scope_unevaluable=True,evidence_complete=True,
        legacy_scope_policy_admission=admission,
        old_raw_producer_did_not_recover_full_domain_open=True,
        independent_floor0_is_offline_disposition_not_repaired_old_control_state=True)

def emitter_scope_policy(launch,identity):
    """Bind only the two actual emitters of the known no-improver shortcut."""
    names=('src/IntervalRowFactory.cpp','src/CplexBaseline.cpp')
    records=[]
    for name in names:
        expected=identity['source_hashes'][name]
        raw=(ROOT/name).read_bytes() if launch['version']=='candidate' else git('show',identity['measured_source_commit']+':'+name)
        assert hashlib.sha256(raw).hexdigest()==expected
        code=re.sub(r'/\*[\s\S]*?\*/|//[^\r\n]*','',raw.decode('utf-8'))
        has_guard=bool(re.search(r'\bround128EmitIntervalNoImproverDomainClosure\s*\(',code))
        records.append(dict(path=name,SHA256=expected,legacy_guard_call_present=has_guard))
    candidate=launch['version']=='candidate'
    if candidate:
        assert not any(row['legacy_guard_call_present'] for row in records), 'candidate_inclusive_emitter_retains_proof_only_shortcut'
    old_d3=not candidate and identity.get('stage')=='D3'
    if old_d3:
        assert identity['candidate_binary_sha256']==ORIGINAL_PE_SHA
        assert launch['method']=='S2' and launch['command'][launch['command'].index('--round127-mode')+1]=='ms2'
    return dict(schema='round133-inclusive-emitter-scope-v1',candidate=candidate,emitters=records,
        candidate_shortcut_removed_from_both_bound_sources=candidate,
        bounded_old_D3_recognition=old_d3 and all(row['legacy_guard_call_present'] for row in records),
        no_blanket_ban_on_genuine_domain_infeasibility_constant_rows=True)

def no_improver_shortcut_analysis(launch,call,model,policy,own_U=None):
    """Identify the old source-specific row pattern; never infer solver error.

    Exact box arithmetic evaluates the existing physical penalty-floor idea.
    It is diagnostic here and does not automatically qualify an old source.
    """
    p=launch['panel'];data=core.evidence.instance(ROOT,p)
    weights=tuple(sorted((f'e_{i}',float(data['w'][i])) for i in range(1,p['V']+1) if data['w'][i]))
    constant=[];patterns=[]
    for index,(terms,sense,rhs) in enumerate(model['rows']):
        if terms or sense!='<=' or rhs!=-1.:continue
        constant.append(index)
        if not index:continue
        previous=model['rows'][index-1]
        if previous[0]!=weights or previous[1]!='>=' or not math.isfinite(previous[2]) or previous[2]<0:continue
        loaded_pmin=previous[2]
        guard=call['lower_g']+p['lambda']*loaded_pmin>=call['cutoff']-1e-9
        # The shared/fallback historical cutoff branch requires positive lambda;
        # a similar true-domain empty row outside this guard is not the marker.
        if not guard or p['lambda']<=1e-12:continue
        penalty=F(0);domains=[];complete_box=True
        for i in range(1,p['V']+1):
            low,high=model['bounds'][f'Y_{i}']
            if not math.isfinite(low) or not math.isfinite(high) or low>high:
                complete_box=False;break
            target=F(data['D'][i]);lo,hi=F(low),F(high)
            assert target>0
            deviation=lo/target-1 if lo>target else 1-hi/target if hi<target else F(0)
            contribution=F(data['w'][i])*deviation
            assert contribution>=0
            penalty+=contribution
            domains.append(dict(station=i,Y_bounds=[str(lo),str(hi)],target=str(target),
                weight=str(F(data['w'][i])),exact_box_minimum_deviation=str(deviation)))
        fact=dict(row_index_zero_based=index,preceding_penalty_row_index_zero_based=index-1,
            loaded_penalty_lower=str(F(loaded_pmin)),old_binary64_guard_satisfied=guard,
            original_guard_margin=str(F(1e-9)),original_certificate_margin=str(F(TOL)),
            known_old_source_marker=policy['bounded_old_D3_recognition'],
            candidate_similar_shape_is_not_itself_a_shortcut_violation=policy['candidate'],
            source_problem='MODEL_SCOPE_ANALYTIC_NO_IMPROVER_SHORTCUT' if policy['bounded_old_D3_recognition'] else 'OTHER_CONSTANT_ROW_SHAPE',
            native_numerical_contradiction_claimed=False,loaded_inventory_box=domains,
            physical_box_embedding_independently_proved=False,
            loaded_box_values_are_diagnostics_not_qualified_physical_bounds=True)
        if complete_box:
            analytic=F(call['lower_g'])+F(p['lambda'])*penalty
            unconditional=min(analytic,F(call['cutoff']))
            deficit=max(F(0),F(call['cutoff'])-unconditional)
            fact.update(exact_loaded_box_penalty_minimum=str(penalty),exact_loaded_box_objective_floor_candidate=str(analytic),
                exact_cutoff_complement_of_loaded_box_floor_candidate=str(unconditional),
                cutoff_minus_loaded_box_candidate=str(deficit),
                candidate_gap_within_original_certificate_margin=deficit<=F(TOL),
                loaded_penalty_floor_minus_exact_loaded_box_minimum=str(F(loaded_pmin)-penalty),
                analytic_floor_qualification_automatically_granted=False)
            if own_U is not None and call['lower_g']==0:
                # This one call's original prefix, its cutoff complement, and
                # F>=G on the remaining G tail cover the original domain.
                # It is an analytic qualification candidate, not a native-INF
                # claim or an automatically admitted performance certificate.
                global_floor=(min(unconditional,F(call['upper_g']))
                    if call['upper_g']<call['gmax'] else unconditional)
                fact.update(exact_single_prefix_loaded_box_global_floor_candidate=str(global_floor),
                    own_U_at_sealed_return=str(F(own_U)),
                    single_prefix_analytic_gap=str(F(own_U)-global_floor),
                    loaded_box_candidate_closure_within_original_margin=-F(TOL)<=F(own_U)-global_floor<=F(TOL),
                    analytic_floor_contradicted_by_own_U_beyond_margin=global_floor>F(own_U)+F(TOL),
                    analytic_closure_requires_valid_remaining_inventory_domain_embedding=True,
                    old_performance_policy_admission_not_inferred_from_this_test=True)
        else:fact.update(exact_loaded_box_penalty_minimum=None,analytic_floor_obstacle='nonfinite_or_empty_actual_inventory_box')
        patterns.append(fact)
    identified=[row for row in patterns if row['known_old_source_marker']]
    return dict(call=call['call'],actual_constant_infeasibility_rows_zero_based=constant,
        identified_legacy_shortcut_rows=identified,similar_row_shapes=patterns,
        model_scope_issue=bool(identified),inclusive_domain_empty_proved_by_marker=False,
        old_side_default_performance_disposition='UNEVALUABLE' if identified else 'UNALTERED',
        analytic_compatibility_requires_independent_review=True)

def strict_global_bound(scope,value,witnesses):
    """The inherited cover algebra with exact physical membership predicates."""
    assert math.isfinite(value) and abs(value)<1e100,'native_bound_unavailable'
    U=min((w['F'] for w in witnesses),default=math.inf)
    if scope['full_original']:
        assert scope['native_preconditions'] and value<=U+TOL
        return value
    assert all(not _same_domain(scope,w) or value<=w['F']+TOL for w in witnesses)
    cutoff=scope['cutoff'];assert math.isfinite(U) and cutoff+TOL>=U
    pieces=[dict(p) for p in scope['cover']];matched=0
    for piece in pieces:
        assert all(math.isfinite(piece[k]) for k in ('lower_g','upper_g','lower','cutoff'))
        assert 0<=piece['lower_g']<=piece['upper_g'] and piece['cutoff']+TOL>=cutoff
        if (piece['id'],piece['lower_g'],piece['upper_g'],piece['cutoff'])==(scope['leaf'],scope['lower_g'],scope['upper_g'],cutoff):
            assert scope['native_preconditions'] and scope['model_sha256'];matched+=1
            piece['lower']=max(piece['lower'],value)
        for witness in witnesses:
            if piece['lower_g']<=witness['G']<=piece['upper_g'] and witness['F']<=piece['cutoff']:
                assert piece['lower']<=witness['F']+TOL
    assert matched==1
    covered=0.;lower=cutoff
    for piece in sorted(pieces,key=lambda p:p['lower_g']):
        assert piece['lower_g']<=covered
        covered=max(covered,piece['upper_g']);lower=min(lower,piece['lower'],piece['cutoff'])
    assert pieces and covered>=min(cutoff,scope['gmax']) and lower<=U+TOL
    return lower

@contextlib.contextmanager
def strict_bound_context():
    original=core.evidence.bound
    numeric_originals=[]
    for name in ('returned_native_proofs','cold_returned_bound'):
        function=getattr(core,name);source=inspect.getsource(function)
        assert '1e90' in source
        source=source.replace('1e90','1e100')
        namespace=dict(function.__globals__)
        exec(compile(source,__file__+'::native_infinity_policy','exec'),namespace)
        numeric_originals.append((name,function));setattr(core,name,namespace[name])
    core.evidence.bound=strict_global_bound
    try:yield
    finally:
        core.evidence.bound=original
        for name,function in numeric_originals:setattr(core,name,function)

def quality_predicate(quality,solve_kind):
    """Independent known-quality predicate; tolerances are residual limits."""
    names=('ObjVal','ObjBoundC','ConstrVio','BoundVio','IntVio','DualVio')
    assert all(name in quality for name in names)
    rc=quality['solution_count_read_return_code']
    assert type(rc) is int
    count=quality['solution_count']
    if rc==0:assert type(count) is int and count>=0
    else:assert count is None,'failed solution-count readback must remain null'
    bad=[] if rc==0 else ['solution_count_unknown']
    status_rc=quality['native_status_read_return_code']
    optimize_rc=quality['optimize_return_code']
    assert type(status_rc) is int and type(optimize_rc) is int
    status=quality['native_status']
    supported_statuses={2,3,7,8,9,10,11,15,16,17}
    if status_rc==0:
        assert type(status) is int
        if status not in supported_statuses:bad.append('native_status_unqualified')
    else:
        assert status is None,'failed native-status readback must remain null'
        bad.append('native_status_unknown')
    if optimize_rc!=0:bad.append('optimize_return_unqualified')
    unknown=[]
    for name in names:
        value=quality[name]
        if value is None:unknown.append(name);continue
        assert isinstance(value,(float,int)) and math.isfinite(value)
        limited=name in ('ConstrVio','BoundVio','IntVio') or (solve_kind=='LP' and name=='DualVio')
        if count is not None and count>0 and limited and value>(1e-5 if name=='IntVio' else 1e-6):bad.append(name)
    return dict(sufficient=not bad,violated_attributes=bad,unknown_attributes=unknown,
                solution_count=count,solution_count_read_return_code=rc,
                native_status=status,native_status_read_return_code=status_rc,
                optimize_return_code=optimize_rc,
                quality_applicability='KNOWN' if rc==0 else 'UNKNOWN_REJECTED',
                residuals_not_qualified_by_assuming_unknown_count_zero=rc!=0,
                retained_attributes={name:quality[name] for name in names},solve_kind=solve_kind,
                objective_error_bound_claimed=False)

def validate_event_lifecycle(payloads, future=True, require_complete=True):
    """Check the actual Optimize-return versus postreturn-evidence lifecycle.

    This pure gate is also the D2 interruption/duplicate/order fixture entry.
    It does not validate physical witnesses, bytes, settings or model mapping;
    `_journal` performs those additional mandatory checks on original records.
    """
    calls={};returned=set();cancelled=set();quality=set();activity=set();rejected=False
    for sequence,e in enumerate(payloads,1):
        assert e.get('schema')==1 and e.get('sequence')==sequence,'incomplete_or_duplicate_event_sequence'
        kind=e.get('kind')
        if sequence==1:
            assert kind=='identity','identity_must_be_first'
            if future:assert e.get('certificate')=='none_source_qualification_round133','wrong_numeric_policy_identity'
            continue
        assert kind!='identity','duplicate_identity'
        if kind=='call':
            cid=e['call'];assert cid==len(calls)+1,'nonsequential_call_identity'
            assert set(calls)<=returned|cancelled,'overlapping_or_unreturned_previous_call'
            if future:
                assert returned<=quality,'missing_postreturn_quality_before_next_call'
                assert not rejected,'new_native_call_after_source_revocation'
            calls[cid]=sequence
        elif kind=='not_started':
            cid=e['call'];assert cid in calls and cid not in returned|cancelled|activity,'invalid_not_started_disposition'
            assert e['actual_Optimize'] is False
            cancelled.add(cid)
        elif kind=='returned':
            cid=e['call'];assert cid in calls and cid not in returned|cancelled,'duplicate_or_unknown_native_return'
            assert e['return_code']==0
            returned.add(cid);activity.add(cid)
        elif kind in ('witness','witness_rejected'):
            cid=e['call']
            if not cid:assert not calls,'late_startup_witness'
            else:
                assert cid in calls and cid not in cancelled,'unbound_witness'
                final=e.get('source')=='native_final_verified_original_routes'
                if final:
                    assert future and cid in returned and cid==max(calls),'final_witness_before_Optimize_return_or_after_later_call'
                else:assert cid not in returned,'callback_witness_after_Optimize_return'
                activity.add(cid)
        elif kind=='bound':
            cid=e['call'];assert cid in calls and cid not in cancelled,'unbound_native_bound'
            if cid in returned:assert future and cid in quality and cid==max(calls),'postreturn_bound_before_quality_or_after_later_call'
            activity.add(cid)
        elif kind=='native_quality':
            cid=e['call'];assert future and cid in returned and cid not in quality and cid==max(calls),'quality_order_or_duplicate'
            quality.add(cid)
        elif kind=='native_infeasible':
            cid=e['call'];assert future and cid in returned and cid in quality and cid==max(calls),'infeasible_order'
        elif kind=='source_rejected':
            cid=e['call'];assert future and cid in calls and cid not in cancelled,'unbound_source_revocation'
            assert e['dependent_control_state_requires_abandonment'] is True
            rejected=True
        elif kind=='failure':
            assert sequence==len(payloads),'publication_after_terminal_failure'
            if require_complete:raise AssertionError('terminal_failure_requires_explicit_failure_disposition')
        else:raise AssertionError(('unknown_event_kind',kind))
    assert payloads,'empty_committed_stream'
    if require_complete:
        assert set(calls)==returned|cancelled,'missing_Optimize_disposition'
        if future:assert returned==quality,'missing_postreturn_quality_tail'
    return dict(declared=len(calls),returned=sorted(returned),not_started=sorted(cancelled),
                postreturn_quality=sorted(quality),source_revoked=rejected)

def expected_settings(launch):
    config=launch['expected_configuration']
    assert type(config['gurobi_seed']) is int and 0<=config['gurobi_seed']<=2000000000
    assert type(config['gurobi_presolve']) is int and -1<=config['gurobi_presolve']<=2
    assert config['threads']==config['mip_threads']==1
    return dict(Threads=config['mip_threads'],Seed=config['gurobi_seed'],
        Presolve=config['gurobi_presolve'],MIPFocus=config['configuration']['MIPFocus'],
        Cuts=config['configuration']['Cuts'],MIPGap=config['requested_mip_gap'],
        MIPGapAbs=config['requested_mip_gap_abs'],FeasibilityTol=config['FeasibilityTol'],
        IntFeasTol=config['IntFeasTol'],OptimalityTol=config['OptimalityTol'])

def _journal(launch,d,observations):
    p=launch['panel'];calls={};returned={};cancelled={};activity=set();witnesses=[];bounds=[]
    rejected=[];quality=[];infeasible=[];identity=None;failure=None
    lifecycle=validate_event_lifecycle([row['payload'] for row in observations],launch.get('version')=='candidate')
    assert len(list((d/'journal').glob('event_*.commit')))==len(observations)
    for seq,row in enumerate(observations,1):
        checked=commits.receipt(d/'journal'/f'event_{seq}.commit',row['first_observed_seconds'],launch['cap_seconds'])
        assert checked==row and row['payload']['sequence']==seq,'missing/reordered/content-mismatched committed event'
        e=row['payload'];kind=e['kind'];assert failure is None,'publication after failure latch'
        if kind=='identity':
            assert seq==1 and identity is None;identity=e
            assert e['input_sha256']==p['input_sha256'] and (e['V'],e['M'])==(p['V'],p['M'])
            assert (e['lambda'],e['T'],e['pickup_seconds'],e['drop_seconds'])==(p['lambda'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'])
            assert e['analytical_full_domain_lower_bound']==0
        elif kind=='call':
            cid=e['call'];assert cid==len(calls)+1 and identity is not None
            settings=e['settings'];wanted=expected_settings(launch)
            assert settings['read_return_code']==0
            # Original E3 did not journal Focus/Cuts/expected; their q0 sidecar
            # and immutable registered old PE remain independently checked.
            old=launch.get('version')!='candidate'
            for name,value in wanted.items():
                if old and name in ('MIPFocus','Cuts') and name not in settings:continue
                assert settings.get(name)==value,('actual parameter mismatch',name,settings,wanted)
            if not old:assert settings.get('expected')==wanted, 'registered/readback parameter profiles diverge'
            assert sha(core.portable(ROOT,e['model_path']))==e['model_sha256']
            gmax=(p['V']-1)/p['V'];assert e['gmax']==gmax and 0<=e['lower_g']<=e['upper_g']<=gmax
            if e['full_original']:
                assert e['lower_g']==0 and e['upper_g']==gmax
                assert e['model_sha256']==p['reference']['canonical_sha256']
            calls[cid]=e
        elif kind=='not_started':
            cid=e['call'];assert cid in calls and cid not in activity|set(returned)|set(cancelled)
            assert e['actual_Optimize'] is False and e['reason']=='no_remaining_original_work_window'
            cancelled[cid]=e
        elif kind=='returned':
            cid=e['call'];assert cid in calls and cid not in returned and cid not in cancelled and e['return_code']==0
            returned[cid]=dict(e,available=row['effective_available_seconds']);activity.add(cid)
        elif kind in ('witness','witness_rejected'):
            cid=e['call'];assert (cid==0 and not calls) or (cid in calls and cid not in cancelled)
            if cid:activity.add(cid)
            if kind=='witness':
                value=core.full_fleet(ROOT,p,e)
                assert abs(value['G']-e['G'])<TOL and abs(value['P']-e['P'])<TOL
                witnesses.append(dict(value,arm=launch['arm_id'],call=cid,sequence=seq,source=e['source'],
                    input_SHA=p['input_sha256'],physical_verified=True,available=row['effective_available_seconds']))
        elif kind=='bound':
            cid=e['call'];assert cid in calls and cid not in cancelled and math.isfinite(e['native_bound'])
            if launch.get('version')=='candidate':
                assert type(e.get('local_available')) in (int,bool) and isinstance(e.get('local_reason'),str)
                assert e.get('retrospective') is False
                native_finite=abs(e['native_bound'])<1e100
                contradiction=native_finite and any(_same_domain(calls[cid],w) and e['native_bound']>w['F']+TOL for w in witnesses)
                expected_local=native_finite and bool(calls[cid]['native_preconditions']) and not contradiction and not rejected
                assert bool(e['local_available'])==expected_local,'producer/local independent qualifier disagreement'
                if rejected:expected_reason=rejected[0]['reason']
                elif not native_finite:expected_reason='native_bound_unavailable'
                elif contradiction:expected_reason='source_bound_witness_contradiction'
                elif not calls[cid]['native_preconditions']:
                    expected_reason=calls[cid].get('precondition_reason') or 'native_model_mapping_not_qualified'
                else:expected_reason='qualified_local_native_bound'
                assert e['local_reason']==expected_reason,'local qualification failure reason mismatch'
                if e['local_available']:
                    expected_value=e['native_bound'] if calls[cid]['full_original'] else min(e['native_bound'],calls[cid]['cutoff'])
                    assert e['local_bound']==expected_value
                else:assert e['local_bound'] is None
                if e['global_available']:assert e['local_available'] and e['global_bound'] is not None
                else:assert e['global_bound'] is None
                try:global_value=strict_global_bound(calls[cid],e['native_bound'],witnesses);possible=True
                except AssertionError:global_value=None;possible=False
                assert bool(e['global_available'])==(possible and not rejected),'producer/global independent qualifier disagreement'
                if e['global_available']:assert abs(global_value-e['global_bound'])<=1e-10
            bounds.append(dict(e,available=row['effective_available_seconds']));activity.add(cid)
        elif kind=='source_rejected':
            cid=e['call'];assert cid in calls and cid not in cancelled
            assert e['reason'] and e['dependent_control_state_requires_abandonment'] is True
            rejected.append(dict(e,available=row['effective_available_seconds']));activity.add(cid)
        elif kind in ('native_quality','native_infeasible'):
            cid=e['call'];assert cid in calls and cid in returned and cid not in cancelled
            if kind=='native_quality':quality_predicate(e,'PENDING_ACTUAL_CALL_KIND')
            (quality if kind=='native_quality' else infeasible).append(dict(e,available=row['effective_available_seconds']))
            activity.add(cid)
            if kind=='native_infeasible':assert type(e['qualified']) in (int,bool) and isinstance(e['reason'],str)
        elif kind=='failure':
            assert seq==len(observations);failure=e
        else:raise AssertionError(('unregistered schema1 journal event',kind))
    assert identity is not None
    return dict(calls=calls,returned_ids=set(returned),not_started_ids=set(cancelled),actual_started_ids=activity,
        declared=len(calls),started=len(activity),returned=len(returned),not_started=len(cancelled),
        unreturned_ids=set(calls)-set(returned)-set(cancelled),witnesses=witnesses,raw_bounds=bounds,bounds=bounds,
        failure=failure,source_rejections=rejected,native_quality=quality,native_infeasible=infeasible,lifecycle=lifecycle,
        return_sequences={k:v['sequence'] for k,v in returned.items()},
        return_available={k:v['available'] for k,v in returned.items()})

def _legacy_view(j,launch,d):
    """Pure adapter of LP-vs-MIP bookkeeping after actual parameter validation.

    No raw field is changed. The old reusable proof helpers use one historical
    Boolean to distinguish integer calls from LPs; the new producer does not.
    """
    view=copy.deepcopy(j)
    ledger=core.rows(d/'external/paper_optimize_ledger.csv') if launch['arm']=='M-B' and j['started'] else []
    actual=[cid for cid in j['calls'] if cid not in j['not_started_ids']]
    assert not ledger or len(ledger)==len(actual)
    kinds={cid:row['solve_kind'] for cid,row in zip(actual,ledger)}
    for cid,c in view['calls'].items():
        c['raw_native_preconditions']=c['native_preconditions']
        c['native_preconditions']=False if kinds.get(cid)=='LP' else bool(c['native_preconditions'])
        if launch.get('version')!='candidate' and kinds.get(cid)!='LP':
            # The original Seed1 administrative flag is separately superseded
            # only by complete actual matrix/return qualification in this reader.
            c['native_preconditions']=True
    view['bounds']=[b for b in view['raw_bounds'] if (abs(b['native_bound'])<1e100 and b.get('local_available',True) and kinds.get(b['call'])!='LP')]
    if launch.get('version')=='candidate':
        # returned is the Optimize API return, before final quality/readback.
        # A qualified returned proof becomes available only at the completed
        # postreturn evidence tail; do not backdate it to the API return.
        view['Optimize_return_sequences']=dict(j['return_sequences'])
        for cid in view['returned_ids']:
            tail=[row for key in ('raw_bounds','native_quality','native_infeasible','source_rejections')
                  for row in j[key] if row.get('call')==cid]
            tail.extend(w for w in j['witnesses'] if w.get('call')==cid)
            view['return_sequences'][cid]=max([j['return_sequences'][cid]]+[row['sequence'] for row in tail])
            view['return_available'][cid]=max([j['return_available'][cid]]+[row['available'] for row in tail])
    view['trace']=[]
    return view,kinds

def _same_domain(scope,witness):
    return scope['full_original'] or (scope['lower_g']<=witness['G']<=scope['upper_g'] and witness['F']<=scope['cutoff'])

def reconcile(claims,witnesses):
    """Objective margin only; never expand a witness's physical domain."""
    result=[]
    for c in sorted(claims,key=lambda x:(x['call'],x['sequence'],x['source'])):
        assert math.isfinite(c['value']) and c['domain_verified']
        for w in sorted(witnesses,key=lambda x:(x['F'],x['G'],x['source'])):
            assert w['physical_verified'] and w['input_SHA']==c['input_SHA']
            if _same_domain(c['scope'],w) and c['value']>w['F']+TOL:
                result.append(dict(c,counterexample={k:w[k] for k in ('source','F','G','input_SHA','available','physical_verified')},
                    reason='source_bound_witness_contradiction',whole_source_rejected=True));break
    return dict(rejections=result,damaged_calls=sorted({r['call'] for r in result}),tolerance=TOL,
                physical_domain_expanded_by_tolerance=False)

def independent_source_checks(launch,j,kinds,chain,result,witnesses,model_scope_excluded_calls=()):
    """Refute native infeasibility and recompute known-quality qualification."""
    quality=[];infeasibility=[]
    excluded=set(model_scope_excluded_calls)
    if excluded:
        assert launch['version']!='candidate' and launch['method']=='S2'
        assert launch['command'][launch['command'].index('--round127-mode')+1]=='ms2'
    for cid,scope in j['calls'].items():
        if launch.get('version')=='candidate':
            # On this fixed registered matrix, actual expected settings, full
            # model/scope mapping and all supported request features have been
            # independently checked. A false mapping flag has no unexplained
            # Seed exception in the future evidence contract.
            assert scope['native_preconditions']==1 and not scope.get('precondition_reason'), 'registered mapping/parameter qualification disagreement'
    for row in j['native_quality']:
        cid=row['call'];kind=kinds.get(cid,'MIP')
        fact=quality_predicate(row,kind)
        if j['calls'][cid]['full_original'] and row['solution_count_read_return_code']==0:
            assert row['solution_count']==result['gurobi_solution_count']
        elif not j['calls'][cid]['full_original']:
            actual=chain['ledger'][cid-1]
            codes={'OPTIMAL':2,'INFEASIBLE':3,'TIME_LIMIT':9,'INTERRUPTED':11,'SUBOPTIMAL':13}
            if row['native_status_read_return_code']==0 and actual['native_status'] in codes:
                assert row['native_status']==codes[actual['native_status']]
        if not fact['sufficient']:
            reject=[r for r in j['source_rejections'] if r['call']==cid and r['reason'].startswith('native_quality_insufficient:')]
            assert reject,'producer did not reject known insufficient native quality'
            assert all(any(name in r['reason'] for r in reject) for name in fact['violated_attributes'])
        quality.append(dict(call=cid,**fact))
    infeasible_ids={row['call'] for row in j['native_infeasible']}
    infeasible_ids.update(cid for cid in chain['actual'] if chain['ledger'] and chain['ledger'][cid-1]['native_status']=='INFEASIBLE')
    if launch['arm'] in ('P-GRB','P-S') and result.get('gurobi_status')==3:infeasible_ids.update(chain['actual'])
    for cid in sorted(infeasible_ids):
        found=[w for w in witnesses if _same_domain(j['calls'][cid],w)]
        if cid in excluded:
            infeasibility.append(dict(call=cid,scope_qualification='KNOWN_OLD_MODEL_SCOPE_SHORTCUT_UNQUALIFIED',
                same_domain_witnesses=[dict(source=w['source'],G=w['G'],F=w['F']) for w in found],
                native_numerical_counterexample_claimed=False,
                inclusive_physical_domain_empty_qualified=False))
            continue
        if found:
            assert any(r['call']==cid and r['reason']=='source_infeasibility_witness_contradiction' for r in j['source_rejections']), 'producer retained native INFEASIBLE contradicted by own same-domain witness'
        infeasibility.append(dict(call=cid,same_domain_counterexamples=[dict(source=w['source'],G=w['G'],F=w['F']) for w in found],
            source_infeasibility_rejected=bool(found),cutoff_floor_is_not_native_infeasibility_qualification=True))
    return dict(quality=quality,infeasibility=infeasibility,extra_Optimize=0)

def _claims(launch,j,chain,result):
    out=[]
    def add(cid,sequence,value,source,available):
        if not isinstance(value,(float,int)) or not math.isfinite(value) or abs(value)>=1e100:return
        out.append(dict(arm=launch['arm_id'],call=cid,sequence=sequence,value=value,source=source,available=available,
            model_SHA=j['calls'][cid]['model_sha256'],input_SHA=launch['panel']['input_sha256'],
            scope=j['calls'][cid],domain_verified=True,dependencies=[cid]))
    for b in j['raw_bounds']:add(b['call'],b['sequence'],b['native_bound'],'raw_committed_native_bound',b['available'])
    for log in chain['logs']:
        cid=log['call'];seq=j['return_sequences'].get(cid,0);available=j['return_available'].get(cid,0.)
        if j['calls'][cid]['full_original']:
            if result.get('gurobi_obj_bound_c_available'):
                value=result['gurobi_obj_bound_c']
                printed=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',log['text'])
                assert printed and abs(float(printed[-1])-value)<=TOL
                add(cid,seq,value,'raw_returned_ObjBoundC',available)
        else:
            row=chain['ledger'][cid-1]
            if row['native_status']=='INFEASIBLE':
                add(cid,seq,j['calls'][cid]['cutoff'],'infeasible_cutoff_complement',available)
            else:
                pattern=r'Optimal objective\s+([-+0-9.eE]+)' if row['solve_kind']=='LP' else r'Best objective [^,]+, best bound ([^,]+), gap'
                found=re.findall(pattern,log['text'])
                if found:add(cid,seq,float(found[-1]),'raw_linked_returned_native_log',available)
    return out

def _normal_endpoint(launch,identity,d,j,result):
    if launch['arm']=='P-S':
        source=inspect.getsource(old_ps.validate_ps_lifecycle)
        source=source.replace("parameters.parameter_readback(r,require_call=True,arm='P-GRB')",
            "parameter_checks._parameters(r,seed=l['seed'],require_call=True,arm='P-GRB')")
        source=source.replace('expected=dict(threads=1,seed=0,presolve=-1,mip_gap=0.,mip_gap_abs=0.)',
            "expected=dict(threads=1,seed=l['seed'],presolve=-1,mip_gap=0.,mip_gap_abs=0.)")
        ns=dict(vars(old_ps),parameter_checks=parameter_checks)
        exec(compile(source,__file__+'::paid_actual_seed','exec'),ns)
        endpoint=types.FunctionType(old_ps.paid_endpoint.__code__,dict(vars(old_ps),validate_ps_lifecycle=ns['validate_ps_lifecycle']))
        return endpoint(ROOT,launch,identity,d,j)
    # The original endpoint requires the already-passed audit file. All of its
    # prerequisite checks are performed here before delegation, so supply that
    # in memory instead of writing a provisional PASS over uncompleted checks.
    source=inspect.getsource(core.endpoint)
    needle="a=read(d/'audit.json')";assert source.count(needle)==1
    source=source.replace(needle,"a=prechecked")
    source=source.replace("if U-L<=decision.CLOSURE_TOL and not certificate:raise AssertionError",
        "if U-L<=decision.CLOSURE_TOL and not certificate and launch.get('method') not in ['S2R','GEOM']:raise AssertionError")
    ns=dict(vars(core),prechecked=dict(passed=True,binary_sha256=identity['candidate_binary_sha256']))
    exec(compile(source,__file__+'::established_complete_endpoint','exec'),ns)
    value=ns['endpoint'](ROOT,launch,identity,d,j,False)
    if launch['method'] in ('S2R','GEOM') and value['arm']['certificate']:
        cover=value['cover'];ledger=value['controller']['controller_native']
        assert cover and cover['live_leaves']==1 and all(q['leaf_id']=='L0' for q in ledger)
        assert any(q['solve_kind']=='MIP' and q['native_status']=='OPTIMAL' for q in ledger)
    return value

def validate_abandoned_control(path,gmax,source_reason):
    """Validate the small abandoned-state evidence, never its old proof value."""
    path=Path(path)
    assert path.is_file(),'abandoned_control_state_evidence_missing'
    raw=path.read_bytes()
    assert raw and raw.endswith(b'\n'),'abandoned_control_state_evidence_truncated'
    # newline='' preserves CSV quoted-field semantics. Any malformed field
    # count, duplicate identity or partial final row fails qualification.
    with path.open('r',encoding='utf-8',newline='') as stream:
        parsed=list(csv.reader(stream,strict=True))
    header=['leaf_id','gamma_L','gamma_U','claimed_lower','status','reason']
    assert parsed and parsed[0]==header,'abandoned_control_state_header_mismatch'
    assert len(parsed)>=2,'abandoned_control_state_has_no_old_leaf'
    allowed={'open','closed','fathomed','empty','invalid','replaced','terminal_ready','coalesced'}
    seen=set();records=[]
    for row in parsed[1:]:
        assert len(row)==len(header),'abandoned_control_state_field_count'
        leaf,lower_g,upper_g,claimed,status,reason=row
        assert leaf and leaf not in seen and leaf!='R133_FULL_DOMAIN_OPEN','abandoned_control_state_leaf_identity'
        seen.add(leaf)
        lo,hi,bound=float(lower_g),float(upper_g),float(claimed)
        assert math.isfinite(lo) and math.isfinite(hi) and 0<=lo<=hi<=gmax,'abandoned_control_state_original_domain'
        assert status in allowed,'abandoned_control_state_status'
        assert math.isfinite(bound) or (status=='empty' and bound==math.inf),'abandoned_control_state_claimed_lower'
        assert reason and reason==source_reason,'abandoned_control_state_source_reason_mismatch'
        records.append(dict(leaf_id=leaf,lower_g=lo,upper_g=hi,claimed_lower=claimed,status=status,reason=reason))
    return dict(path=str(path),SHA256=sha(path),bytes=len(raw),old_leaf_records=len(records),
                checked_header_fields_identity_domain_claim_status_reason=True,
                old_claims_retained_as_abandoned_not_qualified=True,records=records)

def _safe_open(launch,d,result,physical,j,controller):
    assert j['source_rejections'] # Native rejection and independent proof are separate
    # The historical result.gap is relative; the independent endpoint below
    # retains the signed absolute difference U-L without changing raw gap.
    assert result['lower_bound']==0
    domain=dict(lower=0.,upper=(launch['panel']['V']-1)/launch['panel']['V'])
    abandoned=None
    if launch['arm']=='M-B':
        leaves=core.rows(d/'external/paper_leaf_ledger.csv')
        live=[row for row in leaves if row['status'] not in ('replaced','coalesced')]
        assert len(live)==1
        leaf=live[0]
        assert leaf['leaf_id']=='R133_FULL_DOMAIN_OPEN' and leaf['status'].lower()=='open'
        assert float(leaf['gamma_L'])==domain['lower'] and float(leaf['gamma_U'])==domain['upper']
        assert float(leaf['lower_bound'])==float(leaf['base_lower_bound'])==0
        assert not leaf['closure_source']
        missing_marker='abandoned_control_state_evidence_missing_or_incomplete'
        assert missing_marker not in result['external_gini_tree_failure_reason'] and missing_marker not in result.get('notes',[]),missing_marker
        abandoned=validate_abandoned_control(d/'external/round133_abandoned_control_state.csv',domain['upper'],j['source_rejections'][0]['reason'])
        assert any(row['event']=='source_revocation_full_domain_open' for row in controller['controller_events'])
        assert result['external_gini_tree_failure_reason'].startswith('native_source_rejected_full_domain_open:')
    return dict(U=physical['F'],L=0.,gap=physical['F'],certificate=False,
        certificate_basis='SOURCE_REJECTED_FULL_DOMAIN_OPEN_ANALYTIC_FLOOR0',source_reduced=True,
        native_proof_qualified=False,full_domain_open=domain,performance_eligible=False,performance_evidence_eligible=False,
        abandoned_control_state_check=abandoned,
        implementation_failure_disposition_verified=True)

def native_release_lifecycle(result,j):
    """Retain native cleanup proof when the old combined flag includes failure.

    The tree's lifecycle_complete flag is `!hard_failure && resource checks`.
    A correctly abandoned proof sets hard_failure, so that raw flag remains
    false. In this branch require the actual original resource identities,
    complete returned-call chain and explicit source-rejection disposition.
    """
    if not j['source_rejections']:return result['external_gini_tree_lifecycle_complete'] is True
    assert not j['unreturned_ids'] and j['started']==j['returned']
    prefix='external_gini_tree_'
    get=lambda suffix:result[prefix+suffix]
    assert get('optimize_count')==get('lp_optimize_count')+get('partial_mip_optimize_count')+get('terminal_mip_optimize_count')
    assert get('terminal_mip_leaf_count')==get('terminal_mip_optimize_count')
    assert get('model_count')==get('model_read_count')==get('model_free_count')
    assert get('environment_count')==get('environment_free_count')
    assert get('same_leaf_resume_count')==get('in_memory_model_reuse_count')
    assert get('integer_domain_restore_count')==get('lp_optimize_count')
    assert get('fresh_restart_count')==get('child_restart_count')==get('reset_call_count')==0
    return True

def verify(launch,identity):
    """One post-seal pure audit; never starts/extends a solver or backfills U."""
    tick=time.perf_counter();d=Path(launch['destination']);p=launch['panel']
    assert not (d/'verification_closeout.json').exists(),'closed verification is immutable; rebuild only aggregates it'
    producer=read(d/'producer_receipt.json');seal=read(d/'producer_seal.json')
    assert producer['producer_seal_SHA']==sha(d/'producer_seal.json') and producer['native_stopped_no_reentry']
    for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest
    assert sha(p['input_path'])==p['input_sha256']
    for name,digest in identity['source_hashes'].items():
        if launch.get('version')=='candidate':assert sha(ROOT/name)==digest,name
        else:
            raw=git('show',identity['measured_source_commit']+':'+name)
            assert hashlib.sha256(raw).hexdigest()==digest,name
    result=read(d/'result.json');completion=read(d/'completion.json');observations=read(d/'observations.json')
    assert completion['returncode']==0 and completion['stop_reason']=='normal_return' and completion['within_cap']
    assert producer['T_produce']<=launch['cap_seconds'] and result['process_return_code']==0
    assert sha(launch['command'][0])==identity['candidate_binary_sha256'] and sha(DLL)==identity['dll_sha256']
    assert read(d/'launch.json')['command']==launch['command']
    physical=core.full_fleet(ROOT,p,result)
    assert abs(physical['F']-result['upper_bound'])<=TOL
    data=core.evidence.instance(ROOT,p)
    assert p['lambda']>=0 and all(x>0 for x in data['D'][1:]) and all(x>=0 and math.isfinite(x) for x in data['w'][1:])
    assert read(d/'production_checks.json')['final_physical_verification']==physical
    j=_journal(launch,d,observations);legacy,kinds=_legacy_view(j,launch,d)
    assert not j['failure'] and not j['unreturned_ids'],'unknown/missing mandatory lifecycle evidence blocks qualification'
    context=models.ArmModels();contracts=[];core.start_reader.ROOT=ROOT
    try:
        emitter_policy=emitter_scope_policy(launch,identity)
        shortcut_models=[]
        for cid,call in j['calls'].items():
            path=core.portable(ROOT,call['model_path'])
            fact,model=context.model_contract(ROOT,p,path,launch['arm'])
            if call['full_original']:
                assert sha(path)==p['reference']['canonical_sha256']
                assert core.lp_model(d.parents[1]/'reference'/p['id']/'original.lp')==model
            scope=context.model_scope_contract(call,model,p)
            shortcut=no_improver_shortcut_analysis(launch,call,model,emitter_policy,physical['F'])
            shortcut_models.append(shortcut)
            contracts.append(dict(call=cid,model=fact,scope=scope,solve_kind=kinds.get(cid,'MIP'),
                raw_native_preconditions=call['native_preconditions'],raw_precondition_reason=call.get('precondition_reason'),
                no_improver_shortcut_check=shortcut))
        known_old=[value for value in shortcut_models if value['model_scope_issue']]
        legacy_issue=None
        if known_old:
            legacy_issue=dict(schema='round133-old-D3-model-scope-shortcut-v1',emitter_policy=emitter_policy,
                models=known_old,old_side_performance_disposition='UNEVALUABLE',
                native_INFEASIBLE_does_not_prove_inclusive_domain_empty=True,
                native_numerical_contradiction_claimed=False,analytic_qualification_granted=False,
                raw_tuple_and_producer_clocks_unchanged=True)
            write(d/'legacy_model_scope_issue.json',legacy_issue)
        view=call_logs.build(ROOT,launch,d,legacy,result,model_parser=lambda path:context.data(path)[1][0])
        source=inspect.getsource(old_audit.return_chain)
        source=source.replace("parameters.parameter_readback(r,require_call=True,arm='P-GRB')",
            "parameter_checks._parameters(r,seed=l['seed'],require_call=True,arm='P-GRB')")
        source=source.replace("assert r['external_gini_tree_lifecycle_complete'] and r['external_gini_tree_backend_parameter_roundtrip_valid']",
            "assert native_release_lifecycle(r,j) and r['external_gini_tree_backend_parameter_roundtrip_valid']")
        ns=dict(vars(old_audit),parameter_checks=parameter_checks,native_release_lifecycle=native_release_lifecycle)
        exec(compile(source,__file__+'::actual_seed_return_chain','exec'),ns)
        with call_logs.activate(view):chain=ns['return_chain'](ROOT,launch,d,legacy,result,completion)
        submitted=[(path,read(path)) for path in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(path).get('submitted')]
        start_checks=[]
        for digest in sorted({value['model_sha256'] for _,value in submitted}):
            path=next(core.portable(ROOT,call['model_path']) for call in j['calls'].values() if call['model_sha256']==digest)
            start_checks.extend(core.start_reader.audit_model(path,[(path,value) for path,value in submitted if value['model_sha256']==digest],
                                'm-binary' if launch['arm']=='M-B' else 'off'))
        paid_start=compact_start.start_audit(ROOT,p,d) if launch['arm']=='P-S' and j['declared'] else None
        H=None;exchange=None
        if launch['arm']!='P-GRB':
            H=startup.reconstruct(ROOT,p,d)
            folder=d/'hga.csv.exchange'
            initial=native_runner.normalize(read(folder/'initial.json'))
            exchange=native_runner.replay_exchange(p,folder,initial)
            assert not read(folder/'result.json')['verification_failed']
            if j['started']:assert H['complete'],'native backend before full own 24+1 H completion'
            initial=[row['payload'] for row in observations if row['payload']['kind']=='witness' and row['payload']['call']==0]
            assert len(initial)==1 and startup.fleet_key(p,initial[0]['routes'])==H['fleet']
        if launch['method']=='P':
            actual=read(d/'round127_parameters.json')
            assert actual==dict(MIPFocus=0,Cuts=-1,NumStart_before_optimize=0,loaded_after_presets=True,authoritative_model_environment=True)
        if launch['method']=='PS' and j['started']:
            actual=read(d/'round130_parameters.json')
            assert actual==dict(MIPFocus=0,Cuts=-1,NumStart_before_optimize=1,loaded_after_presets=True,authoritative_model_environment=True)
        controller=core.evidence.controller_tables(d,result)
        claims=_claims(launch,j,chain,result)
        own_witnesses=j['witnesses']+[dict(physical,arm=launch['arm_id'],source='own_sealed_return',input_SHA=p['input_sha256'],
                               available=completion['fully_observed_end_to_end_seconds'],physical_verified=True)]
        excluded_scope={entry['call'] for entry in known_old}
        for claim in claims:
            if claim['call'] in excluded_scope:
                claim.update(domain_verified=False,qualification_reason='KNOWN_OLD_MODEL_SCOPE_SHORTCUT',
                             native_numerical_contradiction_claimed=False)
        source_checks=independent_source_checks(launch,j,kinds,chain,result,own_witnesses,excluded_scope)
        rejection=reconcile([claim for claim in claims if claim['domain_verified']],own_witnesses)
        rejection.update(model_scope_unqualified_calls=sorted(excluded_scope),
            excluded_model_scope_claims=[claim for claim in claims if not claim['domain_verified']])
        if rejection['rejections']:assert j['source_rejections'],'producer failed to identify own contradicted source'
        if legacy_issue:
            # Only now have the producer/model/return/Start/H/physical checks
            # all completed. This approved branch completes an old observation,
            # not a new old-source proof or an algorithm qualification.
            gate=legacy_scope_gate()
            arm=legacy_unevaluable_arm(physical,legacy_issue,gate)
            endpoint=dict(arm=arm,cover=None)
            write(d/'legacy_model_scope_disposition.json',dict(classification='UNEVALUABLE',
                reason='MODEL_SCOPE_ANALYTIC_SHORTCUT_UNQUALIFIED',not_a_native_numerical_counterexample=True,
                evidence_complete=True,own_physical_U=physical['F'],independent_analytic_floor=0.,
                raw_producer_tuple=dict(U=result['upper_bound'],L=result['lower_bound'],
                    certificate=result['strict_certified_original_problem'],
                    raw_claimed_T_cert=producer['T_produce'] if result['strict_certified_original_problem'] else None),
                original_T_produce=producer['T_produce'],producer_receipt_SHA=sha(d/'producer_receipt.json'),
                source_issue_SHA=sha(d/'legacy_model_scope_issue.json'),reader_policy_admission=gate,
                old_analytic_qualification_granted=False))
        elif result['strict_certificate_class']=='independent_zero_nonnegative_floor':
            assert exact_zero(physical,data,p) and physical['F']==0
            assert result['strict_certified_original_problem'] and result['lower_bound']==0
            assert result['strict_lower_bound_source']=='independent_full_domain_nonnegative_floor'
            if j['source_rejections']:
                arm=_safe_open(launch,d,result,physical,j,controller)
            else:
                arm=dict(source_reduced=False,native_proof_qualified=True,
                         implementation_failure_disposition_verified=True)
            arm.update(U=0.,L=0.,gap=0.,certificate=True,
                certificate_basis='INDEPENDENT_EXACT_ZERO_FULL_DOMAIN_NONNEGATIVE_FLOOR',
                performance_eligible=True,performance_evidence_eligible=True,
                independent_proof=True,native_search_cover_required_for_this_proof=False)
            endpoint=dict(arm=arm,cover=None)
        elif j['source_rejections']:
            arm=_safe_open(launch,d,result,physical,j,controller);endpoint=dict(arm=arm,cover=None)
        else:
            # Only physically/domain-qualified local observations feed the
            # old complete cover. Raw observations remain in j/raw files.
            with strict_bound_context():
                for b in legacy['bounds']:
                    if b['global_available']:
                        recomputed=core.evidence.bound(legacy['calls'][b['call']],b['native_bound'],j['witnesses'])
                        assert abs(recomputed-b['global_bound'])<=1e-10
                with call_logs.activate(view):endpoint=_normal_endpoint(launch,identity,d,legacy,result)
            arm=endpoint['arm'];arm.update(source_reduced=False,native_proof_qualified=True,performance_eligible=True,
                performance_evidence_eligible=True,implementation_failure_disposition_verified=True)
        own_zero=exact_zero(physical,data,p)
        arm.update(id=launch['id'],arm=launch['arm'],arm_id=launch['arm_id'],method=launch['method'],seed=launch['seed'],
            version=launch['version'],binary_layer=launch['binary_layer'],PE_SHA=identity['candidate_binary_sha256'],DLL_SHA=identity['dll_sha256'],
            input_SHA=p['input_sha256'],formal_protocol_qualified=not bool(legacy_issue),numbers_qualified=True,
            certificate_qualified=(arm.get('independent_proof',False) or not bool(j['source_rejections'])) and not bool(legacy_issue),
            implementation_qualified=not bool(legacy_issue),model_scope_qualified=not bool(legacy_issue),
            evidence_complete=True,own_exact_zero=own_zero,own_zero_independent_proof=own_zero,
            T_produce=producer['T_produce'],T_cert=producer['T_produce'] if arm['certificate'] and arm['performance_eligible'] else None,
            native_Optimize=j['started'],declared_calls=j['declared'],returned_calls=j['returned'],
            native_status=result.get('gurobi_status'),raw_claimed_L=result['lower_bound'],raw_claimed_certificate=result['strict_certified_original_problem'],
            raw_claimed_T_cert=producer['T_produce'] if result['strict_certified_original_problem'] else None,
            raw_result_relative_gap=result.get('gap'),
            signed_gap=arm['U']-arm['L'],destination=str(d),not_holdout=True)
        if H:
            compact=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            arm.update(H_complete=H['complete'],H_semantic_SHA=compact(H['semantic_traces']),
                       H_fleet_SHA=compact(H['fleet']),H_final_inventory=H['physical']['Y'])
        assert arm['L']<=arm['U']+TOL
        if not arm['certificate']:assert arm['T_cert'] is None
        audit=dict(schema='round133-full-postproduction-audit-v1',passed=not bool(legacy_issue),implementation_qualified=not bool(legacy_issue),
            evidence_complete=True,controlled_legacy_model_scope_unevaluable=bool(legacy_issue),
            raw_observations_SHA=sha(d/'observations.json'),producer_seal_SHA=sha(d/'producer_seal.json'),
            physical=physical,endpoint=arm,model_contracts=contracts,Start_checks=start_checks,paid_Start=paid_start,
            inclusive_emitter_scope_policy=emitter_policy,
            full_H=dict(complete=H['complete'],seed_ids=H['seed_ids'],physical=H['physical'],fleet=H['fleet']) if H else None,
            neutral_exchange_replay=exchange,
            call_log_bindings=view['bindings'],source_rejections=j['source_rejections'],own_source_adjudication=rejection,
            native_quality=j['native_quality'],native_infeasible=j['native_infeasible'],
            independent_source_checks=source_checks,
            Optimize_return_sequences=j['return_sequences'],qualified_return_sequences=legacy['return_sequences'],
            raw_tree_lifecycle_complete=result.get('external_gini_tree_lifecycle_complete'),
            qualified_cover=endpoint.get('cover'),Optimize=0,raw_bytes_unchanged=True,
            source_rejection_is_not_ordinary_qualified_open=bool(j['source_rejections']))
        write(d/'audit.json',audit);write(d/'native_claims.json',claims);write(d/'claim_rejections.json',rejection)
        write(d/'independent_evidence.json',dict(physical=physical,own_U=physical['F'],own_exact_zero=own_zero,
            independent_floor0=True,witnesses=own_witnesses,created_after_producer_seal=True,inside_own_whole=False,
            extra_solution_or_bound_backfilled=False))
        for name,digest in seal['required_SHA'].items():assert sha(d/name)==digest
        write(d/'verification_closeout.json',dict(necessary_verification_complete=True,implementation_qualified=not bool(legacy_issue),
            evidence_complete=True,controlled_legacy_model_scope_unevaluable=bool(legacy_issue),
            legacy_scope_policy_admission=arm.get('legacy_scope_policy_admission'),
            audit_SHA=sha(d/'audit.json'),endpoint_source='audit.json.endpoint',own_evidence_SHA=sha(d/'independent_evidence.json'),
            claims_SHA=sha(d/'native_claims.json'),rejection_SHA=sha(d/'claim_rejections.json'),
            producer_receipt_SHA=sha(d/'producer_receipt.json'),no_new_solution_or_certificate_backfilled=True,
            native_proof_qualified=arm['native_proof_qualified'],performance_eligible=arm['performance_eligible']))
        verified=time.perf_counter()
        write(d/'arm_total_receipt.json',dict(t_verified_perf=verified,t_verified_unix=time.time(),
            T_verify=verified-producer['t_produce_perf'],T_total=verified-producer['t0_perf'],
            producer_receipt_SHA=sha(d/'producer_receipt.json'),verification_closeout_SHA=sha(d/'verification_closeout.json'),
            necessary_verification_complete=True,future_group_review_not_in_clock=True))
        from round115_common import clock_evidence
        clock=clock_evidence(d,launch)
        arm.update(T_verify=clock['T_verify'],T_total=clock['T_total'])
        arm.update(audit_SHA=sha(d/'audit.json'),verification_closeout_SHA=sha(d/'verification_closeout.json'),
                   arm_total_receipt_SHA=sha(d/'arm_total_receipt.json'))
        write(d/'round134_endpoint.json',arm)
        return dict(arm=arm,audit_SHA=sha(d/'audit.json'),seconds=time.perf_counter()-tick)
    except BaseException as error:
        write(d/'round134_verification_failure.json',dict(UTC=utc(),error=repr(error),Optimize=0,
            source_and_raw_preserved=True,implementation_qualified=False,not_an_ordinary_open=True,
            own_physical_U=physical['F'],independent_analytic_floor=0.,
            independent_own_zero=physical['F']==physical['G']==physical['P']==0,
            physical_evidence_retained=physical,native_proof_qualified=False,performance_evidence_eligible=False))
        raise
    finally:context.clear()

def rebuild(stage):
    """Aggregate sealed small endpoints only; this is not a poll-time raw replay."""
    manifest=read(OUT/'plans'/f'{stage}_matrix_frozen.json');arms=[];missing=[]
    for group in manifest['groups']:
        launch=group['launch'];d=Path(launch['destination']);endpoint=d/'round134_endpoint.json'
        if not endpoint.exists():missing.append(dict(position=group['position'],arm_id=launch['arm_id']));continue
        close=read(d/'verification_closeout.json')
        if not close['implementation_qualified']:
            assert close.get('controlled_legacy_model_scope_unevaluable') and close.get('evidence_complete')
            assert launch['version']!='candidate' and stage=='D3'
            assert close['legacy_scope_policy_admission']==legacy_scope_gate()
        arm=read(endpoint);assert arm['arm_id']==launch['arm_id'] and arm['input_SHA']==launch['panel']['input_sha256']
        assert arm['audit_SHA']==close['audit_SHA']==sha(d/'audit.json')
        assert arm['verification_closeout_SHA']==sha(d/'verification_closeout.json')
        assert arm['arm_total_receipt_SHA']==sha(d/'arm_total_receipt.json')
        arms.append(arm)
    import round127_analysis as comparison
    pairs=[];by={(a['id'],a['seed'],a['method']):a for a in arms}
    if stage=='D1':
        for seed in (0,1):
            for left,right in (('S2','P'),('S2','PS'),('PS','P')):
                pairs.append(comparison.pair('K-15-S',by.get(('K-15-S',seed,left)),by.get(('K-15-S',seed,right)),
                    kind='Round133 fixed qualification; exposed regression',seed=seed))
            pairs.append(comparison.pair('SC-B20-S',by.get(('SC-B20-S',seed,'GEOM')),by.get(('SC-B20-S',seed,'S2R')),
                kind='Round133 same-build numerical qualification control',seed=seed))
    else:
        source=inspect.getsource(comparison.pair)
        needle="a['PE_SHA']==b['PE_SHA'] and ";assert source.count(needle)==1
        source=source.replace(needle,'')
        namespace=dict(vars(comparison));exec(compile(source,__file__+'::version_pair','exec'),namespace)
        for role in ('SC-C15-B','SC-B20-S'):
            for seed in (0,1):
                candidates=[a for a in arms if a['id']==role and a['seed']==seed and a['version']=='candidate']
                originals=[a for a in arms if a['id']==role and a['seed']==seed and a['version']!='candidate']
                left=dict(candidates[0],method='candidate S2') if candidates else None
                right=dict(originals[0],method='original E3 S2') if originals else None
                pairs.append(namespace['pair'](role,left,right,kind='Round133 fixed full paired version bridge',seed=seed))
    target=OUT/'reports'/stage;target.mkdir(parents=True,exist_ok=True)
    write(target/'arms.json',dict(arms=arms,missing_positions=missing,expected_positions=len(manifest['groups']),
          matrix_SHA=sha(OUT/'plans'/f'{stage}_matrix_frozen.json'),no_native_or_large_poll_replay=True))
    write(target/'pairs.json',dict(pairs=pairs,expected_comparisons=8 if stage=='D1' else 4,
          certification_first=True,open_time_imputed_as_cap=False))
    if arms:
        fields=list(dict.fromkeys(k for arm in arms for k in arm))
        with (target/'arms.csv').open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fields);writer.writeheader()
            writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in arm.items()} for arm in arms)
    if pairs:
        fields=list(dict.fromkeys(k for row in pairs for k in row))
        with (target/'pairs.csv').open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fields);writer.writeheader();writer.writerows(pairs)
    print(json.dumps(dict(stage=stage,complete=len(arms),missing=len(missing),expected=len(manifest['groups']))))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['D1','D3']);args=parser.parse_args();rebuild(args.stage)

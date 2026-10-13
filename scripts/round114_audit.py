"""Necessary current evidence audit; a typed rejection cannot skip closeout."""
from round114_common import ROOT, OUT, read, write, sha
from pathlib import Path
import collections, math, re, time
import round113_audit as inherited
import round114_ps as ps
import round108_reader as core
import round111_seed_audit as models
import round94_lpg_contemporary as parameters
import round86_native_evidence as journal_receipts
from round94_lpg_formal_recovery_v3 import MIP_KINDS
from round114_claims import ClaimRejection, reconcile, missing_return_gate, FAILURES
import round118_call_logs as call_logs

last_metrics={}
SETTINGS=ps.SETTINGS

def journal(root,l,d,observations):
    p=l['panel'];calls={};returned={};cancelled={};witnesses=[];bounds=[];failure=None;activity=set()
    identity=None
    commits=list((d/'journal').glob('event_*.commit'))
    assert len(commits)==len(observations),'unobserved committed event'
    for seq,row in enumerate(observations,1):
        checked=journal_receipts.receipt(d/'journal'/f'event_{seq}.commit',row['first_observed_seconds'],l['cap_seconds'])
        assert checked==row,'journal receipt mismatch'
        e=row['payload'];kind=e['kind'];assert not failure,'publication after failure latch'
        if kind=='identity':
            assert seq==1 and identity is None;identity=e
            assert e['input_sha256']==p['input_sha256'] and (e['V'],e['M'])==(p['V'],p['M'])
            assert (e['lambda'],e['T'],e['pickup_seconds'],e['drop_seconds'])==(p['lambda'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'])
            assert e['analytical_full_domain_lower_bound']==0
        elif kind=='call':
            cid=e['call'];assert cid==len(calls)+1 and e['settings']==SETTINGS
            assert sha(core.portable(root,e['model_path']))==e['model_sha256'];calls[cid]=e
            gmax=(p['V']-1)/p['V'];assert e['gmax']==gmax and 0<=e['lower_g']<=e['upper_g']<=gmax
            if e['full_original']:
                assert e['native_preconditions'] and e['lower_g']==0 and e['upper_g']==gmax
                assert e['model_sha256']==p['reference']['canonical_sha256']
        elif kind=='not_started':
            cid=e['call'];assert cid in calls and cid not in activity|set(returned)|set(cancelled)
            assert e['actual_Optimize'] is False and e['reason']=='no_remaining_original_work_window';cancelled[cid]=e
        elif kind=='returned':
            cid=e['call'];assert cid in calls and cid not in returned and cid not in cancelled and e['return_code']==0
            returned[cid]=dict(e,available=row['effective_available_seconds']);activity.add(cid)
        elif kind=='witness':
            cid=e['call'];assert cid==0 and not calls or cid in calls and cid not in returned and cid not in cancelled
            if cid:activity.add(cid)
            w=core.full_fleet(root,p,e);assert abs(w['G']-e['G'])<1e-7 and abs(w['P']-e['P'])<1e-7
            witnesses.append(dict(w,arm=l['arm'],call=cid,sequence=seq,source=e['source'],input_SHA=p['input_sha256'],
                physical_verified=True,available=row['effective_available_seconds']))
        elif kind=='bound':
            cid=e['call'];assert cid in calls and cid not in returned and cid not in cancelled
            assert math.isfinite(e['native_bound']);activity.add(cid);bounds.append(dict(e,available=row['effective_available_seconds']))
        elif kind=='witness_rejected':
            cid=e['call'];assert cid==0 or cid in calls and cid not in returned and cid not in cancelled
            if cid:activity.add(cid)
        elif kind=='failure':
            assert seq==len(observations) and e['reason'] in FAILURES;failure=e
        else:raise AssertionError(('unknown journal event',kind))
    assert identity is not None
    return dict(calls=calls,returned_ids=set(returned),not_started_ids=set(cancelled),actual_started_ids=activity,
        declared=len(calls),started=len(activity),returned=len(returned),not_started=len(cancelled),
        unreturned_ids=set(calls)-set(returned)-set(cancelled),witnesses=witnesses,bounds=bounds,failure=failure,
        return_sequences={k:v['sequence'] for k,v in returned.items()},return_available={k:v['available'] for k,v in returned.items()})

def phases(d,cap):
    rows=core.rows(d/'phases.csv');previous=-1
    assert rows and rows[0]['event']=='process_entry' and rows[-1]['event']=='process_exit'
    assert rows[-1]['status']=='complete' and rows[-1]['detail']=='rc=0'
    for seq,q in enumerate(rows):
        t=float(q['process_seconds']);assert int(q['sequence'])==seq and previous<=t<=cap;previous=t
        assert abs(float(q['nominal_deadline_remaining_seconds'])-float(q['work_deadline_remaining_seconds'])-30)<.01
    names=['final_result_serialization_start','final_result_serialization_complete','process_exit']
    indices=[]
    for name in names:
        hits=[n for n,q in enumerate(rows) if q['event']==name];assert len(hits)==1;indices+=hits
    assert indices==sorted(indices)
    return rows

def return_chain(root,l,d,j,r,c):
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    assert r['process_return_code']==0 and r['process_shutdown_margin_seconds']==30
    saved=read(d/'launch.json');assert saved['command']==l['command'] and saved['panel']==l['panel']
    phase=phases(d,l['cap_seconds']);logs=[];ledger=[]
    actual=[cid for cid in j['calls'] if cid not in j['not_started_ids']]
    assert set(actual)==j['actual_started_ids'],'unresolved declaration is not actual Optimize'
    if l['arm'] in ['P-GRB','P-S'] and actual:
        assert actual==[1] and r['gurobi_optimize_count']==r['native_mip_mipopt_count']==1
        assert r['gurobi_optimize_return_code']==r['native_mipopt_return_code']==0
        for key in ['gurobi_environment_count','gurobi_model_count','gurobi_model_read_count','gurobi_model_free_count','gurobi_environment_free_count',
            'native_mip_environment_count','native_mip_problem_count','native_mip_model_read_count','native_mip_freeprob_count','native_mip_close_count']:assert r[key]==1,key
        for key in ['native_mip_evidence_capture_complete','native_mip_problem_freed','native_mip_environment_closed','native_mip_lifecycle_valid',
            'gurobi_solver_finalization_reached','native_mip_solver_finalization_reached','gurobi_lifecycle_valid','gurobi_native_domain_audit_passed']:assert r[key] is True,key
        assert r['native_mip_freeprob_return_code']==r['native_mip_close_return_code']==0
        parameters.parameter_readback(r,require_call=True,arm='P-GRB')
        assert sum(q['event']=='plain_gurobi_optimize_launch' and q['status']=='start' for q in phase)==1
    elif l['arm'] in ['ENS-C','M-B'] and actual:
        ledger=core.rows(d/'external/paper_optimize_ledger.csv');assert len(ledger)==len(actual)
        assert r['external_gini_tree_optimize_count']==len(ledger)
        assert r['external_gini_tree_environment_count']==r['external_gini_tree_environment_free_count']==1
        count=r['external_gini_tree_model_count']
        assert count==r['external_gini_tree_model_read_count']==r['external_gini_tree_model_free_count']
        assert len({q['model_sha256'] for q in ledger})<=count<=len(ledger)
        assert r['external_gini_tree_lp_optimize_count']==sum(q['solve_kind']=='LP' for q in ledger)
        assert r['external_gini_tree_lp_optimize_count']+r['external_gini_tree_partial_mip_optimize_count']+r['external_gini_tree_terminal_mip_optimize_count']==len(ledger)
        assert r['external_gini_tree_lifecycle_complete'] and r['external_gini_tree_backend_parameter_roundtrip_valid']
        for cid,q in zip(actual,ledger):
            call=j['calls'][cid]
            assert q['leaf_id']==call['leaf'] and q['model_sha256']==call['model_sha256'] and int(q['optimize_return_code'])==0
            assert core.portable(root,q['native_log'])==core.portable(root,call['native_log_path'])
            assert q['solve_kind']=='LP' and not call['native_preconditions'] or q['solve_kind'] in MIP_KINDS and call['native_preconditions']
    for cid in actual:
        call=j['calls'][cid];path=core.portable(root,call['native_log_path']);text=call_logs.call_text(root,call,cid)
        assert text.count('Optimize a model with ')==1,'unknown extra/unbound Optimize in call log'
        assert ('Optimal objective' in text or 'Best objective ' in text or 'Infeasible model' in text) and ('Solved in ' in text or 'Explored ' in text or 'Infeasible model' in text)
        logs.append(dict(call=cid,path=path.relative_to(root).as_posix(),SHA=sha(path),text=text))
    missing=j['unreturned_ids']
    if missing:
        assert j['failure'] is not None and missing=={actual[-1]} and not j['not_started_ids']
    else:assert j['failure'] is None
    return dict(actual=actual,ledger=ledger,logs=logs,phase=phase,missing=sorted(missing),normal_return_verified=True)

def claims_for(l,j,chain,r):
    p=l['panel'];claims=[]
    def add(cid,seq,value,source,available):
        call=j['calls'][cid]
        claims.append(dict(arm=l['arm'],call=cid,sequence=seq,model_SHA=call['model_sha256'],input_SHA=p['input_sha256'],scope=call,
            value=value,source=source,available=available,domain_verified=True,dependencies=[cid]))
    for b in j['bounds']:add(b['call'],b['sequence'],b['native_bound'],'committed_native_bound',b['available'])
    for log in chain['logs']:
        cid=log['call'];seq=j['return_sequences'].get(cid,j['failure']['sequence'] if j['failure'] else 0)
        available=j['return_available'].get(cid,float(chain['phase'][-1]['process_seconds']))
        if l['arm'] in ['P-GRB','P-S']:
            printed=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',log['text']);assert printed
            value=r['gurobi_obj_bound_c'];assert r['gurobi_obj_bound_c_available'] and math.isfinite(value)
            assert abs(float(printed[-1])-value)<=1e-7 and abs(r['native_mip_best_bound']-value)<=1e-7
            add(cid,seq,value,'final_ObjBoundC_API_and_terminal_log',available)
        else:
            row=chain['ledger'][cid-1]
            if row['solve_kind']=='LP':
                printed=re.findall(r'Optimal objective\s+([-+0-9.eE]+)',log['text'])
                if printed:add(cid,seq,float(printed[-1]),'linked_LP_terminal_log',available)
            else:
                printed=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',log['text'])
                if printed and math.isfinite(float(printed[-1])) and abs(float(printed[-1]))<1e90:
                    add(cid,seq,float(printed[-1]),'linked_MIP_terminal_log',available)
    return claims

def independent(root,l,d,j,r,c,chain):
    p=l['panel'];a=core.evidence.instance(root,p);physical=core.full_fleet(root,p,r)
    assert p['lambda']>=0 and all(x>0 for x in a['D'][1:]) and all(x>=0 and math.isfinite(x) for x in a['w'][1:])
    assert math.isfinite(physical['F']) and physical['F']>=0 and abs(physical['F']-r['upper_bound'])<=1e-7
    zero=all(x==y for x,y in zip(physical['Y'][1:],a['D'][1:]));assert not zero or physical['F']==physical['G']==physical['P']==0.
    return dict(schema='round114-independent-arm-evidence-v1',arm=l['arm'],input_SHA=p['input_sha256'],own_U=physical['F'],own_exact_zero=zero,
        own_physical_verified=True,independent_floor0=True,independent_floor_source='original_G>=0_lambda>=0_weights>=0_absolute_penalty',
        physical=physical,witnesses=j['witnesses']+[dict(physical,arm=l['arm'],source='own_normal_return_result',input_SHA=p['input_sha256'],
            available=c['fully_observed_end_to_end_seconds'],physical_verified=True)],identity_verified=True,input_verified=True,
        model_domain_verified=True,journal_verified=True,return_verified=True,files_verified=True,
        clock_valid=False,necessary_closeout_complete=False,inside_own_whole=True,clock_pending_until_actual_whole=True,
        result_SHA=sha(d/'result.json'),observations_SHA=sha(d/'observations.json'),completion_SHA=sha(d/'completion.json'),
        counts=dict(declared=j['declared'],actual_Optimize=j['started'],journal_returned=j['returned'],
            independently_verified_returned=len(chain['actual']),explicit_not_started=j['not_started']),
        model_SHAs=[c['model_sha256'] for c in j['calls'].values()],raw_native_claims_preserved=True)

def rejected_cover_geometry(d,U,gmax):
    leaves=core.rows(d/'external/paper_leaf_ledger.csv')
    trace=core.rows(d/'external/global_bound_trace.csv')
    assert leaves and trace
    live=[q for q in leaves if q['status'] not in ['replaced','coalesced']]
    assert live
    covered=0.
    for q in sorted(live,key=lambda q:float(q['gamma_L'])):
        lo,hi=float(q['gamma_L']),float(q['gamma_U'])
        assert math.isfinite(lo) and math.isfinite(hi) and 0<=lo<=hi<=gmax
        assert lo<=covered+1e-7
        covered=max(covered,hi)
    assert covered+1e-7>=min(U,gmax)
    return dict(geometry_verified=True,covered_gini_upper=covered,live_leaves=len(live),
        raw_leaf_ledger_SHA=sha(d/'external/paper_leaf_ledger.csv'),raw_trace_SHA=sha(d/'external/global_bound_trace.csv'),
        native_cover_numbers_preserved_but_not_qualification_predicates=True,native_cover_certificate_qualified=False)

def rejected_mandatory(root,l,d,j,r,chain,ind,adjudication):
    context=models.ArmModels();contracts=[]
    try:
        for cid,call in j['calls'].items():
            path=core.portable(root,call['model_path'])
            if call['full_original']:
                assert sha(path)==l['panel']['reference']['canonical_sha256'];m=core.lp_model(path)
                contract=dict(SHA=sha(path),columns=len(m['order']),rows=len(m['rows']),full_original=True)
            else:contract,m=context.model_contract(root,l['panel'],path,l['arm'])
            scope=context.model_scope_contract(call,m,l['panel']);contracts.append(dict(contract,scope=scope,call=cid))
            if cid in j['not_started_ids']:continue
            text=next(q['text'] for q in chain['logs'] if q['call']==cid)
            size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',text);assert size
            assert (int(size[1]),int(size[2]))==(len(m['rows']),len(m['order']))
            header=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',text)
            counts=collections.Counter(m['types'].values())
            if chain['ledger'] and chain['ledger'][cid-1]['solve_kind']=='LP':
                # Simplex logs can omit the all-continuous type line. The
                # call-scoped view checks the LP transition/restoration ledger.
                if header:assert (int(header[1]),int(header[2]),int(header[3]))==(len(m['order']),0,0)
            else:
                assert header and (int(header[1]),int(header[2])-int(header[3]),int(header[3]))==(counts['C'],counts['I'],counts['B'])
        core.start_reader.ROOT=root
        submitted=[(p,read(p)) for p in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(p).get('submitted')]
        for digest in sorted({q['model_sha256'] for _,q in submitted}):
            path=next(core.portable(root,c['model_path']) for c in j['calls'].values() if c['model_sha256']==digest)
            core.start_reader.audit_model(path,[(p,q) for p,q in submitted if q['model_sha256']==digest],'m-binary' if l['arm']=='M-B' else 'off')
        if l['arm']=='P-S':ps.inherited.start_audit(root,l['panel'],d)
        if l['arm'] in ['ENS-C','M-B']:
            assert r['external_gini_tree_root_coverage_valid'] and r['external_gini_tree_parent_child_coverage_valid']
            ind['rejected_cover_geometry']=rejected_cover_geometry(d,ind['own_U'],(l['panel']['V']-1)/l['panel']['V'])
        if chain['missing']:
            bad=chain['actual'][-1];bad_call=j['calls'][bad]
            same_domain=any(q['call']==bad and q['reason']==j['failure']['reason'] for q in adjudication['rejections'])
            assert same_domain
            ownzero=any(w['F']==0. and all(x==y for x,y in zip(w['Y'][1:],core.evidence.instance(root,l['panel'])['D'][1:])) for w in j['witnesses'])
            terminal=not chain['ledger'] or chain['ledger'][-1]['solve_kind']!='LP'
            log=chain['logs'][-1]['text'];assert 'Optimal solution found' in log
            final=re.findall(r'Best objective ([^,]+), best bound ([^,]+), gap',log);assert final
            assert float(final[-1][0])==float(final[-1][1])==0.
            if not chain['ledger']:
                assert r['gurobi_status']==r['native_mip_status_code']==2
                assert r['gurobi_obj_val_available'] and r['gurobi_obj_val']==r['gurobi_obj_bound_c']==0.
            else:assert chain['ledger'][-1]['native_status']=='OPTIMAL'
            f=dict(prefix_continuous=True,failure_terminal=True,failure_reason=j['failure']['reason'],damaged_call=bad,
                actual_call_ids=chain['actual'],journal_returned_ids=sorted(j['returned_ids']),explicit_not_started_ids=sorted(j['not_started_ids']),
                terminal_MIP=terminal,all_actual_calls_bound=True,normal_return=True,API_or_ledger_return_verified=True,
                logs_parameters_models_cleanup_verified=True,serialization_process_exit_verified=True,own_committed_exact_zero=ownzero,
                same_domain_counterexample_verified=same_domain,independent_floor0=ind['independent_floor0'],clock_valid=True)
            ind['narrow_missing_return']=dict(missing_return_gate(f),original_clock_still_pending=True,evidence_predicates=f)
        else:assert j['started']==j['returned']
        return contracts
    finally:context.clear()

def adapter(l,observations,c,i):
    global last_metrics
    tick=time.perf_counter();d=Path(l['destination']);r=read(d/'result.json');root=ROOT
    assert c['stop_reason']=='normal_return' and c['returncode']==0
    assert sha(root/l['panel']['input_path'])==l['panel']['input_sha256']
    expected={'P-GRB':'custom','P-S':'research-round112-self-paid-ens-start-original-compact',
        'ENS-C':'research-round83-vds-equal-net-exchange','M-B':'research-round99-ensc-discrete-structure-m-binary'}[l['arm']]
    assert r['algorithm_preset']==expected
    j=journal(root,l,d,observations);chain=return_chain(root,l,d,j,r,c)
    ind=independent(root,l,d,j,r,c,chain);claims=claims_for(l,j,chain,r);adjudication=reconcile(claims,ind['witnesses'])
    if adjudication['rejections']:
        contracts=rejected_mandatory(root,l,d,j,r,chain,ind,adjudication)
        ind['model_contracts']=contracts
        value=dict(independent_evidence=ind,claims=claims,adjudication=adjudication,
            endpoint=dict(U=ind['own_U'],L=0.,gap=ind['own_U'],certificate=ind['own_exact_zero'],
                status=r['status'],source='OWN_ZERO_CERTIFICATE' if ind['own_exact_zero'] else 'SOURCE_REDUCED_OPEN'),
            normal_result_certificate=ind['own_exact_zero'],passed=False,raw_audit_failure_preserved=True,
            error='ClaimRejection(proven_same_domain_native_claim_rejection)',native_proof_qualified=False,
            independent_evidence_audit_passed=True,whole_pending=True,committed_events=len(observations),
            binary_sha256=i['candidate_binary_sha256'],witnesses=j['witnesses'],final_physical_verification=ind['physical'],
            native_calls_started=j['started'],native_calls_returned=j['returned'])
        write(d/'independent_evidence.json',ind);write(d/'native_claims.json',claims);write(d/'claim_rejections.json',adjudication)
        last_metrics=dict(inclusive_seconds=time.perf_counter()-tick,typed_claim_rejection=True)
        raise ClaimRejection(value)
    assert not j['failure'] and not j['unreturned_ids'],'unknown missing lifecycle'
    value=ps.adapter(l,observations,c,i) if l['arm']=='P-S' else inherited.adapter(l,observations,c,i)
    # The healthy path still runs the inherited full native/Start/cover audit.
    value.update(independent_evidence_audit_passed=True,native_proof_qualified=True,whole_pending=True)
    write(d/'independent_evidence.json',ind);write(d/'native_claims.json',claims);write(d/'claim_rejections.json',adjudication)
    last_metrics=dict(inclusive_seconds=time.perf_counter()-tick,typed_claim_rejection=False)
    return value

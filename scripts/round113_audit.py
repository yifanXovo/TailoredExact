"""Necessary P-S audit and offline boundary share the real no-Optimize gate."""
import csv, math, re, time
from pathlib import Path
from round113_common import ROOT, read, sha
import round112_audit as inherited
import round108_reader as core
import round94_lpg_contemporary as parameters

last_metrics={}
SETTINGS=dict(read_return_code=0,Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,
    FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)

def event_lifecycle(observations):
    """A declaration is not a start. Missing returned is never a cancellation."""
    calls={}; returned={}; cancelled={}; activity=set(); identities=[]
    for seq,row in enumerate(observations,1):
        e=row['payload'];assert e['sequence']==seq
        kind=e['kind']
        if kind=='identity':
            assert seq==1;identities.append(e)
        elif kind=='call':
            i=e['call'];assert i==len(calls)+1 and i not in calls
            calls[i]=e
        elif kind=='not_started':
            i=e['call'];assert i in calls and i not in cancelled and i not in returned and i not in activity
            assert e['actual_Optimize'] is False and e['reason']=='no_remaining_original_work_window'
            cancelled[i]=e
        elif kind=='returned':
            i=e['call'];assert i in calls and i not in returned and i not in cancelled and e['return_code']==0
            returned[i]=e;activity.add(i)
        elif kind in ['bound','witness','witness_rejected']:
            i=e.get('call',0)
            if kind=='bound':assert i>0
            if i:
                assert i in calls and i not in cancelled
                # Native callback evidence must precede the native returned event.
                assert i not in returned
                activity.add(i)
            elif kind in ['witness','witness_rejected']:
                assert not calls, 'own startup witness follows model declaration'
        else:raise AssertionError(('journal failure/unknown event',e))
    assert len(identities)==1
    return dict(calls=calls,returned_ids=set(returned),not_started_ids=set(cancelled),
        declared=len(calls),returned=len(returned),not_started=len(cancelled),
        actual_started_ids=activity,started=len(activity),
        undeclared_start_not_inferred=True,pending_declaration_ids=set(calls)-set(cancelled)-activity,
        unreturned_ids=set(calls)-set(cancelled)-set(returned),identity=identities[0])

def ps_journal(root,p,d,observations=None):
    observations=read(d/'observations.json') if observations is None else observations
    life=event_lifecycle(observations);witnesses=[];bounds=[];trace=[]
    identity=life['identity']
    assert identity['input_sha256']==p['input_sha256']
    assert (identity['lambda'],identity['T'],identity['pickup_seconds'],identity['drop_seconds'])==(
        p['lambda'],p['T_seconds'],p['pickup_seconds'],p['drop_seconds'])
    assert (identity['V'],identity['M'])==(p['V'],p['M']) and identity['analytical_full_domain_lower_bound']==0
    # Production intentionally keeps the original compact option copy custom;
    # the completed result names the effective P-S entry separately.
    assert identity['preset']=='custom' and identity['method']=='gurobi'
    for seq,row in enumerate(observations,1):
        e=row['payload'];raw=d/'journal'/f'event_{seq}.json';commit=d/'journal'/f'event_{seq}.commit'
        checked=__import__('round86_native_evidence').receipt(commit,row['first_observed_seconds'],p['cap_seconds'])
        assert checked['payload']==e and checked['sha256']==row['sha256']
        assert checked['data_close_seconds']==row['data_close_seconds']
        assert checked['effective_available_seconds']==row['effective_available_seconds']
        if e['kind']=='call':
            assert e['full_original'] and e['native_preconditions'] and e['settings']==SETTINGS
            assert sha(core.portable(root,e['model_path']))==e['model_sha256']==p['reference']['canonical_sha256']
            assert e['lower_g']==0 and e['upper_g']==e['gmax']==(p['V']-1)/p['V']
        elif e['kind']=='witness':
            w=core.full_fleet(root,p,e)
            assert abs(w['G']-e['G'])<1e-7 and abs(w['P']-e['P'])<1e-7
            witnesses.append(dict(w,call=e['call'],source=e['source'],sequence=seq,available=row['effective_available_seconds']))
        elif e['kind']=='bound':
            assert not e['inconsistent']
            L=core.evidence.bound(life['calls'][e['call']],e['native_bound'],witnesses) if e['global_available'] else None
            assert L is None and e['global_bound'] is None or L is not None and abs(L-e['global_bound'])<1e-10
            bounds.append(dict(e,available=row['effective_available_seconds']))
        if witnesses:
            U=min(w['F'] for w in witnesses);L=max([0]+[b['global_bound'] for b in bounds if b['global_available']])
            assert L<=U+1e-7
            trace.append(dict(sequence=seq,available=row['effective_available_seconds'],kind=e['kind'],U=U,L=L,gap=U-L))
    for b in bounds:
        if b['global_available']:core.evidence.bound(life['calls'][b['call']],b['native_bound'],witnesses)
    assert witnesses and witnesses[0]['call']==0 and witnesses[0]['source']=='round112_own_verified_ENS_startup'
    return dict(life,witnesses=witnesses,bounds=bounds,trace=trace,
        return_sequences={row['payload']['call']:row['payload']['sequence'] for row in observations if row['payload']['kind']=='returned'},
        return_available={row['payload']['call']:row['effective_available_seconds'] for row in observations if row['payload']['kind']=='returned'})

def phase_rows(d,cap):
    with (d/'phases.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    assert rows and rows[0]['event']=='process_entry' and rows[-1]['event']=='process_exit'
    assert rows[-1]['status']=='complete' and rows[-1]['detail']=='rc=0'
    previous=-1
    for seq,row in enumerate(rows):
        assert int(row['sequence'])==seq
        t=float(row['process_seconds']);nominal=float(row['nominal_deadline_remaining_seconds']);work=float(row['work_deadline_remaining_seconds'])
        assert math.isfinite(t) and previous<=t<=cap and math.isfinite(work) and math.isfinite(nominal)
        # Ledger clocks are separate immediate reads; preserve their actual values.
        assert abs(nominal-work-30)<.01 and abs(nominal+t-cap)<.01
        previous=t
    assert sum(r['event']=='round112_ENS_H' and r['status']=='start' for r in rows)==1
    assert sum(r['event']=='round112_ENS_H' and r['status']=='complete' for r in rows)==1
    assert sum(r['event']=='final_result_serialization_complete' for r in rows)==1
    return rows

def validate_ps_lifecycle(root,l,d,j,r,c,own):
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    assert r['process_return_code']==0 and r['process_shutdown_margin_seconds']==30
    assert '--round112-ens-start-compact' in l['command'] and '--plain-baseline' in l['command']
    assert r['algorithm_preset']=='research-round112-self-paid-ens-start-original-compact'
    assert r['gurobi_hga_start_requested'] is False
    saved_launch=read(d/'launch.json')
    assert saved_launch['command']==l['command'] and saved_launch['panel']==l['panel']
    assert not any(s in r['status'].lower() for s in ['error','failed','invalid','numeric'])
    rows=phase_rows(d,l['cap_seconds'])
    launch=[q for q in rows if q['event']=='plain_gurobi_optimize_launch']
    mapped=[q for q in rows if q['event']=='round112_compact_start']
    def unique_phase(event,status):
        hits=[q for q in rows if q['event']==event and q['status']==status]
        assert len(hits)==1
        return int(hits[0]['sequence'])
    hs=unique_phase('round112_ENS_H','start');he=unique_phase('round112_ENS_H','complete')
    ss=unique_phase('final_result_serialization_start','start')
    se=unique_phase('final_result_serialization_complete','complete')
    assert hs<he<ss<se<int(rows[-1]['sequence'])
    assert j['declared']<=1 and len(launch)<=1
    backend_log=d/'native.log'
    log=backend_log.read_text(encoding='utf-8') if backend_log.exists() else ''
    actual_log=bool(re.search(r'Optimize a model with|Explored \d+ nodes|Root relaxation:|User MIP start',log))
    assert r['gurobi_optimize_count']==j['started']
    Start=None;parameter_readback={}
    if j['declared']:
        assert sha(d/'compact.lp')==l['panel']['reference']['canonical_sha256']
        assert r['gurobi_native_domain_audit_passed']
        for k,key in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:
            assert r[key]==l['panel']['reference'][k]
        assert [v['status'] for v in mapped]==['start','complete']
        assert he<int(mapped[0]['sequence'])<int(mapped[1]['sequence'])<ss
        # These checks happened before beginCall, also on the no-Optimize path.
        Start=inherited.start_audit(root,l['panel'],d)
        Start['mapping_validation_submission_seconds']=read(d/'native.log.round112.start.json')['mapping_validation_submission_seconds']
        if j['started']:
            parameter_readback=parameters.parameter_readback(r,require_call=True,arm='P-GRB')
        else:
            expected=dict(threads=1,seed=0,presolve=-1,mip_gap=0.,mip_gap_abs=0.)
            for name,value in expected.items():
                prefix='gurobi_'+name+'_'
                assert r[prefix+'requested']==r[prefix+'effective']==value
                assert r[prefix+'set_return_code']==r[prefix+'get_return_code']==0
            assert r['gurobi_version']=='13.0.2'
            parameter_readback={name:{suffix:r['gurobi_'+name+'_'+suffix] for suffix in
                ['requested','effective','set_return_code','get_return_code']} for name in expected}
    else:
        assert not mapped and not (d/'compact.lp').exists() and not (d/'native.log.round112.start.json').exists()
    if j['started']:
        assert j['declared']==j['returned']==1 and not j['not_started'] and not j['unreturned_ids']
        assert len(launch)==1 and launch[0]['status']=='start'
        assert float(launch[0]['work_deadline_remaining_seconds'])>0
        assert int(mapped[-1]['sequence'])<int(launch[0]['sequence'])
        assert int(launch[0]['sequence'])<ss
        assert actual_log and r['gurobi_lifecycle_valid'] and r['gurobi_solver_finalization_reached']
        assert r['status'] not in ['startup_zero','startup_deadline']
        branch='ONE_STARTED_RETURNED_ORIGINAL_COMPACT_MIP'
    else:
        assert not launch and not actual_log and not j['returned'] and not j['bounds']
        assert all(w['call']==0 for w in j['witnesses'])
        assert r['gurobi_solution_count']==0 and not r['gurobi_solver_finalization_reached']
        assert not r['gurobi_obj_bound_available'] and not r['gurobi_obj_bound_c_available']
        assert not r['native_mip_best_bound_available'] and not r['native_mip_objective_available']
        assert not (d/'native.log.round112.native.json').exists()
        assert r['status'] in ['startup_zero','startup_deadline']
        assert r['lower_bound']==0
        if j['not_started']:
            assert j['declared']==j['not_started']==1 and j['not_started_ids']=={1}
            assert r['status']=='startup_deadline' and own['F']>1e-7
            cancellation=next(row for row in read(d/'observations.json') if row['payload']['kind']=='not_started')
            assert cancellation['data_close_seconds']>=l['cap_seconds']-30
            assert cancellation['data_close_seconds']<=float(next(q for q in rows if q['event']=='final_result_serialization_start')['process_seconds'])
            branch='MAPPED_EXPLICIT_NOT_STARTED'
        elif r['status']=='startup_zero':
            assert j['declared']==0
            assert own['F']<=1e-7 and r['strict_certified_original_problem']
            branch='OWN_STARTUP_ZERO'
        else:
            assert j['declared']==0, 'unresolved declaration is not a normal premodel return'
            assert own['F']>1e-7 and not r['strict_certified_original_problem']
            branch='PREMODEL_STARTUP_DEADLINE'
        if r['status']=='startup_deadline':
            serial=next(q for q in rows if q['event']=='final_result_serialization_start')
            assert float(serial['work_deadline_remaining_seconds'])<=0
            assert not r['strict_certified_original_problem']
    return dict(branch=branch,declared_calls=j['declared'],actual_Optimize=j['started'],
        returned=j['returned'],explicit_not_started=j['not_started'],Start=Start,
        parameter_readback=parameter_readback,backend_exposure='EXPOSED' if j['started'] else 'BACKEND_NOT_EXPOSED',
        independent_floor0=True,standalone_started_journal_event_required=False)

def paid_endpoint(root,l,i,d,j):
    p=l['panel'];r=read(d/'result.json');c=read(d/'completion.json')
    own=core.full_fleet(root,p,read(d/'result.json.round112.startup.json'));physical=core.full_fleet(root,p,r)
    lifecycle=validate_ps_lifecycle(root,l,d,j,r,c,own)
    U=min([own['F'],physical['F']]+[w['F'] for w in j['witnesses']])
    assert physical['F']<=own['F']+1e-7 and abs(physical['F']-U)<=1e-7
    L=max([0.]+[b['global_bound'] for b in j['bounds'] if b['global_available']]);damage=[]
    if j['started']:
        native=core.cold_returned_bound(root,d,j,r)
        L=max(L,native['L'])
        cert=bool(r['gurobi_status']==2 and U-L<=1e-7)
    else: L=0.;cert=r['status']=='startup_zero'
    assert math.isfinite(U) and math.isfinite(L) and L<=U+1e-7
    assert cert==r['strict_certified_original_problem']
    a=dict(id=l['id'],arm=l['arm'],U=U,L=L,gap=U-L,certificate=cert,certificate_qualified=True,numbers_qualified=True,
        status=r['status'],native_Optimize=j['started'],declared_native_calls=j['declared'],explicit_not_started=j['not_started'],
        PE_SHA=i['candidate_binary_sha256'],DLL_SHA=i['dll_sha256'],cap_seconds=l['cap_seconds'],own_startup_U=own['F'],
        native_adoption=read(d/'native.log.round112.native.json') if j['started'] else 'BACKEND_NOT_EXPOSED')
    return dict(arm=a,physical=physical,own_startup=own,Start=lifecycle['Start'],result=r,completion=c,
        controller=core.evidence.controller_tables(d,r),cover=None,lifecycle=lifecycle,numerical_damage=damage)

def adapter(l,observations,c,i):
    global last_metrics
    if l['arm']!='P-S':
        value=inherited.adapter(l,observations,c,i);last_metrics=dict(inherited.last_metrics)
        return value
    tick=time.perf_counter();d=Path(l['destination'])
    j=ps_journal(ROOT,l['panel'],d,observations)
    ep=paid_endpoint(ROOT,l,i,d,j)
    a=ep['arm']
    value=dict(passed=True,binary_sha256=i['candidate_binary_sha256'],committed_events=len(observations),
        native_calls_declared=j['declared'],native_calls_started=j['started'],native_calls_returned=j['returned'],
        native_calls_not_started=j['not_started'],physical_witnesses=len(j['witnesses']),witnesses=j['witnesses'],
        UB=a['U'],LB=a['L'],gap=a['gap'],own_startup=ep['own_startup'],final_physical_verification=ep['physical'],
        normal_result_certificate=a['certificate'],Start=ep['Start'],parameter_readback=ep['lifecycle']['parameter_readback'],
        lifecycle=ep['lifecycle'],numerical_damage=ep['numerical_damage'],
        endpoint=dict(U=a['U'],L=a['L'],gap=a['gap'],certificate=a['certificate'],status=a['status'],source='own_H_and_original_compact'))
    last_metrics=dict(inclusive_seconds=time.perf_counter()-tick)
    return value

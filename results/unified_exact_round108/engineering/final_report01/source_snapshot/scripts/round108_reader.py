"""Reconstruct Round108 from raw public evidence; standard library, no solver.

ROOT is supplied explicitly. Absolute paths retained by the measured executable
are translated to this root; there is no original-worktree fallback. Reuses the
R107 physical/native-journal reader and R99 strict LP/Start parser, not their
endpoint, certificate, clipped-gap or selection code.
"""
import argparse, collections, json, math, re
from pathlib import Path
import round107_reader as evidence
import round99_pure_start_audit as start_reader
import round108_decisions as decision
import round108_scopes as scopes

read=evidence.read;sha=evidence.sha;rows=evidence.rows;write=evidence.write
table=evidence.table;portable=evidence.portable;close=evidence.close
ROUND='results/unified_exact_round108'

def require_identity(root,identity,candidate):
    assert identity['candidate_binary_sha256']==candidate['production_PE_SHA']
    assert identity['dll_sha256']==candidate['DLL_SHA']
    assert identity['source_hashes']==candidate['source_bindings']
    for name,digest in candidate['source_bindings'].items():assert sha(root/name)==digest, name
    for name,digest in identity['helpers'].items():assert sha(root/name)==digest,name
    assert identity['prereg_sha256']==sha(portable(root,identity['protocol_path']))
    assert identity['runner_sha256']==sha(root/'scripts/round108_campaign.py')

def lp_model(path):
    """Parse the observed original one-line LP grammar, retaining semantics."""
    order=[];seen=set();bounds={};types={};constraints=[];objective=None;section=None
    def register(name):
        assert start_reader.NAME.fullmatch(name)
        if name not in seen:seen.add(name);order.append(name)
    def linear(body):
        terms,constant=start_reader.expression(body,register);merged=collections.defaultdict(float)
        for name,value in terms:merged[name]+=value
        return tuple(sorted((name,value) for name,value in merged.items() if value)),constant
    with path.open(encoding='utf-8') as file:
        for raw in file:
            line=raw.strip()
            if not line or line.startswith('\\'):continue
            if line in ['Minimize','Subject To','Bounds','Generals','Binaries','End']:section=line;continue
            if section=='Minimize':
                assert objective is None and line.startswith('obj:');objective=linear(line.split(':',1)[1])
            elif section=='Subject To':
                body=line.split(':',1)[1];match=start_reader.REL.search(body);assert match
                terms,constant=linear(body[:match.start()]);rhs=float(match[2])-constant
                assert math.isfinite(rhs);constraints.append((terms,match[1],rhs))
            elif section=='Bounds':
                t=line.split();assert len(t)==5 and t[1]==t[3]=='<='
                low,name,high=float(t[0]),t[2],float(t[4]);register(name)
                assert name not in bounds and low<=high;bounds[name]=(low,high)
            elif section in ['Generals','Binaries']:
                for name in line.split():register(name);assert name not in types;types[name]='I' if section=='Generals' else 'B'
            else:raise AssertionError(('unrecognized LP',path,line))
    assert section=='End' and objective is not None and set(bounds)==seen
    return dict(order=order,bounds=bounds,types={n:types.get(n,'C') for n in order},rows=constraints,objective=objective)

def model_contract(root,p,path,arm):
    m=lp_model(path);t=m['types'];names=m['order'];quantities=[n for n in names if n.startswith(('p_','d_'))]
    assert len(quantities)==2*p['V']*p['M']
    assert all(t[n]==('C' if arm=='M-B' else 'I') for n in quantities)
    assert all(t[n] in ['I','B'] for n in names if n.startswith(('x_','load_','Y_')))
    assert all(t[n]=='B' for n in names if n.startswith(('mode_','z_','state_')) and not n.startswith('state_g_'))
    modes=[n for n in names if n.startswith('mode_')];assert len(modes)==p['V']*p['M']
    counter=collections.Counter(m['rows']);a=evidence.instance(root,p);link_count=0
    if arm=='M-B':
        for i in range(1,p['V']+1):
            terms={n:1. for n in quantities if n.endswith('_'+str(i))}
            selectors=[n for n in names if re.fullmatch(r'state_'+str(i)+r'_\d+',n)]
            assert selectors
            for n in selectors:
                amount=abs(a['b'][i]-int(n.rsplit('_',1)[1]))
                if amount:terms[n]=-float(amount)
            assert counter[(tuple(sorted(terms.items())),'=',0.)]>=1,('missing frozen A',path,i)
            terms={f'z_{k}_{i}':1. for k in range(p['M'])};selector=f'state_{i}_{a["b"][i]}'
            if selector in t:terms[selector]=1.
            assert counter[(tuple(sorted(terms.items())),'=',1.)]>=1,('missing frozen B',path,i)
            link_count+=2
    return dict(path=path.relative_to(root).as_posix(),SHA=sha(path),rows=len(m['rows']),columns=len(names),
        quantity_columns=len(quantities),quantity_type='C' if arm=='M-B' else 'I',direction_columns=len(modes),
        frozen_A_B_rows_checked=link_count,route_load_Y_integer=True,state_assignment_direction_binary=True),m

def full_fleet(root,p,w):
    # Missing vehicles are explicit empty routes, never borrowed from another arm.
    w=dict(w);routes=list(w['routes']);cars={r.get('vehicle',r.get('vehicle_id')) for r in routes}
    assert len(cars)==len(routes) and cars<=set(range(p['M']))
    for k in range(p['M']):
        if k not in cars:routes.append(dict(vehicle=k,nodes=[0,0],operations=[]))
    w['routes']=routes;physical=evidence.physical(root,p,w)
    assert all(math.isfinite(physical[k]) for k in ['G','P','F'])
    return dict(physical,routes=routes,complete_fleet_vehicles=p['M'],empty_vehicles_added=p['M']-len(cars))

def returned_native_proofs(root,j,controller):
    """Final native log bounds become evidence only at the linked return.

    The original journal's returned event retains rc, not final ObjBound.
    Its callback bounds need not include the final optimal bound. A per-call
    native log, actual optimize ledger, model hash and successful return supply
    that missing evidence; the printed value is retained without rounding repair.
    """
    calls=[(i,c) for i,c in j['calls'].items() if i not in j['not_started_ids'] and not c['full_original']]
    actual=controller['controller_native'];assert len(calls)==len(actual)
    proofs=[]
    for (call_id,call),row in zip(calls,actual):
        assert row['leaf_id']==call['leaf'] and row['model_sha256']==call['model_sha256']
        assert int(row['optimize_return_code'])==0 and call_id in j['returned_ids']
        assert portable(root,row['native_log'])==portable(root,call['native_log_path']), 'returned proof must use this call native log'
        if not call['native_preconditions']:continue
        assert row['solve_kind']!='LP'
        path=portable(root,row['native_log']);native_text=path.read_text(encoding='utf-8')
        printed=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',native_text)
        if row['native_status']=='OPTIMAL':assert 'Optimal solution found' in native_text and printed
        if not printed:continue
        value=float(printed[-1])
        if not decision.finite(value) or abs(value)>=1e90:
            assert row['native_status']!='OPTIMAL';continue
        proofs.append(dict(call=call_id,lo=call['lower_g'],hi=call['upper_g'],L=value,cutoff=call['cutoff'],
            sequence=j['return_sequences'][call_id],source='linked_returned_original_integer_native_log_final_bound',
            native_status=row['native_status'],native_log=path.relative_to(root).as_posix(),native_log_SHA=sha(path),full_original=False))
    return proofs


def cold_returned_bound(root,d,j,r):
    """Qualify the original cold model's final readback against its own log."""
    assert len(j['calls'])==1 and j['started']==j['returned']==1
    call_id,call=next(iter(j['calls'].items()))
    assert call['full_original'] and call['native_preconditions'] and call_id in j['returned_ids']
    path=portable(root,call['native_log_path']);assert path==(d/'native.log').resolve()
    assert call['model_sha256']==sha(d/'compact.lp')
    native_text=path.read_text(encoding='utf-8')
    if r['gurobi_status']==2:assert 'Optimal solution found' in native_text
    elif r['gurobi_status']==9:assert 'Time limit reached' in native_text
    elif r['gurobi_status']==11:assert 'Solve interrupted' in native_text
    else:raise AssertionError(('cold native terminal status needs qualification',r['gurobi_status']))
    printed=re.findall(r'Best objective [^,]+, best bound ([^,]+), gap',native_text)
    assert printed and decision.finite(float(printed[-1]))
    value=r['native_mip_best_bound']
    assert r['native_mip_best_bound_available'] is True and decision.finite(value) and abs(value)<1e90
    assert close(float(printed[-1]),value) and close(value,r['lower_bound'])
    callbacks=[b['global_bound'] for b in j['bounds'] if b['global_available']]
    assert not callbacks or value+decision.CLOSURE_TOL>=max(callbacks)
    return dict(call=call_id,lo=call['lower_g'],hi=call['upper_g'],L=value,cutoff=None,
        sequence=j['return_sequences'][call_id],source='linked_returned_complete_original_cold_native_log_and_readback',
        native_status=r['gurobi_status'],native_log=path.relative_to(root).as_posix(),native_log_SHA=sha(path),
        printed_native_final_bound=float(printed[-1]),full_original=True)


def scoped_proofs(j,controller,U):
    """Raw native/complete-LP bounds, qualified for their original true-G scope."""
    proofs=[]
    lp_calls=[(i,c) for i,c in j['calls'].items() if i not in j['not_started_ids'] and not c['native_preconditions']]
    actual_lp=[r for r in controller['controller_native'] if r['solve_kind']=='LP']
    status_lp=controller['controller_LP_status']
    assert len(lp_calls)==len(actual_lp)==len(status_lp)
    linked_lp={i:(a,s) for (i,c),a,s in zip(lp_calls,actual_lp,status_lp)}
    for call_id,call in j['calls'].items():
        if call_id in j['not_started_ids'] or call['cutoff']+decision.CLOSURE_TOL<U:continue
        if call['native_preconditions']:
            values=[b['native_bound'] for b in j['bounds'] if b['call']==call_id]
            if values:
                assert all(decision.finite(v) for v in values)
                best=min((b for b in j['bounds'] if b['call']==call_id and b['native_bound']==max(values)),key=lambda b:b['sequence'])
                proofs.append(dict(call=call_id,lo=call['lower_g'],hi=call['upper_g'],L=max(values),cutoff=call['cutoff'],
                    sequence=best['sequence'],source='qualified_original_integer_native_bound'))
        else:
            # LP returns are linked to their actual model/call/native ledger.
            # They are valid relaxations, never integer native-precondition calls.
            a,s=linked_lp[call_id]
            assert a['leaf_id']==s['leaf_id']==call['leaf'] and a['model_sha256']==call['model_sha256']
            assert abs(float(s['gamma_L'])-call['lower_g'])<=1e-12 and abs(float(s['gamma_U'])-call['upper_g'])<=1e-12
            assert int(a['optimize_return_code'])==0 and s['native_status']==a['native_status']
            if not int(s['terminal_valid']):continue
            if int(s['optimal']) and int(s['bound_available']):
                L=float(s['lower_bound']);assert decision.finite(L)
                proofs.append(dict(call=call_id,lo=call['lower_g'],hi=call['upper_g'],L=L,cutoff=call['cutoff'],
                    sequence=j['return_sequences'][call_id],source='actual_optimal_complete_original_LP_relaxation'))
            elif int(s['infeasible']):
                assert a['native_status']=='INFEASIBLE'
                proofs.append(dict(call=call_id,lo=call['lower_g'],hi=call['upper_g'],L=call['cutoff'],cutoff=call['cutoff'],
                    sequence=j['return_sequences'][call_id],source='complete_original_LP_infeasible_below_qualified_cutoff'))
    proofs.extend(p for p in j.get('returned_native_proofs',[]) if p['cutoff']+decision.CLOSURE_TOL>=U)
    return proofs

def supported_leaf_bound(leaf,proofs,claim_cutoff=None):
    lo,hi=float(leaf['gamma_L']),float(leaf['gamma_U'])
    points=sorted({lo,hi,*[v for p in proofs for v in [p['lo'],p['hi']] if lo<v<hi]})
    intervals=list(zip(points,points[1:])) or [(lo,hi)]
    # A scope's original inverse embedding is for physical true G in its
    # interval. High-epigraph candidates outside that true-G scope do not turn a
    # local bound/INF into a global proof. Full interval coverage is required.
    lower=math.inf
    for left,right in intervals:
        valid=[min(p['L'],p['cutoff']) for p in proofs if p['lo']<=left+1e-12 and p['hi']+1e-12>=right]
        lower=min(lower,max([left]+valid)) # original nonnegative penalty: F>=true G
    claimed=float(leaf['lower_bound'])
    if claim_cutoff is not None:claimed=min(claimed,claim_cutoff)
    assert claimed<=lower+decision.CLOSURE_TOL,('unsupported conditional leaf lower bound',leaf,claim_cutoff,lower)
    return lower

def chronological_cover(j,controller,U):
    """Every saved cover bound must already be available at its event sequence.

    An objective cutoff c can establish only min(native/LP bound,c) on its
    true-G interval; outside the cutoff, F>=c supplies the remaining cases.
    This proof qualification never clips the published signed endpoint gap.
    """
    proofs=scoped_proofs(j,controller,U);events=[];available={};audit=[]
    for p in proofs:
        if not j['calls'][p['call']]['native_preconditions']:events.append((p['sequence'],'LP',p))
        elif p['source']=='linked_returned_original_integer_native_log_final_bound':events.append((p['sequence'],'returned',p))
    for call in j['calls'].values():events.append((call['sequence'],'call',call))
    for b in j['bounds']:events.append((b['sequence'],'bound',b))
    for sequence,kind,payload in sorted(events,key=lambda e:e[0]):
        if kind in ['LP','returned']:
            prior=available.get(payload['call'])
            if prior is None or payload['L']>prior['L']:available[payload['call']]=payload
            continue
        call=payload if kind=='call' else j['calls'][payload['call']]
        if kind=='bound' and call['native_preconditions']:
            p=dict(call=payload['call'],lo=call['lower_g'],hi=call['upper_g'],L=payload['native_bound'],
                cutoff=call['cutoff'],sequence=sequence,source='prior_or_current_committed_original_integer_native_bound')
            previous=available.get(p['call'])
            if previous is None or p['L']>previous['L']:available[p['call']]=p
        if call['full_original']:continue
        if kind=='bound' and not payload['global_available']:continue
        pieces=[dict(piece) for piece in call['cover']]
        if kind=='bound':
            matched=0
            for piece in pieces:
                if (piece['id'],piece['lower_g'],piece['upper_g'],piece['cutoff'])==(call['leaf'],call['lower_g'],call['upper_g'],call['cutoff']):
                    piece['lower']=max(piece['lower'],payload['native_bound']);matched+=1
            assert matched==1
        for piece in pieces:
            leaf=dict(gamma_L=piece['lower_g'],gamma_U=piece['upper_g'],lower_bound=piece['lower'])
            supported=supported_leaf_bound(leaf,list(available.values()),piece['cutoff'])
            assert all(p['sequence']<=sequence for p in available.values())
            audit.append(dict(sequence=sequence,event_kind=kind,call=call['call'],leaf=piece['id'],
                lo=piece['lower_g'],hi=piece['upper_g'],reported_lower=piece['lower'],independently_supported_lower=supported,
                unconditional_claim=min(piece['lower'],piece['cutoff']),
                latest_support_sequence=max((p['sequence'] for p in available.values()),default=0),
                future_evidence_used=False,cutoff=piece['cutoff']))
    return audit

def complete_cover(d,U,j,controller,gmax):
    trace=rows(d/'external/global_bound_trace.csv');leaves=rows(d/'external/paper_leaf_ledger.csv')
    assert trace and leaves;timeline=[];previous=-math.inf;previous_U=math.inf
    for n,r in enumerate(trace,1):
        upper=float(r['verified_global_upper_bound']);active=evidence.number(r['active_leaf_valid_lower_bound'])
        other=evidence.number(r['other_open_leaf_min_valid_lower_bound'])
        raw=min([upper]+[v for v in [active,other] if v is not None]);reported=float(r['valid_global_lower_bound'])
        assert close(raw,reported) and math.isfinite(reported) and reported>=previous-decision.CLOSURE_TOL
        assert upper<=previous_U+decision.CLOSURE_TOL and reported<=upper+decision.CLOSURE_TOL
        previous=reported;previous_U=upper
        timeline.append(dict(row=n,**r,recomputed_complete_cover_bound=reported))
    live=[r for r in leaves if r['status'] not in ['replaced','coalesced']];assert live
    covered=0.;valid_sources={'objective_nonnegative_penalty_G_floor','optimal_complete_lp_relaxation',
        'valid_child_target_native_bound','valid_next_leaf_target_native_bound','native_terminal_mip_bound','inherited_parent_lp_bound',
        'optimal_complete_child_lp_relaxation','complete_disjunction_min_child_bound','native_partial_mip_bound',
        'gamma_lower_bound_floor','inherited_parent_valid_bound','inherited_requeued_parent_native_bound',
        'inherited_parent_partial_native_bound','minimum_original_sibling_valid_bound'}
    proof_rows=controller['controller_native'];lp_rows=controller['controller_LP_status'];proofs=scoped_proofs(j,controller,U)
    for leaf in sorted(live,key=lambda r:float(r['gamma_L'])):
        lo,hi=float(leaf['gamma_L']),float(leaf['gamma_U']);L=float(leaf['lower_bound'])
        assert 0<=lo<=hi and lo<=covered+decision.CLOSURE_TOL and math.isfinite(L) and L>=-decision.CLOSURE_TOL
        covered=max(covered,hi);assert leaf['status']!='invalid'
        sources=set(leaf['lower_bound_sources'].split(';'))-{''}
        assert sources and sources<=valid_sources,('unreviewed bound provenance',leaf)
        if int(leaf['lp_complete']):
            matches=[r for r in lp_rows if r['leaf_id']==leaf['leaf_id']]
            assert matches and any(int(r['terminal_valid']) for r in matches)
        if sources & {'native_terminal_mip_bound','valid_child_target_native_bound','valid_next_leaf_target_native_bound'}:
            assert any(r['leaf_id']==leaf['leaf_id'] and r['solve_kind']!='LP' and int(r['optimize_return_code'])==0 for r in proof_rows)
        if leaf['closure_source']=='native_terminal_mip_optimal':
            assert any(r['leaf_id']==leaf['leaf_id'] and r['solve_kind']=='MIP' and r['native_status']=='OPTIMAL' for r in proof_rows)
        supported_leaf_bound(leaf,proofs,U)
    assert covered+decision.CLOSURE_TOL>=min(U,gmax)
    # The trace retains qualified raw bounds. U is independently recomputed and
    # is deliberately NOT used to clip final L or a last-bit negative gap.
    final=trace[-1];raw_trace_L=float(final['valid_global_lower_bound'])
    raw_cutoff=float(final['verified_global_upper_bound'])
    relevant=[r for r in live if float(r['gamma_L'])<raw_cutoff-decision.CLOSURE_TOL]
    # Match the original scheduler's complete relevant-leaf aggregation. The
    # observational trace caps some values by its reported upper bound; that
    # capped trace is checked but cannot replace the raw qualified endpoint LB.
    L=min((float(r['lower_bound']) for r in relevant),default=0.)
    assert close(min(raw_cutoff,L),raw_trace_L)
    assert L<=U+decision.CLOSURE_TOL and close(U,float(final['verified_global_upper_bound']))
    # Each final leaf has already been proved by its complete scope partition.
    # A previously reconstructed global number or a same-leaf LP alone is not
    # a substitute for that proof (valid child LP disjunctions may be stronger).
    terminal={'closed','fathomed','empty'}
    # Every lower bound above was independently supported on its complete true-G
    # partition. The original scheduler also discharges a saved "open" leaf
    # once that qualified bound excludes improvement of the current physical U.
    def discharged(r):
        return r['status'] in terminal or float(r['gamma_L'])>=U-decision.CLOSURE_TOL or float(r['lower_bound'])>=U-decision.CLOSURE_TOL
    closed=all(discharged(r) for r in live)
    return dict(L=L,raw_trace_final_L=raw_trace_L,complete_coverage=True,all_relevant_closed=closed,live_leaves=len(live),
        open_leaves=sum(not discharged(r) for r in live),
        covered_gini_upper=covered,timeline=timeline,leaves=leaves,scoped_proofs=proofs)

def model_scope_contract(call,model,p):
    """Bind proof metadata to the actually saved original interval matrix."""
    if call['full_original']:return dict(full_original_reference_already_checked=True)
    lo,hi,cutoff=call['lower_g'],call['upper_g'],call['cutoff']
    assert model['bounds']['G']==(lo,hi), 'native scope differs from saved G domain'
    counter=collections.Counter(model['rows'])
    # The inherited writer encodes this domain in Bounds. Redundant explicit
    # G rows belong to other optional formulations and are not required here.
    assert counter[(model['objective'][0],'<=',cutoff-model['objective'][1])]>=1,'saved objective cutoff differs from call'
    for gamma,sense in [(hi,'<='),(lo,'>=')]:
        terms={f'h_{i}_{k}':1. for i in range(1,p['V']+1) for k in range(i+1,p['V']+1)}
        if gamma:
            for i in range(1,p['V']+1):terms[f'r_{i}']=-p['V']*gamma
        assert counter[(tuple(sorted(terms.items())),sense,0.)]>=1,'saved true-G cap/floor differs from call'
    return dict(saved_G_lower=lo,saved_G_upper=hi,saved_objective_cutoff=cutoff,
        true_G_cap_floor_checked=True,metadata_scope_is_actual_model_scope=True)

def endpoint(root,launch,ident,d,j,formal):
    p=launch['panel'];r=read(d/'result.json');c=read(d/'completion.json');a=read(d/'audit.json')
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap'] and a['passed']
    saved_launch=read(d/'launch.json')
    assert saved_launch['command']==launch['command'] and saved_launch['prereg_sha256']==ident['prereg_sha256']
    assert saved_launch['panel']==p and a['binary_sha256']==ident['candidate_binary_sha256']
    assert sha(root/p['input_path'])==p['input_sha256']
    expected={'P-GRB':'custom','ENS-C':'research-round83-vds-equal-net-exchange','M-B':'research-round99-ensc-discrete-structure-m-binary'}[launch['arm']]
    assert r['algorithm_preset']==expected
    phys=full_fleet(root,p,r);U=phys['F'];controller=evidence.controller_tables(d,r)
    gmax=(p['V']-1.)/p['V']
    for call in j['calls'].values():
        assert call['gmax']==gmax and 0<=call['lower_g']<=call['upper_g']<=gmax+decision.CLOSURE_TOL
    j['returned_native_proofs']=returned_native_proofs(root,j,controller)
    chronological=chronological_cover(j,controller,U)
    for b in j['bounds']:
        if b['global_available']:evidence.bound(j['calls'][b['call']],b['native_bound'],j['witnesses']+[phys])
    cover=None
    if launch['arm']=='P-GRB':
        assert j['started']==1 and j['returned']==1 and r['gurobi_optimize_count']==1
        assert all(q['full_original'] and q['native_preconditions'] for q in j['calls'].values())
        assert r['gurobi_hga_start_requested'] is False and r['gurobi_native_domain_audit_passed'] is True
        assert sha(d/'compact.lp')==p['reference']['canonical_sha256']
        assert sha(d.parent.parent/'reference'/p['id']/'original.lp')==p['reference']['canonical_sha256']
        for key,field in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:assert r[field]==p['reference'][key]
        good=[b['global_bound'] for b in j['bounds'] if b['global_available']]
        L=max([0.]+good)
        final_native=cold_returned_bound(root,d,j,r)
        j['returned_native_proofs'].append(final_native)
        L=max(L,final_native['L'])
        certificate=r['gurobi_status']==2 and U-L<=decision.CLOSURE_TOL
        proof='complete_original_cold_compact_native_OPTIMAL_and_physical_UB' if certificate else 'complete_original_cold_compact_qualified_native_bound_open'
    elif U<=decision.ZERO_TOL and not j['started']:
        a0=evidence.instance(root,p);assert p['lambda']>=0 and all(w>=0 for w in a0['w'][1:])
        L=0.;certificate=True;proof='independent_zero_physical_UB_and_global_nonnegative_objective_floor'
        cover=dict(L=L,complete_coverage=True,all_relevant_closed=True,live_leaves=0,open_leaves=0,covered_gini_upper=0.,timeline=[],leaves=[])
    else:
        cover=complete_cover(d,U,j,controller,gmax);L=cover['L']
        # Closure requires actual cover/provenance/returned calls and lifecycle;
        # a near-zero gap alone never supplies these obligations.
        assert j['started']==j['returned']
        required=['root_coverage_valid','parent_child_coverage_valid','all_leaf_bounds_valid','leaf_bounds_monotone',
            'global_bound_monotone','lifecycle_complete','feasibility_consistency_gate']
        assert all(r['external_gini_tree_'+key] is True for key in required)
        failure_reason=r['external_gini_tree_failure_reason']
        assert failure_reason=='none' or (failure_reason=='overall_global_deadline' and
            r['status'] in ['time_limit','round31_c6_external_gini_tree_time_limit']),failure_reason
        certificate=cover['all_relevant_closed'] and U-L<=decision.CLOSURE_TOL
        proof='qualified_complete_original_interval_cover_closed' if certificate else 'qualified_complete_original_interval_cover_open'
        if U-L<=decision.CLOSURE_TOL and not certificate:raise AssertionError('numerically closed bound with unresolved complete certificate obligations')
    assert close(U,r['upper_bound']) and close(L,r['lower_bound']) and L<=U+decision.CLOSURE_TOL
    assert certificate==r['strict_certified_original_problem'],('unresolved certificate flag disagreement',launch['id'],launch['arm'],certificate)
    t=read(d/'whole_arm_receipt.json')['complete_seconds'] if formal else c['fully_observed_end_to_end_seconds']
    if formal:
        timing=read(d/'whole_arm_receipt.json');assert timing['completion_SHA']==sha(d/'completion.json') and timing['audit_SHA']==sha(d/'audit.json')
        assert timing['includes_admission_identity_checks_startup_native_calls_callbacks_raw_writes_postexit_audit_crosscheck']
        assert t<=p['cap_seconds'],('complete arm exceeded preregistered cap',t,p['cap_seconds'])
    arm=dict(id=p['id'],arm=launch['arm'],U=U,L=L,gap=U-L,certificate=certificate,certificate_qualified=True,
        numbers_qualified=decision.finite(U) and decision.finite(L),certificate_basis=proof,complete_seconds=t,
        formal_performance=formal,status=r['status'],stop_reason=c['stop_reason'],PE_SHA=ident['candidate_binary_sha256'],DLL_SHA=ident['dll_sha256'],
        V=p['V'],M=p['M'],Q_vector=p['Q_vector'],T_seconds=p['T_seconds'],cap_seconds=p['cap_seconds'],
        input_SHA=p['input_sha256'],native_Optimize=j['started'],route_oracle=0,IIS=0,
        source_commit=ident['measured_source_commit'],tiny_negative_gap_within_original_tolerance=U-L<0,
        exact_native_first_witness_time_observed=False,raw_claimed_U=r['upper_bound'],raw_claimed_L=r['lower_bound'],
        raw_claimed_strict_certificate=r['strict_certified_original_problem'],raw_claimed_relative_gap=r.get('gap'),
        raw_tree_termination_reason=r.get('external_gini_tree_failure_reason'),
        legacy_metadata_native_best_bound_return_code=r.get('native_mip_best_bound_return_code'),
        legacy_metadata_serialized_bound_matches_native=r.get('strict_serialized_lower_bound_matches_native'),
        qualified_bounds_rebuilt_from_actual_native_journal_and_cover=True)
    arm['relative_gap'],arm['relative_gap_null_reason']=decision.relative(arm)
    return dict(arm=arm,physical=phys,cover=cover,controller=controller,result=r,completion=c,chronological_cover=chronological)

def rebuild(root,dest,qualification_only=False):
    root=Path(root).resolve();out=root/ROUND;dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    start_reader.ROOT=root
    candidate=read(out/'candidate_identity.json');formal_gate=read(out/'review/performance_admission.json') if not qualification_only else None
    if formal_gate:assert formal_gate['decision']=='ACCEPT' and formal_gate['candidate_identity_SHA']==sha(out/'candidate_identity.json')
    correction=read(out/'review/reader_correction_review01.json')
    assert correction['decision']=='ACCEPT' and correction['candidate_identity_SHA']==sha(out/'candidate_identity.json')
    assert correction['original_reader_SHA']==candidate['decision_reader_SHA']
    assert sha(out/'engineering/signed_gap_reader_correction01/round108_decisions.py')==correction['original_reader_SHA']
    assert sha(root/'scripts/round108_decisions.py')==correction['corrected_reader_SHA']
    campaigns=[('qualification/cli01',False)]+([] if qualification_only else [('bridge01',True),('confirmation01',True)])
    arms=[];qualified=[];records=collections.defaultdict(list);journals=[];unstarted=[];failures=[]
    for campaign,formal in campaigns:
        camp=out/campaign;ident=read(camp/'identity.json')
        # Qualification is before the final observational wrapper receipt; its
        # immutable original helper bindings are independently retained.
        if formal:require_identity(root,ident,candidate)
        else:
            assert ident['candidate_binary_sha256']==candidate['production_PE_SHA'] and ident['dll_sha256']==candidate['DLL_SHA']
            assert ident['source_hashes']==candidate['source_bindings']
        for launch in ident['launches']:
            d=portable(root,launch['destination']);label=dict(campaign=campaign,id=launch['id'],arm=launch['arm'],number=launch['number'])
            if not (d/'completion.json').exists():
                assert not d.exists(),'incomplete started arm needs explicit failure review'
                unstarted.append(dict(label,cap_seconds=launch['cap_seconds']));continue
            completion=read(d/'completion.json')
            if completion['stop_reason']!='normal_return' or completion['returncode']!=0 or not (d/'result.json').exists():
                failures.append(dict(label,completion=completion));continue
            observations=read(d/'observations.json')
            for observed in observations:
                payload=observed['payload']
                keys={'call':['full_original','native_preconditions'],'bound':['global_available','inconsistent'],'not_started':['actual_Optimize']}.get(payload['kind'],[])
                for key in keys:assert type(payload[key]) in [int,bool] and payload[key] in [0,1],('non-boolean native flag',key,payload)
                if payload['kind']=='witness_rejected':records['rejected_witnesses'].append(dict(label,payload=payload,available_seconds=observed['effective_available_seconds']))
            j=evidence.journal(root,launch['panel'],d)
            j['return_sequences']={r['payload']['call']:r['payload']['sequence'] for r in observations if r['payload']['kind']=='returned'}
            ep=endpoint(root,launch,ident,d,j,formal);p=launch['panel']
            journals.append((label,j,ep));arm=dict(campaign=campaign,**ep['arm']);(arms if formal else qualified).append(arm)
            # The original supervisor starts after the wrapper's identity checks.
            # Its total excluded pre/post work is an upper bound on the unknown
            # prelaunch offset. Add all of it for safe complete-window witness
            # bounds/checkpoints; do not pretend to know the exact offset.
            available_offset_upper=arm['complete_seconds']-ep['completion']['fully_observed_end_to_end_seconds']
            assert available_offset_upper>=0
            ep['availability_offset_upper']=available_offset_upper
            records['physical_fleets'].append(dict(label,**ep['physical']))
            records['physical_UBs'].append(dict(label,**ep['physical'],source='final_endpoint_own_complete_fleet',
                sequence=None,available=arm['complete_seconds'],discovery_seconds_lower=0.,
                discovery_seconds_upper=arm['complete_seconds'],native_first_find_exact=False))
            for w in j['witnesses']:
                # Also verify complete vehicle namespace for every own UB.
                payload=next(r['payload'] for r in observations if r['payload']['sequence']==w['sequence'])
                fleet=full_fleet(root,p,payload)
                records['physical_UBs'].append(dict(label,**w,routes=fleet['routes'],complete_fleet_vehicles=p['M'],
                    discovery_seconds_lower=0.,discovery_seconds_upper=w['available']+available_offset_upper,
                    original_supervisor_available_seconds=w['available'],unseparated_wrapper_offset_upper_seconds=available_offset_upper,
                    discovery_clock='complete arm entry; all excluded pre/post wrapper work conservatively added',native_first_find_exact=False))
            records['native_bounds'].extend(dict(label,**b) for b in j['bounds'])
            records['returned_native_bounds'].extend(dict(label,**b) for b in j['returned_native_proofs'])
            records['chronological_cover_provenance'].extend(dict(label,**r) for r in ep['chronological_cover'])
            for i,call in j['calls'].items():
                records['native_calls'].append(dict(label,call=i,actual_Optimize=i not in j['not_started_ids'],returned=i in j['returned_ids'],
                    model_SHA=call['model_sha256'],model_scope=call['model_scope'],full_original=call['full_original'],
                    native_bound_preconditions=call['native_preconditions'],native_log_path=portable(root,call['native_log_path']).relative_to(root).as_posix(),
                    settings=call['settings'],gini_lower=call['lower_g'],gini_upper=call['upper_g'],cutoff=call['cutoff']))
            if ep['cover']:
                for row in ep['cover']['timeline']:records['frontier'].append(dict(label,**row))
                for row in ep['cover']['leaves']:records['leaf_obligations'].append(dict(label,**row))
                for row in ep['cover'].get('scoped_proofs',[]):records['scoped_bound_proofs'].append(dict(label,**row))
            for name,data in ep['controller'].items():records[name].extend(dict(label,**r) for r in data)
            r=ep['result'];controller=ep['controller']
            model_paths=[d/'compact.lp'] if launch['arm']=='P-GRB' else sorted((d/'external/models').glob('*.lp'))
            bysha={sha(path):path for path in model_paths};typed_models={}
            for path in model_paths:
                rec,model=model_contract(root,p,path,launch['arm']);records['models'].append(dict(label,**rec));typed_models[rec['SHA']]=model
            for call_id,call in j['calls'].items():
                if call_id in j['not_started_ids']:continue
                checked=model_scope_contract(call,typed_models[call['model_sha256']],p)
                records['model_scope_bindings'].append(dict(label,call=call_id,model_SHA=call['model_sha256'],**checked))
            proof_rows=ep['controller']['controller_native']
            actual_LPs=[q for q in proof_rows if q['solve_kind']=='LP']
            assert len(actual_LPs)==len(controller['controller_LP_status'])
            LP_status_by_log={q['native_log']:s for q,s in zip(actual_LPs,controller['controller_LP_status'])}
            if launch['arm']=='P-GRB':
                proof_rows=[dict(model_sha256=sha(d/'compact.lp'),solve_kind='MIP',native_status='OPTIMAL' if r['gurobi_status']==2 else 'OPEN',native_log=str(d/'native.log'))]
                assert 'Loaded user MIP start' not in (d/'native.log').read_text(encoding='utf-8')
            for proof in proof_rows:
                model=typed_models[proof['model_sha256']];log=portable(root,proof['native_log']);text=log.read_text(encoding='utf-8')
                size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',text)
                assert size and (int(size[1]),int(size[2]))==(len(model['rows']),len(model['order']))
                counts=collections.Counter(model['types'].values());native_counts=None
                if proof['solve_kind']!='LP':
                    match=re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',text);assert match
                    native_counts=dict(C=int(match[1]),I=int(match[2])-int(match[3]),B=int(match[3]))
                    assert native_counts=={k:counts.get(k,0) for k in ['C','I','B']}
                    if proof['native_status']=='OPTIMAL':assert 'Optimal solution found' in text
                elif proof['native_status']=='OPTIMAL':
                    objective=re.findall(r'Optimal objective\s+([-+0-9.eE]+)',text);assert objective
                    status=LP_status_by_log[proof['native_log']]
                    if int(status['terminal_valid']):
                        assert int(status['optimal']) and close(float(objective[-1]),float(status['lower_bound']))
                elif proof['solve_kind']=='LP' and proof['native_status']=='INFEASIBLE':
                    assert 'Infeasible model' in text,'LP infeasibility requires linked actual native terminal evidence'
                records['native_type_readbacks'].append(dict(label,model_SHA=proof['model_sha256'],solve_kind=proof['solve_kind'],
                    log_path=log.relative_to(root).as_posix(),log_SHA=sha(log),rows=int(size[1]),columns=int(size[2]),
                    restored_native_types=native_counts,LP_type_evidence='original captured VType relaxation/restoration; no integer type line in native simplex log' if proof['solve_kind']=='LP' else None))
            submitted=[(path,read(path)) for path in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(path).get('submitted')]
            for digest in sorted({m['model_sha256'] for _,m in submitted}):
                assert digest in bysha
                recs=start_reader.audit_model(bysha[digest],[(path,m) for path,m in submitted if m['model_sha256']==digest], 'm-binary' if launch['arm']=='M-B' else 'off')
                records['starts'].extend(dict(label,**r) for r in recs)
            controller=ep['controller'];r=ep['result'];c=ep['completion']
            lp=sum(float(q['solver_runtime']) for q in controller['controller_native'] if q['solve_kind']=='LP')
            mip=r['gurobi_runtime'] if launch['arm']=='P-GRB' else sum(float(q['solver_runtime']) for q in controller['controller_native'] if q['solve_kind']!='LP')
            startup=r['process_elapsed_at_exact_phase_start_seconds'] if launch['arm']!='P-GRB' else 0.
            residual=c['process_wall_seconds']-startup-lp-mip;assert residual>=-1e-3
            wrapper_residual=arm['complete_seconds']-c['process_wall_seconds'];assert wrapper_residual>=0
            records['time_partitions'].append(dict(label,complete_seconds=arm['complete_seconds'],startup_seconds=startup,
                LP_native_inclusive_seconds=lp,MIP_native_callback_inclusive_seconds=mip,
                controller_model_mapping_raw_write_residual_seconds=residual,prelaunch_postexit_audit_crosscheck_seconds=wrapper_residual,
                AM_and_mapper_separate_timer='not measured; merged in residual',HGA_seconds_overlapping_startup=r.get('hga_wall_time_seconds'),
                nested_native_seconds_added=False,partition_sum=startup+lp+mip+residual+wrapper_residual))
            kinds=collections.Counter(q['solve_kind'] for q in controller['controller_native'])
            if launch['arm']=='P-GRB':kinds['MIP']=j['started']
            covers=ep['cover']['timeline'] if ep['cover'] else []
            open_counts=[int(q['open_relevant_leaf_count']) for q in covers]
            root_LPs=[q for q in controller['controller_LP_status'] if q['leaf_id']=='L0']
            records['mechanism_summary'].append(dict(label,initial_own_physical_U=j['witnesses'][0]['F'] if j['witnesses'] else None,
                actual_native_Optimize=j['started'],LP_calls=kinds['LP'],
                partial_target_MIP_calls=kinds['CHILD_BOUND_TARGET_MIP']+kinds['NEXT_LEAF_TARGET_MIP'],
                child_bound_target_MIP_calls=kinds['CHILD_BOUND_TARGET_MIP'],next_leaf_target_MIP_calls=kinds['NEXT_LEAF_TARGET_MIP'],
                terminal_MIP_calls=kinds['MIP'],other_solve_kinds={k:v for k,v in kinds.items() if k not in ['LP','CHILD_BOUND_TARGET_MIP','NEXT_LEAF_TARGET_MIP','MIP']},
                AM_action_counts=dict(collections.Counter(q['selected_action'] for q in controller['controller_AM'])),
                actual_tree_event_counts=dict(collections.Counter(q['event'] for q in controller['controller_events'])),
                maximum_open_relevant_leaves=max(open_counts,default=0),multiple_open_relevant_leaves_observed=any(n>1 for n in open_counts),
                final_live_leaves=ep['cover']['live_leaves'] if ep['cover'] else None,
                root_LP_lower_bounds=[q['lower_bound'] for q in root_LPs],reported_integer_witnesses=len(j['witnesses']),
                no_assignment_route_oracle=True,lookahead_LP_is_committed_split=False,
                quantity_type_and_A_B_causal_contributions_reidentified=False))
            if formal:
                for checkpoint in [300,600,900,1200,1800,3600,5400]:
                    if checkpoint>p['cap_seconds']:continue
                    available=[x for x in j['trace'] if x['available']+available_offset_upper<=checkpoint]
                    if checkpoint>arm['complete_seconds']:
                        records['checkpoints'].append(dict(label,seconds=checkpoint,observed=False,U=None,L=None,gap=None,
                            reason='process ended before checkpoint; no endpoint extrapolation'));continue
                    if not available:
                        records['checkpoints'].append(dict(label,seconds=checkpoint,observed=False,U=None,L=None,gap=None,reason='no qualified own journal evidence available'));continue
                    z=available[-1];records['checkpoints'].append(dict(label,seconds=checkpoint,observed=True,U=z['U'],L=z['L'],gap=z['U']-z['L'],
                        original_supervisor_available_seconds=z['available'],safe_complete_window_available_upper=z['available']+available_offset_upper,
                        reason='committed own physical/native complete-scope evidence; all excluded wrapper overhead added conservatively'))
    for role in dict.fromkeys(a['id'] for a in arms):
        group=[a for a in arms if a['id']==role]
        assert max(a['L'] for a in group)<=min(a['U'] for a in group)+decision.CLOSURE_TOL
        certified=[a for a in group if a['certificate']]
        if certified:
            optimum=certified[0]['U'];assert all(close(a['U'],optimum) for a in certified)
            for label,j,ep in journals:
                if label['id']!=role or label['campaign'].startswith('qualification'):continue
                hits=[w for w in j['witnesses'] if abs(w['F']-optimum)<=decision.CLOSURE_TOL]
                endpoint_hit=abs(ep['physical']['F']-optimum)<=decision.CLOSURE_TOL
                uppers=[w['available']+ep['availability_offset_upper'] for w in hits]+([ep['arm']['complete_seconds']] if endpoint_hit else [])
                records['optimal_witness_bounds'].append(dict(label,reliable_original_Fstar=optimum,
                    witnessed=bool(uppers),discovery_seconds_lower=0. if uppers else None,
                    discovery_seconds_upper=min(uppers) if uppers else None,
                    native_first_find_exact=False,reason='safe interval ending at first committed verified optimal-valued own witness or complete endpoint observation' if uppers else 'no recorded optimal-valued own fleet in window'))
    gate=None;selection=None
    if not qualification_only:
        bridge=[a for a in arms if a['campaign']=='bridge01']
        if len(bridge)==6:gate=decision.bridge(bridge);write(dest/'admission_decision.json',gate)
        data={(a['id'],a['arm']):a for a in arms}
        for role in ['F2','C2','S12','B24','L48','F5','N36']:
            for control in ['P-GRB','ENS-C']:
                if (role,'M-B') in data and (role,control) in data:records['pairs'].append(dict(id=role,**decision.pair(data[role,'M-B'],data[role,control])))
        eligibility={r:True for r in decision.UNSEEN}
        eligibility_record=read(out/'review/sealed_input_eligibility.json')
        assert eligibility_record['all_four_eligible_at_freeze'] is True
        assert eligibility_record['input_manifest_SHA']==sha(out/'input_manifest.json')
        cancelled=[]
        cancellation=read(out/'cancellation_decision.json') if (out/'cancellation_decision.json').exists() else None
        if cancellation:
            cancelled=cancellation['cancelled_arms'];assert gate is not None
            if not gate['bridge_pass']:assert len(cancelled)==15 and len(arms)==6
            else:assert decision.early_impossible(arms)['positive_selection_unreachable']
            expected={(q['id'],q['arm']) for q in cancelled};actual={(q['id'],q['arm']) for q in unstarted}
            assert expected==actual
            records['cancelled']=cancelled
        if gate and (cancellation or len(arms)==21):
            selection=decision.selection(arms,gate,eligibility,cancelled);write(dest/'selection_decision.json',selection)
            records.update(scopes.scope_tables(arms,records['pairs'],selection,gate))
        if gate:write(dest/'continuation_decision.json',decision.early_impossible(arms))
    fee_rows=evidence.fees(out);records['fees']=fee_rows
    assert sum(r['conservative_process_starts'] for r in fee_rows)<=48 and sum(r['outer_seconds'] for r in fee_rows)<=80000
    records['failures']=failures;records['unstarted']=unstarted
    records['worst_losses']=sorted((r for r in records['pairs'] if r['classification'] in ['LOSS','MIXED']),key=lambda r:(not r['severe_regression'],r['control'],r['id']))
    table(dest/'arms.csv',arms);table(dest/'qualification_arms.csv',qualified)
    for name,data in sorted(records.items()):table(dest/(name+'.csv'),data)
    summary=dict(formal_arms=len(arms),functional_qualification_arms=len(qualified),failed_formal_arms=len(failures),
        conservative_starts=sum(r['conservative_process_starts'] for r in fee_rows),outer_solver_fee_seconds=sum(r['outer_seconds'] for r in fee_rows),
        actual_Optimize=sum(j['started'] for _,j,_ in journals),Optimize_returned=sum(j['returned'] for _,j,_ in journals),route_oracle=0,IIS=0,
        PE_SHA=candidate['production_PE_SHA'],DLL_SHA=candidate['DLL_SHA'],reader_SHA=sha(Path(__file__)),
        original_frozen_decision_reader_SHA=candidate['decision_reader_SHA'],current_decision_reader_SHA=sha(root/'scripts/round108_decisions.py'),
        independent_reader_correction_review_SHA=sha(out/'review/reader_correction_review01.json'),
        evidence_and_math_reconstruction_only=True,independent_engine_performance_rerun=False,stage=selection['stage'] if selection else None,
        table_rows={k:len(v) for k,v in sorted(records.items())})
    write(dest/'summary.json',summary);return summary

def compare(expected,actual):
    expected=Path(expected);actual=Path(actual);fields=0
    assert {p.name for p in expected.glob('*.csv')}=={p.name for p in actual.glob('*.csv')}
    for path in sorted(expected.glob('*.csv')):
        x,y=rows(path),rows(actual/path.name);assert len(x)==len(y),path.name
        for i,(a,b) in enumerate(zip(x,y),1):
            assert a==b,(path.name,i,[(k,a.get(k),b.get(k)) for k in a if a[k]!=b.get(k)])
            fields+=len(a)
    names={p.name for p in expected.glob('*.json')};assert names=={p.name for p in actual.glob('*.json')}
    for name in sorted(names):assert read(expected/name)==read(actual/name),name
    return dict(passed=True,exact_csv_fields_compared=fields,exact_JSON_files_compared=sorted(names))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--qualification-only',action='store_true');parser.add_argument('--compare');a=parser.parse_args()
    print(json.dumps(rebuild(a.root,a.out,a.qualification_only),allow_nan=False))
    if a.compare:print(json.dumps(compare(a.compare,a.out),allow_nan=False))

"""Current-only manifest reconstruction using the qualified R114/R115 predicates.

No original-root fallback, native library, Optimize, new witness or new bound.
Cross-arm claims are reconciled separately for each exact input/physical role.
"""
import argparse,collections,copy,csv,json,math,time
from pathlib import Path
import round108_reader as core
import round114_audit as audit
import round114_ps as ps
import round111_decisions as decisions
from round114_claims import reconcile,qualify_endpoint
from round115_common import clock_evidence as inherited_clock
from compare_round112_startup import compare as compare_H
from read_round113 import native_log
csv.field_size_limit(64*1024*1024)
ROUND='results/unified_exact_round116'
PAIRS=[('ENS-C','P-GRB'),('M-B','P-GRB'),('P-S','P-GRB'),('ENS-C','P-S'),('M-B','P-S'),('M-B','ENS-C')]
read,write,sha,table,portable=core.read,core.write,core.sha,core.table,core.portable

def clock_evidence(d,l):
    v=inherited_clock(d,l);v['total_exceeds_cap']=v['T_total']>l['cap_seconds'];return v

def proof_class(a):
    if not a.get('formal_protocol_qualified'):return 'UNVERIFIABLE'
    if a.get('own_exact_zero'):return 'OWN_ZERO_CERTIFICATE'
    if a.get('source_reduced'):return 'SOURCE_REDUCED_OPEN'
    if a.get('certificate') and a['U']>0:return 'CLEAN_NONZERO_CERTIFICATE'
    if a.get('L',0)>0:return 'RELIABLE_POSITIVE_LB_OPEN'
    return 'INDEPENDENT_FLOOR_OPEN'

def pair(a,c):
    return decisions.pair(a,c)

def reconstruct_arm(root,l,i,recs):
    d=portable(root,l['destination']);p=l['panel'];label=dict(id=l['id'],arm=l['arm'],group_number=l['group_number'],number=l['number'],global_launch_number=l.get('global_launch_number'))
    required=['result.json','completion.json','audit.json','observations.json','producer_receipt.json','producer_seal.json',
        'production_checks.json','independent_evidence.json','native_claims.json','claim_rejections.json','verification_closeout.json','arm_total_receipt.json']
    if not all((d/n).is_file() for n in required):
        missing=[n for n in required if not (d/n).is_file()];launched=(d/'launch.json').is_file()
        a=dict(label,formal_protocol_qualified=False,certificate_qualified=False,numbers_qualified=False,
            U=None,L=None,gap=None,certificate=None,complete_seconds=None,T_produce=None,T_verify=None,T_total=None,
            cap_seconds=l['cap_seconds'],native_Optimize=None,actually_executed=launched,
            status='EXECUTION_OR_CLOSEOUT_BLOCKED' if launched else 'UNSTARTED',failure_reason='REQUIRED_EVIDENCE_MISSING' if launched else 'FIXED_ARM_NOT_STARTED',
            missing_files=missing,PE_SHA=i['candidate_binary_sha256'],DLL_SHA=i['dll_sha256'],input_SHA=p['input_sha256'],proof_evidence='UNVERIFIABLE')
        recs['execution_failures'].append(a);return dict(l=l,d=d,i=i,label=label,arm=a,complete=False)
    assert sha(root/p['input_path'])==p['input_sha256']
    clock=clock_evidence(d,l);ind=read(d/'independent_evidence.json');obs=read(d/'observations.json');r=read(d/'result.json');c=read(d/'completion.json')
    closeout=read(d/'verification_closeout.json');assert closeout['own_evidence_SHA']==sha(d/'independent_evidence.json') and closeout['no_new_solution_or_certificate_backfilled']
    assert read(d/'production_checks.json')['final_physical_verification']==ind['physical']
    assert ind['created_after_producer_seal'] and not ind['inside_own_whole']
    j=audit.journal(root,l,d,obs);chain=audit.return_chain(root,l,d,j,r,c)
    rebuilt=audit.independent(root,l,d,j,r,c,chain)
    for k in ['own_U','own_exact_zero','independent_floor0','physical','counts','result_SHA','observations_SHA','completion_SHA']:assert rebuilt[k]==ind[k],('independent evidence drift',l['id'],l['arm'],k)
    claims=audit.claims_for(l,j,chain,r);assert claims==read(d/'native_claims.json')
    local=reconcile(claims,ind['witnesses']);assert local==read(d/'claim_rejections.json')
    necessary=read(d/'audit.json');normal=None;ep={}
    if local['rejections']:
        assert necessary['passed'] is False and necessary['claim_rejection_recorded'] and necessary['independent_evidence_audit_passed']
        audit.rejected_mandatory(root,l,d,j,r,chain,copy.deepcopy(ind),local)
    else:
        assert necessary['passed'] and necessary['independent_evidence_audit_passed']
        oldj=ps.ps_journal(root,p,d) if l['arm']=='P-S' else core.evidence.journal(root,p,d)
        oldj['return_sequences']=j['return_sequences'];oldj['return_available']=j['return_available']
        ep=ps.paid_endpoint(root,l,i,d,oldj) if l['arm']=='P-S' else core.endpoint(root,l,i,d,oldj,False)
        normal=ep['arm']
        for k in ['U','L','gap']:assert abs(normal[k]-necessary['endpoint'][k])<=1e-7
        assert normal['certificate']==necessary['endpoint']['certificate']
    recs['fleets'].append(dict(label,**ind['physical']));recs['clock_qualification'].append(dict(label,**clock))
    recs['native_claims'].extend(dict(label,**q) for q in claims)
    recs['own_UB_flow'].extend(dict(label,**q) for q in ind['witnesses'])
    recs['native_counts'].append(dict(label,**ind['counts'],LP=sum(q['solve_kind']=='LP' for q in chain['ledger'])))
    recs['progress_publication'].append(dict(label,**read(d/'progress_publication_receipt.json')))
    for call in j['calls'].values():
        recs['native_calls'].append(dict(label,call=call['call'],model_SHA=call['model_sha256'],full_original=call['full_original'],
            lower_g=call['lower_g'],upper_g=call['upper_g'],cutoff=call['cutoff'],settings=call['settings'],
            journal_returned=call['call'] in j['returned_ids'],independently_verified_return=call['call'] in chain['actual'],
            explicit_not_started=call['call'] in j['not_started_ids'],
            **(native_log(root,call['native_log_path']) if call['call'] in chain['actual'] else dict(Optimize=False,not_started=True))))
    controller=core.evidence.controller_tables(d,r)
    for k,rows in controller.items():recs[k].extend(dict(label,**q) for q in rows)
    recs['split_exposure'].append(dict(label,actual_atomic_split_events=sum(q.get('event')=='atomic_split' for q in controller['controller_events']),hidden_cause='unknown'))
    for key in ['Start','cover','chronological_cover']:
        if ep.get(key) is not None:recs[{'Start':'compact_Starts','cover':'covers','chronological_cover':'chronological_covers'}[key]].append(dict(label,evidence=ep[key]))
    H=r['process_elapsed_at_exact_phase_start_seconds'] if l['arm']!='P-GRB' else 0.
    LP=sum(float(q['solver_runtime']) for q in chain['ledger'] if q['solve_kind']=='LP')
    MIP=r['gurobi_runtime'] if l['arm'] in ['P-GRB','P-S'] else sum(float(q['solver_runtime']) for q in chain['ledger'] if q['solve_kind']!='LP')
    recs['time_partitions'].append(dict(label,T_produce=clock['T_produce'],T_verify=clock['T_verify'],T_total=clock['T_total'],H_seconds=H,
        LP_inclusive_seconds=LP,MIP_inclusive_seconds=MIP,process_write_model_controller_residual_seconds=c['process_wall_seconds']-H-LP-MIP,
        admission_and_producer_closeout_seconds=clock['T_produce']-c['process_wall_seconds'],nested_seconds_added=False,causal_subtraction_allowed=False))
    return dict(l=l,d=d,i=i,label=label,clock=clock,ind=ind,j=j,chain=chain,claims=claims,normal=normal,ep=ep,r=r,controller=controller,complete=True)

def finalize_arm(root,item,final,recs):
    if not item['complete']:
        a=item['arm'];recs['numerical_reliability'].append(dict(item['label'],actual_calls='unknown',returned_calls='unknown',qualified_calls='unknown',rejected_calls='unknown',
            max_proven_contradiction=None,contradiction_status='unknown',native_proof_qualified=None,certificate_source='UNVERIFIABLE',usable_comparisons=[]));return a
    l,d,ind,j,r,clock=(item[k] for k in ['l','d','ind','j','r','clock']);damage=[q for q in final['damaged_calls'] if q['arm']==l['arm']]
    if damage and not read(d/'claim_rejections.json')['damaged_calls']:
        audit.rejected_mandatory(root,l,d,j,r,item['chain'],copy.deepcopy(ind),final)
    endpoint=qualify_endpoint(dict(ind,clock_valid=clock['within_cap'],necessary_closeout_complete=True),damage,item['normal'])
    a=dict(endpoint,**item['label'],T_produce=clock['T_produce'],T_verify=clock['T_verify'],T_total=clock['T_total'],complete_seconds=clock['T_produce'],
        cap_seconds=l['cap_seconds'],V=l['panel']['V'],M=l['panel']['M'],Q_vector=l['panel']['Q_vector'],T_seconds=l['panel']['T_seconds'],
        status=r['status'],actually_executed=True,native_Optimize=j['started'],input_SHA=l['panel']['input_sha256'],PE_SHA=item['i']['candidate_binary_sha256'],
        DLL_SHA=item['i']['dll_sha256'],own_exact_zero=ind['own_exact_zero'],raw_claimed_U=r['upper_bound'],raw_claimed_L=r['lower_bound'],
        raw_claimed_certificate=r['strict_certified_original_problem'],raw_audit_passed=read(d/'audit.json')['passed'],
        producer_receipt_SHA=sha(d/'producer_receipt.json'),original_receipts_unchanged=True)
    a['proof_evidence']=proof_class(a);a['certificate_source']=a['proof_evidence'] if a['certificate'] else a.get('endpoint_source',a.get('certificate_basis','ORIGINAL_NATIVE_BOUND'))
    a['relative_gap'],a['relative_gap_null_reason']=decisions.relative(a)
    bad={q['call'] for q in damage};rejections=[q for q in final['rejections'] if q['arm']==l['arm']]
    recs['numerical_reliability'].append(dict(item['label'],actual_calls=j['started'],returned_calls=j['returned'],
        independently_verified_returns=len(item['chain']['actual']),qualified_calls=len(set(item['chain']['actual'])-bad),rejected_calls=len(bad),
        explicit_not_started=j['not_started'],max_proven_contradiction=max((q['value']-q['counterexample']['F'] for q in rejections),default=None),
        contradiction_status='PROVEN_SAME_DOMAIN' if rejections else 'NONE_FOUND_IN_PERFORMED_CHECKS_NOT_A_GUARANTEE',
        counterexample_model_scope=[dict(call=q['call'],sequence=q['sequence'],model_SHA=q['model_SHA'],scope=q['scope'],counterexample=q['counterexample'],
            rejected_dependencies=q['dependencies']) for q in rejections],
        confirmed_dependent_positive_certificate_rejected=bool(rejections and r['strict_certified_original_problem'] and r['upper_bound']>0),
        other_dependent_closure='see original controller ledgers; internal unavailable causes unknown',
        native_proof_qualified=a.get('native_proof_qualified'),certificate_source=a['certificate_source'],proof_evidence=a['proof_evidence'],
        usable_comparisons=['own_U','safe_gap','own_certificate','T_produce','secondary_T_total'] if a['formal_protocol_qualified'] else [],
        native_search_pruning_repaired=False,zero_certificate_does_not_credit_damaged_native=True))
    recs['claim_revocations'].extend(dict(item['label'],**q) for q in rejections)
    recs['checkpoints'].append(dict(item['label'],seconds=a['T_produce'],U=a['U'],L=a['L'],gap=a['gap'],certificate=a['certificate'],reason='sealed complete endpoint'))
    offset=read(d/'native_end_receipt.json')['complete_seconds_until_native_end']-read(d/'completion.json')['fully_observed_end_to_end_seconds']
    for point in [300,600,900,1200,1800,3600]:
        if point>=a['T_produce']:continue
        hits=[q for q in j['witnesses'] if q['available']+max(0.,offset)<=point]
        if not hits:continue
        U=min(q['F'] for q in hits)
        bound=[q['global_bound'] for q in j['bounds'] if q['global_available'] and q['call'] not in bad and q['available']+max(0.,offset)<=point]
        L=0. if damage else max([0.]+bound)
        recs['checkpoints'].append(dict(item['label'],seconds=point,U=U,L=L,gap=U-L,certificate=False,source_reduced=bool(damage),reason='actually available own committed records'))
    target=a['U'] if a['certificate'] else None
    hits=[q for q in j['witnesses'] if target is not None and abs(q['F']-target)<=1e-7]
    first=min(hits,key=lambda q:q['available']) if hits else None
    recs['target_discovery'].append(dict(item['label'],certificate_source=a['certificate_source'],
        first_verified_target_record_sequence=first['sequence'] if first else None,
        target_record_available_upper_seconds=first['available']+max(0.,offset) if first else None,
        complete_producer_certificate_seconds=a['T_produce'] if a['certificate'] else None,native_first_discovery='unknown',
        own_zero=ind['own_exact_zero'],availability_is_record_upper_not_internal_discovery=True))
    item['arm']=a;return a

def phase_decision(arms,pairs,complete,reliability):
    if not complete:return dict(execution_stage='BLOCKED',priority='BLOCKED',full_panel_A_D_assessed=False)
    primary=[p for p in pairs if p['candidate']=='M-B' and p['control']=='P-GRB'];assert len(primary)==6
    if any(r['rejected_calls'] not in (0,'unknown') for r in reliability):key='A';name='PROOF_RELIABILITY_PRIORITY'
    elif any(p['severe_regression'] for p in primary) or sum(p['classification']=='LOSS' for p in primary)>=2:key='B';name='PRIMARY_BENCHMARK_GAP_IDENTIFIED'
    elif all(p['evaluable'] for p in primary) and sum(p['classification']=='WIN' for p in primary)>=3 and sum(p['classification']=='LOSS' for p in primary)<=1 and any(p['classification']=='WIN' and p['id'].startswith(('E50','E100')) for p in primary) and any(a['arm']=='M-B' and a['proof_evidence']=='CLEAN_NONZERO_CERTIFICATE' for a in arms):key='C';name='LIMITED_EXTERNAL_SUPPORT'
    else:key='D';name='EXTERNAL_EVIDENCE_LIMITED_OR_MIXED'
    return dict(execution_stage='COMPLETE',priority=key,decision=name,full_panel_A_D_assessed=True,default_changed=False,next_phase_automatically_executed=False,statistical_significance_claim=False)

def rebuild(root,dest,qualification_only=False,allow_pending=False):
    tick=time.perf_counter();root=Path(root).resolve();out=root/ROUND;dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    core.start_reader.ROOT=root;candidate=read(out/'candidate_identity.json');production=read(out/'production_identity.json');recs=collections.defaultdict(list)
    for n,h in production['source_bindings'].items():assert sha(root/n)==h
    for n,h in candidate['helpers'].items():assert sha(root/n)==h
    assert len(production['source_bindings'])==206
    campaigns=[('qualification/cli01',False)]
    fixed=read(out/'fixed_manifest.json')
    if not qualification_only:
        gate=read(out/'review/performance_admission.json');assert gate['decision']=='ACCEPT' and gate['candidate_identity_SHA']==sha(out/'candidate_identity.json')
        campaigns += [(g['campaign'],True) for g in fixed['groups']]
    arms=[];qual=[];same=[];reconciliations=[]
    for name,formal in campaigns:
        i=read(out/name/'identity.json');assert i['helpers']==candidate['helpers'] and i['source_hashes']==production['source_bindings']
        assert i['runner_sha256']==sha(root/'scripts/round116_campaign.py') and i['prereg_sha256']==sha(out/'protocol.json')
        assert i['candidate_binary_sha256']==production['production_PE_SHA'] and i['dll_sha256']==production['DLL_SHA']
        items=[reconstruct_arm(root,l,i,recs) for l in i['launches']]
        claims=[q for v in items if v['complete'] for q in v['claims']];witnesses=[q for v in items if v['complete'] for q in v['ind']['witnesses']]
        final=reconcile(claims,witnesses);assert final==reconcile(list(reversed(claims)),list(reversed(witnesses)))
        reconciliations.append(dict(id=i['launches'][0]['id'],formal=formal,**final,actual_reconciliation_unix=time.time(),
            sealed_receipts_unchanged=True,same_exact_input_and_physical_parameters_only=True))
        current=[finalize_arm(root,v,final,recs) for v in items];(arms if formal else qual).extend(current)
        by={v['l']['arm']:v for v in items if v['complete']}
        if all(m in by for m in ['P-S','ENS-C','M-B']):
            H=compare_H(root,i['launches'][0]['panel'],{m:by[m]['d'] for m in ['P-S','ENS-C','M-B']})
            recs['same_H_fleets'].extend(dict(id=i['launches'][0]['id'],arm=m,**v) for m,v in H['arms'].items())
            for h in H['comparisons']:
                exposed=by[h['candidate']]['j']['started']>0 and by['P-S']['j']['started']>0
                h.update(formal=formal,backend_exposed=exposed,attribution_eligible=h['qualified'] and exposed,
                    attribution_reason='MATCHED_H_BACKENDS_EXPOSED' if h['qualified'] and exposed else 'H_NOT_COMPLETED' if not h['full_H_complete'] else 'BACKEND_NOT_EXPOSED' if h['qualified'] else 'START_MISMATCH')
                same.append(h)
        else:
            same.extend(dict(id=i['launches'][0]['id'],candidate=m,control='P-S',formal=formal,qualified=False,attribution_eligible=False,attribution_reason='FIXED_ARM_MISSING') for m in ['ENS-C','M-B'])
    pairs=[];secondary=[];conclusions={};lookup={(a['id'],a['arm']):a for a in arms}
    if not qualification_only:
        for role in read(out/'input_manifest.json')['roles']:
            for X,C in PAIRS:
                a,c=lookup[role['id'],X],lookup[role['id'],C];v=pair(a,c)
                deltas=dict(dU=a['U']-c['U'],dL=a['L']-c['L'],dGap=a['gap']-c['gap']) if v['evaluable'] else dict(dU=None,dL=None,dGap=None)
                h=next((h for h in same if h['id']==role['id'] and h['candidate']==X),None) if C=='P-S' and X in ['ENS-C','M-B'] else None
                pairs.append(dict(v,id=role['id'],**deltas,main_clock='T_produce',candidate_proof_evidence=a['proof_evidence'],control_proof_evidence=c['proof_evidence'],
                    backend_attribution_eligible=h['attribution_eligible'] if h else None,backend_attribution_reason=h['attribution_reason'] if h else None))
                av=dict(a,complete_seconds=a['T_total']);cv=dict(c,complete_seconds=c['T_total']);secondary.append(dict(pair(av,cv),id=role['id'],main_clock='secondary_T_total'))
        assert len(arms)==24 and len(pairs)==36
        for X in ['ENS-C','M-B','P-S']:
            vector=[dict(id=r['id'],**next(v for v in pairs if v['id']==r['id'] and v['candidate']==X and v['control']=='P-GRB')) for r in read(out/'input_manifest.json')['roles']]
            conclusions[X+'/P-GRB']=dict(six_role_vector=vector,denominator=6,eligible=sum(v['evaluable'] for v in vector),severe_losses=[v['id'] for v in vector if v['severe_regression']])
        for X in ['ENS-C','M-B']:
            vector=[next(v for v in pairs if v['id']==r['id'] and v['candidate']==X and v['control']=='P-S') for r in read(out/'input_manifest.json')['roles']]
            eligible=all(v['evaluable'] and v['backend_attribution_eligible'] for v in vector)
            wins=any(v['classification']=='WIN' for v in vector);loss=any(v['classification'] in ['LOSS','MIXED'] for v in vector)
            status='INCOMPLETE_ATTRIBUTION' if not eligible else 'MIXED_INCREMENT_OBSERVED' if wins and loss else 'POSITIVE_ONLY_OBSERVED' if wins else 'NO_POSITIVE_INCREMENT_OBSERVED'
            conclusions[X+'/P-S']=dict(six_role_vector=vector,denominator=6,eligible=sum(v['evaluable'] and v['backend_attribution_eligible'] for v in vector),status=status)
    recs['same_H']=same
    fee_rows=[]
    for lp in sorted((out/'fees').glob('*/launch.json')):
        l=read(lp)
        if not (lp.parent/'receipt.json').exists():assert allow_pending and l['qualification'];continue
        r=read(lp.parent/'receipt.json');assert r['actual_exit_observed']
        fee_rows.append(dict(label=lp.parent.name,starts=l['conservative_process_starts'],seconds=r['outer_seconds_upper'],qualification=l['qualification'],exit_code=r['exit_code'],nested_seconds_added=False))
    assert sum(f['starts'] for f in fee_rows)<=56 and sum(f['seconds'] for f in fee_rows)<=65000
    assert sum(f['starts'] for f in fee_rows if f['qualification'])<=16 and sum(f['seconds'] for f in fee_rows if f['qualification'])<=1800
    complete=len(arms)==24 and all(a['formal_protocol_qualified'] and a['actually_executed'] for a in arms)
    summary=dict(execution_stage='QUALIFICATION_ONLY' if qualification_only else 'COMPLETE' if complete else 'BLOCKED',
        formal_positions=len(arms),actual_formal_children=sum(a['actually_executed'] for a in arms),qualified_formal_arms=sum(a['formal_protocol_qualified'] for a in arms),
        pair_positions=len(pairs),evaluable_pairs=sum(p['evaluable'] for p in pairs),qualified_qualification_CLI=sum(a['formal_protocol_qualified'] for a in qual),
        main_clock='T_produce',proof_evidence_counts=dict(collections.Counter(a['proof_evidence'] for a in arms)),
        budget_starts=sum(f['starts'] for f in fee_rows),budget_seconds=sum(f['seconds'] for f in fee_rows),
        actual_native_Optimize=sum(r['actual_Optimize'] for r in recs['native_counts']),source_snapshot_SHA=candidate['raw_source_SHA'],
        decision=phase_decision(arms,pairs,complete,recs['numerical_reliability']) if not qualification_only else None,
        independent_third_party_reproduction=False,old_comparisons_are_not_current_observations=True)
    write(dest/'cohort_reconciliation.json',reconciliations);write(dest/'backend_conclusions.json',conclusions)
    write(dest/'summary.json',summary);write(dest/'current_core.json',dict(arms=arms,qualification_arms=qual,pairs=pairs,secondary_pairs=secondary,same_H=same,summary=summary))
    for n,v in dict(recs,arms=arms,qualification_arms=qual,pairs=pairs,secondary_pairs=secondary,fees=fee_rows).items():
        if v:table(dest/(n+'.csv'),v)
    return dict(summary,reader_seconds=time.perf_counter()-tick)

def compare(expected,actual):
    expected=Path(expected);actual=Path(actual);names=[]
    for p in sorted(expected.iterdir()):
        if p.suffix not in ['.json','.csv']:continue
        q=actual/p.name;assert q.exists(),('missing reconstructed core',p.name)
        if p.name=='cohort_reconciliation.json':
            a=read(p);b=read(q)
            for rows in [a,b]:
                for row in rows:row.pop('actual_reconciliation_unix',None)
            assert a==b
        else:assert p.read_bytes()==q.read_bytes(),('core field/byte mismatch',p.name)
        names.append(p.name)
    return dict(all_current_core_equal=True,files=names,original_root_fallback=False,Optimize=0)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--qualification-only',action='store_true');parser.add_argument('--allow-pending',action='store_true');parser.add_argument('--compare')
    a=parser.parse_args();value=rebuild(a.root,a.out,a.qualification_only,a.allow_pending)
    if a.compare:value['core_comparison']=compare(a.compare,a.out)
    print(json.dumps(value),flush=True)

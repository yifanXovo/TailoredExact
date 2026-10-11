"""Offline Round112 raw reconstruction, explicit root only, no native loading."""
import argparse, collections, json, math, re
from pathlib import Path
import round108_reader as core
import round111_seed_audit as model_audit
import round111_decisions as decisions
from round112_audit import start_audit
from compare_round112_startup import compare as compare_H

ROUND='results/unified_exact_round112'
read,write,sha,table,portable=core.read,core.write,core.sha,core.table,core.portable

def identities(root,out,ident):
    production=read(out/'production_identity.json');candidate=read(out/'candidate_identity.json')
    assert ident['candidate_binary_sha256']==production['production_PE_SHA']==candidate['production_PE_SHA']
    assert ident['dll_sha256']==production['DLL_SHA']==candidate['DLL_SHA']
    assert ident['source_hashes']==production['source_bindings']==candidate['source_bindings']
    for name,h in production['source_bindings'].items():assert sha(root/name)==h,name
    for name,h in ident['helpers'].items():assert sha(root/name)==h,name
    assert ident['helpers']==candidate['helpers'] and ident['prereg_sha256']==sha(out/'protocol.json')
    assert ident['runner_sha256']==sha(root/'scripts/round112_campaign.py')

def clock(d,l,formal):
    w=read(d/'whole_arm_receipt.json');a=read(d/'postexit_audit_receipt.json')
    n=read(d/'native_end_receipt.json');c=read(d/'completion.json')
    t=w['complete_seconds']
    assert 0<n['complete_seconds_until_native_end']<=a['complete_seconds_until_audit_end']<=t<=l['cap_seconds']
    assert w['metrics_written_before_whole'] and (d/'audit_execution_metrics.json').is_file()
    assert w['includes_admission_identity_startup_native_outputs_necessary_postexit_audit_crosscheck_metrics']
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    return t

def paid_endpoint(root,l,i,d,j):
    p=l['panel'];r=read(d/'result.json');c=read(d/'completion.json');a=read(d/'audit.json')
    assert a['passed'] and r['algorithm_preset']=='research-round112-self-paid-ens-start-original-compact'
    assert read(d/'launch.json')['command']==l['command'] and '--round112-ens-start-compact' in l['command']
    own=core.full_fleet(root,p,read(d/'result.json.round112.startup.json'))
    final=core.full_fleet(root,p,r);U=min([own['F'],final['F']]+[w['F'] for w in j['witnesses']])
    assert final['F']<=own['F']+1e-7 and abs(final['F']-U)<=1e-7
    assert j['started']<=1 and j['started']==j['returned']==r['gurobi_optimize_count']
    assert all(v['full_original'] and v['native_preconditions'] for v in j['calls'].values())
    controller=core.evidence.controller_tables(d,r);start=None
    if j['started']:
        assert sha(d/'compact.lp')==p['reference']['canonical_sha256']
        assert r['gurobi_native_domain_audit_passed'] and r['gurobi_lifecycle_valid']
        for k,key in [('fingerprint','gurobi_model_fingerprint'),('columns','gurobi_num_vars'),('rows','gurobi_num_constrs')]:assert r[key]==p['reference'][k]
        start=start_audit(root,p,d)
        start['mapping_validation_submission_seconds']=read(d/'native.log.round112.start.json')['mapping_validation_submission_seconds']
        native=core.cold_returned_bound(root,d,j,r)
        L=max([0.,native['L']]+[b['global_bound'] for b in j['bounds'] if b['global_available']])
        cert=bool(r['gurobi_status']==2 and U-L<=1e-7)
    else:
        assert r['status'] in ['startup_zero','startup_deadline'];L=0.
        cert=r['status']=='startup_zero';assert not cert or U<=1e-7
    assert L<=U+1e-7 and abs(U-a['endpoint']['U'])<=1e-7 and abs(L-a['endpoint']['L'])<=1e-7
    assert cert==a['endpoint']['certificate']==r['strict_certified_original_problem']
    arm=dict(id=l['id'],arm=l['arm'],U=U,L=L,gap=U-L,certificate=cert,certificate_qualified=True,numbers_qualified=True,
        status=r['status'],native_Optimize=j['started'],PE_SHA=i['candidate_binary_sha256'],DLL_SHA=i['dll_sha256'],
        cap_seconds=l['cap_seconds'],own_startup_U=own['F'],native_adoption=read(d/'native.log.round112.native.json') if j['started'] else 'BACKEND_NOT_EXPOSED')
    return dict(arm=arm,physical=final,own_startup=own,Start=start,result=r,completion=c,controller=controller,cover=None)

def native_log(root,path):
    path=portable(root,path);text=path.read_text(encoding='utf-8');stats={}
    size=re.search(r'Optimize a model with (\d+) rows, (\d+) columns',text)
    if size:stats.update(rows=int(size[1]),columns=int(size[2]))
    ending=re.findall(r'Explored (\d+) nodes \((\d+) simplex iterations\) in ([-+0-9.eE]+) seconds \(([-+0-9.eE]+) work units\)',text)
    if ending:
        n,it,t,w=ending[-1];stats.update(nodes=int(n),iterations=int(it),solver_seconds=float(t),Work=float(w))
    roots=re.findall(r'Root relaxation: objective ([-+0-9.eE]+)',text)
    stats['root_relaxation_objectives']=[float(v) for v in roots]
    stats['cut_counts']=None
    cut_block=re.search(r'Cutting planes:\s*\n(.*?)(?:\n\s*\n|Explored)',text,re.S)
    if cut_block:
        stats['cut_counts']={}
        for name,n in re.findall(r'^\s*([^:\n]+):\s*(\d+)\s*$',cut_block[1],re.M):stats['cut_counts'][name.strip()]=int(n)
    stats['Start_native_log_evidence']=[s.strip() for s in text.splitlines() if 'MIP start' in s]
    stats.update(path=path.relative_to(root).as_posix(),SHA=sha(path),unrecorded_fields='unknown',hidden_branching_cause='unknown')
    return stats

def interrupted(root,l,d,recs):
    """Replay committed partial bytes without creating an endpoint or observer clock."""
    label=dict(campaign='campaign',id=l['id'],arm=l['arm'],number=l['number'])
    p=l['panel'];calls={};returned=set();not_started=set();witnesses=[];events=[]
    commits=sorted((d/'journal').glob('event_*.commit'),key=lambda v:int(v.stem.split('_')[-1]))
    for sequence,path in enumerate(commits,1):
        fields=path.read_text().split();raw=path.with_suffix('.json');e=read(raw)
        assert fields[0]=='NEJ1' and int(fields[1])==sequence==e['sequence']
        assert int(fields[3])==raw.stat().st_size and fields[4]==sha(raw)
        events.append(e);recs['partial_journal'].append(dict(label,payload=e,commit_SHA=sha(path),payload_SHA=sha(raw),data_close_native_seconds=float(fields[2]),formal_endpoint=False,observer_available_seconds=None))
        if e['kind']=='identity':assert e['input_sha256']==p['input_sha256']
        elif e['kind']=='call':
            assert e['call'] not in calls and sha(portable(root,e['model_path']))==e['model_sha256'];calls[e['call']]=e
        elif e['kind']=='returned':assert e['call'] in calls and e['return_code']==0;returned.add(e['call'])
        elif e['kind']=='not_started':assert not e['actual_Optimize'];not_started.add(e['call'])
        elif e['kind']=='witness':
            w=core.full_fleet(root,p,e);assert abs(w['F']-e['objective'])<=1e-7
            witnesses.append(w);recs['partial_fleets'].append(dict(label,**w,sequence=sequence,source=e['source'],formal_endpoint=False))
        elif e['kind'] not in ['bound','witness_rejected']:raise AssertionError(e)
    context=model_audit.ArmModels();models={}
    try:
        for call in calls.values():
            path=portable(root,call['model_path']);h=sha(path)
            if h not in models:
                contract,m=context.model_contract(root,p,path,l['arm']);models[h]=m
                recs['partial_model_contracts'].append(dict(label,**contract,formal_endpoint=False))
            if not call['full_original']:recs['partial_scope_contracts'].append(dict(label,**context.model_scope_contract(call,models[h],p),formal_endpoint=False))
            recs['partial_native_calls'].append(dict(label,call=call['call'],settings=call['settings'],returned=call['call'] in returned,full_original=call['full_original'],lower_g=call['lower_g'],upper_g=call['upper_g'],cutoff=call['cutoff'],formal_endpoint=False,**native_log(root,call['native_log_path'])))
    finally:context.clear()
    for e in events:
        if e['kind']=='bound':
            assert not e['inconsistent']
            lower=core.evidence.bound(calls[e['call']],e['native_bound'],witnesses) if e['global_available'] else None
            assert lower is None and e['global_bound'] is None or lower is not None and abs(lower-e['global_bound'])<1e-10
            recs['partial_bounds'].append(dict(label,**e,formal_endpoint=False,whole_clock_qualified=False))
    missing=[name for name in ['result.json','completion.json','observations.json','audit.json','native_end_receipt.json','postexit_audit_receipt.json','whole_arm_receipt.json'] if not (d/name).exists()]
    recs['execution_failures'].append(dict(label,reason='EXECUTION_STATUS_RENAME_PERMISSION_ERROR',missing_required=missing,committed_events=len(events),partial_own_U=min((w['F'] for w in witnesses),default=None),started_calls=len(calls)-len(not_started),returned_calls=len(returned),unreturned_calls=sorted(set(calls)-returned-not_started),formal_endpoint=False,qualified_final_L=None,whole_seconds=None))
    return len(calls)-len(not_started),len(returned)

def rebuild(root,dest,qualification_only=False):
    root=Path(root).resolve();out=root/ROUND;dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    core.start_reader.ROOT=root
    campaigns=[('qualification/cli02',False),('qualification/positive01',False),('qualification/zero01',False)]
    if not qualification_only:
        gate=read(out/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
        assert gate['candidate_identity_SHA']==sha(out/'candidate_identity.json')
        campaigns.append(('campaign',True))
    recs=collections.defaultdict(list);arms=[];qual=[];byrole=collections.defaultdict(dict);journals={};partial_started=partial_returned=0
    for name,formal in campaigns:
        camp=out/name;i=read(camp/'identity.json');identities(root,out,i)
        for l in i['launches']:
            d=portable(root,l['destination']);p=l['panel'];label=dict(campaign=name,id=l['id'],arm=l['arm'],number=l['number'])
            assert sha(root/p['input_path'])==p['input_sha256']
            if not (d/'completion.json').exists():
                launched=(d/'launch.json').is_file()
                status='INTERRUPTED_EXECUTION' if launched else 'UNSTARTED'
                if launched:
                    assert formal and l['number']==13 and l['id']=='G50-C1' and l['arm']=='M-B'
                    failure=read(out/'fees/main04/receipt.json');assert failure['exit_code']==1 and failure['actual_exit_observed']
                    assert 'WinError 5' in (out/'fees/main04/failure.txt').read_text(encoding='utf-8')
                    starts,returns=interrupted(root,l,d,recs);partial_started+=starts;partial_returned+=returns
                else:recs['unstarted'].append(label)
                if formal:
                    arms.append(dict(label,status=status,launched=launched,formal_performance=True,formal_protocol_qualified=False,certificate_qualified=False,numbers_qualified=False,U=None,L=None,gap=None,relative_gap=None,relative_gap_null_reason='NO_QUALIFIED_FORMAL_ENDPOINT',certificate=None,complete_seconds=None,native_Optimize=None,PE_SHA=i['candidate_binary_sha256'],DLL_SHA=i['dll_sha256'],input_SHA=p['input_sha256'],cap_seconds=l['cap_seconds'],seed=0,V=p['V'],M=p['M'],Q_vector=p['Q_vector'],T_seconds=p['T_seconds'],failure_reason='EXECUTION_STATUS_RENAME_PERMISSION_ERROR' if launched else 'FIXED_ARM_NOT_STARTED'))
                continue
            j=core.evidence.journal(root,p,d);t=clock(d,l,formal)
            observations=read(d/'observations.json')
            j['return_sequences']={v['payload']['call']:v['payload']['sequence'] for v in observations if v['payload']['kind']=='returned'}
            j['return_available']={v['payload']['call']:v['effective_available_seconds'] for v in observations if v['payload']['kind']=='returned'}
            ep=paid_endpoint(root,l,i,d,j) if l['arm']=='P-S' else core.endpoint(root,l,i,d,j,False)
            a=ep['arm'];a.update(label,launched=True,complete_seconds=t,formal_performance=formal,formal_protocol_qualified=True,
                seed=0,V=p['V'],M=p['M'],Q_vector=p['Q_vector'],T_seconds=p['T_seconds'],input_SHA=p['input_sha256'],cap_seconds=l['cap_seconds'])
            a['relative_gap'],a['relative_gap_null_reason']=decisions.relative(a)
            (arms if formal else qual).append(a)
            if formal:byrole[l['id']][l['arm']]=(l,d,ep,j)
            journals[(name,l['number'])]=(ep,j,t)
            recs['fleets'].append(dict(label,**ep['physical']))
            if ep.get('cover') is not None:recs['covers'].append(dict(label,**ep['cover']))
            if ep.get('chronological_cover') is not None:recs['chronological_covers'].append(dict(label,evidence=ep['chronological_cover']))
            recs['returned_native_proofs'].extend(dict(label,**v) for v in j.get('returned_native_proofs',[]))
            if ep.get('own_startup'):recs['startup_fleets'].append(dict(label,**ep['own_startup']))
            if ep.get('Start'):recs['compact_Starts'].append(dict(label,**ep['Start']))
            for w in j['witnesses']:
                payload=observations[w['sequence']-1]['payload'];full=core.full_fleet(root,p,payload)
                recs['own_UB_flow'].append(dict(label,**(w|full)))
            for b in j['bounds']:recs['native_bounds'].append(dict(label,**b))
            for z in j['trace']:recs['journal_trace'].append(dict(label,**z))
            context=model_audit.ArmModels();models={}
            try:
                for call in j['calls'].values():
                    path=portable(root,call['model_path']);h=sha(path)
                    if h not in models:
                        if l['arm'] in ['P-GRB','P-S']:
                            assert h==p['reference']['canonical_sha256'];m=core.lp_model(path);contract=dict(SHA=h,original_cold_numeric_model=True)
                        else:contract,m=context.model_contract(root,p,path,l['arm'])
                        models[h]=m;recs['model_contracts'].append(dict(label,**contract))
                    if not call['full_original']:recs['scope_contracts'].append(dict(label,**context.model_scope_contract(call,models[h],p)))
                    log=native_log(root,call['native_log_path']);recs['native_calls'].append(dict(label,call=call['call'],settings=call['settings'],full_original=call['full_original'],lower_g=call['lower_g'],upper_g=call['upper_g'],cutoff=call['cutoff'],**log))
            finally:context.clear()
            for k,v in ep['controller'].items():recs[k].extend(dict(label,**row) for row in v)
            submitted=[(path,read(path)) for path in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(path).get('submitted')]
            for h in sorted({m['model_sha256'] for _,m in submitted}):
                paths=[portable(root,c['model_path']) for c in j['calls'].values() if c['model_sha256']==h];assert paths
                values=core.start_reader.audit_model(paths[0],[(p,m) for p,m in submitted if m['model_sha256']==h],'m-binary' if l['arm']=='M-B' else 'off')
                recs['tailored_Starts'].extend(dict(label,**v) for v in values)
            r=ep['result'];c=ep['completion'];native=ep['controller']['controller_native']
            lp=sum(float(v['solver_runtime']) for v in native if v['solve_kind']=='LP')
            mip=r['gurobi_runtime'] if l['arm'] in ['P-GRB','P-S'] else sum(float(v['solver_runtime']) for v in native if v['solve_kind']!='LP')
            startup=r['process_elapsed_at_exact_phase_start_seconds'] if l['arm']!='P-GRB' else 0.
            residual=c['process_wall_seconds']-startup-lp-mip;assert residual>=-.01
            recs['time_partitions'].append(dict(label,whole_seconds=t,H_seconds=startup,LP_inclusive_seconds=lp,MIP_inclusive_seconds=mip,
                model_mapping_controller_write_residual_seconds=residual,admission_and_postexit_seconds=t-c['process_wall_seconds'],
                separately_measured_Start_seconds=(ep.get('Start') or {}).get('mapping_validation_submission_seconds'),nested_seconds_added=False))
            if formal:
                offset=t-c['fully_observed_end_to_end_seconds'];assert offset>=0
                for point in (300,600,900,1200,1800,3600):
                    if point>l['cap_seconds']:continue
                    hits=[v for v in j['trace'] if v['available']+offset<=point]
                    if point>=t:
                        value=dict(U=a['U'],L=a['L'],gap=a['gap']) if a['certificate'] else dict(U=None,L=None,gap=None)
                        recs['checkpoints'].append(dict(label,seconds=point,observed=a['certificate'],reason='own certificate continued' if a['certificate'] else 'normal early exit without certificate; no extrapolation',**value))
                    elif hits:
                        v=hits[-1];recs['checkpoints'].append(dict(label,seconds=point,observed=True,U=v['U'],L=v['L'],gap=v['U']-v['L'],reason='own committed evidence with all wrapper residual added',availability_upper=v['available']+offset))
                    else:recs['checkpoints'].append(dict(label,seconds=point,observed=False,U=None,L=None,gap=None,reason='no qualified evidence yet'))
    pair_rows=[];vectors={}
    if not qualification_only:
        protocol=read(out/'protocol.json');lookup={(a['id'],a['arm']):a for a in arms}
        for role,group in byrole.items():
            certified=[ep['arm']['U'] for _,_,ep,_ in group.values() if ep['arm']['certificate']]
            target=min(certified) if certified else None
            for method,(l,d,ep,j) in group.items():
                a=ep['arm'];offset=a['complete_seconds']-ep['completion']['fully_observed_end_to_end_seconds']
                hits=[w for w in j['witnesses'] if target is not None and w['F']<=target+1e-7]
                first=min(hits,key=lambda w:w['available']) if hits else None
                recs['target_discovery'].append(dict(id=role,arm=method,number=l['number'],reliable_positive_certified_target=target if target is not None and target>1e-7 else None,first_verified_own_record_available_upper_seconds=first['available']+offset if first and target>1e-7 else None,first_sequence=first['sequence'] if first else None,first_source=first['source'] if first else None,whole_certification_seconds=a['complete_seconds'] if a['certificate'] else None,unknown_native_true_first_discovery=True,external_target_not_imported_as_UB_or_Start=True,reason='OWN_COMMITTED_WITNESS' if first else 'NO_RELIABLE_TARGET' if target is None else 'OWN_TARGET_WITNESS_NOT_OBSERVED'))
                events=ep['controller']['controller_events']
                recs['split_exposure'].append(dict(id=role,arm=method,number=l['number'],actual_atomic_split_events=sum(v.get('event')=='atomic_split' for v in events),event_kinds=dict(collections.Counter(v.get('event','unknown') for v in events)),AM_single_factor_cause_identified=False))
        for p in protocol['roles']:
            role=p['id'];group=byrole[role]
            if all(m in group for m in ['P-S','ENS-C','M-B']):
                same=compare_H(root,p,{m:group[m][1] for m in ['P-S','ENS-C','M-B']})
                recs['same_H'].extend(same['comparisons'])
                for method,v in same['arms'].items():recs['same_H_fleets'].append(dict(id=role,arm=method,complete_H=v['complete'],seed_ids=v['seed_ids'],fleet=v['fleet'],physical=v['physical'],trace_files=sorted(v['semantic_traces']),semantic_traces=v['semantic_traces']))
            else:same=dict(comparisons=[])
            for candidate,control in protocol['pairs']:
                if (role,candidate) in lookup and (role,control) in lookup:
                    a,c=lookup[role,candidate],lookup[role,control];value=decisions.pair(a,c)
                    if not value['evaluable']:value['reason']='EXECUTION_STATUS_RENAME_PERMISSION_ERROR' if any(v.get('status')=='INTERRUPTED_EXECUTION' for v in [a,c]) else 'FIXED_ARM_NOT_STARTED' if any(v.get('status')=='UNSTARTED' for v in [a,c]) else value.get('comparison_failure','INSUFFICIENT_COMPARISON')
                    pair_rows.append(dict(value,id=role,candidate_U=a['U'],candidate_L=a['L'],candidate_gap=a['gap'],candidate_certificate=a['certificate'],candidate_complete_seconds=a['complete_seconds'],control_U=c['U'],control_L=c['L'],control_gap=c['gap'],control_certificate=c['certificate'],control_complete_seconds=c['complete_seconds']))
                else:pair_rows.append(dict(id=role,candidate=candidate,control=control,classification='UNEVALUABLE',evaluable=False,reason='FIXED_ARM_MISSING'))
            for X in ['ENS-C','M-B']:
                match=next((v for v in same['comparisons'] if v['candidate']==X),None)
                pair=next(v for v in pair_rows if v['id']==role and v['candidate']==X and v['control']=='P-S')
                available=all(lookup.get((role,m),{}).get('formal_protocol_qualified') is True for m in [X,'P-S'])
                exposed=available and all(lookup[(role,m)]['native_Optimize']>0 for m in [X,'P-S'])
                eligible=bool(match and match['qualified'] and exposed and pair['evaluable'])
                reasons=[]
                if not available:reasons.append(pair.get('reason','MISSING_OR_UNEVALUABLE'))
                elif not exposed:reasons.append('BACKEND_NOT_EXPOSED')
                if match and not match['qualified']:reasons.append(match['reason'])
                if not match or not pair['evaluable']:reasons.append('MISSING_OR_UNEVALUABLE')
                reason='QUALIFIED' if eligible else reasons[0]
                vectors.setdefault(X,[]).append(dict(id=role,classification=pair['classification'],eligible=eligible,reason=reason,reason_codes=reasons,severe_regression=pair.get('severe_regression')))
        assert len(pair_rows)==30
    fees=[]
    for path in sorted((out/'fees').glob('*/launch.json')):
        l=read(path);f=read(path.parent/'receipt.json');assert f['actual_exit_observed'] and f['necessary_trailer_complete']
        assert 0<f['outer_seconds_lower']<=f['outer_seconds_upper']
        fees.append(dict(label=path.parent.name,starts=l['conservative_process_starts'],qualification=l['qualification'],outer_seconds_upper=f['outer_seconds_upper'],actual_children=f['actual_native_children'],exit_code=f['exit_code'],no_failed_slot_refund=True,nested_seconds_added=False))
    assert sum(f['starts'] for f in fees)<=56 and sum(f['outer_seconds_upper'] for f in fees)<=48000
    assert sum(f['starts'] for f in fees if f['qualification'])<=20 and sum(f['outer_seconds_upper'] for f in fees if f['qualification'])<=1800
    conclusions={}
    for X,rows in vectors.items():
        counts=collections.Counter(v['classification'] for v in rows if v['eligible'])
        status='INCOMPLETE_ATTRIBUTION' if not all(v['eligible'] for v in rows) else 'POSITIVE_ONLY_OBSERVED' if counts['WIN']>=1 and counts['LOSS']==counts['MIXED']==0 else 'NO_POSITIVE_INCREMENT_OBSERVED' if counts['WIN']==counts['MIXED']==0 else 'MIXED_INCREMENT_OBSERVED'
        conclusions[X]=dict(status=status,denominator=5,eligible_count=sum(v['eligible'] for v in rows),counts=dict(counts),five_role_vector=rows)
    recs['pairs']=pair_rows;recs['fees']=fees
    table(dest/'arms.csv',arms);table(dest/'qualification_arms.csv',qual)
    for name,rows in sorted(recs.items()):table(dest/(name+'.csv'),rows)
    failed_qualification_started=0
    for d in sorted((out/'qualification/cli01/raw').glob('*')):
        if not d.is_dir():continue
        events=[read(p) for p in (d/'journal').glob('event_*.json')]
        calls={e['call'] for e in events if e['kind']=='call'};not_started={e['call'] for e in events if e['kind']=='not_started'}
        failed_qualification_started+=len(calls-not_started)
    assert failed_qualification_started==2
    qualified=sum(a['formal_protocol_qualified'] for a in arms)
    summary=dict(stage='QUALIFICATION_ONLY' if qualification_only else 'ATTRIBUTION_COMPLETE' if qualified==20 else 'BLOCKED',formal_arm_positions=len(arms),formal_arms=qualified,started_formal_arms=sum(a['launched'] for a in arms),qualified_formal_arms=qualified,interrupted_formal_arms=len(recs['execution_failures']),unstarted_formal_arms=sum(a.get('status')=='UNSTARTED' for a in arms),pair_positions=len(pair_rows),evaluable_pairs=sum(v['evaluable'] for v in pair_rows),unevaluable_pairs=sum(not v['evaluable'] for v in pair_rows),qualified_qualification_arms=len(qual),backend_conclusions=conclusions,
        conservative_starts=sum(f['starts'] for f in fees),outer_fee_seconds_upper=sum(f['outer_seconds_upper'] for f in fees),native_Optimize_completed_arm_journals=sum(j['started'] for _,j,_ in journals.values()),formal_native_Optimize_qualified_arms=sum(j['started'] for key,(_,j,_) in journals.items() if key[0]=='campaign'),native_Optimize_interrupted_arm=partial_started,returned_Optimize_interrupted_arm=partial_returned,failed_qualification_native_Optimize=failed_qualification_started,all_actual_started_Optimize=sum(j['started'] for _,j,_ in journals.values())+partial_started+failed_qualification_started,reader_SHA=sha(__file__),pure_offline=True,native_rerun=False,default_ENS_changed=False,primary_benchmark='cold P-GRB')
    write(dest/'summary.json',summary);write(dest/'backend_conclusions.json',conclusions)
    return summary

def compare(expected,actual):
    return core.compare(expected,actual)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);p.add_argument('--qualification-only',action='store_true');p.add_argument('--compare')
    a=p.parse_args();print(json.dumps(rebuild(a.root,a.out,a.qualification_only),allow_nan=False))
    if a.compare:print(json.dumps(compare(a.compare,a.out),allow_nan=False))

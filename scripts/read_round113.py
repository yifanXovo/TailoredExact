"""Offline R113 geo8 plus the fixed qualified R112 twelve, explicit root only."""
import argparse, collections, csv, json, math, os, re
from pathlib import Path
import round108_reader as core
import round111_seed_audit as model_audit
import round111_decisions as decisions
from round113_audit import ps_journal, paid_endpoint
from compare_round112_startup import compare as compare_H

ROUND='results/unified_exact_round113'
LAYER='R112_COMPLETE12_PLUS_R113_GEO8'
csv.field_size_limit(64*1024*1024)
read,write,sha,table,portable=core.read,core.write,core.sha,core.table,core.portable

def identities(root,out,ident):
    production=read(out/'production_identity.json');candidate=read(out/'candidate_identity.json')
    assert ident['candidate_binary_sha256']==production['production_PE_SHA']==candidate['production_PE_SHA']
    assert ident['dll_sha256']==production['DLL_SHA']==candidate['DLL_SHA']
    assert ident['source_hashes']==production['source_bindings']==candidate['source_bindings']
    for name,h in production['source_bindings'].items():assert sha(root/name)==h,name
    for name,h in ident['helpers'].items():assert sha(root/name)==h,name
    assert ident['helpers']==candidate['helpers'] and ident['prereg_sha256']==sha(out/'protocol.json')
    assert ident['runner_sha256']==sha(root/'scripts/round113_campaign.py')

def clock(d,l,formal):
    w=read(d/'whole_arm_receipt.json');a=read(d/'postexit_audit_receipt.json')
    n=read(d/'native_end_receipt.json');c=read(d/'completion.json')
    t=w['complete_seconds']
    assert 0<n['complete_seconds_until_native_end']<=a['complete_seconds_until_audit_end']<=t<=l['cap_seconds']
    assert w['metrics_written_before_whole'] and (d/'audit_execution_metrics.json').is_file()
    assert w['progress_publication_receipt_written_before_whole']
    assert w['progress_receipt_SHA']==sha(d/'progress_publication_receipt.json')
    assert w['includes_admission_identity_startup_native_outputs_necessary_postexit_audit_crosscheck_metrics']
    assert c['returncode']==0 and c['stop_reason']=='normal_return' and c['within_cap']
    return t

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

def rebuild(root,dest,qualification_only=False,allow_current_qualification_fee_pending=False):
    root=Path(root).resolve();out=root/ROUND;dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    core.start_reader.ROOT=root
    campaigns=[('qualification/cli01',False)]
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
            required=['result.json','completion.json','observations.json','audit.json','whole_arm_receipt.json','progress_publication_receipt.json']
            if not all((d/v).is_file() for v in required):
                launched=(d/'launch.json').is_file()
                status='INTERRUPTED_EXECUTION' if launched else 'UNSTARTED'
                count=None;reason='FIXED_ARM_NOT_STARTED'
                if launched:
                    events=[read(q) for q in sorted((d/'journal').glob('event_*.json'))]
                    reason='AUTHORITATIVE_EXECUTION_OR_CLOCK_INCOMPLETE'
                    completion=read(d/'completion.json') if (d/'completion.json').exists() else None
                    if completion and completion['returncode']==0 and completion['stop_reason']=='normal_return':
                        status='POSTEXIT_VALIDATION_BLOCKED';reason='POSTEXIT_CONSISTENCY_FAILURE_WITHOUT_WHOLE_RECEIPT'
                        # Verify returned native activity without promoting this arm's rejected endpoint.
                        joint=core.evidence.journal(root,p,d)
                        result=read(d/'result.json')
                        assert result['gurobi_optimize_count']==joint['started']==joint['returned']
                        assert l['arm']=='P-GRB' and joint['started']==1 and joint['not_started']==0
                        phases=core.evidence.rows(d/'phases.csv')
                        assert sum(v['event']=='plain_gurobi_optimize_launch' and v['status']=='start' for v in phases)==1
                        assert sum(v['event']=='process_exit' and v['status']=='complete' and v['detail']=='rc=0' for v in phases)==1
                        for call in joint['calls'].values():
                            assert call['full_original'] and call['model_sha256']==p['reference']['canonical_sha256']
                            assert sha(portable(root,call['model_path']))==call['model_sha256']
                            log=native_log(root,call['native_log_path']);assert log.get('solver_seconds',0)>0
                            recs['unqualified_native_calls'].append(dict(label,call=call['call'],actual_Optimize=True,returned=True,
                                formal_endpoint=False,settings=call['settings'],full_original=True,**log))
                        count=joint['started'];partial_started+=count;partial_returned+=joint['returned']
                    recs['execution_failures'].append(dict(label,status=status,reason=reason,child_completion=completion,missing_required=[v for v in required if not (d/v).is_file()],
                        formal_endpoint=False,whole_seconds=None,declared_calls=sum(e['kind']=='call' for e in events),
                        returned=sum(e['kind']=='returned' for e in events),actual_Optimize=count if count is not None else 'unknown_without_joint_phase_log_qualification'))
                else:
                    if (out/'fees/main01/failure.txt').exists():reason='CURRENT_AUTHORITY_BARRIER_FIXED_STOP'
                    recs['unstarted'].append(dict(label,reason=reason))
                if formal:
                    arms.append(dict(label,status=status,launched=launched,formal_performance=True,formal_protocol_qualified=False,certificate_qualified=False,numbers_qualified=False,U=None,L=None,gap=None,relative_gap=None,relative_gap_null_reason='NO_QUALIFIED_FORMAL_ENDPOINT',certificate=None,complete_seconds=None,native_Optimize=count,PE_SHA=i['candidate_binary_sha256'],DLL_SHA=i['dll_sha256'],input_SHA=p['input_sha256'],cap_seconds=l['cap_seconds'],seed=0,V=p['V'],M=p['M'],Q_vector=p['Q_vector'],T_seconds=p['T_seconds'],failure_reason=reason,origin_round=113,evidence_layer=LAYER))
                continue
            j=ps_journal(root,p,d) if l['arm']=='P-S' else core.evidence.journal(root,p,d)
            t=clock(d,l,formal)
            observations=read(d/'observations.json')
            j['return_sequences']={v['payload']['call']:v['payload']['sequence'] for v in observations if v['payload']['kind']=='returned'}
            j['return_available']={v['payload']['call']:v['effective_available_seconds'] for v in observations if v['payload']['kind']=='returned'}
            ep=paid_endpoint(root,l,i,d,j) if l['arm']=='P-S' else core.endpoint(root,l,i,d,j,False)
            necessary=read(d/'audit.json');assert necessary['passed']
            for key in ['U','L','gap']:assert abs(ep['arm'][key]-necessary['endpoint'][key])<=1e-7
            assert ep['arm']['certificate']==necessary['endpoint']['certificate']
            ep['arm']['necessary_audit_to_reader_difference']={key:ep['arm'][key]-necessary['endpoint'][key] for key in ['U','L','gap']}
            a=ep['arm'];a.update(label,launched=True,complete_seconds=t,formal_performance=formal,formal_protocol_qualified=True,
                seed=0,V=p['V'],M=p['M'],Q_vector=p['Q_vector'],T_seconds=p['T_seconds'],input_SHA=p['input_sha256'],cap_seconds=l['cap_seconds'],
                origin_round=113,evidence_layer=LAYER,performance_helper_identity=sha(out/'candidate_identity.json'),original_clock_path=portable(root,l['destination']).relative_to(root).as_posix()+'/whole_arm_receipt.json')
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
            if ep.get('lifecycle'):recs['P-S_lifecycle'].append(dict(label,**ep['lifecycle']))
            recs['progress_publication'].append(dict(label,**read(d/'progress_publication_receipt.json')))
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
                    log=native_log(root,call['native_log_path']);recs['native_calls'].append(dict(label,call=call['call'],actual_Optimize=call['call'] not in j['not_started_ids'],
                        returned=call['call'] in j['returned_ids'],explicit_not_started=call['call'] in j['not_started_ids'],settings=call['settings'],full_original=call['full_original'],lower_g=call['lower_g'],upper_g=call['upper_g'],cutoff=call['cutoff'],**log))
            finally:context.clear()
            for k,v in ep['controller'].items():recs[k].extend(dict(label,**row) for row in v)
            submitted=[(path,read(path)) for path in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(path).get('submitted')]
            for h in sorted({m['model_sha256'] for _,m in submitted}):
                paths=[portable(root,c['model_path']) for c in j['calls'].values() if c['model_sha256']==h];assert paths
                values=core.start_reader.audit_model(paths[0],[(p,m) for p,m in submitted if m['model_sha256']==h],'m-binary' if l['arm']=='M-B' else 'off')
                recs['tailored_Starts'].extend(dict(label,**v) for v in values)
            r=ep['result'];c=ep['completion'];native=ep['controller']['controller_native']
            kinds=collections.Counter(v['solve_kind'] for v in native)
            if l['arm'] in ['P-GRB','P-S']:kinds['MIP']=j['started']
            recs['native_counts'].append(dict(label,declared_calls=len(j['calls']),actual_Optimize=j['started'],returned=j['returned'],
                explicit_not_started=j['not_started'],LP=kinds['LP'],MIP=sum(v for k,v in kinds.items() if k!='LP'),solve_kinds=dict(kinds)))
            lp=sum(float(v['solver_runtime']) for v in native if v['solve_kind']=='LP')
            mip=r['gurobi_runtime'] if l['arm'] in ['P-GRB','P-S'] else sum(float(v['solver_runtime']) for v in native if v['solve_kind']!='LP')
            startup=r['process_elapsed_at_exact_phase_start_seconds'] if l['arm']!='P-GRB' else 0.
            residual=c['process_wall_seconds']-startup-lp-mip;assert residual>=-.01
            recs['time_partitions'].append(dict(label,whole_seconds=t,H_seconds=startup,LP_inclusive_seconds=lp,MIP_inclusive_seconds=mip,
                model_mapping_controller_write_residual_seconds=residual,admission_and_postexit_seconds=t-c['process_wall_seconds'],
                separately_measured_Start_seconds=(ep.get('Start') or {}).get('mapping_validation_submission_seconds'),nested_seconds_added=False))
            if formal:
                offset=t-c['fully_observed_end_to_end_seconds'];assert offset>=0
                recs['checkpoints'].append(dict(label,seconds=t,observed=True,reason='true complete endpoint',U=a['U'],L=a['L'],gap=a['gap'],certificate=a['certificate']))
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
                zero_hits=[w for w in j['witnesses'] if w['F']<=1e-7]
                zero_first=min(zero_hits,key=lambda w:w['available']) if zero_hits else None
                recs['target_discovery'].append(dict(id=role,arm=method,number=l['number'],reliable_positive_certified_target=target if target is not None and target>1e-7 else None,
                    first_verified_own_record_available_upper_seconds=first['available']+offset if first else None,
                    first_verified_own_zero_available_upper_seconds=zero_first['available']+offset if zero_first else None,
                    own_zero_inventory_exact=all(ep['physical']['Y'][i]==core.evidence.instance(root,l['panel'])['D'][i] for i in range(1,l['panel']['V']+1)),
                    first_sequence=first['sequence'] if first else None,first_source=first['source'] if first else None,
                    whole_certification_seconds=a['complete_seconds'] if a['certificate'] else None,unknown_native_true_first_discovery=True,
                    external_target_not_imported_as_UB_or_Start=True,reason='OWN_COMMITTED_WITNESS' if first else 'NO_RELIABLE_TARGET' if target is None else 'OWN_TARGET_WITNESS_NOT_OBSERVED'))
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
                    if not value['evaluable']:value['reason']=next((v['failure_reason'] for v in [a,c] if v.get('failure_reason')),value.get('comparison_failure','INSUFFICIENT_COMPARISON'))
                    delta=dict(dU=a['U']-c['U'],dL=a['L']-c['L'],dGap=a['gap']-c['gap']) if value['evaluable'] else dict(dU=None,dL=None,dGap=None)
                    pair_rows.append(dict(value,id=role,candidate_U=a['U'],candidate_L=a['L'],candidate_gap=a['gap'],candidate_certificate=a['certificate'],candidate_complete_seconds=a['complete_seconds'],control_U=c['U'],control_L=c['L'],control_gap=c['gap'],control_certificate=c['certificate'],control_complete_seconds=c['complete_seconds'],origin_round=113,evidence_layer=LAYER,**delta))
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
                vectors.setdefault(X,[]).append(dict(id=role,classification=pair['classification'],eligible=eligible,reason=reason,reason_codes=reasons,severe_regression=pair.get('severe_regression'),origin_round=113,performance_helper_identity=sha(out/'candidate_identity.json')))
        assert len(pair_rows)==12
        old=out/'inherited_r112';manifest=read(old/'dependency_manifest.json')
        for name,h in manifest['files'].items():assert sha(old/name)==h
        old_arms=core.evidence.rows(old/'reports_final/arms.csv')
        clocks=read(old/'clock_manifest.json')
        assert sha(old/'clock_manifest.json')==read(out/'candidate_identity.json')['inherited_clock_manifest_SHA']
        for name,h in clocks['files'].items():assert sha(old/name)==h
        clock_by_number={v['number']:v for v in clocks['arms']}
        assert len(clock_by_number)==12 and clocks['original_clock_adjusted'] is False
        inherited_arms=[]
        for row in old_arms:
            if row['formal_protocol_qualified']!='True':continue
            row=dict(row)
            for key in ['U','L','gap','complete_seconds','cap_seconds']:row[key]=float(row[key])
            for key in ['certificate','certificate_qualified','numbers_qualified','formal_protocol_qualified']:row[key]=row[key]=='True'
            retained=clock_by_number[int(row['number'])]
            receipt=read(old/retained['path']);audit=read(old/retained['audit_path']);completion=read(old/retained['completion_path'])
            assert (row['id'],row['arm'])==(retained['id'],retained['arm'])
            assert receipt['complete_seconds']==row['complete_seconds']==retained['original_complete_seconds']
            assert audit['passed'] and completion['returncode']==0 and row['complete_seconds']<=row['cap_seconds']
            assert row['PE_SHA']==retained['PE_SHA'] and row['DLL_SHA']==retained['DLL_SHA'] and row['input_SHA']==retained['input_SHA']
            for key in ['U','L','gap']:assert abs(audit['endpoint'][key]-row[key])<=1e-7
            assert audit['endpoint']['certificate']==row['certificate']
            row.update(origin_round=112,evidence_layer=LAYER,performance_helper_identity=sha(old/'candidate_identity.json'),
                original_clock_path='results/unified_exact_round113/inherited_r112/'+retained['path'],
                original_result_path='results/unified_exact_round113/inherited_r112/'+retained['result_path'],
                old_raw_reaudited=False)
            inherited_arms.append(row)
        assert len(inherited_arms)==12
        table(dest/'new_arms.csv',arms);table(dest/'new_pairs.csv',pair_rows)
        table(dest/'inherited_arms.csv',inherited_arms)
        old_pairs=core.evidence.rows(old/'reports_final/pairs.csv');inherited_pairs=[]
        for row in old_pairs:
            if row['evaluable']!='True':continue
            row=dict(row,evaluable=True,origin_round=112,evidence_layer=LAYER,performance_helper_identity=sha(old/'candidate_identity.json'),
                original_pair_source='inherited_r112/reports_final/pairs.csv')
            inherited_pairs.append(row)
        assert len(inherited_pairs)==18
        table(dest/'inherited_pairs.csv',inherited_pairs)
        arms=inherited_arms+arms;pair_rows=inherited_pairs+pair_rows
        assert len(arms)==20 and len(pair_rows)==30
        previous=read(old/'reports_final/backend_conclusions.json')
        for X in ['ENS-C','M-B']:
            retained=[dict(v,origin_round=112,performance_helper_identity=sha(old/'candidate_identity.json')) for v in previous[X]['five_role_vector'][:3]]
            assert [v['classification'] for v in retained]==['WIN','WIN','LOSS'] and all(v['eligible'] for v in retained)
            vectors[X]=retained+vectors[X]
    fees=[]
    for path in sorted((out/'fees').glob('*/launch.json')):
        l=read(path)
        if not (path.parent/'receipt.json').exists():
            assert qualification_only and allow_current_qualification_fee_pending and l['qualification'] and l['wrapper_pid']==os.getpid()
            recs['fees_pending'].append(dict(label=path.parent.name,declared_starts=l['conservative_process_starts'],
                current_reader_driver_still_active=True,final_outer_seconds=None,not_a_final_charge=True))
            continue
        f=read(path.parent/'receipt.json');assert f['actual_exit_observed'] and f['necessary_trailer_complete']
        assert 0<f['outer_seconds_lower']<=f['outer_seconds_upper']
        fees.append(dict(label=path.parent.name,starts=l['conservative_process_starts'],qualification=l['qualification'],outer_seconds_upper=f['outer_seconds_upper'],actual_children=f['actual_native_children'],exit_code=f['exit_code'],no_failed_slot_refund=True,nested_seconds_added=False))
    assert sum(f['starts'] for f in fees)<=28 and sum(f['outer_seconds_upper'] for f in fees)<=26000
    assert sum(f['starts'] for f in fees if f['qualification'])<=12 and sum(f['outer_seconds_upper'] for f in fees if f['qualification'])<=1200
    conclusions={}
    for X,rows in vectors.items():
        counts=collections.Counter(v['classification'] for v in rows if v['eligible'])
        status='INCOMPLETE_ATTRIBUTION' if not all(v['eligible'] for v in rows) else 'POSITIVE_ONLY_OBSERVED' if counts['WIN']>=1 and counts['LOSS']==counts['MIXED']==0 else 'NO_POSITIVE_INCREMENT_OBSERVED' if counts['WIN']==counts['MIXED']==0 else 'MIXED_INCREMENT_OBSERVED'
        conclusions[X]=dict(status=status,denominator=5,eligible_count=sum(v['eligible'] for v in rows),counts=dict(counts),five_role_vector=rows)
    recs['pairs']=pair_rows;recs['fees']=fees
    table(dest/'arms.csv',arms);table(dest/'qualification_arms.csv',qual)
    for name,rows in sorted(recs.items()):table(dest/(name+'.csv'),rows)
    qualified=sum(a['formal_protocol_qualified'] is True for a in arms if a.get('origin_round')==113)
    summary=dict(stage='QUALIFICATION_ONLY' if qualification_only else 'GEOGRAPHIC_ATTRIBUTION_COMPLETE' if qualified==8 else 'BLOCKED',
        evidence_layer=LAYER,new_formal_arm_positions=0 if qualification_only else 8,new_qualified_formal_arms=qualified,
        inherited_qualified_formal_arms=0 if qualification_only else 12,layered_arm_positions=len(arms),
        incomplete_new_formal_arms=len(recs['execution_failures']),interrupted_new_formal_arms=sum(a.get('status')=='INTERRUPTED_EXECUTION' for a in arms),postexit_blocked_new_formal_arms=sum(a.get('status')=='POSTEXIT_VALIDATION_BLOCKED' for a in arms),unstarted_new_formal_arms=sum(a.get('status')=='UNSTARTED' for a in arms),
        pair_positions=len(pair_rows),new_pair_positions=0 if qualification_only else 12,inherited_evaluable_pairs=0 if qualification_only else 18,
        evaluable_pairs=sum(v['evaluable'] for v in pair_rows),unevaluable_pairs=sum(not v['evaluable'] for v in pair_rows),qualified_qualification_arms=len(qual),backend_conclusions=conclusions,
        conservative_starts=sum(f['starts'] for f in fees),outer_fee_seconds_upper=sum(f['outer_seconds_upper'] for f in fees),
        native_Optimize_completed_new_and_qualification_journals=sum(j['started'] for _,j,_ in journals.values()),
        unqualified_new_formal_actual_Optimize=partial_started,unqualified_new_formal_returned=partial_returned,
        actual_Optimize_all_observed_new_and_qualification=sum(j['started'] for _,j,_ in journals.values())+partial_started,
        formal_native_Optimize_qualified_new_arms=sum(j['started'] for key,(_,j,_) in journals.items() if key[0]=='campaign'),
        reader_SHA=sha(__file__),pure_offline=True,native_rerun=False,default_ENS_changed=False,primary_benchmark='cold P-GRB',
        prior_round112_state='BLOCKED',prior_partial13_endpoint_rejected=True,old_clock_adjusted=False,all20_measured_under_new_wrapper=False)
    summary['current_reader_fee_pending']=bool(recs['fees_pending'])
    write(dest/'summary.json',summary);write(dest/'backend_conclusions.json',conclusions)
    return summary

def compare(expected,actual):
    return core.compare(expected,actual)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True);p.add_argument('--qualification-only',action='store_true');p.add_argument('--compare')
    a=p.parse_args();print(json.dumps(rebuild(a.root,a.out,a.qualification_only),allow_nan=False))
    if a.compare:print(json.dumps(compare(a.compare,a.out),allow_nan=False))

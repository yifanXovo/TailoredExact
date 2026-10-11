"""Evidence-only root reconstruction; no original-worktree fallback or solver."""
import argparse,collections,csv,json,math,os
from pathlib import Path
import round108_reader as core
import round114_audit as audit
import round114_ps as ps
import round111_decisions as decisions
from round114_claims import reconcile,qualify_endpoint
from compare_round112_startup import compare as compare_H
from read_round113 import clock,native_log

ROUND='results/unified_exact_round114'
LAYER='R112_COMPLETE12_PLUS_R113_G50_4_PLUS_R114_G100_4'
csv.field_size_limit(64*1024*1024)
read,write,sha,table,portable=core.read,core.write,core.sha,core.table,core.portable

def typed(row):
    out={}
    for k,v in row.items():
        if v=='':out[k]=None
        elif v in ['True','False']:out[k]=v=='True'
        elif k in ['number','V','M','seed','origin_round','native_Optimize']:out[k]=int(v)
        elif k in ['U','L','gap','complete_seconds','cap_seconds','candidate_U','candidate_L','candidate_gap','candidate_complete_seconds',
            'control_U','control_L','control_gap','control_complete_seconds','dU','dL','dGap']:out[k]=float(v)
        else:out[k]=v
    return out

def inherited(root,out):
    old=out/'inherited_r113';manifest=read(old/'dependency_manifest.json')
    for name,h in manifest['files'].items():assert sha(old/name)==h
    arms=[typed(r) for r in core.rows(old/'reports_final/arms.csv') if r['id']!='G100-R2']
    pairs=[typed(r) for r in core.rows(old/'reports_final/pairs.csv') if r['id']!='G100-R2']
    assert len(arms)==16 and len(pairs)==24 and sum(r['formal_protocol_qualified'] for r in arms)==15
    assert sum(r['evaluable'] for r in pairs)==21
    cold=next(a for a in arms if a['id']=='G50-C1' and a['arm']=='P-GRB')
    assert cold['U'] is None and cold['L'] is None and cold['complete_seconds'] is None and not cold['formal_protocol_qualified']
    # Original R112 clocks and R113 G50 clocks are finite signed inheritance;
    # no historical LP is parsed, no endpoint or clock is manufactured.
    old12=old/'inherited_r112';clocks=read(old12/'clock_manifest.json')
    for name,h in clocks['files'].items():assert sha(old12/name)==h
    lookup={(a['id'],a['arm']):a for a in arms}
    for arm in arms:
        arm.update(evidence_layer=LAYER,source_reduced=False,native_proof_qualified=arm['formal_protocol_qualified'],
            historical_original_clock_unchanged=True,new_R114_measurement=False)
        if not arm['formal_protocol_qualified']:continue
        if arm['origin_round']==112:
            authority=next(q for q in clocks['arms'] if q['number']==arm['number'])
            d=old12/Path(authority['path']).parent
        else:d=old/'authoritative/campaign/raw'/f'{arm["number"]:02d}_{arm["id"]}_S0_{arm["arm"]}'
        receipt=read(d/'whole_arm_receipt.json');original_audit=read(d/'audit.json');completion=read(d/'completion.json')
        assert receipt['complete_seconds']==arm['complete_seconds']<=arm['cap_seconds'] and original_audit['passed']
        assert completion['returncode']==0 and completion['stop_reason']=='normal_return'
        for k in ['U','L','gap']:assert abs(original_audit['endpoint'][k]-arm[k])<=1e-7
        assert original_audit['endpoint']['certificate']==arm['certificate']
        arm['original_clock_path']=(d/'whole_arm_receipt.json').relative_to(root).as_posix()
    for row in pairs:
        if row['evaluable']:
            check=decisions.pair(lookup[row['id'],row['candidate']],lookup[row['id'],row['control']])
            assert check['classification']==row['classification'] and check['severe_regression']==row['severe_regression']
        row.update(evidence_layer=LAYER,historical_pair_unchanged=True,new_R114_pair=False)
    return arms,pairs,read(old/'reports_final/backend_conclusions.json')

def rebuild(root,dest,qualification_only=False,allow_pending=False):
    root=Path(root).resolve();out=root/ROUND;dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    core.start_reader.ROOT=root;candidate=read(out/'candidate_identity.json');production=read(out/'production_identity.json')
    for name,h in production['source_bindings'].items():assert sha(root/name)==h
    assert len(production['source_bindings'])==206
    if not qualification_only:
        gate=read(out/'review/performance_admission.json');assert gate['decision']=='ACCEPT'
        assert gate['candidate_identity_SHA']==sha(out/'candidate_identity.json')
        assert gate['campaign_identity_SHA']==sha(out/'campaign/identity.json') and gate['helpers']==candidate['helpers']
    campaigns=[('qualification/cli01',False)]+([] if qualification_only else [('campaign',True)])
    recs=collections.defaultdict(list);local=[];new=[];qual=[];byrole={};all_claims=[];all_witnesses=[]
    for name,formal in campaigns:
        camp=out/name;i=read(camp/'identity.json')
        assert i['source_hashes']==production['source_bindings'] and i['helpers']==candidate['helpers']
        assert i['prereg_sha256']==sha(out/'protocol.json') and i['runner_sha256']==sha(root/'scripts/round114_campaign.py')
        assert i['candidate_binary_sha256']==production['production_PE_SHA']==candidate['production_PE_SHA']
        assert i['dll_sha256']==production['DLL_SHA']==candidate['DLL_SHA']
        for n,h in i['helpers'].items():assert sha(root/n)==h
        for l in i['launches']:
            d=portable(root,l['destination']);p=l['panel'];label=dict(campaign=name,id=l['id'],arm=l['arm'],number=l['number'])
            assert sha(root/p['input_path'])==p['input_sha256']
            required=['result.json','completion.json','audit.json','observations.json','whole_arm_receipt.json','independent_evidence.json',
                'native_claims.json','claim_rejections.json','independent_endpoint_closeout.json']
            if not all((d/q).is_file() for q in required):
                status='UNSTARTED' if not (d/'launch.json').exists() else 'EXECUTION_OR_CLOSEOUT_BLOCKED'
                row=dict(label,origin_round=114,evidence_layer=LAYER,status=status,formal_protocol_qualified=False,
                    certificate_qualified=False,numbers_qualified=False,U=None,L=None,gap=None,certificate=None,complete_seconds=None,
                    failure_reason='FIXED_ARM_NOT_STARTED' if status=='UNSTARTED' else 'REQUIRED_EXECUTION_OR_CLOCK_EVIDENCE_MISSING',
                    missing_files=[q for q in required if not (d/q).is_file()],native_Optimize=None,PE_SHA=i['candidate_binary_sha256'],DLL_SHA=i['dll_sha256'])
                (new if formal else qual).append(row);recs['execution_failures'].append(row);continue
            t=clock(d,l,formal);whole=read(d/'whole_arm_receipt.json');ind=read(d/'independent_evidence.json')
            assert whole['independent_evidence_SHA']==sha(d/'independent_evidence.json')
            assert whole['independent_closeout_SHA']==sha(d/'independent_endpoint_closeout.json')
            assert whole['own_UB_floor_zero_evidence_written_before_whole'] and not whole['future_cohort_review_in_clock']
            obs=read(d/'observations.json');r=read(d/'result.json');c=read(d/'completion.json');j=audit.journal(root,l,d,obs)
            chain=audit.return_chain(root,l,d,j,r,c);rebuilt_ind=audit.independent(root,l,d,j,r,c,chain)
            for key in ['own_U','own_exact_zero','independent_floor0','physical','counts','result_SHA','observations_SHA','completion_SHA']:
                assert rebuilt_ind[key]==ind[key],('current independent evidence differs',key)
            claims=audit.claims_for(l,j,chain,r);assert claims==read(d/'native_claims.json')
            local_rejection=reconcile(claims,ind['witnesses']);assert local_rejection==read(d/'claim_rejections.json')
            necessary=read(d/'audit.json');normal=None;ep={}
            if local_rejection['rejections']:
                assert necessary['passed'] is False and necessary['claim_rejection_recorded'] and necessary['independent_evidence_audit_passed']
                audit.rejected_mandatory(root,l,d,j,r,chain,copy_json(ind),local_rejection)
            else:
                assert necessary['passed']
                oldj=ps.ps_journal(root,p,d) if l['arm']=='P-S' else core.evidence.journal(root,p,d)
                oldj['return_sequences']=j['return_sequences'];oldj['return_available']=j['return_available']
                ep=ps.paid_endpoint(root,l,i,d,oldj) if l['arm']=='P-S' else core.endpoint(root,l,i,d,oldj,False)
                normal=ep['arm']
                for k in ['U','L','gap']:assert abs(normal[k]-necessary['endpoint'][k])<=1e-7
                assert normal['certificate']==necessary['endpoint']['certificate']
            item=dict(l=l,d=d,i=i,j=j,ind=ind,normal=normal,ep=ep,t=t,label=label,chain=chain,formal=formal)
            local.append(item)
            if formal:all_claims+=claims;all_witnesses+=ind['witnesses'];byrole[l['arm']]=item
            else:
                e=dict(ind,clock_valid=True,necessary_closeout_complete=True)
                endpoint=qualify_endpoint(e,local_rejection['damaged_calls'],normal)
                qual.append(dict(endpoint,**label,complete_seconds=t,origin_round=114,native_Optimize=j['started'],not_performance=True))
            recs['fleets'].append(dict(label,**ind['physical']))
            recs['native_counts'].append(dict(label,**ind['counts'],LP=sum(q['solve_kind']=='LP' for q in chain['ledger']),
                actual_declared_not_started_not_conflated=True))
            recs['native_bounds'].extend(dict(label,**q) for q in claims)
            recs['own_UB_flow'].extend(dict(label,**q) for q in ind['witnesses'])
            recs['progress_publication'].append(dict(label,**read(d/'progress_publication_receipt.json')))
            for call in j['calls'].values():
                recs['native_calls'].append(dict(label,call=call['call'],model_SHA=call['model_sha256'],full_original=call['full_original'],
                    lower_g=call['lower_g'],upper_g=call['upper_g'],cutoff=call['cutoff'],settings=call['settings'],
                    journal_returned=call['call'] in j['returned_ids'],independently_verified_return=call['call'] in chain['actual'],
                    explicit_not_started=call['call'] in j['not_started_ids'],
                    **(native_log(root,call['native_log_path']) if call['call'] in chain['actual'] else dict(Optimize=False,not_started=True))))
            controller=core.evidence.controller_tables(d,r)
            for k,rows in controller.items():recs[k].extend(dict(label,**q) for q in rows)
            recs['split_exposure'].append(dict(label,actual_atomic_split_events=sum(q.get('event')=='atomic_split' for q in controller['controller_events']),
                parent_atomic_replacement_required=True,hidden_cause='unknown'))
            for key in ['Start','cover','chronological_cover']:
                if ep.get(key) is not None:recs[{'Start':'compact_Starts','cover':'covers','chronological_cover':'chronological_covers'}[key]].append(dict(label,evidence=ep[key]))
            H=r['process_elapsed_at_exact_phase_start_seconds'] if l['arm']!='P-GRB' else 0.
            LP=sum(float(q['solver_runtime']) for q in chain['ledger'] if q['solve_kind']=='LP')
            MIP=r['gurobi_runtime'] if l['arm'] in ['P-GRB','P-S'] else sum(float(q['solver_runtime']) for q in chain['ledger'] if q['solve_kind']!='LP')
            recs['time_partitions'].append(dict(label,whole_seconds=t,H_seconds=H,LP_inclusive_seconds=LP,MIP_inclusive_seconds=MIP,
                process_write_model_controller_residual_seconds=c['process_wall_seconds']-H-LP-MIP,
                admission_and_necessary_postexit_seconds=t-c['process_wall_seconds'],nested_seconds_added=False,causal_subtraction_allowed=False))
    final=reconcile(all_claims,all_witnesses)
    assert final==reconcile(list(reversed(all_claims)),list(reversed(all_witnesses)))
    final.update(phase='offline_final_cohort_reconciliation',original_whole_receipts_unchanged=True,
        own_evidence_created_inside_original_whole_only=True,future_review_charged_as_engineering=True)
    write(dest/'cohort_reconciliation.json',final)
    for item in local:
        if not item['formal']:continue
        l,d,j,ind,t=item['l'],item['d'],item['j'],item['ind'],item['t'];damage=[q for q in final['damaged_calls'] if q['arm']==l['arm']]
        endpoint=qualify_endpoint(dict(ind,clock_valid=True,necessary_closeout_complete=True),damage,item['normal'])
        row=dict(endpoint,**item['label'],origin_round=114,evidence_layer=LAYER,complete_seconds=t,cap_seconds=l['cap_seconds'],
            status=read(d/'result.json')['status'],native_Optimize=j['started'],input_SHA=l['panel']['input_sha256'],
            PE_SHA=item['i']['candidate_binary_sha256'],DLL_SHA=item['i']['dll_sha256'],source_commit=item['i']['measured_source_commit'],
            performance_helper_identity=sha(out/'candidate_identity.json'),original_clock_path=(d/'whole_arm_receipt.json').relative_to(root).as_posix(),
            own_exact_zero=ind['own_exact_zero'],new_R114_measurement=True,raw_audit_passed=read(d/'audit.json')['passed'])
        row['relative_gap'],row['relative_gap_null_reason']=decisions.relative(row);new.append(row);item['final_arm']=row
        offset=read(d/'native_end_receipt.json')['complete_seconds_until_native_end']-read(d/'completion.json')['fully_observed_end_to_end_seconds']
        zero=[q for q in j['witnesses'] if q['F']==0. and q['Y'][1:]==core.evidence.instance(root,l['panel'])['D'][1:]]
        first=min(zero,key=lambda q:q['available']) if zero else None
        recs['target_discovery'].append(dict(item['label'],own_exact_zero=ind['own_exact_zero'],first_committed_zero_sequence=first['sequence'] if first else None,
            first_committed_zero_availability_upper_seconds=first['available']+max(0.,offset) if first else None,
            postreturn_independent_validation_available_upper_seconds=read(d/'postexit_audit_receipt.json')['complete_seconds_until_audit_end'] if first else None,
            complete_certificate_available_seconds=t if row['certificate'] else None,native_true_first_discovery='unknown',
            conservative_validation_upper_distinct_from_commit=True))
        recs['checkpoints'].append(dict(item['label'],seconds=t,observed=True,U=row['U'],L=row['L'],gap=row['gap'],certificate=row['certificate'],
            source_reduced=row['source_reduced'],native_proof_qualified=row['native_proof_qualified'],reason='true complete endpoint'))
        for point in [300,600,900,1200,1800,3600]:
            if point>=t:
                if row['certificate']:recs['checkpoints'].append(dict(item['label'],seconds=point,observed=True,U=row['U'],L=row['L'],gap=row['gap'],certificate=True,reason='already established own certificate continued'))
                continue
            hits=[q for q in j['witnesses'] if q['available']+max(0.,offset)<=point]
            if not hits:continue
            U=min(q['F'] for q in hits);bad={q['call'] for q in damage}
            bound=[q['global_bound'] for q in j['bounds'] if q['global_available'] and q['call'] not in bad and q['available']+max(0.,offset)<=point]
            L=max([0.]+bound) if not damage else 0.
            recs['checkpoints'].append(dict(item['label'],seconds=point,observed=True,U=U,L=L,gap=U-L,certificate=False,
                source_reduced=bool(damage),native_proof_qualified=not damage,reason='actual committed own physical witness; final values never backfilled'))
    pairrows=[];conclusions={};same=[]
    if not qualification_only:
        protocol=read(out/'protocol.json');lookup={(q['id'],q['arm']):q for q in new};role=protocol['roles'][0]['id']
        if all(m in byrole for m in ['P-S','ENS-C','M-B']):
            H=compare_H(root,protocol['roles'][0],{m:byrole[m]['d'] for m in ['P-S','ENS-C','M-B']});same=H['comparisons']
            recs['same_H']=same
            recs['same_H_fleets']=[dict(id=role,arm=m,**v) for m,v in H['arms'].items()]
        for X,C in protocol['pairs']:
            a,c=lookup[role,X],lookup[role,C];v=decisions.pair(a,c)
            delta=dict(dU=a['U']-c['U'],dL=a['L']-c['L'],dGap=a['gap']-c['gap']) if v['evaluable'] else dict(dU=None,dL=None,dGap=None)
            pairrows.append(dict(v,id=role,origin_round=114,evidence_layer=LAYER,**delta,
                candidate_source_reduced=a.get('source_reduced'),control_source_reduced=c.get('source_reduced'),
                candidate_native_proof_qualified=a.get('native_proof_qualified'),control_native_proof_qualified=c.get('native_proof_qualified'),
                candidate_endpoint_source=a.get('endpoint_source',a.get('certificate_basis')),control_endpoint_source=c.get('endpoint_source',c.get('certificate_basis')),
                reason=None if v['evaluable'] else a.get('failure_reason',c.get('failure_reason'))))
        assert len(pairrows)==6
        oldarms,oldpairs,previous=inherited(root,out)
        for X in ['ENS-C','M-B']:
            vector=previous[X]['five_role_vector'][:4];v=next(q for q in pairrows if q['candidate']==X and q['control']=='P-S')
            match=next((q for q in same if q['candidate']==X),None)
            exposed=all(lookup[role,m].get('native_Optimize',0) for m in [X,'P-S'])
            eligible=bool(v['evaluable'] and match and match['qualified'] and exposed)
            vector=vector+[dict(id=role,classification=v['classification'],eligible=eligible,origin_round=114,
                reason='QUALIFIED' if eligible else 'MISSING_STRICT_PAIR_SAME_H_OR_BACKEND_EXPOSURE',
                source_reduced=v['candidate_source_reduced'] or v['control_source_reduced'],severe_regression=v['severe_regression'])]
            conclusions[X]=dict(status='MIXED_INCREMENT_OBSERVED' if all(q['eligible'] for q in vector) else 'INCOMPLETE_ATTRIBUTION',
                eligible_count=sum(q['eligible'] for q in vector),denominator=5,five_role_vector=vector)
        arms=oldarms+new;pairs=oldpairs+pairrows
        assert len(arms)==20 and len(pairs)==30 and sum(q['evaluable'] for q in pairs)<=27
        recs['historical_execution_ledger_G100_unstarted']=[typed(r) for r in core.rows(out/'inherited_r113/reports_final/new_arms.csv') if r['id']=='G100-R2']
        table(dest/'inherited_arms.csv',oldarms);table(dest/'inherited_pairs.csv',oldpairs)
    else:arms=[];pairs=[]
    fees=[]
    for path in sorted((out/'fees').glob('*/launch.json')):
        l=read(path)
        if not (path.parent/'receipt.json').exists():
            assert qualification_only and allow_pending and l['wrapper_pid']==os.getpid() and l['qualification']
            recs['fees_pending'].append(dict(label=path.parent.name,seconds=None,actual_driver_still_running=True));continue
        r=read(path.parent/'receipt.json');assert r['actual_exit_observed'] and r['necessary_trailer_complete']
        fees.append(dict(label=path.parent.name,starts=l['conservative_process_starts'],qualification=l['qualification'],
            seconds=r['outer_seconds_upper'],exit_code=r['exit_code'],actual_children=r['actual_native_children'],failed_slots_not_refunded=True))
    assert sum(f['starts'] for f in fees)<=16 and sum(f['seconds'] for f in fees)<=17000
    assert sum(f['starts'] for f in fees if f['qualification'])<=8 and sum(f['seconds'] for f in fees if f['qualification'])<=900
    summary=dict(execution_status='QUALIFICATION_ONLY' if qualification_only else 'G100_COLLECTION_COMPLETE' if len(new)==4 and all(q['formal_protocol_qualified'] for q in new) else 'BLOCKED',
        scientific_status=conclusions,evidence_layer=LAYER,new_formal_positions=len(new),new_qualified_measurements=sum(q['formal_protocol_qualified'] for q in new),
        inherited_qualified_measurements=0 if qualification_only else 15,total_qualified_measurements=sum(q['formal_protocol_qualified'] for q in arms),
        layered_arm_positions=len(arms),new_pairs=len(pairrows),pair_positions=len(pairs),evaluable_pairs=sum(q['evaluable'] for q in pairs),
        unevaluable_pairs=sum(not q['evaluable'] for q in pairs),old_G50_P_pairs_still_unqualified=3,
        qualified_qualification_CLI=sum(q['formal_protocol_qualified'] for q in qual),conservative_starts=sum(f['starts'] for f in fees),outer_seconds_upper=sum(f['seconds'] for f in fees),
        qualification_starts=sum(f['starts'] for f in fees if f['qualification']),qualification_seconds=sum(f['seconds'] for f in fees if f['qualification']),
        current_reader_fee_pending=bool(recs['fees_pending']),rejected_calls=final['damaged_calls'],
        source_reduced_new_arms=[q['arm'] for q in new if q.get('source_reduced')],reader_SHA=sha(__file__),Optimize=0,
        default_ENS_changed=False,primary_benchmark='cold P-GRB',old_R113_state='BLOCKED',no_historical_clock_recreated=True,
        qualification_native_Optimize=sum(q['native_Optimize'] for q in qual if q.get('native_Optimize') is not None),
        formal_actual_Optimize=sum(q.get('native_Optimize',0) or 0 for q in new))
    table(dest/'arms.csv',arms);table(dest/'new_arms.csv',new);table(dest/'pairs.csv',pairs);table(dest/'new_pairs.csv',pairrows)
    table(dest/'qualification_arms.csv',qual);recs['fees']=fees
    for name,rows in sorted(recs.items()):table(dest/(name+'.csv'),rows)
    write(dest/'summary.json',summary);write(dest/'backend_conclusions.json',conclusions)
    return summary

def copy_json(v):return json.loads(json.dumps(v))

def compare(expected,actual):
    expected=Path(expected);actual=Path(actual);files=[]
    for p in sorted(expected.iterdir()):
        if p.suffix not in ['.csv','.json']:continue
        q=actual/p.name;assert q.is_file(),p.name
        if p.name=='summary.json':
            a=read(p);b=read(q);a.pop('reader_SHA',None);b.pop('reader_SHA',None)
        else:a=read(p) if p.suffix=='.json' else core.rows(p);b=read(q) if p.suffix=='.json' else core.rows(q)
        assert a==b,('restored core field mismatch',p.name);files.append(p.name)
    return dict(all_fields_equal=True,files=files,CSV_field_limit=csv.field_size_limit(),original_worktree_fallback=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--qualification-only',action='store_true');parser.add_argument('--compare');a=parser.parse_args()
    value=rebuild(a.root,a.out,a.qualification_only)
    if a.compare:value['core_comparison']=compare(a.compare,a.out)
    print(json.dumps(value),flush=True)

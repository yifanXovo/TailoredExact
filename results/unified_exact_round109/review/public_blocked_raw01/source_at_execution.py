"""Independent final24/raw-failure/17missing audit, including restored-root mode.

This explicit incomplete-inventory adapter does not relax the exact42 contract.
It computes BLOCKED from the actual native fault and missing scientific work.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,math,runpy,sys,time,traceback
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--dll');ap.add_argument('--public',action='store_true');ap.add_argument('--reports');args=ap.parse_args()
ROOT=Path(args.root).resolve();OUT=ROOT/'results/unified_exact_round109';REVIEW=OUT/'review';DEST=Path(args.out).resolve();assert DEST.is_relative_to(REVIEW);DEST.mkdir(exist_ok=False)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):
    with (DEST/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
tick=time.perf_counter();error=None;value={};save('launch.json',dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),source_SHA=digest(__file__),explicit_read_root=str(ROOT),public_mode=args.public,Optimize=0,native_environment=0));(DEST/'source_at_execution.py').write_bytes(Path(__file__).read_bytes())
try:
    original=sys.argv[:];sys.argv=[str(REVIEW/'round109_independent_raw.py'),'--root',str(ROOT),'--mode','public' if args.public else 'final','--out',str(DEST)]
    if not args.public:assert args.dll;sys.argv+=['--dll',args.dll]
    else:assert args.dll is None
    core=runpy.run_path(str(REVIEW/'round109_independent_raw.py'));sys.argv=original
    snapshot=DEST/'reviewer_sources';snapshot.mkdir()
    for name in ['round109_independent_raw.py','round109_independent_kernel.py','round109_independent_parser.py','round109_independent_decision.py','round109_independent_seed_scope.py','round109_independent_numerical.py','round109_independent_main06.py']:(snapshot/name).write_bytes(core['data'](REVIEW/name))
    protocol,manifest,feasible=core['frozen_protocol']();candidate,identity=core['current_bindings']();launches=core['bind_launches'](identity,manifest);refs=core['audit_references'](manifest)
    qi=core['obj'](OUT/'qualification/cli01/identity.json');qr=core['obj'](OUT/'qualification/identity.json');qualified=[]
    assert qr['passed'] and len(qi['launches'])==5 and qr['qualified_argv']==[l['command'] for l in qi['launches']] and qr['actual_seeds']==[0,0,0,1,1]
    for launch in qi['launches']:
        a,_,_=core['audit_arm'](launch,qi,False);qualified.append(a);core['cache'].clear()
    fees=core['audit_fees'](launches);assert fees['paid_starts']==51 and fees['paid_outer_seconds']==18618.079987913487
    arms=[];mechanisms=[]
    for launch in launches[:24]:
        a,_,_=core['audit_arm'](launch,identity,True);arms.append(a);core['cache'].clear()
        d=core['under_root'](launch['destination']);calls=Counter(r['solve_kind'] for r in a['native_records']);obs=core['obj'](d/'observations.json')
        saved_covers=[v['payload']['cover'] for v in obs if v['payload']['kind']=='call' and not v['payload']['full_original']]
        computed_peak=max((sum(x['lower_g']<min(v['payload']['cutoff'],v['payload']['gmax'])-1e-7 for x in v['payload']['cover']) for v in obs if v['payload']['kind']=='call' and not v['payload']['full_original']),default=0)
        m=dict(number=launch['number'],id=a['id'],arm=a['arm'],seed=a['seed'],actual_Optimize=sum(calls.values()),solve_kinds=dict(calls),native_records=a['native_records'],models=a['model_contracts'],submitted_Starts=len(a['starts']),Start_attempts=a['start_attempts'],own_final_partition=a['cover'],maximum_potentially_relevant_saved_cover_pieces_at_native_calls=computed_peak,AM_actions={},target_kind_counts={},maximum_observed_open_relevant_leaf_count=None)
        if a['arm']!='P-GRB' and (d/'external').exists():
            for fname,key in [('adaptive_mass_decision_ledger.csv','AM_actions'),('native_target_ledger.csv','target_kind_counts')]:
                rows=core['rows'](d/'external'/fname);column='selected_action' if key=='AM_actions' else 'target_kind';m[key]=dict(Counter(r[column] for r in rows));m[fname+'_SHA']=core['sha'](d/'external'/fname)
            traces=core['rows'](d/'external/global_bound_trace.csv');m['maximum_observed_open_relevant_leaf_count']=max((int(v['open_relevant_leaf_count']) for v in traces),default=0)
            m['actual_genuine_partition_splits']=len((a['cover'] or {}).get('actual_parent_child_partitions',[]));m['atomic_split_events']=(a['cover'] or {}).get('actual_atomic_split_events',[])
        mechanisms.append(m)
    assert len(arms)==24 and all(a['seed']==0 and a['id'].startswith(('G20','G50')) for a in arms)
    # Actual failure is re-read; the historical Windows/PE diagnosis merely
    # binds corroborating offline provenance and the resource boundary.
    failed_launch=launches[24];d=core['under_root'](failed_launch['destination']);actual=core['obj'](d/'launch.json');completion=core['obj'](d/'completion.json');audit=core['obj'](d/'audit.json')
    assert actual['command']==failed_launch['command'] and actual['panel']==failed_launch['panel'] and completion['returncode']==0xC00000FD and completion['stop_reason']=='abnormal_process_exit'
    assert completion['committed_events']==0 and core['obj'](d/'observations.json')==[] and audit['passed'] is False and audit['endpoint'] is None
    assert not core['data'](d/'stdout.log') and not core['data'](d/'stderr.log') and all(not (d/name).exists() for name in ['result.json','native.log','whole_arm_receipt.json'])
    assert [v['event'] for v in core['rows'](d/'phases.csv')]==['process_entry','instance_parsing_start']
    sample=json.loads(core['data'](d/'samples.jsonl').splitlines()[0]);assert sample['provisional_U'] is None and sample['formal_endpoint'] is False
    missing=[dict(number=l['number'],id=l['id'],arm=l['arm'],seed=l['seed'],native_argv=l['command'],scientific_endpoint=None,state='never_started') for l in launches[25:]]
    assert [r['number'] for r in missing]==list(range(26,43)) and all(not core['under_root'](l['destination']).exists() for l in launches[25:])
    diagpath=REVIEW/'main09_stack_diagnosis03/audit.json';diag=core['obj'](diagpath);assert diag['decision']=='ACCEPT_DIAGNOSIS_BLOCKED' and diag['production_PE_SHA']==candidate['production_PE_SHA'] and diag['native_failure']['exit_code']==completion['returncode'] and diag['windows_evidence']['pid']==core['obj'](d/'affinity.json')['pid']
    for field,name in [('events_SHA','windows_application_events.stdout'),('disassembly_SHA','fault_offset_disassembly.stdout')]:assert diag['windows_evidence'][field]==core['sha'](diagpath.parent/name)
    windows=core['txt'](diagpath.parent/'windows_application_events.stdout');asm=core['txt'](diagpath.parent/'fault_offset_disassembly.stdout');assert 'c00000fd' in windows and '<Data>976c</Data>' in windows and '004e2693' in windows and '1404e2693:' in asm and '_CharMatcher' in asm
    assert diag['PE_stack']['reserve_bytes']==2097152 and diag['PE_stack']['commit_bytes']==4096 and diag['same_PE_ordinary_environment_recovery_qualified'] is False and diag['resumption_allowed'] is False
    admission=core['obj'](REVIEW/'performance_admission.json');assert admission['decision']=='ACCEPT' and admission['bindings']['candidate_identity_SHA']==core['sha'](OUT/'candidate_identity.json');eligibility=admission['input_eligibility'];assert len(eligibility)==12 and all(eligibility.values())
    unresolved=['NATIVE_STACK_OVERFLOW_BEFORE_INSTANCE_PARSED','FINAL_PE_REPAIR_REQUIRES_ALL42_BEYOND_FROZEN_BUDGET']
    selection=core['decision']['selection'](arms,eligibility,unresolved);assert selection['stage']=='BLOCKED' and selection['completed_formal_arms']==24 and len(selection['main_pairs'])==8 and not selection['seed1_pairs']
    selection.update(valid_normal_formal_numbers=list(range(1,25)),failed_formal_numbers=[25],unstarted_formal_numbers=list(range(26,43)),completed_formal_seed1_arms=0,formal_seed_sensitivity_assessed=False,
        reason_code_interpretation='Inherited incomplete-panel gate placeholders; no observed formal Seed sensitivity or V100 performance rejection',effective_stage_reason_codes=unresolved,remaining_strata_and_seed_support_gates_not_assessed=True,default_ENS_changed=False)
    own_pairs=list(selection['main_pairs'].values())+selection['other_main_pairs'];counts={}
    for x,y in [('M-B','P-GRB'),('M-B','ENS-C'),('ENS-C','P-GRB')]:
        matched=[p for p in own_pairs if (p['candidate'],p['control'])==(x,y)];counts[x+'/'+y]=dict(Counter(p['classification'] for p in matched));counts[x+'/'+y]['severe_regressions']=sum(p['severe_regression'] is True for p in matched)
    losses=[]
    for p in own_pairs:
        if p['classification'] in ['LOSS','MIXED']:
            p=dict(p)
            if p['candidate_gap'] is not None and p['control_gap'] is not None:
                p.update(candidate_minus_control_U=p['candidate_U']-p['control_U'],candidate_minus_control_L=p['candidate_L']-p['control_L'],candidate_minus_control_gap=p['candidate_gap']-p['control_gap']);assert abs(p['candidate_minus_control_gap']-(p['candidate_minus_control_U']-p['candidate_minus_control_L']))<=1e-12
            losses.append(p)
    science=dict(stage='BLOCKED',valid24=True,failed25=True,unstarted17=True,frozen_main_denominator=12,completed_main_roles=8,frozen_seed_groups=3,formal_seed1_arms_completed=0,no_V100_valid_solve_endpoint=True,qualification_Seed1_only=True,own_pair_counts=counts,own_pairs=own_pairs,materiality_losses_and_MIXED=losses,original_tolerances_and_pair_thresholds_unchanged=True,missing_partial_support_gates_not_performance_rejections=True,
        paid_starts=fees['paid_starts'],paid_outer_seconds=fees['paid_outer_seconds'],remaining_starts=72-fees['paid_starts'],finalPE_minimum42_native_children=42,finalPE_minimum_total_starts=fees['paid_starts']+42,paid_plus_finalPE_all42_nominal_seconds=fees['paid_outer_seconds']+88200,resumption_allowed=False)
    # Comparison occurs strictly after independent physics, provenance,
    # classification and BLOCKED construction. It is optional at local run.
    compared=None
    if args.reports:
        reports=core['under_root'](args.reports);published=core['rows'](reports/'arms.csv');pp=core['rows'](reports/'pairs.csv');ps=core['obj'](reports/'selection_decision.json');summary=core['obj'](reports/'summary.json')
        assert len(published)==24 and summary['formal_arms']==24 and summary['failed_formal_arms']==1 and summary['conservative_starts']==51 and summary['outer_solver_fee_seconds']==fees['paid_outer_seconds']
        for a in arms:
            b=next(v for v in published if (v['id'],int(v['seed']),v['arm'])==(a['id'],a['seed'],a['arm']));assert abs(float(b['U'])-a['U'])<=1e-7 and abs(float(b['L'])-a['L'])<=1e-7 and abs(float(b['gap'])-a['gap'])<=1e-7 and (b['certificate']=='True')==a['certificate']
            assert (b['complete_seconds']=='' if a['complete_seconds'] is None else abs(float(b['complete_seconds'])-a['complete_seconds'])<=1e-9)
            if a['complete_seconds'] is None:assert json.loads(b['complete_seconds_interval'])==a['complete_seconds_interval']
        assert len(pp)==len(own_pairs)==24
        for p in own_pairs:
            b=next(v for v in pp if (v['id'],int(v['seed']),v['candidate'],v['control'])==(p['id'],p['seed'],p['candidate'],p['control']));assert b['classification']==p['classification'] and (b['severe_regression']=='True')==(p['severe_regression'] is True)
            if p.get('certified_time_ratio_interval') is not None:assert b['certified_time_ratio']=='' and json.loads(b['certified_time_ratio_interval'])==p['certified_time_ratio_interval']
        assert ps['stage']==selection['stage'] and ps['main_counts'].get('WIN',0)==selection['main_WIN'] and ps['main_counts'].get('LOSS',0)==selection['main_LOSS'] and ps['main_severe_P_regressions']==selection['main_severe_P_regressions'] and ps['completed_formal_seed1_arms']==0 and ps['formal_seed_sensitivity_assessed'] is False
        assert {k:len(v) for groups in ps['stratum_WIN_roles'].values() for k,v in groups.items()}==selection['stratum_WIN']
        assert [v['number'] for v in core['rows'](reports/'failures.csv')]==['25'] and [int(v['number']) for v in core['rows'](reports/'unstarted.csv') if v['campaign']=='campaign']==list(range(26,43))
        compared={p.name:core['sha'](p) for p in [reports/'arms.csv',reports/'pairs.csv',reports/'selection_decision.json',reports/'summary.json',reports/'failures.csv',reports/'unstarted.csv']}
    value=dict(decision='ACCEPT_INDEPENDENT_BLOCKED',stage='BLOCKED',resumption_allowed=False,selection=selection,science= science,own_actual_arms=arms,own_qualification=qualified,own_input_checks=feasible,own_references=refs,mechanism=mechanisms,fees=fees,
        failed25=dict(number=25,completion=completion,raw_audit=audit,scientific_endpoint=None,provisional_sample_never_qualified=sample,binding={n:core['sha'](d/n) for n in ['launch.json','completion.json','audit.json','observations.json','phases.csv','stdout.log','stderr.log','samples.jsonl']}),unstarted17=missing,actual_stack_diagnosis_SHA=core['sha'](diagpath),
        candidate_identity_SHA=core['sha'](OUT/'candidate_identity.json'),campaign_identity_SHA=core['sha'](OUT/'campaign/identity.json'),all42_native_argv=[l['command'] for l in launches],primary_comparison=compared,
        reviewer_sources={p.name:core['sha'](p) for p in snapshot.iterdir()},read_bindings=core['reads'],completed_checks=core['require'].__globals__['count'],public_mode=args.public,explicit_read_root=str(ROOT),no_original_root_fallback=True,
        actual_PE_DLL_rehash=not args.public,reviewer_calls=dict(Optimize=0,native_environment=0,IIS=0,compiler=0,production_edits=0),engineering_elapsed_seconds=time.perf_counter()-tick)
    save('audit.json',value);save('selection_decision.json',selection);print(json.dumps(dict(decision=value['decision'],stage='BLOCKED',checks=value['completed_checks'],counts=counts,paid_starts=fees['paid_starts'],paid_outer_seconds=fees['paid_outer_seconds'])),flush=True)
except Exception:
    error=traceback.format_exc();save('audit.json',dict(decision='HOLD',error=error));print(error,file=sys.stderr,flush=True)
save('receipt.json',dict(exit_code=int(error is not None),decision='HOLD' if error else 'ACCEPT_INDEPENDENT_BLOCKED',engineering_elapsed_seconds=time.perf_counter()-tick,source_SHA=digest(__file__),audit_SHA=digest(DEST/'audit.json'),Optimize=0,native_environment=0,explicit_read_root=str(ROOT),cwd=str(Path.cwd())))
if error:sys.exit(1)

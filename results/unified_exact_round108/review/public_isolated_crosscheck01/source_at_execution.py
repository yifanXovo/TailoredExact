"""Independent public-root crosscheck of this reviewer's raw reconstruction.

No project imports, native loads, solving, builds or original-root fallback.
The raw audit, not the primary summary, supplies endpoints and classifications.
Only the explicitly supplied current root's review directory is written.
"""
import argparse, csv, hashlib, json, math, sys, time, traceback
from collections import Counter
from pathlib import Path

cli=argparse.ArgumentParser()
cli.add_argument('--root',required=True)
cli.add_argument('--audit',required=True)
cli.add_argument('--out',required=True)
args=cli.parse_args()
root=Path(args.root).resolve(); out=root/'results/unified_exact_round108'
dest=Path(args.out).resolve(); audit_path=Path(args.audit).resolve()
assert dest.is_relative_to(out/'review') and audit_path.is_relative_to(out/'review')
dest.mkdir(exist_ok=False)
reads={}; checks=0
def data(p):
    p=Path(p).resolve(); assert p.is_relative_to(root),'outside explicit root'
    b=p.read_bytes();reads[p.relative_to(root).as_posix()]=hashlib.sha256(b).hexdigest();return b
def sha(p):return hashlib.sha256(data(p)).hexdigest()
def obj(p):return json.loads(data(p).decode('utf-8-sig'))
def rows(p):return list(csv.DictReader(data(p).decode('utf-8-sig').splitlines()))
def require(condition,message):
    global checks
    checks+=1
    if not condition:raise AssertionError(message)
def number(a,b,message,tol=1e-12):
    require(math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b))<=tol,message)
def boolean(s):
    require(s in ['True','False'], 'literal CSV Boolean')
    return s=='True'
def write(p,value):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def fleet(routes):
    return {r['vehicle']:dict(nodes=r['nodes'],operations=sorted(r['operations'],key=lambda o:o['station'])) for r in routes}
def portable(value):return str(value).replace('\\','/')

tick=time.perf_counter(); source=sha(Path(__file__))
command=[sys.executable,*sys.argv]
write(dest/'launch.json',dict(actual_command=command,explicit_read_root=str(root),source_SHA=source,
    independent_raw_audit_SHA=sha(audit_path),Optimize=0,LP_solve=0,native_environment=0,compiler=0))
answer={}; error=None; decision='HOLD'
try:
    a=obj(audit_path);report=out/'reports_final'
    require(a['decision']=='ACCEPT' and not a['error'],'completed independent all-raw audit accepted')
    require(a['bindings']['isolated_public_math'] is True,'actual explicit isolated public mathematics mode')
    binary=a['bindings']['binary_identity']
    require(binary['retained_actual_run_identity_only'] and not binary['PE_bytes_rehashed'] and not binary['DLL_bytes_rehashed'] and not binary['independent_engine_performance_rerun'],'no native binary read or performance rerun claim in the isolated root')
    require(not (root/'build/research/round108-frozen-mb-v1/ExactEBRP.exe').exists(),'no measured PE available or read')
    require(all(Path(p).resolve().is_relative_to(root) for p in a['read_bindings']),'every actual independent evidence byte read is in this explicit recovered root')
    restore=obj(root/'restore_receipt.json')
    require(restore['exit_code']==0 and restore['public_files_only'] and not restore['original_workspace_reads'] and Path(restore['restored_root']).resolve()==root,'actual public-only restoration into this fresh root')
    require(restore['restorer_SHA']==sha(root/'scripts/round108_public.py'),'actual public restorer and recovered source byte identity')
    package_review=obj(out/'review/packaging_exact_parts_review01.json')
    require(package_review['decision']=='ACCEPT' and package_review['candidate_source_SHA']==restore['restorer_SHA'],'actual accepted precise-part restorer source')
    require(a['reviewer_script_SHA']==sha(out/'review/campaign_raw_audit01.py'),'exact current independently executed source')
    require(len(a['arms'])==21 and len(a['qualification'])==3,'exact21 formal and3 qualification')
    allarms=a['qualification']+a['arms']; own={(r['id'],r['arm']):r for r in allarms}
    published=rows(report/'qualification_arms.csv')+rows(report/'arms.csv')
    require(len(own)==len(published)==24,'complete unique endpoint namespace')
    require(set(own)=={(r['id'],r['arm']) for r in published},'all final published endpoints have own raw reconstruction')
    for r in published:
        z=own[r['id'],r['arm']]
        for k in ['U','L','gap','complete_seconds','relative_gap']:
            number(z[k],r[k],'independent/published endpoint '+str((r['id'],r['arm'],k)))
        for k in ['certificate','numbers_qualified','certificate_qualified']:
            require(z[k]==boolean(r[k]),'independent/published qualified flags')
        require(z['PE_SHA']==r['PE_SHA'] and z['DLL_SHA']==r['DLL_SHA'],'all published endpoint measured binary identities')
        number(float(r['U'])-float(r['L']),r['gap'],'published signed gap retained',1e-15)
    pairs={(p['id'],p['control']):p for p in a['gate']['pairs']}
    pubpairs=rows(report/'pairs.csv')
    require(len(pairs)==len(pubpairs)==14,'all two-control paired comparisons retained')
    for p in pubpairs:
        z=pairs[p['id'],p['control']]
        require(z['classification']==p['classification'] and z['severe_regression']==boolean(p['severe_regression']),'all14 raw arithmetic pair class/severity agree')
        require(z['percentage_gap_path_applicable']==boolean(p['percentage_gap_path_applicable']),'signed percentage path exactly guarded')
        for k in ['UB_improvement','gap_improvement','LB_change','a_U','a_gap','UB_ratio','gap_ratio']:
            if z[k] is None:require(p[k]=='','nonapplicable ratios null')
            else:number(z[k],p[k],'pair scalar '+k)
        if p['a_t']!='':number(z['a_t'],p['a_t'],'both certified time threshold')
        if p['time_improvement']!='':number(z['time_improvement'],p['time_improvement'],'both certified complete time difference')
    selection=obj(report/'selection_decision.json')
    for k in ['stage','completed_formal_arms','cancelled_arms','unseen_WIN','unseen_LOSS','exact_four_unseen_eligibility','default_ENS_changed','broad_performance_stability_proved']:
        require(a['selection'][k]==selection[k],'independently derived final selection field '+k)
    root_selection_copied=(out/'selection_decision.json').is_file()
    if root_selection_copied:require(obj(out/'selection_decision.json')==selection,'root selection exact reports_final copy')
    gate=obj(report/'admission_decision.json')
    require(gate==obj(out/'admission_decision.json'),'root bridge exact reports_final copy')
    require(gate['bridge_pass']==a['gate']['bridge_pass'] and all(gate['gates'][r]['passed']==a['gate']['gates'][r]['passed'] for r in ['F2','C2']),'independent all-six gate matches durable decision')
    require(obj(report/'continuation_decision.json')['positive_selection_unreachable']==a['gate']['current_positive_selection_unreachable']['positive_selection_unreachable'],'exact cancellation predicate matches')

    # Compare every endpoint and every own journal fleet against rebuilt rows.
    phys=rows(report/'physical_UBs.csv'); indexed={}
    for r in phys:
        key=(r['id'],r['arm'],int(r['sequence']) if r['sequence'] else None)
        require(key not in indexed,'unique same-arm physical row');indexed[key]=r
    expected=[]
    for z in allarms:
        expected.append((z,None,z['physical']))
        expected.extend((z,w['sequence'],w) for w in z['all_physical_witnesses'])
    require(len(expected)==len(phys),'all current full physical fleet rows, without omissions')
    for z,seq,ph in expected:
        p=indexed[z['id'],z['arm'],seq]
        for x,y in [('U','F'),('G','G'),('P','P')]:number(ph[x],p[y],'own physical objective component')
        require(ph['final_inventories']==json.loads(p['Y']),'own station inventory exact')
        require(fleet(ph['full_routes'])==fleet(json.loads(p['routes'])),'own complete fleet node/operation identity')
        number(max(r['duration_seconds'] for r in ph['routes']),p['maximum_duration'],'own closed physical fleet duration',1e-8)
        ownroutes=sorted(ph['routes'],key=lambda r:r['vehicle'])
        require([r['total_pickup'] for r in ownroutes]==json.loads(p['pickups']) and [r['return_load'] for r in ownroutes]==json.loads(p['return_loads']),'own total pickup/depot return loads')
        require(not boolean(p['native_first_find_exact']),'no exact native discovery claim')
        if seq is not None:
            number(ph['safe_complete_arm_available'],p['discovery_seconds_upper'],'own physical observation safe upper interval',1e-9)
            number(ph['raw_available'],p['available'],'raw original availability retained',1e-9)

    # Model and native call identities are independently read, not summary counts.
    modelmap={(z['id'],z['arm'],portable(m['path'])):m for z in allarms for m in z['model_contracts']}
    pubmodels=rows(report/'models.csv');require(len(modelmap)==len(pubmodels),'all actual saved models disclosed')
    for p in pubmodels:
        z=modelmap[p['id'],p['arm'],p['path']]
        require(z['SHA']==p['SHA'],'saved model exact hash')
        for k in ['columns','rows','quantity_columns']:require(z[k]==int(p[k]),'saved original model dimensions')
        require(z['AB_exact_rows']==int(p['frozen_A_B_rows_checked']),'all exact A/B equations disclosed')
        require(p['quantity_type']==('C' if p['arm']=='M-B' else 'I'),'actual p/d native types')
    native={(z['id'],z['arm'],n['call']):n for z in allarms for n in z['native_records']}
    pubcalls=rows(report/'native_calls.csv');require(len(native)==len(pubcalls),'all Optimize native call evidence')
    for p in pubcalls:
        n=native[p['id'],p['arm'],int(p['call'])]
        require(boolean(p['actual_Optimize']) and boolean(p['returned']),'every current native call actually returned')
        require(n['model_SHA']==p['model_SHA'] and portable(n['actual_read_native_log'])==p['native_log_path'],'actual returned native call exact model/log path')
    types=rows(report/'native_type_readbacks.csv');require(len(types)==len(native),'every native call type/log readback disclosed')
    typemap={(p['id'],p['arm'],p['log_path']):p for p in types}
    for (role,method,call),n in native.items():
        p=typemap[role,method,portable(n['actual_read_native_log'])]
        require(n['model_SHA']==p['model_SHA'] and n['native_log_SHA']==p['log_SHA'] and n['solve_kind']==p['solve_kind'],'exact native log/type source binding')
        if n['native_types'] is not None:require(n['native_types']==json.loads(p['restored_native_types']),'all pre-presolve restored domains')
    starts={(z['id'],z['arm'],portable(s['metadata_path'])):s for z in allarms for s in z['starts']}
    pubstarts=rows(report/'starts.csv');require(len(starts)==len(pubstarts),'actual submitted Starts distinct from attempted/skipped mappings')
    for p in pubstarts:
        s=starts[p['id'],p['arm'],p['start_path']]
        require(s['metadata_SHA']==p['start_sha256'] and s['values_SHA']==p['vector_sha256'] and s['model_SHA']==p['model_sha256'],'complete Start vector and exact own model bound')
        require(s['columns']==int(p['columns']) and s['rows_checked']==int(p['rows']),'all Start native columns and original rows checked')
        number(s['own_physical_U'],p['objective'],'normalized own Start physical/native objective')
        require(s['max_row_violation']<=1e-6 and float(p['maximum_absolute_residual'])<=1e-6,'all actual Start residuals within inherited tolerance')
        require(set(s['all_normalized_route_columns_checked'])=={'x','conn','p','d','mode','z','load','ord','Y','state'},'complete exact normalized own Start vector families')

    # Recompute all checkpoint windows independently and prohibit late extrapolation.
    ck=rows(report/'checkpoints.csv');ownck={(z['id'],z['arm'],c['seconds']):c for z in a['arms'] for c in z['checkpoints']}
    require(len(ck)==len(ownck),'exact actual checkpoint namespace')
    checkpoint_time_metadata_differences=0
    for p in ck:
        c=ownck[p['id'],p['arm'],int(p['seconds'])]
        require(c['observed']==boolean(p['observed']),'actual checkpoint observed/missing status')
        if c['observed']:
            for k in ['U','L','gap']:number(c[k],p[k],'independent raw checkpoint '+k)
            require(c['safe_complete_arm_available']<=c['seconds'],'no future checkpoint support')
            if abs(c['safe_complete_arm_available']-float(p['safe_complete_window_available_upper']))>1e-9:checkpoint_time_metadata_differences+=1
        else:require(p['U']==p['L']==p['gap']=='','missing checkpoint no endpoint extrapolation')

    # Safe original Fstar witness intervals only where this raw review has a certificate.
    optimal=[]
    for role in ['F2','C2','S12','B24','L48','F5','N36']:
        group=[z for z in a['arms'] if z['id']==role]
        require(max(z['L'] for z in group)<=min(z['U'] for z in group)+1e-7,'cross-arm qualified bounds no contradiction')
        certified=[z for z in group if z['certificate']]
        if not certified:continue
        star=certified[0]['U']
        require(all(abs(z['U']-star)<=1e-7 for z in certified),'reliable original Fstar consistent among actual certificates')
        for z in group:
            upper=[w['safe_complete_arm_available'] for w in z['all_physical_witnesses'] if abs(w['U']-star)<=1e-7]
            if abs(z['U']-star)<=1e-7:upper.append(z['complete_seconds'])
            optimal.append(dict(id=role,arm=z['arm'],reliable_original_Fstar=star,witnessed=bool(upper),discovery_seconds_lower=0. if upper else None,discovery_seconds_upper=min(upper) if upper else None,native_first_find_exact=False))
    puboptimal=rows(report/'optimal_witness_bounds.csv');require(len(optimal)==len(puboptimal),'Fstar absent for all uncertified roles')
    optimalmap={(z['id'],z['arm']):z for z in optimal}
    for p in puboptimal:
        z=optimalmap[p['id'],p['arm']]
        number(z['reliable_original_Fstar'],p['reliable_original_Fstar'],'independent original Fstar')
        require(z['witnessed']==boolean(p['witnessed']) and not boolean(p['native_first_find_exact']),'safe observed witness interval only')
        for k in ['discovery_seconds_lower','discovery_seconds_upper']:
            if z[k] is None:require(p[k]=='','unobserved Fstar endpoint null')
            else:number(z[k],p[k],'independent safe Fstar interval',1e-9)

    fee=a['fees'];pf=rows(report/'fees.csv')
    require(fee['paid_corrected_starts']==sum(int(p['conservative_process_starts']) for p in pf),'corrected full outer conservative starts')
    number(fee['paid_outer_seconds'],sum(float(p['outer_seconds']) for p in pf),'closed outer fees, no nested seconds',1e-9)
    require(fee['next_complete_group'] is None and fee['next_whole_group_reserved_starts']==fee['next_whole_group_reserved_seconds']==0,'post-final no fictitious next reserve')
    summary=obj(report/'summary.json')
    require(summary['formal_arms']==21 and summary['functional_qualification_arms']==3 and summary['failed_formal_arms']==0,'final summary actual arm closure counts')
    require(summary['actual_Optimize']==summary['Optimize_returned']==len(native),'final Optimize counts independently derived')
    require(summary['conservative_starts']==fee['paid_corrected_starts'],'summary corrected fees')
    number(summary['outer_solver_fee_seconds'],fee['paid_outer_seconds'],'summary actual closed outer seconds',1e-9)
    require(summary['table_rows']['physical_UBs']==len(phys) and summary['table_rows']['models']==len(pubmodels) and summary['table_rows']['starts']==len(starts),'all physical/model/Start disclosure counts')
    reporttext=data(root/'scripts/round108_report.py').decode('utf-8-sig')
    require(sha(root/'scripts/round108_report.py')=='f3d5b5cbf8ce02882afe3e4a1e7a0b11689ceeb65bf1357438c0618882902a41','review current final report writer bytes')
    for token in ['equal-capacity route normalization','24 finite normalization cases','R100 function/call-site','no performance rerun','not proof of stable generalization','ENS-C remains the default','Relative ENS dominance is not a hidden condition','No cross-instance mean','new isolated restoration']:
        require(token in reporttext,'report exact scope disclosure '+token)
    require(sha(root/'scripts/round108_reader.py')==a['bindings']['pure_current_campaign_reader_SHA'],'unchanged final primary reader source')
    require(sha(root/'scripts/round108_decisions.py')==a['bindings']['approved_current_decision_SHA'],'unchanged current decision source')
    severe=[dict(id=p['id'],control=p['control'],classification=p['classification'],severe=p['severe_regression']) for p in pairs.values() if p['classification'] in ['LOSS','MIXED']]
    mechanisms=[]
    for z in allarms:
        kinds=Counter(n['solve_kind'] for n in z['native_records'])
        mechanisms.append(dict(id=z['id'],arm=z['arm'],Optimize=len(z['native_records']),LP=kinds['LP'],CHILD_BOUND_TARGET_MIP=kinds['CHILD_BOUND_TARGET_MIP'],NEXT_LEAF_TARGET_MIP=kinds['NEXT_LEAF_TARGET_MIP'],terminal_MIP=kinds['MIP'],saved_models=len(z['model_contracts']),submitted_Starts=len(z['starts']),Start_mapping_attempts=len(z['start_attempts']),physical_journal_witnesses=z['total_physical_witnesses']))
    n36={z['arm']:{k:z[k] for k in ['U','L','gap','relative_gap','certificate','complete_seconds']} for z in a['arms'] if z['id']=='N36'}
    answer=dict(decision='ACCEPT',final_stage=a['selection']['stage'],unseen_WIN=a['selection']['unseen_WIN'],unseen_LOSS=a['selection']['unseen_LOSS'],formal_arms=21,functional_arms=3,
        endpoint_rows=24,paired_comparisons=14,physical_UB_rows=len(phys),models=len(pubmodels),actual_Optimize=len(native),returned_Optimize=len(native),submitted_Starts=len(starts),mapping_attempts=sum(len(z['start_attempts']) for z in allarms),checkpoints=len(ck),checkpoint_event_time_metadata_differences=checkpoint_time_metadata_differences,
        checkpoint_metadata_note='This reviewer retains the latest available raw event even when its numbers do not change; U/L/gap and observed/missing match all primary windows.',reliable_original_Fstar_rows=len(optimal),Fstar_intervals=optimal,
        losses=severe,N36=n36,pairs=list(pairs.values()),mechanisms=mechanisms,fees=fee,
        completed_raw_checks=a['completed_checks'],raw_audit_SHA=sha(audit_path),raw_audit_receipt_SHA=sha(audit_path.parent/'receipt.json'),raw_source_SHA=a['reviewer_script_SHA'],read_root=str(root),binary_identity=a['bindings']['binary_identity'],
        candidate_identity_SHA=a['bindings']['candidate_identity_SHA'],performance_admission_SHA=a['bindings']['performance_admission_SHA'],development_protocol_SHA=a['bindings']['development_protocol_SHA'],confirmation_protocol_SHA=a['bindings']['confirmation_protocol_SHA'],input_manifest_SHA=a['bindings']['input_manifest_SHA'],qualification_identity_SHA=a['bindings']['qualification_identity_SHA'],bridge_identity_SHA=a['bindings']['bridge_identity_SHA'],confirmation_identity_SHA=a['bindings']['confirmation_identity_SHA'],eligibility_review_SHA=a['bindings']['eligibility_review_SHA'],
        production_source_binding_count=len(a['bindings']['source_bindings']),frozen_performance_helper_binding_count=len(a['bindings']['performance_helper_bindings']),primary_reader_SHA=sha(root/'scripts/round108_reader.py'),decision_reader_SHA=sha(root/'scripts/round108_decisions.py'),report_writer_SHA=sha(root/'scripts/round108_report.py'),public_tool_SHA=sha(root/'scripts/round108_public.py'),reproduce_SHA=sha(out/'reproduce.md') if (out/'reproduce.md').is_file() else None,
        root_selection_exact_copy_present=root_selection_copied,root_selection_copy_required_before_report_pack=True,
        actual_restore_receipt_SHA=sha(root/'restore_receipt.json'),every_actual_evidence_read_in_recovered_root=True,
        public_recovery_actually_reviewed=True,public_math_rerun_pending=False,independent_engine_performance_rerun=False,production_algorithm_change=False,default_ENS_changed=False,broad_performance_stability_proved=False)
    decision='ACCEPT'
except Exception as e:
    error=type(e).__name__+': '+str(e);answer['traceback']=traceback.format_exc()
answer.update(decision=decision,error=error,completed_crosschecks=checks,source_SHA=source,read_bindings=reads,
    Optimize=0,LP_solve=0,native_environment=0,compiler=0)
write(dest/'crosscheck.json',answer)
write(dest/'receipt.json',dict(actual_command=command,explicit_read_root=str(root),source_SHA=source,exit_code=0 if decision=='ACCEPT' else 1,decision=decision,error=error,seconds=time.perf_counter()-tick,crosscheck_SHA=sha(dest/'crosscheck.json'),Optimize=0,LP_solve=0,native_environment=0,compiler=0))
print(json.dumps(dict(decision=decision,error=error,checks=checks,Optimize=answer.get('actual_Optimize'),models=answer.get('models'),physical_UBs=answer.get('physical_UB_rows'),starts=answer.get('submitted_Starts'),stage=answer.get('final_stage')),ensure_ascii=False),flush=True)
if decision!='ACCEPT':sys.exit(1)
